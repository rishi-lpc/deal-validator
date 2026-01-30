#!/usr/bin/env python

from typing import Any, Dict

import pandas as pd


def get_index_value(index_code: str, index_date, work_days_prior_to_index: int) -> float:
    """Fetch the index rate for the given code/date (currently stubbed)."""
    print(
        "\033[94m",
        "Warning: Index rate of 4.32105% is hardcoded for now. Need a connector to actual index rates",
        "\033[0m",
    )
    return 3.6995


def get_interest_rate(
    row: Dict[str, Any],
    pricing_details: Dict[str, Any],
    loan_closing_date,
) -> tuple[float, float, float]:
    """Determine interest rate details for the given accrual row and pricing descriptor."""

    work_days_prior_to_index = 2
    interest_rate_type = pricing_details["LLC_BI__INTEREST_RATE_TYPE__C"]
    accrual_rate = pricing_details.get("CM_ACCRUED_RATE__C", 0)

    if interest_rate_type == "Fixed":
        all_in_rate = pricing_details["LLC_BI__ALL_IN_RATE__C"]
        base_rate = all_in_rate - accrual_rate
    else:
        index_code = pricing_details["LLC_BI__INDEX__C"]
        if interest_rate_type == "Floating with Index":
            start_date = row["accrual_start_date"]
        else:  # Fixed with Index
            start_date = loan_closing_date

        index_rate = get_index_value(index_code, start_date, work_days_prior_to_index)
        floor_rate = pricing_details.get("LLC_BI__RATE_FLOOR__C", 0)
        ceiling_rate = pricing_details.get("LLC_BI__RATE_CEILING__C", 9999)
        spread = pricing_details.get("LLC_BI__SPREAD__C", 0)

        base_rate = max(index_rate, floor_rate)
        if ceiling_rate > 0:
            base_rate = min(base_rate, ceiling_rate)

        base_rate = base_rate + spread - accrual_rate

    return interest_rate_type, base_rate, accrual_rate


def adjust_accrual_days_for_30_360(accrual_start_date, accrual_end_date, interest_accrual_method):
    """
    Adjusts the number of accrual days for 30/360 interest calculation method. 
    """

    actual_accrual_days = (accrual_end_date - accrual_start_date).days + 1

    standard_30_360_days = (accrual_end_date.month - accrual_start_date.month) * 30 + 30

    period_start = accrual_start_date.replace(day=1)
    period_end = accrual_end_date + pd.offsets.MonthEnd(0)

    actual_days_in_calendar_span = (period_end - period_start).days + 1

    adjusted_30_360_accrual_days = actual_accrual_days * (standard_30_360_days / actual_days_in_calendar_span)

    return actual_accrual_days, adjusted_30_360_accrual_days


def get_interest_accrual_multiplier(
    pricing_details,
    is_complete_period,
    units,
    accrual_start_date,
    accrual_end_date,
):

    if not is_complete_period:
        interest_accrual_method = pricing_details["CM_PARTIAL_PERIOD_INTERST_ACCRUAL_METHOD__C"]
    else:
        interest_accrual_method = pricing_details.get("CM_INTEREST_ACCRUAL_METHOD__C", "Actual_360")

    actual_accrual_days, adjusted_30_360_accrual_days = adjust_accrual_days_for_30_360(
        accrual_start_date, accrual_end_date, interest_accrual_method
    )

    interest_accrual_multiplier = 0
    if interest_accrual_method == "Actual_360":
        interest_accrual_multiplier = (1 / 360) * actual_accrual_days
    if interest_accrual_method == "30_360":
       interest_accrual_multiplier = (1 / 360) * adjusted_30_360_accrual_days 

    # for P&I 
    p_n_i_interest_multiplier = (1 / 360) * adjusted_30_360_accrual_days  




    return interest_accrual_multiplier, interest_accrual_method, actual_accrual_days, adjusted_30_360_accrual_days, p_n_i_interest_multiplier


def process_amort_row(
    row: Dict[str, Any],
    pricing_details: Dict[str, Any],
    loan_closing_date,
) -> Dict[str, Any]:
    accrual_start_date = row["accrual_start_date"]
    accrual_end_date = row["accrual_end_date"]

    (
        interest_accrual_multiplier,
        interest_accrual_method,
        actual_accrual_days,
        adjusted_30_360_accrual_days,
        p_n_i_interest_multiplier
    ) = get_interest_accrual_multiplier(
        pricing_details, row["_is_complete_period"], row["_units"], accrual_start_date, accrual_end_date
    )
    interest_rate_type, base_rate, accrual_rate = get_interest_rate(
        row, pricing_details, loan_closing_date
    )

    row.update(
        {
            "interest_accrual_method": interest_accrual_method,
            "actual_accrual_days": actual_accrual_days,
            "adjusted_30_360_accrual_days": adjusted_30_360_accrual_days,
            "interest_rate_type": interest_rate_type,
            "period_multiplier": interest_accrual_multiplier,
            "p_n_i_interest_multiplier": p_n_i_interest_multiplier,
            "base_interest_rate": base_rate,
            "accrual_interest_rate": accrual_rate,
            "period_base_interest_multiplier": (base_rate / 100) * interest_accrual_multiplier,
            "period_accrual_interest_multiplier": (accrual_rate / 100) * interest_accrual_multiplier,
            "period_p_n_i_interest_multiplier": (base_rate / 100) * p_n_i_interest_multiplier
        }
    )
    return row


def generate_interest_and_pik_multipliers(
    loan_terms: Dict[str, Any],
    transactions_with_draws: pd.DataFrame,
) -> pd.DataFrame:
    """
    Generate the pricing schedule dataframe that was previously exported by Step 4.

    Args:
        loan_terms: Loan metadata dictionary.
        transactions_with_draws: DataFrame returned from step3 `merge_transactions_into_schedule`.

    Returns:
        DataFrame containing interest and PIK multipliers.
    """
    records = transactions_with_draws.to_dict("records")
    for row in records:
        zone_index = int(row["_pricing_zone_index"])
        pricing_details = loan_terms["PRICING_DETAILS"][zone_index]
        process_amort_row(row, pricing_details, loan_terms["LLC_BI__CLOSEDATE__C"])
    return pd.DataFrame(records)
