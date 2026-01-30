#!/usr/bin/env python

from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Any, Dict, List
from datetime import datetime
import calendar
import pandas as pd

#util functions
def parse_date(d):
    if isinstance(d, str):
        return datetime.strptime(d, "%Y-%m-%d").date()
    return d

def get_pricing_zones(loan_terms: Dict[str, Any]) -> List[Dict[str, Any]]:
    loan_closing = parse_date(loan_terms["LLC_BI__CLOSEDATE__C"])
    pricing_details = loan_terms['PRICING_DETAILS']
    terms = []

    for each_pricing in pricing_details:
        terms.append({
            "start_date": parse_date(each_pricing['LLC_BI__EFFECTIVE_DATE__C_Y']), 
            "length": each_pricing['LLC_BI__TERM_LENGTH__C_Y'], 
            "units": each_pricing['LLC_BI__TERM_UNIT__C_Y'],
            "pricing_details":each_pricing #reattach full details
        })

    # Sort terms by start_date
    terms.sort(key=lambda x: x['start_date'])

    # Show warnings based on sorted terms
    if terms and terms[0]['start_date'] > loan_closing:
        print('\033[94m',f"""Warning: Loan pricing starts from ({terms[0]['start_date']}) while loan is closed on
{loan_closing}. There is no pricing information for the period in between.""",'\033[0m')

    if terms and terms[0]['start_date'] < loan_closing:
        print(f"""Warning: Loan pricing starts from ({terms[0]['start_date']}) while loan is closed on
{loan_closing}. Loan will not accrue from pricing date but from closing date.""")

    return terms

def add_end_dates_to_zones(all_zones: List[Dict[str, Any]], loan_terms: Dict[str, Any]) -> None:
    
    #get maturity data - this is the end date for the last pricing zone
    all_zones[-1]['end_date'] = parse_date(loan_terms['LLC_BI__MATURITY_DATE__C'])

    next_zone_start = all_zones[-1]['start_date']
    for zone in all_zones[-2::-1]: #reverse order starting from second-last zone    
        zone['end_date'] = next_zone_start - relativedelta(days=1)
        next_zone_start = zone['start_date']

def end_of_semimonth(d: date) -> (bool, date):
    """
    Determine if `d` starts a proper semimonth period and the end date of the semimonth containing `d`.

    Args:
        d: Calendar date.

    Returns:
        A tuple `(is_proper_start, period_end)` where:
        - `is_proper_start` is True when `d` is the first day (1) or the sixteenth (16) of the month.
        - `period_end` is the 15th if `d.day <= 15`, otherwise the last day of the month.
    """

    if d.day <= 15:
        return (d.day == 1, d.replace(day=15))
    else:
        last_day = calendar.monthrange(d.year, d.month)[1]
        return (d.day == 16, date(d.year, d.month, last_day))

def end_of_months(d:date, month_advancement: int) -> (bool, date):
    """
    Compute the last date of the period ending `month_advancement` months after the month containing `d`,
    and whether `d` is at a proper month boundary for the period.

    Args:
        d: Calendar date.
        month_advancement: Number of months in the period (e.g., 1 for monthly, 3 for quarterly).

    Returns:
        A tuple `(is_proper_start, period_end)` where:
        - `is_proper_start` is True when `d.day == 1`.
        - `period_end` is the last day of the month `month_advancement` months after the first of `d`’s month.
    """
    return (d.day==1, d.replace(day=1) + relativedelta(months=(month_advancement)) - relativedelta(days=1))

def unit_end_date(frequency: str, start_date: date):
    """
    Map a unit frequency to its period-end computation for `start_date`.

    Args:
        frequency: One of 'Unit_Days', 'Unit_Semimonths', 'Unit_Months', 'Unit_Bimonths',
                   'Unit_Quarters', 'Unit_Semiannum', 'Unit_Years'.
        start_date: Date within the desired period.

    Returns:
        A tuple `(is_proper_start, period_end)` as defined by the selected frequency.
    """
    term_unit_mapping = {
        "Unit_Days": lambda d: (True, d),
        "Unit_Semimonths": lambda d: end_of_semimonth(d),  # Approximate half-month
        "Unit_Months": lambda d: end_of_months(d,1), 
        "Unit_Bimonths": lambda d: end_of_months(d,2),
        "Unit_Quarters": lambda d: end_of_months(d,3),
        "Unit_Semiannum": lambda d: end_of_months(d,6),
        "Unit_Years": lambda d: end_of_months(d,12)
    }
    x=  term_unit_mapping.get(frequency)(start_date) #dynamic function execution
    return x

