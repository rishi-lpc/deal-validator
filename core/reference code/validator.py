import json
from step99 import get_loan_terms_metadata
from datetime import datetime

def quick_message_maker(parent_dict_name, text_message, buffer):
        t = {}
        t['TABLE'] = parent_dict_name.upper()
        t['ID'] = None
        t['FIELD'] = None
        t['MESSAGE'] = text_message
        buffer.append(t)

def log_required_fields_error(parent_dict, parent_table_name, required_high_level_keys, buff, metadata):
    for key in required_high_level_keys:
        if(key not in parent_dict.keys()):
            t = {}
            t['TABLE'] = parent_table_name.upper()
            t['ID'] = parent_dict['ID']
            t['FIELD'] = key.upper()
            label = [lab for lab in metadata if (lab['FIELD'] == t['FIELD'] and lab['TABLE'] == t['TABLE'])][0]['DISPLAYNAME']
            t['MESSAGE'] = f"\"{label}\" is required."
    
            buff.append(t)

def log_date_relationship_error(parent_dict1, parent_table_name1, date1_key,
                                parent_dict2, parent_table_name2, date2_key, 
                                date1_rel_with_date2, buff, metadata) -> bool:

    try: 
        dt1 = datetime.strptime(parent_dict1[date1_key], "%Y-%m-%d").date()
        dt2 = datetime.strptime(parent_dict2[date2_key], "%Y-%m-%d").date()
    except ValueError as e:
        return # do nothing - this method is not responsible to check format of dates
    except KeyError as e:
        return # do nothing - this method is not responsible to check format of dates
    
    t = {}
    t['TABLE'] = parent_table_name1.upper()
    t['ID'] = parent_dict1['ID']
    
    if(date1_rel_with_date2 == "EQ"):
        if(dt1 != dt2):            
            t['FIELD'] = date1_key.upper()
            label1 = [lab for lab in metadata if (lab['FIELD'] == t['FIELD'] and lab['TABLE'] == t['TABLE'])][0]['DISPLAYNAME']
            label2 = [lab for lab in metadata if (lab['FIELD'] == date2_key.upper() and lab['TABLE'] == parent_table_name2.upper())][0]['DISPLAYNAME']
            t['MESSAGE'] = f"{label1} ({dt1}) and {label2} ({dt2}) are required to be the same date. But they are not"
        
    elif(date1_rel_with_date2 == "GT"):
        if(dt1 <= dt2):  
            t['FIELD'] = date1_key.upper()
            label1 = [lab for lab in metadata if (lab['FIELD'] == t['FIELD'] and lab['TABLE'] == t['TABLE'])][0]['DISPLAYNAME']
            label2 = [lab for lab in metadata if (lab['FIELD'] == date2_key.upper() and lab['TABLE'] == parent_table_name2.upper())][0]['DISPLAYNAME']
            t['MESSAGE'] = f"{label1} ({dt1}) is supposed to be after {label2} ({dt2}). But it is not"
    
    elif(date1_rel_with_date2 == "GT_E"):
        if(dt1 < dt2):  
            t['FIELD'] = date1_key.upper()
            label1 = [lab for lab in metadata if (lab['FIELD'] == t['FIELD'] and lab['TABLE'] == t['TABLE'])][0]['DISPLAYNAME']
            label2 = [lab for lab in metadata if (lab['FIELD'] == date2_key.upper() and lab['TABLE'] == parent_table_name2.upper())][0]['DISPLAYNAME']
            t['MESSAGE'] = f"{label1} ({dt1}) is supposed to be after or same as {label2} ({dt2}). But it is not"

    if(date1_rel_with_date2 == "LT"):
        if(dt1 >= dt2):  
            t['FIELD'] = date1_key.upper()
            label1 = [lab for lab in metadata if (lab['FIELD'] == t['FIELD'] and lab['TABLE'] == t['TABLE'])][0]['DISPLAYNAME']
            label2 = [lab for lab in metadata if (lab['FIELD'] == date2_key.upper() and lab['TABLE'] == parent_table_name2.upper())][0]['DISPLAYNAME']
            t['MESSAGE'] = f"{label1} ({dt1}) is supposed to be before {label2} ({dt2}). But it is not"
        
    if(date1_rel_with_date2 == "LT_E"):
        if(dt1 > dt2):  
            t['FIELD'] = date1_key.upper()
            label1 = [lab for lab in metadata if (lab['FIELD'] == t['FIELD'] and lab['TABLE'] == t['TABLE'])][0]['DISPLAYNAME']
            label2 = [lab for lab in metadata if (lab['FIELD'] == date2_key.upper() and lab['TABLE'] == parent_table_name2.upper())][0]['DISPLAYNAME']
            t['MESSAGE'] = f"{label1} ({dt1}) is supposed to be before or same as {label2} ({dt2}). But it is not"
    
    if('MESSAGE' in t.keys()):
        buff.append(t)



