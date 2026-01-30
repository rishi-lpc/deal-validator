#!/usr/bin/env python

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import calendar
import json

import pandas as pd
from dateutil.relativedelta import relativedelta


def parse_date(d: str):
    if isinstance(d, str):
        return datetime.strptime(d, "%Y-%m-%d").date()
    return d

def get_events_from_accounting():
    events = []
    try: 
        with open('../generated_data/-1. loan_events.json','r') as f:
            events = json.load(f)
    
        for e in events:
            e.update({'event_date': parse_date(e['event_date']), 
                    'record_type': 'actual_from_accounting'})
    except Exception as E:
        print('Warning: Could not load any actual Accounting Data, will simulate all data')
        
    return events

def get_next_payment_date(frequency: str, start_date: datetime.date):
    def monday_of_next_week(d):
        return d + relativedelta(weekday=0, days=+1) + timedelta(weeks=1 if d.weekday() != 0 else 0)

    def monday_of_week_after_next(d):
        return d + relativedelta(weekday=0, days=+1) + timedelta(weeks=2 if d.weekday() != 0 else 1)

    def first_day_of_next_month(d):
        return (d + relativedelta(months=1)).replace(day=1)

    def first_day_of_next_year(d):
        return datetime.date(d.year + 1, 1, 1)

    def same_day_next_quarter(d):
        return d + relativedelta(months=3)

    payment_frequency_map = {
        "Weekly": monday_of_next_week,
        "Biweekly": monday_of_week_after_next,
        "Frequency_Monthly": first_day_of_next_month,
        "Frequency_Quarterly": same_day_next_quarter,
        "Frequency_Annually": first_day_of_next_year
    }

    func = payment_frequency_map.get(frequency)
    if not func:
        raise ValueError(f"Unsupported frequency: {frequency}")

    return func(start_date)



def calculate_number_of_payments(number_of_terms, term_unit, payment_frequency):
    
    supported_combinations = {
        "Weekly": {
            "Unit_Months": 4,
            "Unit_Bimonths": 8,
            "Unit_Quarters": 12,
            "Unit_Semiannum": 26,
            "Unit_Years": 52
        },
        "Biweekly": {
            "Unit_Months": 2,
            "Unit_Bimonths": 4,
            "Unit_Quarters": 6,
            "Unit_Semiannum": 13,
            "Unit_Years": 26
        },
        "Frequency_Monthly": {
            "Unit_Months": 1,
            "Unit_Bimonths": 2,
            "Unit_Quarters": 3,
            "Unit_Semiannum": 6,
            "Unit_Years": 12
        },
        "Frequency_Quarterly": {
            "Unit_Months": 1/3,
            "Unit_Quarters": 1,
            "Unit_Semiannum": 2,
            "Unit_Years": 4
        },
        "Frequency_Annually": {
            "Unit_Years": 1
        }
    }
    try:
        return int(number_of_terms * supported_combinations[payment_frequency][term_unit])
    except KeyError:
        raise ValueError(f"Payment Frequency in {payment_frequency} is currently not supported with Terms Length in {term_unit}")
    

def get_payment_dates(zone):

    # add first effective date for this zone - if it is duplicate with the global first_payment_date - we will remove it outside the scope of single zone
    payment_effective_date = parse_date(zone['LLC_BI__EFFECTIVE_DATE__C_Y'])
    payment_dates = []
    next_payment_date = payment_effective_date
    payment_dates.append(next_payment_date)
    
    
    length_term = zone['LLC_BI__TERM_LENGTH__C_Y']
    term_unit = zone['LLC_BI__TERM_UNIT__C_Y']
    event_details = zone['LLC_BI__PAYMENT_TYPE__C']
    payment_frequency = zone['LLC_BI__FREQUENCY__C']
    
    if(payment_frequency == 'At Maturity'):
        return payment_dates  #maturity date will be added outside the scope of a single payment zone
    else:
        number_of_payments_to_make = calculate_number_of_payments(length_term, term_unit, payment_frequency)
        for i in range(number_of_payments_to_make):
            next_payment_date = get_next_payment_date(payment_frequency, next_payment_date)
            payment_dates.append(next_payment_date)

        return payment_dates
    


