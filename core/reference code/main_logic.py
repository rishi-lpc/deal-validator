"""
Business logic for Amortization Engine API endpoints.
This file can be copied between funcapp/ and server/ folders.
Framework-agnostic - no Azure or Flask dependencies.
"""

import pandas as pd
import numpy as np
import io

from step0 import get_loan_terms, get_loan_list
from step1 import generate_accrual_schedule
from step2 import form_transactions
from step3 import merge_transactions_into_schedule
from step4 import generate_interest_and_pik_multipliers
from step5 import calculate_interest_principal_pik_and_cap_draws
from step6 import add_fees
from step99 import prepare_for_client, compute_cashflows, calculate_IRR, calculate_MOIC, calculate_XIRR
from step7_pref_equity import calculate_pref_equity_catch_up
from validator import validate_loan_terms


# ============================================================================
# Utility Functions
# ============================================================================

def dict_keys_upper(d):
    """Recursively convert all dictionary keys to uppercase."""
    if isinstance(d, dict):
        return {k.upper(): dict_keys_upper(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [dict_keys_upper(i) for i in d]
    else:
        return d


def make_json_safe(obj):
    """Recursively convert pandas/numpy/unsupported types to JSON-safe types."""
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    if isinstance(obj, (pd.Series, np.ndarray)):
        return obj.tolist()
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    return obj


def outbound_special_changes_for_signal(loan_term):
    """Restructure loan terms for Signal API output format."""
    all_loan_level_details = {}
    keys_to_del = []
    for k in loan_term.keys():
        if('PRICING_DETAILS' in k or 'PAYMENT_DETAILS' in k or 'FEE_DETAILS' in k or 'DRAW_DETAILS' in k):
            pass
        else:
            all_loan_level_details[k] = loan_term[k]
            keys_to_del.append(k)

    for d in keys_to_del:
        del loan_term[d]

    loan_term['LOAN_INFO'] = []
    loan_term['LOAN_INFO'].append(all_loan_level_details)

    return loan_term


def inbound_special_changes_for_signal(loan_terms):
    """Restructure incoming loan terms from Signal API format."""
    loan_info_obj = loan_terms['LOAN_INFO'][0]  # it is an array with just one element

    if('LOAN_INFO' in loan_terms.keys()):
        for k in loan_info_obj.keys():
            loan_terms[k] = loan_info_obj[k]

    del loan_terms["LOAN_INFO"]

    return loan_terms


# ============================================================================
# Business Logic Functions
# ============================================================================

def get_loan_details_logic(loan_id):
    """Get loan details by loan ID.

    Args:
        loan_id: The loan identifier

    Returns:
        dict: Loan terms
    """
    loan_terms = get_loan_terms(loan_id)
    return loan_terms


def get_loan_list_logic(starts_with=None, force_update=False, cached_list=None):
    """Get list of loans, optionally filtered by name prefix.

    Args:
        starts_with: Optional prefix to filter loan names
        force_update: Force refresh of cached loan list
        cached_list: Previously cached loan list (or None)

    Returns:
        tuple: (filtered_loan_list, updated_cache)
    """
    loan_list_data = None

    if cached_list and not force_update:
        loan_list_data = cached_list
    else:
        loan_list_data = get_loan_list()

    if starts_with:
        ret_val = [item for item in loan_list_data if item['NAME'].lower().startswith(starts_with)]
    else:
        ret_val = loan_list_data

    return ret_val, loan_list_data


def run_amortization_logic(
    loan_id=None,
    loan_terms=None,
    scenario="At Underwriting",
    run_name=None,
    skip_validation=False,
    request_method="GET",
    write_debug_files=False
):
    """Execute amortization calculation with validation.

    Args:
        loan_id: Loan ID to fetch terms (if loan_terms not provided)
        loan_terms: Loan terms dict (if already loaded)
        scenario: Scenario name (default "At Underwriting")
        run_name: Name for this run (used in DRAFT runs)
        skip_validation: Skip validation checks
        request_method: "GET" or "POST" (affects run_type)
        write_debug_files: Write intermediate Excel files for debugging

    Returns:
        dict: Response with structure:
            {
                'loan_terms': {...},
                'Warnings': [...],
                'Errors': [...],
                'amort_tables': [...]  # if validation passes
            }
    """
    # Get loan terms if not provided
    if not loan_terms:
        loan_terms = get_loan_terms(loan_id)

    # Uppercase all keys
    loan_terms = dict_keys_upper(loan_terms)

    # Write debug file if requested (Flask local debugging)
    if write_debug_files:
        import json
        with open('loan_terms.json', 'w') as f:
            json.dump(loan_terms, f, sort_keys=True, indent=4)

    # Validation
    validator_warning_buffer = None
    validator_error_buffer = None
    fatal_validator_error = 0

    if not skip_validation:
        validator_warning_buffer, validator_error_buffer = validate_loan_terms(loan_terms)
        fatal_validator_error = len(validator_error_buffer)

    # Initialize return values
    stage1_with_fees = None
    irr_val = 0
    xirr_val = 0
    moic_val = 0
    pref_metrics = None
    types = None

    # Only run calculations if validation passes
    if fatal_validator_error == 0:
        # Core amortization calculation pipeline
        accrual_schedule = generate_accrual_schedule(loan_terms)
        transactions = form_transactions(loan_terms, 'At Underwriting', '2025-03-01')
        merged_transactions_with_draws = merge_transactions_into_schedule(
            loan_terms, accrual_schedule, transactions
        )
        interest_and_pik_multiplier = generate_interest_and_pik_multipliers(
            loan_terms, merged_transactions_with_draws
        )
        a_b_amount_factor = loan_terms.get('A_B_AMOUNT_FACTOR', 1)
        stage1 = calculate_interest_principal_pik_and_cap_draws(
            interest_and_pik_multiplier, a_b_amount_factor
        )
        stage1_with_fees = add_fees(loan_terms, stage1)

        # Write debug file if requested (Flask local debugging)
        if write_debug_files:
            stage1_with_fees.to_excel('./pre-final.xlsx')

        # Extract pref equity params from pricing details BEFORE prepare_for_client
        target_irr = None
        min_moic = None

        pricing_details = loan_terms.get('PRICING_DETAILS', [])
        if pricing_details:
            for pricing in pricing_details:
                target_irr = pricing.get('CM_MAXIMUM_EXIT_IRR__C')
                min_moic = pricing.get('CM_MINIMUM_EXIT_MULTIPLE__C')
                if target_irr is not None or min_moic is not None:
                    print(f"Found pref equity params: TARGET_IRR={target_irr}, MIN_MOIC={min_moic}")
                    break

        # Apply pref equity catch-up BEFORE prepare_for_client
        if target_irr is not None or min_moic is not None:
            try:
                stage1_with_fees, pref_metrics = calculate_pref_equity_catch_up(
                    stage1_with_fees,
                    target_irr=target_irr,
                    min_moic=min_moic
                )
                print(f"Pref Equity Catch-Up Applied: ${pref_metrics['total_catch_up']:,.2f}")
                if pref_metrics['resulting_irr_annual'] is not None:
                    print(f"Resulting Annual IRR: {pref_metrics['resulting_irr_annual']:.2%}")
                print(f"Resulting MOIC: {pref_metrics['resulting_moic']:.2f}x")
            except Exception as e:
                print(f"Warning: Pref equity calculation failed: {e}")

        # Prepare for client
        stage1_with_fees, types = prepare_for_client(stage1_with_fees)

        # Write debug file if requested (Flask local debugging)
        if write_debug_files:
            stage1_with_fees.to_excel('./final.xlsx')

        # Compute metrics
        compute_cashflows(stage1_with_fees)
        irr_val = calculate_IRR(stage1_with_fees) * 12
        xirr_val = calculate_XIRR(stage1_with_fees)
        moic_val = calculate_MOIC(stage1_with_fees)

        # Write debug file if requested (Flask local debugging)
        if write_debug_files:
            stage1_with_fees.to_excel('./final_with_cash_flow.xlsx')
            print("IRR:", irr_val)
            print("XIRR:", xirr_val)
            print("MOIC:", moic_val)

    # Build response
    ret_val = {}
    ret_val['loan_terms'] = outbound_special_changes_for_signal(loan_terms)
    ret_val['Warnings'] = validator_warning_buffer
    ret_val['Errors'] = validator_error_buffer

    if fatal_validator_error == 0:
        ret_val['amort_tables'] = []

        # Build metrics dictionary
        metrics_dict = {
            "irr": str(round(irr_val*100, 3)) + "%",
            "xirr": str(round(xirr_val*100, 3)) + "%",
            "moic": str(round(moic_val, 3)) if moic_val else '-'
        }

        # Add pref_irr for pref equity deals (using simple IRR: monthly * 12)
        if pref_metrics is not None and pref_metrics.get('resulting_irr_periodic') is not None:
            pref_irr_simple = pref_metrics['resulting_irr_periodic'] * 12
            metrics_dict["pref_irr"] = str(round(pref_irr_simple*100, 3)) + "%"

        # Determine run type based on request method
        if request_method == "GET":
            ret_val['amort_tables'].append({
                "scenario": "At Underwriting",
                "run_type": "FINAL",
                "run_name": "FINAL",
                "data": stage1_with_fees.to_dict('records'),
                "metrics": metrics_dict,
                "metadata": types
            })
        else:
            ret_val['amort_tables'].append({
                "scenario": "At Underwriting",
                "run_type": "DRAFT",
                "run_name": run_name,
                "data": stage1_with_fees.to_dict('records'),
                "metrics": metrics_dict,
                "metadata": types
            })

    ret_val = dict_keys_upper(ret_val)

    return ret_val


def generate_amort_excel_logic(loan_id):
    """Generate amortization table and return as Excel BytesIO.

    Args:
        loan_id: The loan identifier

    Returns:
        tuple: (BytesIO excel file, filename)
    """
    loan_terms = get_loan_terms(loan_id)
    accrual_schedule = generate_accrual_schedule(loan_terms)
    transactions = form_transactions(loan_terms, 'At Underwriting', '2025-03-01')

    merged_transactions_with_draws = merge_transactions_into_schedule(
        loan_terms, accrual_schedule, transactions
    )
    interest_and_pik_multiplier = generate_interest_and_pik_multipliers(
        loan_terms, merged_transactions_with_draws
    )
    a_b_amount_factor = loan_terms.get('A_B_AMOUNT_FACTOR', 1)
    stage1 = calculate_interest_principal_pik_and_cap_draws(
        interest_and_pik_multiplier, a_b_amount_factor
    )
    stage1_with_fees = add_fees(loan_terms, stage1)

    # Write to in-memory BytesIO
    output = io.BytesIO()
    stage1_with_fees.to_excel(output, index=False)
    output.seek(0)

    filename = f"{loan_terms['NAME']}.xlsx"

    return output, filename
