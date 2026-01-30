#!/usr/bin/env python

from typing import Dict, List, Optional

import json
from datetime import date, datetime

import pandas as pd


def parse_date(value: Optional[str]) -> date:
    if isinstance(value, date):
        return value
    if value is None:
        raise ValueError("Cannot parse None as date")
    return datetime.strptime(value, "%Y-%m-%d").date()


def calculate_exit_fee(active_exit_fee, principal_paid, loan_amount):

    our_share_of_fee = 1.0
    if('CM_FEE_SHARE__C' in active_exit_fee.keys()):
        our_share_of_fee = active_exit_fee['CM_FEE_SHARE__C']/100.0
        
    
    if('CM_CONDITIONAL_EXIT_FEE_REDUCTION__C' in active_exit_fee.keys() and 'CM_EXIT_FEE_REDUCTION_CONDITION_MET__C' in active_exit_fee.keys() \
      and active_exit_fee['CM_CONDITIONAL_EXIT_FEE_REDUCTION__C'] and active_exit_fee['CM_EXIT_FEE_REDUCTION_CONDITION_MET__C']):
        #conditional reduction is configured and is now met
        print('Exit Fee Reduction being executed')
        reduced_perc_provided = 'CM_CONDITIONAL_EXIT_FEE_PERCENTAGE__C' in active_exit_fee.keys()
        reduced_amt_provided = 'CM_CONDITIONAL_EXIT_FEE_AMOUNT__C' in active_exit_fee.keys()

        reduced_perc = active_exit_fee['CM_CONDITIONAL_EXIT_FEE_PERCENTAGE__C']/100
        reduced_amt = active_exit_fee['CM_CONDITIONAL_EXIT_FEE_AMOUNT__C']
        
        if(reduced_perc_provided and not reduced_amt_provided):
            return principal_paid * reduced_perc * our_share_of_fee
        elif(not reduced_perc_provided and reduced_amt_provided):
            return reduced_amt * our_share_of_fee
        elif(reduced_perc_provided and reduced_amt_provided):
            if(reduced_perc_provided != 0.0):
                return principal_paid * reduced_perc * our_share_of_fee
            else:
                return reduced_amt * our_share_of_fee
            
    else:

        perc = None
        amt = None
        if('LLC_BI__PERCENTAGE__C' in active_exit_fee.keys()):
            perc = active_exit_fee['LLC_BI__PERCENTAGE__C']/100.0

        if('LLC_BI__AMOUNT__C' in active_exit_fee.keys()):
            amt = active_exit_fee['LLC_BI__AMOUNT__C']
            

        print(f"++++++++ {principal_paid} ++++++++ {amt}++++++++ {our_share_of_fee}++++++++") 
        if(active_exit_fee['LLC_BI__CALCULATION_TYPE__C'] == 'Percentage'):
            return principal_paid * perc * our_share_of_fee
        else: 
            return (principal_paid/loan_amount) * amt * our_share_of_fee




