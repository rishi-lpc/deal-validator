#!/usr/bin/env python

from typing import Any, Dict

import json
from datetime import datetime

import numpy as np
import numpy_financial as npf
import pandas as pd

capitalized_draw_unfunded_bucket: Dict[str, float] = {}


def parse_date(value: Any):
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d").date()
    return value


def apply_row_index_for_principal_calc(pricing_schedule: pd.DataFrame) -> None:
    mask = (pricing_schedule["calculate_principal_for_next_month"] == 1) & (
        pricing_schedule["payment_type_next_month"] == "Principal & Interest"
    )
    pricing_schedule["principal_payment_index"] = 0
    pricing_schedule.loc[mask, "principal_payment_index"] = range(1, mask.sum() + 1)


def cumprinc(rate, nper, pv, start_period, end_period, when=0, a_b_factor=1):
    # For A/B tranche loans, calculate payment based on combined amount
    adjusted_pv = pv * a_b_factor
    payment = -npf.pmt(rate, nper, adjusted_pv, 0, when)
    # Prorate payment back to this tranche's amount
    return payment / a_b_factor


def calc_draw_amount(row, principal_due_at_start_of_period, interest_due_at_start_of_period, cummulative_pik_amount_due):
    # dynamic draw calc - draw must be calculated before interest and principals are calculated

        #identfy columns that are of format draw:<draw_type>:details
        col_starting_with_draw = [type for type in row.keys() if type.startswith('draw:')]
        col_ending_with_details = [type for type in col_starting_with_draw if type.endswith(':details')]
        draw_types = [d.split(':')[1].split('[')[0].strip() for d in col_ending_with_details]
    
        for i,draw_type in enumerate(draw_types):
            corresponding_amount_column_name = col_ending_with_details[i].replace('details','amount')
            corresponding_unfunded_column_name = col_ending_with_details[i].replace('details','unfunded')
            actual_column_name = col_ending_with_details[i]

            if(row['is_draw'] == 1):
                
                if(corresponding_unfunded_column_name not in capitalized_draw_unfunded_bucket.keys()):
                    capitalized_draw_unfunded_bucket[corresponding_unfunded_column_name] = row[corresponding_unfunded_column_name]
                     
                #get the draw_details json
                draw_details = row[actual_column_name]
                
                if('Capitalized Interest' in actual_column_name):
                    
                    if(pd.isna(draw_details)):
                        # this will happen when draw is happening from a different bucket and not from this current bucket
                        row[corresponding_unfunded_column_name] = capitalized_draw_unfunded_bucket[corresponding_unfunded_column_name]                    
                    else:
                        draw_details = json.loads(draw_details)
                        #account = draw_details['ACCOUNT']
                        
                        if('CM_DRAW_RESET_TYPE__C' in draw_details.keys() and draw_details['CM_DRAW_RESET_TYPE__C'] == 'Push to Deadline' and parse_date(draw_details['CM_DRAW_DATE_DEADLINE__C']) == row['accrual_start_date'].date()):
                            row['amount_drawn'] = row['amount_drawn'] + capitalized_draw_unfunded_bucket[corresponding_unfunded_column_name]
                            row[corresponding_amount_column_name] = capitalized_draw_unfunded_bucket[corresponding_unfunded_column_name]
                            row[corresponding_unfunded_column_name] = 0
                            
                        elif('CM_DRAW_RESET_TYPE__C' in draw_details.keys() and draw_details['CM_DRAW_RESET_TYPE__C'] == 'Push to End Date' and parse_date(draw_details['END_DATE']) == row['accrual_start_date'].date()):
                            row['amount_drawn'] = row['amount_drawn'] + capitalized_draw_unfunded_bucket[corresponding_unfunded_column_name]
                            row[corresponding_amount_column_name] = capitalized_draw_unfunded_bucket[corresponding_unfunded_column_name]
                            row[corresponding_unfunded_column_name] = 0
                            
                        else:

                            paid_out_of_capitalized_interest_bucket = interest_due_at_start_of_period
                            if(capitalized_draw_unfunded_bucket[corresponding_unfunded_column_name] < interest_due_at_start_of_period):
                                paid_out_of_capitalized_interest_bucket = capitalized_draw_unfunded_bucket[corresponding_unfunded_column_name] #whatever is left
                                
                            row['amount_drawn'] = row['amount_drawn'] + paid_out_of_capitalized_interest_bucket
                            row[corresponding_amount_column_name] = paid_out_of_capitalized_interest_bucket
                            row[corresponding_unfunded_column_name] = capitalized_draw_unfunded_bucket[corresponding_unfunded_column_name] - paid_out_of_capitalized_interest_bucket
                                
                        capitalized_draw_unfunded_bucket[corresponding_unfunded_column_name] = row[corresponding_unfunded_column_name]             

            elif('Capitalized Interest' in actual_column_name): #no draw but we are still working with a Capitalied Interest
                row[corresponding_unfunded_column_name] = capitalized_draw_unfunded_bucket[corresponding_unfunded_column_name]