def get_next_draw_date(date, freq):
    def first_day_of_next_month(d):
        return (d + relativedelta(months=1)).replace(day=1)

    payment_frequency_map = {
        "Monthly": first_day_of_next_month,
    }

    print(':::::: ',freq,'  :::::::') 
    func = payment_frequency_map.get(freq)
    return func(date)




def process_draw_events(draw_dates, draw_policy, policy_index):

    print(
        "\033[94m",
        "HERE HERE HERE"
        "\033[0m",
    )

    _ret = []
    
    if('MADE_UP_NAME' in draw_policy['NAME'] or ('LLC_BI__PAID_AT_CLOSING__C' in draw_policy.keys() and draw_policy['LLC_BI__PAID_AT_CLOSING__C'] != 'Funded at Closing')):
        
            
        if('Capitalized Interest' in draw_policy['LLC_BI__FEE_TYPE__C']):
            _ret = [
                {**draw, "record_type": "simulated", "amount": 0, "event_details":draw_policy, "draw_policy_index": policy_index
                }
                for draw in draw_dates
            ]
    
        #elif(draw_policy['LLC_BI__FEE_TYPE__C'] in ['', None, 'Working Capital', 'Debt Service Reserve','Operating Deficit Reserve']):
        else:
            amount_to_distribute = draw_policy['LLC_BI__AMOUNT__C']
            averge_draw_amt = amount_to_distribute/len(draw_dates)
    
            _ret = [
                {
                    **draw, 
                    "record_type": "simulated", 
                    "amount": averge_draw_amt, 
                    "event_details": draw_policy, 
                    "draw_policy_index": policy_index
                }
                for draw in draw_dates
            ]
    else: 
        print(f"WARNING: {draw_policy['NAME']} - { draw_policy['LLC_BI__FEE_TYPE__C']} was not added to Reserve Buckets as it is either funded at closing or does not contain any indication of when it is funded")
    return _ret

def get_reset_amount_dates(draw_dates, draw_policy, policy_index):

    reset_amount = None
    if('CM_DRAW_RESET_TYPE__C' in draw_policy.keys()):
        reset_amount = draw_policy['CM_DRAW_RESET_TYPE__C']

    freq = "Monthly"
    if('FREQ' in draw_policy.keys()):
        freq =  draw_policy['FREQ']
    else:
        print(f"Warning: No FREQ policy is provided for draw policy:{draw_policy['NAME']} - {draw_policy['LLC_BI__FEE_TYPE__C']}. \'Monthly\' policy will be imposed")
        


    _ret = []
    
    if(reset_amount == 'Skip' or reset_amount == 'Push to End Date'): #dates already in list
        pass
    elif(reset_amount == 'Push to Deadline'):
        _ret.append({"event_type": "draw", "reset_date":True ,"event_date":parse_date(draw_policy['CM_DRAW_DATE_DEADLINE__C']),"draw_policy_index": policy_index}) 
    elif(reset_amount == 'Push to Next'):
        print('*******',draw_dates[-1]['event_date'],'*******')
        _ret.append({"event_type": "draw", "reset_date":True, "event_date":get_next_draw_date(draw_dates[-1]['event_date'],freq),"draw_policy_index": policy_index})
    elif(reset_amount == 'Redistribute'):
        pass #will do this after underwriting is done. 
    else:
        print(f"Warning: No RESET_AMOUNT policy is provided for draw policy:{draw_policy['NAME']}-{draw_policy['LLC_BI__FEE_TYPE__C']}. \'Skip\' policy will be imposed")

    return _ret