def process_exit_fees(stage1, exit_fee_schedule, as_of_date, loan_terms):

    if(not exit_fee_schedule or len(exit_fee_schedule) == 0):
        return

    
    if 'exit_fee_due_at_start_of_next_period' not in stage1.columns:
        stage1['exit_fee_due_at_start_of_next_period'] = 0.0  # create empty column first
    if 'cummulative_unpaid_exit_fee_due_at_start_of_next_period' not in stage1.columns:
        stage1['cummulative_unpaid_exit_fee_due_at_start_of_next_period'] = 0.0  # create empty column first
    if 'all_fees_due' not in stage1.columns:
        stage1['all_fees_due'] = 0.0  # create empty column first
        
        
    closing_date = parse_date(loan_terms['LLC_BI__CLOSEDATE__C'])
    maturity_date = parse_date(loan_terms['LLC_BI__MATURITY_DATE__C'])
    loan_amount = loan_terms['LLC_BI__AMOUNT__C']
    
    active_exit_fee = None
    if(not as_of_date): # at underwriting
        
        as_of_date = maturity_date # will mature - for underwriting
        for exit_fee in exit_fee_schedule:
            
            if('CM_FEE_DATE__C' in exit_fee.keys()):
                start_date = parse_date(exit_fee['CM_FEE_DATE__C'])            
            else:
                start_date = closing_date
        
            if('CM_END_DATE__C' in exit_fee.keys()):
                end_date = parse_date(exit_fee['CM_END_DATE__C'])            
            else:
                end_date = maturity_date

            if(start_date <= as_of_date and as_of_date <= end_date):
                active_exit_fee = exit_fee
                break
        
        cal_type = active_exit_fee['LLC_BI__CALCULATION_TYPE__C']

        # when_payable_whole_list = ['Prepayment in Full','Repayment in Full','Partial Prepayment (Including Amortization)','Partial Prepayment (Excluding Amortization)']
        # when_payable_unselected = active_exit_fee['CM_EXIT_FEE_PAYABLE_UPON__C']
        # when_payable = [payable for payable in when_payable_whole_list if payable not in when_payable_unselected]
        when_payable =  active_exit_fee['CM_EXIT_FEE_PAYABLE_UPON__C'].split(';')

        #unlike closing fee - which will be paid on a fixed day (closing date) and draw fees, which will be paid
        #depending on when borrowers decide to draw, which cannot be known in advance - the exit fees are paid 
        # when principle is paid (either each month) or at the end once. So for exit fees we will have to 
        #include the value in the invoice - so we are going to track exit fee as "due_at_start_of_next_period" format
        index_when_principal_due_next_month = stage1[stage1['principal_due_at_start_of_next_period'] > 0].index

        #the if statements in the for loop below are arranged in a specific priotity sequence. If one of then is triggered it will 
        #automatically cover the calculation for other values written in if statements below it. We cannot have two conditions contribute
        #it will cause repeted exit fee accrual
        at_least_one_payable_event_already_triggered = False
        for payable_event in when_payable:

            last_row_index = stage1.shape[0]-1
            
            if(payable_event == 'Partial Prepayment (Including Amortization)' and not at_least_one_payable_event_already_triggered):
                print('Partial Prepayment (Including Amortization)')
                at_least_one_payable_event_already_triggered = True
                for i in index_when_principal_due_next_month:
                    
                    ef = calculate_exit_fee(active_exit_fee, stage1.loc[i, 'principal_due_at_start_of_next_period'], loan_amount)
                    stage1.loc[i, 'exit_fee_due_at_start_of_next_period'] = ef + stage1.loc[i, 'exit_fee_due_at_start_of_next_period']
                    stage1.loc[i, 'all_fees_due'] = stage1.loc[i, 'all_fees_due'] + ef
                

            elif(payable_event == 'Partial Prepayment (Excluding Amortization)' and not at_least_one_payable_event_already_triggered):
                print('Partial Prepayment (Excluding Amortization)')
                at_least_one_payable_event_already_triggered = True
                for i in index_when_principal_due_next_month:
                    
                    ef = calculate_exit_fee(active_exit_fee, stage1.loc[i, 'principal_due_at_start_of_next_period'], loan_amount)
                    stage1.loc[i, 'cummulative_unpaid_exit_fee_due_at_start_of_next_period'] =  ef + \
                                                                                                 stage1.loc[i-1, 'cummulative_unpaid_exit_fee_due_at_start_of_next_period']
                
                stage1.loc[last_row_index, 'all_fees_due'] = stage1.loc[last_row_index, 'all_fees_due'] + stage1.loc[last_row_index, 'cummulative_unpaid_exit_fee_due_at_start_of_next_period']
            
            elif((payable_event == 'Repayment in Full' or payable_event == 'Prepayment in Full') and not at_least_one_payable_event_already_triggered):
                print('Full Payment triggered')
                at_least_one_payable_event_already_triggered = True
                
                ef = calculate_exit_fee(active_exit_fee, stage1.loc[last_row_index, 'principal_due_at_start_of_next_period'], loan_amount)
                stage1.loc[last_row_index, 'exit_fee_due_at_start_of_next_period'] = ef + stage1.loc[last_row_index, 'exit_fee_due_at_start_of_next_period']
                stage1.loc[last_row_index, 'all_fees_due'] =  stage1.loc[last_row_index, 'all_fees_due'] + ef


def process_closing_fees(stage1: pd.DataFrame, closing_fees: List[Dict]) -> None:
    if (not closing_fees):
        stage1["closing_fee_due"] = 0.0
        return
    
    total_closing_fee = 0
    total_closing_fee = sum(fee.get("LLC_BI__AMOUNT__C", 0) for fee in closing_fees if 'LLC_BI__AMOUNT__C' in fee.keys())


    if "closing_fee_due" not in stage1.columns:
        stage1["closing_fee_due"] = 0.0
    stage1.at[stage1.index[0], "closing_fee_due"] += total_closing_fee

    if "all_fees_due" not in stage1.columns:
        stage1["all_fees_due"] = 0.0
    stage1.at[stage1.index[0], "all_fees_due"] += total_closing_fee