def calc_interest_and_principal_dues(
    row,
    cumulative_outstanding_principal,
    principal_due_at_start_of_period,
    interest_due_at_start_of_period,
    cumulative_pik_amount_due,
    p_n_i_interest_accrued,
    a_b_amount_factor=1
):
    calc_draw_amount(row, principal_due_at_start_of_period, interest_due_at_start_of_period, cumulative_pik_amount_due)


    row["principal_paid_at_start"] = principal_due_at_start_of_period

    interest_moved = 0
    p_n_i_interest_moved = 0
    if row["is_interest_due_at_start"] == 1:
        row["interest_paid_at_start"] = interest_due_at_start_of_period
        row["p_n_i_interest_due_at_start"] = p_n_i_interest_accrued 

    else:
        interest_moved = interest_due_at_start_of_period
        row["base_interest_amount_unpaid_from_previous_period"] = interest_moved

        p_n_i_interest_moved = p_n_i_interest_accrued
        row["p_n_i_interest_carried_from_previous_period"] = p_n_i_interest_moved


    row["cummulative_outstanding_principal"] = (
        cumulative_outstanding_principal + row["amount_drawn"] - row["principal_paid_at_start"]
    )

    row["base_interest_amount_due_for_this_period"] = (
        row["period_base_interest_multiplier"] * row["cummulative_outstanding_principal"]
    )
    row["base_interest_amount_due_at_start_of_next_period"] = interest_moved + (
        row["period_base_interest_multiplier"] * row["cummulative_outstanding_principal"]
    )

    row["p_n_i_interest_due_for_this_period"] = (
        row["period_p_n_i_interest_multiplier"] * row["cummulative_outstanding_principal"]
    ) 

    row["p_n_i_interest_amount_due_at_start_of_next_period"] = p_n_i_interest_moved + (
        row["period_p_n_i_interest_multiplier"] * row["cummulative_outstanding_principal"]
    )



    row["cummulative_pik_amount_due"] = cumulative_pik_amount_due + (
        row["cummulative_outstanding_principal"] + cumulative_pik_amount_due
    ) * row["period_accrual_interest_multiplier"]

    row["principal_due_at_start_of_next_period"] = 0
    if not row["payment_type_next_month"]:
        row["principal_due_at_start_of_next_period"] = row["cummulative_outstanding_principal"]
    elif row["payment_type_next_month"] == "Interest Only":
        row["principal_due_at_start_of_next_period"] = 0
    elif row["payment_type_next_month"] == "Principal & Interest":
        # Only calculate P&I if the next row actually has principal due (not a draw/maturity row)
        if row.get("calculate_principal_for_next_month") == True:
            amortization_term = row["amortization_term"]
            row["principal_due_at_start_of_next_period"] = cumprinc(
                row["period_p_n_i_interest_multiplier"],
                amortization_term - row["principal_payment_index"] + 1,
                row["cummulative_outstanding_principal"],
                row["principal_payment_index"],
                row["principal_payment_index"],
                0,
                a_b_amount_factor,
            ) - row["p_n_i_interest_amount_due_at_start_of_next_period"]
        # else: principal_due_at_start_of_next_period remains 0 (set at line 147)

    return (
        row["cummulative_outstanding_principal"],
        row["principal_due_at_start_of_next_period"],
        row["base_interest_amount_due_at_start_of_next_period"],
        row["cummulative_pik_amount_due"],
        row["p_n_i_interest_amount_due_at_start_of_next_period"]

    )


def calc_interest_and_principal(pricing_schedule: pd.DataFrame, a_b_amount_factor: float = 1) -> pd.DataFrame:
    pricing_schedule["amount_drawn"] = pricing_schedule["amount_drawn"].fillna(0)
    pricing_schedule["principal_paid_at_start"] = pricing_schedule["principal_paid_at_start"].fillna(0)
    pricing_schedule["is_interest_due_at_start"] = pricing_schedule["is_interest_due_at_start"].fillna(0)

    pricing_schedule["payment_type_next_month"] = pricing_schedule["payment_type"].shift(-1)

    if('is_principal_due_at_start' in pricing_schedule):
        pricing_schedule["calculate_principal_for_next_month"] = pricing_schedule["is_principal_due_at_start"].shift(-1)
    else: 
        pricing_schedule["is_principal_due_at_start"] = 0
        pricing_schedule["calculate_principal_for_next_month"] = pricing_schedule["is_principal_due_at_start"].shift(-1)


    if('amortization_term' in pricing_schedule.keys()):
        pricing_schedule["amortization_term"] = pricing_schedule["amortization_term"].shift(-1)

    apply_row_index_for_principal_calc(pricing_schedule)

    records = pricing_schedule.to_dict("records")

    cumulative_outstanding_principal = 0
    cumulative_pik_amount_due = 0
    interest_due_at_start_of_period = 0
    principal_due_at_start_of_period = 0
    p_n_i_interest_accrued = 0


    for row in records:
        (
            cumulative_outstanding_principal,
            principal_due_at_start_of_period,
            interest_due_at_start_of_period,
            cumulative_pik_amount_due,
            p_n_i_interest_accrued
        ) = calc_interest_and_principal_dues(
            row,
            cumulative_outstanding_principal,
            principal_due_at_start_of_period,
            interest_due_at_start_of_period,
            cumulative_pik_amount_due,
            p_n_i_interest_accrued,
            a_b_amount_factor
        )

    return pd.DataFrame(records)


def calculate_interest_principal_pik_and_cap_draws(interest_and_pik_multiplier: pd.DataFrame, a_b_amount_factor: float = 1) -> pd.DataFrame:
    """
    Compute the Stage 1 pricing schedule with interest, principal, PIK, and draw adjustments.

    Args:
        interest_and_pik_multiplier: DataFrame produced by Step 4.
        a_b_amount_factor: Factor for A/B tranche loan calculations (default 1).

    Returns:
        Pricing schedule DataFrame equivalent to the old Stage1.xlsx.
    """
    return calc_interest_and_principal(interest_and_pik_multiplier.copy(), a_b_amount_factor)
