#!/usr/bin/env python

import math
import re
import warnings
from typing import Any, Dict, List

from simple_salesforce import Salesforce

import data_loader_utils as dlu
import time

# Suppress the specific openpyxl warning emitted during workbook imports.
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Salesforce OAuth client credentials. These should eventually come from a secure store.
_CREDS = {
    "client_id": "3MVG9H_KVs6V9LiP4AGwr.K0ufOjN3I1poplR_fK9cg930ILmT47atYSm2YVbtP5mMQmL2IjW6L.RaERxoL.e",
    "client_secret": "FA512A88FAC1F97FAB9BC003158A8585589B9A9F3540ED9C7BC83627002E75FB",
    "client_url": "https://locustpoint.my.salesforce.com/services/oauth2/token",
}

def dict_keys_upper(d):
    if isinstance(d, dict):
        return {k.upper(): dict_keys_upper(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [dict_keys_upper(i) for i in d]
    else:
        return d



def remove_none(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return a new list where None/NaN values have been removed from dictionary records."""
    cleaned_records = []
    for record in records:
        cleaned_record = {
            key: value
            for key, value in record.items()
            if value is not None and not (isinstance(value, float) and math.isnan(value))
        }
        cleaned_records.append(cleaned_record)
    return cleaned_records


def _connect() -> Salesforce:
    """Create a Salesforce connection using predefined credentials."""
    return dlu.connect(_CREDS)


def _filter_dataframe(df, column: str, value: str):
    """Filter a DataFrame by column/value if the frame is non-empty."""
    if df.empty:
        return df
    return df[df[column] == value].copy()


def _records(df) -> List[Dict[str, Any]]:
    """Convert a DataFrame to cleaned dictionary records."""
    if df.empty:
        return []
    return remove_none(df.to_dict("records"))


def get_loan_terms(loan_id: str) -> Dict[str, Any]:
    """
    Load Salesforce data for the given loan and return the assembled terms payload.

    Args:
        loan_id: Salesforce loan identifier.

    Returns:
        Dictionary mirroring the legacy `loan_terms.json` structure.

    Raises:
        ValueError: If the requested loan cannot be located.
    """
    if not loan_id:
        raise ValueError("loan_id must be provided.")

    sf = _connect()

    # Loan core terms.
    loans_df = dlu.get_sf_data(
        sf,
        "LLC_BI__LOAN__c",
        [
            "ID",
            "NAME",
            "LLC_BI__Amount__c",
            "LLC_BI__Maturity_Date__c",
            "LLC_BI__CloseDate__c",
            "LLC_BI__First_Payment_Date__c",
            "LLC_BI__Term_Months__c",
            "LLC_BI__Amortized_Term_Months__c",
            "LLC_BI__Prepayment_Penalty__c",
            "cm_Prepayment_Minimal_Interest_Months__c",
            "LLC_BI__Prepayment_Penalty_Description__c",
            "LLC_BI__Funding_at_Close__c",
            "LLC_BI__ParentLoan__c",
        ],
    )
    loan_row = _records(_filter_dataframe(loans_df, "ID", loan_id))
    if not loan_row:
        raise ValueError(f"Loan {loan_id} not found.")

    # Handle A/B-Tranche logic for parent loan amounts
    loan_terms = loan_row[0]
    loan_name = loan_terms.get("NAME", "")

    # Check if loan name contains A-Tranche or B-Tranche (fuzzy match for spaces/hyphens)
    # Pattern matches variations like: "A-Tranche", "A Tranche", "ATranche", "B-Tranche", etc.
    tranche_pattern = r'[AB][\s-]*[Tt]ranche'
    is_tranche_loan = re.search(tranche_pattern, loan_name)

    if is_tranche_loan and loan_terms.get("LLC_BI__PARENTLOAN__C"):
        parent_loan_id = loan_terms["LLC_BI__PARENTLOAN__C"]

        # Fetch parent loan amount
        parent_loan_df = dlu.get_sf_data(
            sf,
            "LLC_BI__LOAN__c",
            ["ID", "LLC_BI__Amount__c"],
        )
        parent_loan_row = _records(_filter_dataframe(parent_loan_df, "ID", parent_loan_id))

        if parent_loan_row and parent_loan_row[0].get("LLC_BI__AMOUNT__C"):
            parent_amount = parent_loan_row[0]["LLC_BI__AMOUNT__C"]
            this_loan_amount = loan_terms.get("LLC_BI__AMOUNT__C", 0)

            # Calculate factor: parent_amount / this_loan_amount
            if this_loan_amount and this_loan_amount != 0:
                loan_terms["A_B_AMOUNT_FACTOR"] = parent_amount / this_loan_amount
            else:
                loan_terms["A_B_AMOUNT_FACTOR"] = 1
        else:
            loan_terms["A_B_AMOUNT_FACTOR"] = 1
    else:
        # For all other loans, set factor to 1
        loan_terms["A_B_AMOUNT_FACTOR"] = 1

    # Pricing rates.
    pricing_rate_df = dlu.get_sf_data(
        sf,
        "LLC_BI__Pricing_Rate_Component__c",
        [
            "cm_Partial_Period_Interst_Accrual_Method__c",
            "cm_Interest_Accrual_Method__c",
            "cm_Accrued_Rate__c",
            "LLC_BI__All_In_Rate__c",
            "LLC_BI__Applied_Loan_Percentage__c",
            "LLC_BI__Applied_Rate__c",
            "LLC_BI__Auto_Pay_Rate_Discount__c",
            "LLC_BI__Calculated_Monthly_Interest_Rate__c",
            "LLC_BI__Comments__c",
            "LLC_BI__Effective_Date__c",
            "LLC_BI__Employee_Rate_Discount__c",
            "LLC_BI__End_Date__c",
            "LLC_BI__Index__c",
            "LLC_BI__Index_Spread_Type__c",
            "LLC_BI__Initial_Adjustment_Rate_Cap__c",
            "LLC_BI__Interest_Rate_Adjustment_Frequency__c",
            "LLC_BI__Interest_Rate_Adjustment_Unit__c",
            "LLC_BI__Interest_Rate_Type__c",
            "LLC_BI__Is_Fixed__c",
            "LLC_BI__Is_Swap__c",
            "LLC_BI__Lifetime_Rate_Cap__c",
            "cm_Loan__c",
            "LLC_BI__lookupKey__c",
            "LLC_BI__Next_Interest_Rate_Change_Date__c",
            "LLC_BI__Periodic_Rate_Cap__c",
            "LLC_BI__Pricing_Stream__c",
            "LLC_BI__Rate__c",
            "LLC_BI__Rate_Adjustment__c",
            "LLC_BI__Rate_Ceiling__c",
            "LLC_BI__Rate_Floor__c",
            "LLC_BI__Sequence__c",
            "LLC_BI__Spread__c",
            "LLC_BI__Term_Length__c",
            "LLC_BI__Term_Unit__c",
            "cm_Minimum_Exit_Multiple__c",
            "cm_Maximum_Exit_IRR__c",
        ],
    )
    pricing_rate_filtered = _filter_dataframe(pricing_rate_df, "CM_LOAN__C", loan_id)

    # Pricing streams.
    pricing_stream_df = dlu.get_sf_data(
        sf,
        "LLC_BI__Pricing_Stream__c",
        [
            "ID",
            "LLC_BI__LOAN__C",
            "LLC_BI__Effective_Date__c",
            "LLC_BI__Term_Length__c",
            "LLC_BI__Term_Unit__c",
            "LLC_BI__Is_Payment_Stream__c",
            "LLC_BI__Is_Rate_Stream__c",
            "LLC_BI__Is_Template__c",
            "LLC_BI__Period_Type__c",
            "LLC_BI__Pricing_Option__c",
        ],
    )
    pricing_stream_filtered = _filter_dataframe(
        pricing_stream_df, "LLC_BI__LOAN__C", loan_id
    )

    overall_pricing_df = pricing_rate_filtered.merge(
        pricing_stream_df,
        left_on="LLC_BI__PRICING_STREAM__C",
        right_on="ID",
        how="left",
    )
    overall_pricing_filtered = _filter_dataframe(
        overall_pricing_df, "CM_LOAN__C", loan_id
    )

    # Payment streams.
    payments_df = dlu.get_sf_data(
        sf,
        "LLC_BI__Pricing_Payment_Component__c",
        [
            "LLC_BI__Count__c",
            "cm_Amortized_Term_Months__c",
            "LLC_BI__Includes_Interest__c",
            "LLC_BI__Includes_Principal__c",
            "LLC_BI__Interest_Frequency__c",
            "LLC_BI__Interest_Unit__c",
            "LLC_BI__Interest_Value__c",
            "LLC_BI__Rate_Stream__c",
            "LLC_BI__Amount__c",
            "LLC_BI__Principal_As_Percent__c",
            "LLC_BI__Base_Principal_Payment_On__c",
            "LLC_BI__Capitalized_Interest_Day_Of_Month__c",
            "LLC_BI__Capitalized_Interest_Effective_Date__c",
            "LLC_BI__Capitalized_Interest_Frequency__c",
            "LLC_BI__Comments__c",
            "LLC_BI__Effective_Date__c",
            "LLC_BI__End_Date__c",
            "LLC_BI__Has_Capitalized_Interest__c",
            "LLC_BI__Interest_Payment_Frequency__c",
            "LLC_BI__Is_Fixed__c",
            "cm_Loan__c",
            "LLC_BI__lookupKey__c",
            "LLC_BI__Maximum_Payment__c",
            "LLC_BI__Minimum_Payment__c",
            "Name",
            "LLC_BI__Number_Of_Payments__c",
            "LLC_BI__Frequency__c",
            "LLC_BI__Payment_Type__c",
            "LLC_BI__Percent_Of_Total_Loan_Amount__c",
            "LLC_BI__Pricing_Stream__c",
            "LLC_BI__Principal_Amount__c",
            "LLC_BI__Principal_Payment_Frequency__c",
            "LLC_BI__Sequence__c",
            "LLC_BI__Skip_Months__c",
            "LLC_BI__Skip_Stream_Target_Index__c",
            "LLC_BI__Term_Length__c",
            "LLC_BI__Term_Unit__c",
            "LLC_BI__Type__c",
        ],
    )
    payments_filtered = _filter_dataframe(payments_df, "CM_LOAN__C", loan_id)

    overall_payments_df = payments_filtered.merge(
        pricing_stream_df,
        left_on="LLC_BI__PRICING_STREAM__C",
        right_on="ID",
        how="left",
    )
    overall_payments_filtered = _filter_dataframe(
        overall_payments_df, "CM_LOAN__C", loan_id
    )

    # Fees and draws.
    fees_and_draws_df = dlu.get_sf_data(
        sf,
        "LLC_BI__Fee__c",
        [
            "ID",
            "NAME",
            "LLC_BI__Loan__c",
            "LLC_BI__Status__c",
            "LLC_BI__Fee_Type__c",
            "LLC_BI__Amount__c",
            "cm_Fee_Date__c",
            "cm_End_Date__c",
            "cm_Draw_Date_Deadline__c",
            "cm_Draw_Frequency__c",
            "cm_Draw_Reset_Type__c",
            "LLC_BI__Paid_at_Closing__c",
            "LLC_BI__Percentage__c",
            "LLC_BI__Calculation_Type__c",
            "cm_Exit_Fee_Payable_Upon__c",
            "LLC_BI__Basis_Source__c",
            "cm_Conditional_Exit_Fee_Reduction__c",
            "cm_Exit_Fee_Reduction_Condition_Met__c",
            "cm_Conditional_Exit_Fee_Percentage__c",
            "cm_Conditional_Exit_Fee_Amount__c",
            "cm_Fee_Share__c",
        ],
    )
    fees_and_draws_filtered = _filter_dataframe(
        fees_and_draws_df, "LLC_BI__LOAN__C", loan_id
    )

    # Exclude Equity Waterfall fee types from fees and reserves
    equity_waterfall_mask = fees_and_draws_filtered["LLC_BI__FEE_TYPE__C"].fillna("").str.contains(
        "Equity Waterfall"
    )
    fees_and_draws_filtered = fees_and_draws_filtered[~equity_waterfall_mask].copy()

    fees_mask = fees_and_draws_filtered["LLC_BI__FEE_TYPE__C"].fillna("").str.contains(
        "Fee"
    )
    fees_df = fees_and_draws_filtered[fees_mask].copy()
    draws_df = fees_and_draws_filtered[~fees_mask].copy()

    loan_terms["PRICING_DETAILS"] = _records(overall_pricing_filtered)

    # Convert CM_MAXIMUM_EXIT_IRR__C from percentage (e.g., 16.5) to decimal (e.g., 0.165)
    for pricing in loan_terms["PRICING_DETAILS"]:
        if "CM_MAXIMUM_EXIT_IRR__C" in pricing and pricing["CM_MAXIMUM_EXIT_IRR__C"] is not None:
            pricing["CM_MAXIMUM_EXIT_IRR__C"] = pricing["CM_MAXIMUM_EXIT_IRR__C"] / 100

    loan_terms["PAYMENT_DETAILS"] = _records(overall_payments_filtered)
    loan_terms["FEE_DETAILS"] = _records(fees_df)
    loan_terms["DRAW_DETAILS"] = _records(draws_df)

    #remove Funded At Close
    loan_terms['DRAW_DETAILS'] = [draw for draw in loan_terms['DRAW_DETAILS'] if (draw.get('LLC_BI__PAID_AT_CLOSING__C', '') not in ['Funded at Closing'])] 

    #make accomodations for acceptably incomplete data in Funded at Modification
    for draw in loan_terms['DRAW_DETAILS']:
        if((draw.get('LLC_BI__PAID_AT_CLOSING__C', '')) == 'Funded at Modification' and 'CM_FEE_DATE__C' in draw):
            draw['CM_END_DATE__C'] = draw['CM_FEE_DATE__C']
    

    now = int(time.time())
    funded_at_close_made_up_draw_stream = {'ID': f'MADE_UP_ID_{now}',
                                        'NAME':f'MADE_UP_NAME_{now}',
                                        'LLC_BI__LOAN__C': f"{loan_terms['ID']}",
                                        'LLC_BI__STATUS__C': 'Active',
                                        'LLC_BI__FEE_TYPE__C': 'Funded At Closing',
                                        'CM_DRAW_FREQUENCY__C': 'Monthly',
                                        'CM_DRAW_RESET_TYPE__C': 'Skip',
                                        'LLC_BI__CALCULATION_TYPE__C': 'Flat Amount',
                                        'CM_CONDITIONAL_EXIT_FEE_REDUCTION__C': False,
                                        'CM_EXIT_FEE_REDUCTION_CONDITION_MET__C': False}
    if('LLC_BI__FUNDING_AT_CLOSE__C' in loan_terms):
       funded_at_close_made_up_draw_stream['LLC_BI__AMOUNT__C'] = loan_terms['LLC_BI__FUNDING_AT_CLOSE__C']
    if('LLC_BI__CLOSEDATE__C' in loan_terms):
        funded_at_close_made_up_draw_stream['CM_FEE_DATE__C'] =  loan_terms['LLC_BI__CLOSEDATE__C']
        funded_at_close_made_up_draw_stream['CM_END_DATE__C'] =loan_terms['LLC_BI__CLOSEDATE__C']

    loan_terms['DRAW_DETAILS'].append(funded_at_close_made_up_draw_stream)

    return dict_keys_upper(loan_terms)



def get_loan_list() -> Dict[str, str]:
    sf = _connect()
    df = dlu.get_sf_data( sf, "LLC_BI__LOAN__c", [ "ID", "NAME","LLC_BI__lookupKey__c","LLC_BI__STATUS__C","LLC_BI__STAGE__C","LLC_BI__Product__c"])


    df = df[
        # (df["ID"].isin(['a0ial0000050WTFAA2', 'a0iVy000009KxJhIAK', 'a0ial000004muX3AAI'])) #&
        (~df['LLC_BI__STATUS__C'].isin(['Declined', 'Withdrawn', 'Superseded'])) &
        (df['LLC_BI__STAGE__C'] != 'Complete') &
        (df['LLC_BI__PRODUCT__C'] != 'Main')

    ]

    df = df.sort_values(by='NAME', ascending=True)
    return df.to_dict('records')