def log_date_error(parent_dict, parent_table_name, dt_key, buff, metadata):
    try: 
        if(dt_key in parent_dict.keys()):
            # print(':::: >>>  ',parent_dict[dt_key])
            datetime.strptime(parent_dict[dt_key], "%Y-%m-%d").date()
    except ValueError as e:
        user_friendly_message = str(e).replace('%Y-%m-%d','YYYY-MM-DD')
        t = {}
        t['TABLE'] = parent_table_name.upper()
        t['ID'] = parent_dict['ID']
        t['FIELD'] = dt_key.upper()
        label = [lab for lab in metadata if (lab['FIELD'] == t['FIELD'] and lab['TABLE'] == t['TABLE'])][0]['DISPLAYNAME']
        t['MESSAGE'] = f"\"{label}\" has a problem: {user_friendly_message }."
        buff.append(t)


def log_amount_error(parent_dict, parent_table_name, amt_key, buff, metadata):
    try:
        if(amt_key in parent_dict.keys()):
            parent_dict[amt_key] = float(parent_dict[amt_key]) # we do this in case front end send us string but the value is valid
    except ValueError as e:
        user_friendly_message = str(e).replace('string to float',f"this to valid a numeric value: ") 
        t = {}
        t['TABLE'] = parent_table_name.upper()
        t['ID'] = parent_dict['ID']
        t['FIELD'] = amt_key.upper()
        label = [lab for lab in metadata if (lab['FIELD'] == t['FIELD'] and lab['TABLE'] == t['TABLE'])][0]['DISPLAYNAME']
        t['MESSAGE'] = f"\"{label}\" has a problem: {user_friendly_message}."
        buff.append(t)



def run_loan_info_level_checks(loan_terms, warning_buffer, errors_buffer, metadata):
    
    # Are all required fields present
    required_fields = ['ID','NAME','LLC_BI__AMOUNT__C','LLC_BI__MATURITY_DATE__C','LLC_BI__CLOSEDATE__C',
                                'LLC_BI__FIRST_PAYMENT_DATE__C','LLC_BI__FUNDING_AT_CLOSE__C']
    log_required_fields_error(loan_terms, 'LOAN_INFO',required_fields, errors_buffer, metadata)

    
    #Are all dates in proper format
    date_fields = [key for key in loan_terms.keys() if 'DATE' in key and key in required_fields]
    for dt_key in date_fields:
        log_date_error(loan_terms, 'LOAN_INFO', dt_key, errors_buffer, metadata)

    #Are numeric fields in proper format
    amount_fields = ['LLC_BI__AMOUNT__C','LLC_BI__FUNDING_AT_CLOSE__C']
    for amt_key in amount_fields:
        log_amount_error(loan_terms, 'LOAN_INFO', amt_key, errors_buffer, metadata)


    #ensure that required Array's have data
    if('PRICING_DETAILS' not in loan_terms.keys() or  len(loan_terms['PRICING_DETAILS']) == 0):
        quick_message_maker('LOAN_INFO',"Pricing Details are required.", errors_buffer)

    if('PRICING_DETAILS' not in loan_terms.keys() or  len(loan_terms['PRICING_DETAILS']) == 0):
        quick_message_maker('LOAN_INFO',"Payment Details are required.", errors_buffer)
        
    if('FEE_DETAILS' not in loan_terms.keys() or  len(loan_terms['FEE_DETAILS']) == 0):
        quick_message_maker('LOAN_INFO', "Fee Details are missing.", warning_buffer)

    if('DRAW_DETAILS' not in loan_terms.keys() or  len(loan_terms['DRAW_DETAILS']) == 0):
        quick_message_maker('LOAN_INFO', "Draw Details are missing. If \"Funded At Closing\" amount is provided, that will be the only draw on this deal", warning_buffer)


    log_date_relationship_error(loan_terms, 'LOAN_INFO' ,'LLC_BI__CLOSEDATE__C',
                                loan_terms, 'LOAN_INFO' ,'LLC_BI__MATURITY_DATE__C',"LT", errors_buffer, metadata)
        
        