def get_unit_based_accrual_periods(start_date, zone_end_date, units, accrual_periods) -> None:
    (is_proper_start, accrual_end_date) = unit_end_date(units, start_date) 
    end_date = min(accrual_end_date, zone_end_date)

    is_proper_end = True
    if(end_date != accrual_end_date):
        is_proper_end = False

    accrual_periods.append(
            {
            "accrual_start_date": start_date,
            "accrual_end_date": end_date,
            "_is_complete_period": (is_proper_start and is_proper_end),
            "_units": units
            }
    )
    if(end_date < zone_end_date):
        new_start_date = end_date + relativedelta(days=1)
        get_unit_based_accrual_periods(new_start_date, zone_end_date, units, accrual_periods)
    else:
        return    

def get_accrual_periods(
    pricing_zone: Dict[str, Any], first_payment_date: date
) -> List[Dict[str, Any]]:
    
    zone_start_date = parse_date(pricing_zone['start_date'])
    zone_end_date = parse_date(pricing_zone['end_date']) 
    units = pricing_zone['units']
    
    accrual_periods = []
    
    # this code used to ensure that the first accrual period runs from 
    # closing date to the first payment date. Since this is no more the requirement 
    # I am commenting it out now 

    
    # # special pricing zone that contain the first payment date
    # if(first_payment_date > zone_start_date and first_payment_date < zone_end_date):
        
    #     # to first payment and then apply the unit
    #     (is_proper_start, general_accrual_end_date) = unit_end_date(units, zone_start_date) 
    #     #general_accrual_end_date means that end date that would have been the end of this period had we not had to stop at
    #     #the first payment date

    #     is_proper_end = True
    #     if(first_payment_date - relativedelta(days=1) != general_accrual_end_date):
    #         is_proper_end = False
        
    #     accrual_periods.append(
    #         {
    #         "accrual_start_date": zone_start_date,
    #         "accrual_end_date": first_payment_date - relativedelta(days=1),
    #         "_is_complete_period": (is_proper_start and is_proper_end),
    #         "_units": units
    #         }
    #     )
    #     #special adjustment 
    #     zone_start_date = first_payment_date 
        
    get_unit_based_accrual_periods(zone_start_date, zone_end_date, units, accrual_periods)
    return accrual_periods

def _generate_pricing_based_accrual_schedule(loan_terms: Dict[str, Any]) -> List[Dict[str, Any]]:
    all_pricing_zones = get_pricing_zones(loan_terms)
    if len(all_pricing_zones) == 0:
        raise ValueError("The deal seems to have no pricing streams in it. Cannot proceed.")
         
    add_end_dates_to_zones(all_pricing_zones, loan_terms)

    first_payment_date = parse_date(loan_terms['LLC_BI__FIRST_PAYMENT_DATE__C'])

    accrual_periods = []
    for zone_index, zone in enumerate(all_pricing_zones):
        periods = get_accrual_periods(zone, first_payment_date)
        for period in periods:
            period['_pricing_zone_index'] = zone_index
        accrual_periods.extend(periods)

    return accrual_periods


def _initialize_schedule(periods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Attach default bookkeeping fields to each accrual period."""
    initialized = []
    for index, period in enumerate(periods):
        entry = {
            **period,
            "event": None,
            "event_date": None,
            "accrual_period": index + 1,
            "accrual_sub_period": 0,
        }
        initialized.append(entry)
    return initialized


def generate_accrual_schedule(loan_terms: Dict[str, Any]) -> pd.DataFrame:
    """
    Build the accrual schedule dataframe for a loan.

    Args:
        loan_terms: Loan metadata dictionary produced by `step0.get_loan_terms`.

    Returns:
        DataFrame equivalent to the legacy `1. accrual_schedule.xlsx` export.
    """
    periods = _generate_pricing_based_accrual_schedule(loan_terms)
    schedule = pd.DataFrame(_initialize_schedule(periods))
    return schedule[
        [
            "event",
            "event_date",
            "accrual_period",
            "accrual_sub_period",
            "accrual_start_date",
            "accrual_end_date",
            "_pricing_zone_index",
            "_is_complete_period",
            "_units",
        ]
    ].copy()