def process_reset_dates(reset_dates, draw_policy):
    # for "At Underwriting" only Capitalized Interest will need reset_dates to be added. All others are not to be added
    if(draw_policy['LLC_BI__FEE_TYPE__C'] == 'Capitalized Interest'):
        return [
            {**reset_date, "record_type": "simulated", "amount": 0, "reset_date":True, "event_details": draw_policy
            }
            for reset_date in reset_dates
        ]
    else:
        return []

    
def add_draw_schedule(loan_terms:dict): 
    draw_schedule = []
    draw_policies = loan_terms['DRAW_DETAILS']
    for idx, draw_policy in enumerate(draw_policies):

        if('CM_FEE_DATE__C' not in draw_policy.keys() or
           'CM_END_DATE__C' not in draw_policy.keys()):
                print(f"Warning: {draw_policy['LLC_BI__FEE_TYPE__C']} ({draw_policy['NAME']}) is missing either Start and End Dates. This Reserve will be ignored. Please provide both dates for this Reserve to be considered")
                continue
        else: 
            start_date = parse_date(draw_policy['CM_FEE_DATE__C'])
            end_date = parse_date(draw_policy['CM_END_DATE__C'])

            deadline = parse_date(loan_terms['LLC_BI__MATURITY_DATE__C'])
            if('CM_DRAW_DATE_DEADLINE__C' in draw_policy.keys()):
                deadline = parse_date(draw_policy['CM_DRAW_DATE_DEADLINE__C'])        
        
        freq = 'Monthly'
        if('CM_DRAW_FREQUENCY__C' in draw_policy.keys()):
            freq = draw_policy['CM_DRAW_FREQUENCY__C']
        
        account = draw_policy['LLC_BI__FEE_TYPE__C']

        draw_date = start_date
        draw_dates = []

        #for capitalized interest go all the way to deadline
        stop_date = deadline if account.startswith('Capitalized Interest Reserve') else end_date
     
        while(draw_date <= stop_date):
            draw_dates.append({"event_type": "draw", "event_date":draw_date})
            draw_date = get_next_draw_date(draw_date,freq)           

        draw_schedule.extend(process_draw_events(draw_dates, draw_policy,idx))        
        reset_dates = get_reset_amount_dates(draw_dates, draw_policy, idx)
        
        f = process_reset_dates(reset_dates, draw_policy)
        if(f and len(f) > 0):
            draw_schedule.extend(f)

    return draw_schedule


def remove_duplicates_and_dates_beyond_maturity(payment_dates: list, start_of_simulation: date, maturity_date: date) -> list:
    # Use a set to remove duplicates
    unique_dates = set(payment_dates)

    # Filter to include only dates between start_of_simulation and maturity_date (inclusive)
    filtered_dates = [
        d for d in unique_dates
        if start_of_simulation <= d[0] <= maturity_date
    ]

    # Return sorted list of valid dates
    return sorted(filtered_dates)

def add_payment_type(as_of_accounting_events: dict, loan_terms):
    pass