def run_pricing_details_related_checks(loan_terms, warning_buffer, errors_buffer, metadata):
    
    for pricing_zone in loan_terms['PRICING_DETAILS']:
        
        # Are all required fields present
        required_fields = ['CM_PARTIAL_PERIOD_INTERST_ACCRUAL_METHOD__C','CM_INTEREST_ACCRUAL_METHOD__C','LLC_BI__EFFECTIVE_DATE__C_Y',
                           'LLC_BI__TERM_LENGTH__C_Y','LLC_BI__TERM_UNIT__C_Y','LLC_BI__INTEREST_RATE_TYPE__C']
        
        if('LLC_BI__INTEREST_RATE_TYPE__C' in pricing_zone):
            interest_rate_type = pricing_zone["LLC_BI__INTEREST_RATE_TYPE__C"]
            if interest_rate_type == "Fixed":
                required_fields.append("LLC_BI__ALL_IN_RATE__C")
            else: 
                required_fields.append("LLC_BI__INDEX__C")
                
        
        log_required_fields_error(pricing_zone, 'PRICING', required_fields, errors_buffer, metadata)
    
        #Are all dates in proper format
        date_fields = [key for key in pricing_zone.keys() if 'DATE' in key and key in required_fields]
        for dt_key in date_fields:
            log_date_error(pricing_zone, 'PRICING', dt_key, errors_buffer, metadata)
    
        #Minor Warning
        if interest_rate_type != "Fixed":
            if("LLC_BI__RATE_FLOOR__C" not in pricing_zone.keys()):
                t = {}
                t['TABLE'] = 'PRICING'
                t['ID'] = pricing_zone['ID']
                t['FIELD'] = 'LLC_BI__RATE_FLOOR__C'
                label = [lab for lab in metadata if (lab['FIELD'] == t['FIELD'] and lab['TABLE'] == t['TABLE'])][0]['DISPLAYNAME']
                t['MESSAGE'] = f"{label} is required for when dealing with Floating Rate pricing. 0% floor will be assumed"                
                warning_buffer.append(t)

            if("LLC_BI__RATE_CEILING__C" not in pricing_zone.keys()):
                t = {}
                t['TABLE'] = 'PRICING'
                t['ID'] = pricing_zone['ID']
                t['FIELD'] = 'LLC_BI__RATE_CEILING__C'
                label = [lab for lab in metadata if (lab['FIELD'] == t['FIELD'] and lab['TABLE'] == t['TABLE'])][0]['DISPLAYNAME']
                t['MESSAGE'] = f"{label} is required for when dealing with Floating Rate pricing. There will be no ceiling"                
                warning_buffer.append(t)

            if("LLC_BI__SPREAD__C" not in pricing_zone.keys()):
                t = {}
                t['TABLE'] = 'PRICING'
                t['ID'] = pricing_zone['ID']
                t['FIELD'] = 'LLC_BI__SPREAD__C'
                label = [lab for lab in metadata if (lab['FIELD'] == t['FIELD'] and lab['TABLE'] == t['TABLE'])][0]['DISPLAYNAME']
                t['MESSAGE'] = f"{label} is required for when dealing with Floating Rate pricing. 0% Spread will be assumed"                
                warning_buffer.append(t)
            

def run_payment_details_related_checks(loan_terms, warning_buffer, errors_buffer, metadata):
    
    for payment_zone in loan_terms['PAYMENT_DETAILS']:
        # Are all required fields present
        required_fields = ['LLC_BI__PAYMENT_TYPE__C','LLC_BI__EFFECTIVE_DATE__C_Y','LLC_BI__TERM_LENGTH__C_Y',
                           'LLC_BI__TERM_UNIT__C_Y','LLC_BI__FREQUENCY__C'
                          ]
        # Check that Amortization info is provided
        if('principal' in payment_zone['LLC_BI__TYPE__C'].lower()):
            required_fields.append('CM_AMORTIZED_TERM_MONTHS__C')
        log_required_fields_error(payment_zone, 'PAYMENT', required_fields, errors_buffer, metadata)
            

        #Are all dates in proper format - we are only going to check values of fields that are required
        date_fields = [key for key in payment_zone.keys() if 'DATE' in key]
        for dt_key in date_fields:
            log_date_error(payment_zone, 'PAYMENT', dt_key, errors_buffer, metadata)


            