def process_draw_fees(stage1: pd.DataFrame, draw_fees: List[Dict], total_loan_amount: float) -> None:
    if( not draw_fees ):
        stage1["draw_fee_due"] = 0.0
        return

    if "draw_fee_due" not in stage1.columns:
        stage1["draw_fee_due"] = 0.0
    if "all_fees_due" not in stage1.columns:
        stage1["all_fees_due"] = 0.0

    draw_rows = stage1.index[stage1.get("is_draw", 0) == 1]
    for draw_fee in draw_fees:
        fee_amount = draw_fee.get("LLC_BI__AMOUNT__C", 0)
        for idx in draw_rows:
            amount_drawn = float(stage1.at[idx, "amount_drawn"])
            proportionate_fee = (amount_drawn / total_loan_amount) * fee_amount
            stage1.at[idx, "draw_fee_due"] += proportionate_fee
            stage1.at[idx, "all_fees_due"] += proportionate_fee


def process_modification_fees(stage1: pd.DataFrame, modification_fees: List[Dict]) -> None:
    if(not modification_fees ):
        return

    if "modification_fee_due" not in stage1.columns:
        stage1["modification_fee_due"] = 0.0
    if "all_fees_due" not in stage1.columns:
        stage1["all_fees_due"] = 0.0

    for fee in modification_fees:
        fee_date = parse_date(fee.get("CM_FEE_DATE__C", stage1.at[stage1.index[0], "accrual_start_date"]))
        amount = fee.get("LLC_BI__AMOUNT__C", 0.0)

        matching_rows = stage1.index[
            pd.to_datetime(stage1["accrual_start_date"]).dt.date == fee_date
        ]
        if len(matching_rows) == 0:
            continue

        idx = matching_rows[0]
        stage1.at[idx, "modification_fee_due"] += amount
        stage1.at[idx, "all_fees_due"] += amount