def add_payment_due_schedule(loan_terms:dict):
    
    maturity_date = loan_terms['LLC_BI__MATURITY_DATE__C']
    loan_payment_zones = loan_terms['PAYMENT_DETAILS']
    first_payment_date = parse_date(loan_terms['LLC_BI__FIRST_PAYMENT_DATE__C'])
    maturity_date = parse_date(loan_terms['LLC_BI__MATURITY_DATE__C'])
    
    payment_dates = []
    #payment_dates.append(first_payment_date) #this should also come from the zone. Outside of that we have no idea 
    #what payment type is associated with it (interest only, amortizing, etc)
    
    for payment_zone in loan_payment_zones:
        event_details = payment_zone['LLC_BI__PAYMENT_TYPE__C']
        zone_payment_dates = [(payment_date, event_details) for payment_date in get_payment_dates(payment_zone)]
        payment_dates.extend(zone_payment_dates)

    payment_dates.append((maturity_date,'Payoff'))
    payment_dates = remove_duplicates_and_dates_beyond_maturity(payment_dates, first_payment_date, maturity_date)

    #reformat data so that it is processing friendly:
    _ret = []
    for d in payment_dates:
        if(d[1] == 'Interest Only'):
            _ret.append({
                'event_type': 'interest due',
                'event_date': d[0],
                'event_details': d[1],
                'amount': None,
                'record_type':'simulated'
            })
        elif(d[1] == 'Principal & Interest' or d[1] == 'Principal + Interest' ):
            _ret.append({
                'event_type': 'interest due',
                'event_date': d[0],
                'event_details': d[1],
                'amount': None,
                'record_type':'simulated'
            })
            _ret.append({
                'event_type': 'principal due',
                'event_date': d[0],
                'event_details': d[1],
                'amount': None,
                'record_type':'simulated',
                'amortization_term': payment_zone['CM_AMORTIZED_TERM_MONTHS__C']
            })
        elif(d[1] == 'Payoff'):
            _ret.append({
                'event_type': 'interest payoff due',
                'event_date': d[0],
                'event_details': loan_payment_zones[len(loan_payment_zones) - 1]['LLC_BI__PAYMENT_TYPE__C'],
                'amount': None,
                'record_type':'simulated'
            })
            _ret.append({
                'event_type': 'principal payoff due',
                'event_date': d[0],
                'event_details': loan_payment_zones[len(loan_payment_zones) - 1]['LLC_BI__PAYMENT_TYPE__C'],
                'amount': None,
                'record_type':'simulated'
            })
                        
        else:
            print(f'Warning: cannot place this event {d}')
            
    return _ret


def get_events(loan_terms: dict, scenario='At Underwriting', as_of_date=date.today()):

    #as-of-date
    as_of_date = parse_date(as_of_date)
    
    if(as_of_date > date.today()):
        print(f'Warning: As-of date ({as_of_date}) cannot be a future date. As-of Date will be set to today ({date.today()})')
        
    if(scenario == 'At Underwriting'):        
        loan_close_date = parse_date(loan_terms['LLC_BI__CLOSEDATE__C'])
        if(as_of_date != loan_close_date):
            print(f'Warning: For At Underwriting scenarios, the provided as-of date ({as_of_date}) will be ignored and loan-close date ({loan_close_date}) will be used instead as as-of date ')
            as_of_date = loan_close_date    
        
    all_accounting_events = get_events_from_accounting()
    
    #only keep accounting events that are earlier or equal to as_of_date
    as_of_accounting_events = [e for e in all_accounting_events if parse_date(e['event_date']) <= parse_date(as_of_date)]
    add_payment_type(as_of_accounting_events, loan_terms)
    
    payments_due_schedule = add_payment_due_schedule(loan_terms)
    as_of_accounting_events.extend(payments_due_schedule)

    draw_schedule = add_draw_schedule(loan_terms)
    as_of_accounting_events.extend(draw_schedule)
    
    as_of_accounting_events.sort(key=lambda x: x['event_date'])
    
    return as_of_accounting_events


def form_transactions(
    loan_terms: dict,
    scenario: str = "At Underwriting",
    as_of_date = None,
) -> pd.DataFrame:
    """
    Produce the transactions dataframe that used to be exported to `2. transactions.xlsx`.

    Args:
        loan_terms: Loan metadata dictionary.
        scenario: Scenario label, defaults to `'At Underwriting'`.
        as_of_date: Optional as-of date; defaults to `date.today()`.

    Returns:
        pandas DataFrame sorted by event date with the scenario column attached.
    """
    events = get_events(loan_terms, scenario, as_of_date)
    df = pd.DataFrame(events)
    df['scenario'] = scenario

    df["event_details"] = df["event_details"].apply(
    lambda x: json.dumps(x, sort_keys=True) if isinstance(x, dict) else x)
    df.drop_duplicates(inplace=True)
    df["event_details"] = df["event_details"].apply(
        lambda x: json.loads(x, sort_keys=True) if isinstance(x, dict) else x)  

    df = df.sort_values(["event_date"]).reset_index(drop=True)
    return df