def run_draw_details_related_checks(loan_terms, warning_buffer, errors_buffer, metadata):

    if 'DRAW_DETAILS' not in loan_terms.keys() or len(loan_terms['DRAW_DETAILS']) == 0:
        return  # No draws to validate

    # Separate draws into two categories
    funded_at_closing_draws = []
    other_draws = []

    for draw in loan_terms['DRAW_DETAILS']:
        # Check if this is "Funded at Closing" (case-insensitive) and NOT a MADE_UP_ ID
        paid_at_closing = draw.get('LLC_BI__PAID_AT_CLOSING__C', '').lower()
        draw_id = draw.get('ID', '')

        if paid_at_closing == 'funded at closing' and not draw_id.startswith('MADE_UP_'):
            funded_at_closing_draws.append(draw)
        else:
            other_draws.append(draw)

    # Rule 1: Warning for "Funded at Closing" draws that will be combined
    if len(funded_at_closing_draws) > 0:
        draw_descriptions = []
        for draw in funded_at_closing_draws:
            fee_type = draw.get('LLC_BI__FEE_TYPE__C', 'Unknown')
            name = draw.get('NAME', draw.get('ID', 'Unknown'))
            draw_descriptions.append(f"{fee_type} ({name})")
        draw_list = ', '.join(draw_descriptions)
        message = f"The following draws will be combined into a single Funded At Close Reserve bucket: {draw_list}"
        quick_message_maker('DRAW', message, warning_buffer)

    # Rule 2: Required fields validation for other draws
    required_fields = ['LLC_BI__AMOUNT__C', 'CM_FEE_DATE__C', 'CM_END_DATE__C', 'LLC_BI__FEE_TYPE__C']
    for draw in other_draws:
        log_required_fields_error(draw, 'DRAW', required_fields, errors_buffer, metadata)

        # Validate date formats
        log_date_error(draw, 'DRAW', 'CM_FEE_DATE__C', errors_buffer, metadata)
        log_date_error(draw, 'DRAW', 'CM_END_DATE__C', errors_buffer, metadata)

        # Validate amount format
        log_amount_error(draw, 'DRAW_DETAILS', 'LLC_BI__AMOUNT__C', errors_buffer, metadata)

        # Rule 4: Date relationship - CM_END_DATE__C >= CM_FEE_DATE__C
        log_date_relationship_error(draw, 'DRAW', 'CM_END_DATE__C',
                                    draw, 'DRAW', 'CM_FEE_DATE__C', 'GT_E', errors_buffer, metadata)

    # Rule 3: Sum validation - other draws should sum to loan amount
    if 'LLC_BI__AMOUNT__C' in loan_terms.keys():
        try:
            total_loan_amount = float(loan_terms['LLC_BI__AMOUNT__C'])
            total_draws = 0.0

            for draw in other_draws:
                if 'LLC_BI__AMOUNT__C' in draw.keys():
                    try:
                        total_draws += float(draw['LLC_BI__AMOUNT__C'])
                    except (ValueError, TypeError):
                        pass  # Skip invalid amounts, they'll be caught by log_amount_error

            # Compare with a small tolerance for floating-point precision
            if abs(total_draws - total_loan_amount) > 0.01:
                message = f"Total draw amounts (${total_draws:,.2f}) do not add up to total loan amount (${total_loan_amount:,.2f})"
                quick_message_maker('DRAW', message, warning_buffer)
        except (ValueError, TypeError):
            pass  # Skip if loan amount is invalid


def validate_loan_terms(loan_terms):
    metadata = get_loan_terms_metadata()
    warning_buffer = []
    errors_buffer = []

    run_loan_info_level_checks(loan_terms, warning_buffer, errors_buffer, metadata)
    run_pricing_details_related_checks(loan_terms, warning_buffer, errors_buffer, metadata)
    run_payment_details_related_checks(loan_terms, warning_buffer, errors_buffer, metadata)
    run_draw_details_related_checks(loan_terms, warning_buffer, errors_buffer, metadata)


    #some additional cross-table checks
    does_any_date_match = False
    for pricing_zone in loan_terms['PRICING_DETAILS']:
        does_any_date_match = False

        if('LLC_BI__CLOSEDATE__C' in loan_terms.keys()):
            closing_date = loan_terms['LLC_BI__CLOSEDATE__C']
            if('LLC_BI__EFFECTIVE_DATE__C_Y' in pricing_zone.keys()):
                effective_date = pricing_zone['LLC_BI__EFFECTIVE_DATE__C_Y']
                # print(":::::::*********::::::::",closing_date, effective_date)
                if(closing_date == effective_date):
                    does_any_date_match = True
                    break

    if(not does_any_date_match):
        quick_message_maker('PRICING',"At least one of the Pricing streams should start on the Closing Date, but none do", errors_buffer)

    does_any_date_match = False
    for payment_zone in loan_terms['PAYMENT_DETAILS']:
        does_any_date_match = False

        if('LLC_BI__FIRST_PAYMENT_DATE__C' in loan_terms.keys()):
            first_payment = loan_terms['LLC_BI__FIRST_PAYMENT_DATE__C']
            if('LLC_BI__EFFECTIVE_DATE__C_Y' in payment_zone.keys()):
                effective_date = payment_zone['LLC_BI__EFFECTIVE_DATE__C_Y']
                # print(":::::::*********::::::::",first_payment, effective_date) 
                if(first_payment == effective_date):
                    does_any_date_match = True
                    break

    if(not does_any_date_match):
        quick_message_maker('PAYMENT',"At least one of the Payment streams should start on the First Payment Date, but none do", errors_buffer)

    return warning_buffer, errors_buffer

#X5xPIoRTLKIdaAkaZ9GR6QOtJe33wTeb4Vl1q4rAdKx1sWLC#MQEi4GgQHYOCMiRf0A6-Wfef9bg_9V7y2WlduUNebME