def form_fee_and_draw_buckets(stage_with_fees, closing_fees, draw_fees, loan_terms):
    all_drawable_fees = []
    all_drawable_fees.extend(closing_fees)
    all_drawable_fees.extend(draw_fees)
    total_draw_fee_from_loan_terms = 0
    fees = [fee for fee in all_drawable_fees if 'LLC_BI__AMOUNT__C' in fee.keys()]
    for f in fees:
        total_draw_fee_from_loan_terms += f['LLC_BI__AMOUNT__C']

    fee_to_use = total_draw_fee_from_loan_terms
    if(round(total_draw_fee_from_loan_terms) != round(stage_with_fees['draw_fee_due'].sum()) + round(stage_with_fees['closing_fee_due'].sum())):
        print("Warning: Seems like all of draw fees were not assessed. Will use the total of draw_fee_due")
        fee_to_use = round(stage_with_fees['draw_fee_due'].sum()) + round(stage_with_fees['closing_fee_due'].sum())

    total_loan_amount = loan_terms['LLC_BI__AMOUNT__C']
    fee_fraction =  fee_to_use/total_loan_amount
    total_loan_amount, fee_to_use, fee_fraction


    draw_details_columns = [c for c in stage_with_fees.columns if c.startswith('draw:') and ':details' in c] 

    for details_column_name in draw_details_columns:

        if('capitalized interest' in details_column_name.lower()):
            funded_col_name = details_column_name.replace('details', 'amount')
            stage_with_fees[funded_col_name] = stage_with_fees[funded_col_name].fillna(0)

            
            total_fee = (stage_with_fees[funded_col_name] * fee_fraction).sum()

            unfunded_col_name = details_column_name.replace('details', 'unfunded')
            stage_with_fees[unfunded_col_name] = stage_with_fees[unfunded_col_name].fillna(0)

            remaining_fee = total_fee
            stage_with_fees[funded_col_name+":adjusted"]= stage_with_fees[funded_col_name]


            #the whole point of this loop is to figure out how many last amount values need to be adjusted to take out the 
            #total fee - remember we are just adjusting the last draw amount (or the last and second last if last is not)
            #sufficient - or third last, second last and last ..if ... not sufficient
            for i in reversed(stage_with_fees.index):
                if stage_with_fees[funded_col_name+":adjusted"].loc[i] <= 0:
                    continue
                deduction = min(stage_with_fees[funded_col_name+":adjusted"].loc[i], remaining_fee)
                stage_with_fees.loc[i, funded_col_name+":adjusted"] -= deduction
                remaining_fee -= deduction
                if remaining_fee <= 1e-4:
                    break

            #reset funded amount column
            stage_with_fees[funded_col_name] = stage_with_fees[funded_col_name+":adjusted"]
            stage_with_fees.drop(funded_col_name+":adjusted", axis=1, inplace=True)
            
            #create fee column
            fee_column_name = funded_col_name.replace('amount', 'fee')
            stage_with_fees[fee_column_name] = stage_with_fees[funded_col_name] * fee_fraction

            #adjust unfunded column
            stage_with_fees[unfunded_col_name] = stage_with_fees[unfunded_col_name] * (1-fee_fraction)

            #create fee-unfunded column
            fee_unfunded_column_name = funded_col_name.replace('amount', 'fee-unfunded')
            stage_with_fees[fee_unfunded_column_name] = total_fee
            stage_with_fees[fee_unfunded_column_name] = stage_with_fees[fee_unfunded_column_name] - stage_with_fees[fee_column_name].cumsum()
            
        
    
        else: #everything other than capitalized interest
            funded_col_name = details_column_name.replace('details', 'amount')
            unfunded_col_name = details_column_name.replace('details', 'unfunded')
            stage_with_fees[funded_col_name] = stage_with_fees[funded_col_name].fillna(0)
            stage_with_fees[unfunded_col_name] = stage_with_fees[unfunded_col_name].fillna(0)
        
            fee_column_name = funded_col_name.replace('amount','fee')
            fee_unfunded_col = unfunded_col_name.replace('unfunded','fee-unfunded')
            print(fee_column_name)
            
            stage_with_fees[fee_column_name] = stage_with_fees[funded_col_name] * fee_fraction
            stage_with_fees[fee_unfunded_col] = stage_with_fees[unfunded_col_name] * fee_fraction
        
            stage_with_fees[funded_col_name] = stage_with_fees[funded_col_name] * (1-fee_fraction)
            stage_with_fees[unfunded_col_name] = stage_with_fees[unfunded_col_name] * (1-fee_fraction)








def add_fees(loan_terms: Dict, stage1: pd.DataFrame) -> pd.DataFrame:
    """
    Append fee calculations to the Stage 1 schedule.

    Args:
        loan_terms: Loan metadata dictionary containing fee details.
        stage1: Stage 1 dataframe produced by Step 5.

    Returns:
        DataFrame with fee columns added (`stage1_with_fees` equivalent).
    """
    stage_with_fees = stage1.copy()
    fees = loan_terms.get("FEE_DETAILS", [])

    closing_fees = [
        fee
        for fee in fees
        if fee.get("LLC_BI__FEE_TYPE__C") == "Closing Fee"
        and fee.get("LLC_BI__PAID_AT_CLOSING__C") == "Funded at Closing"
    ]
    draw_fees = [
        fee
        for fee in fees
        if fee.get("LLC_BI__FEE_TYPE__C") == "Closing Fee"
        and fee.get("LLC_BI__PAID_AT_CLOSING__C") == "Funded at Draw"
    ]
    modification_fees = [
        fee
        for fee in fees
        if fee.get("LLC_BI__FEE_TYPE__C") == "Closing Fee"
        and fee.get("LLC_BI__PAID_AT_CLOSING__C") == "Funded at Modification"
    ]
    exit_fees = [fee for fee in fees if fee.get("LLC_BI__FEE_TYPE__C") == "Exit Fee"]
    print(f":::::::::::: EXIT FEES :::::::::: {exit_fees} ")

    process_closing_fees(stage_with_fees, closing_fees)
    process_draw_fees(stage_with_fees, draw_fees, loan_terms.get("LLC_BI__AMOUNT__C", 1.0))
    process_modification_fees(stage_with_fees, modification_fees)
    process_exit_fees(stage_with_fees, exit_fees, None, loan_terms)

    form_fee_and_draw_buckets(stage_with_fees, closing_fees, draw_fees, loan_terms)

    return stage_with_fees
