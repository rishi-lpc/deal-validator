"""
Flask App Wrapper for Amortization Engine (Local Testing).
Framework-specific request/response handling only.
All business logic is in main_logic.py
"""

from flask import Flask, request, send_file
import json

from main_logic import (
    get_loan_details_logic,
    get_loan_list_logic,
    run_amortization_logic,
    generate_amort_excel_logic,
    inbound_special_changes_for_signal,
    dict_keys_upper
)
import data_loader_utils as dlu
from step0 import get_loan_terms
from validator import validate_loan_terms

# Global cache for loan list
global global_loan_list
global_loan_list = None

# Create the Flask application
app = Flask(__name__)


@app.route('/get_loan_details', methods=['GET'])
def get_loan_details():
    """Get loan details by loan ID."""
    # Extract parameters
    loan_id = request.args.get('loan_id')

    # Validate
    if not loan_id:
        return {"error": "Missing loan_id parameter"}, 400

    # Call business logic
    result = get_loan_details_logic(loan_id)

    # Format response
    return result


@app.route('/get_loan_list', methods=['GET'])
def loan_list():
    """Get list of all loans, optionally filtered by name prefix."""
    global global_loan_list

    # Extract parameters
    starts_with = None
    if request.args.get('starts_with'):
        starts_with = request.args.get('starts_with').lower()

    # Note: Flask version doesn't support force_update parameter
    # (kept simple for local testing)

    # Call business logic
    result, global_loan_list = get_loan_list_logic(
        starts_with=starts_with,
        force_update=False,
        cached_list=global_loan_list
    )

    # Format response
    return result


@app.route('/get_run_test', methods=['GET', 'POST'])
def get_run():
    """Run amortization calculation with validation."""
    # Extract loan terms from POST body if present
    loan_terms = None
    if request.method == 'POST':
        loan_terms = request.get_json()['loan_terms']
        loan_terms = inbound_special_changes_for_signal(loan_terms)

    # Extract query parameters
    loan_id = None
    if request.args.get('loan_id'):
        loan_id = request.args.get('loan_id')

    scenario = "At Underwriting"
    if request.args.get('scenario'):
        scenario = request.args.get('scenario')

    run_name = None
    if request.args.get('run_name'):
        run_name = request.args.get('run_name')

    skip_validation = request.args.get('skip_validation')
    if skip_validation:
        skip_validation = (skip_validation.lower() == "true")

    # Call business logic (Flask writes debug files for local testing)
    result = run_amortization_logic(
        loan_id=loan_id,
        loan_terms=loan_terms,
        scenario=scenario,
        run_name=run_name,
        skip_validation=skip_validation,
        request_method=request.method,
        write_debug_files=True  # Flask writes debug files for local testing
    )

    # Format response
    return result


@app.route('/process_loan', methods=['GET', 'POST'])
def process_loan():
    """Generate Excel amortization table for download (alternative endpoint)."""
    # Extract loan terms from POST body
    loan_terms = request.get_json()['loan_terms']
    print(loan_terms.keys())

    if request.method == 'POST':
        loan_terms = inbound_special_changes_for_signal(loan_terms)

    # Extract query parameters
    loan_id = None
    if request.args.get('loan_id'):
        loan_id = request.args.get('loan_id')

    # Note: This endpoint uses loan_terms from POST but could also use loan_id
    # For now, keeping the original logic which uses loan_terms directly

    # Call business logic using loan_terms directly
    # (This is a bit different from generate_amort which uses loan_id)
    from step1 import generate_accrual_schedule
    from step2 import form_transactions
    from step3 import merge_transactions_into_schedule
    from step4 import generate_interest_and_pik_multipliers
    from step5 import calculate_interest_principal_pik_and_cap_draws
    from step6 import add_fees
    from step99 import prepare_for_client, compute_cashflows
    from step7_pref_equity import calculate_pref_equity_catch_up
    import io

    if not loan_terms:
        loan_terms = get_loan_terms(loan_id)

    loan_terms = dict_keys_upper(loan_terms)

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
                break

    # Apply pref equity catch-up BEFORE prepare_for_client
    if target_irr is not None or min_moic is not None:
        try:
            stage1_with_fees, pref_metrics = calculate_pref_equity_catch_up(
                stage1_with_fees,
                target_irr=target_irr,
                min_moic=min_moic
            )
        except Exception as e:
            print(f"Warning: Pref equity calculation failed: {e}")

    stage1_with_fees, types = prepare_for_client(stage1_with_fees)
    stage1_with_fees.to_excel('./final.xlsx')

    # Compute cashflows
    compute_cashflows(stage1_with_fees)

    # Instead of writing to disk, write to an in-memory buffer
    output = io.BytesIO()
    stage1_with_fees.to_excel(output, index=False)
    output.seek(0)

    print(loan_terms.keys())

    filename = f"{loan_terms['NAME']}.xlsx"
    return send_file(
        output,
        download_name=filename,
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/validate_loans', methods=['GET'])
def validate_loans():
    """Validate all loans in a fund (Flask-only endpoint for batch validation)."""
    all_loans = loan_list()

    _CREDS = {
        "client_id": "3MVG9H_KVs6V9LiP4AGwr.K0ufOjN3I1poplR_fK9cg930ILmT47atYSm2YVbtP5mMQmL2IjW6L.RaERxoL.e",
        "client_secret": "FA512A88FAC1F97FAB9BC003158A8585589B9A9F3540ED9C7BC83627002E75FB",
        "client_url": "https://locustpoint.my.salesforce.com/services/oauth2/token",
    }
    sf = dlu.connect(_CREDS)
    df = dlu.get_sf_data(
        sf, "LLC_BI__LOAN__c",
        ["ID", "NAME", "CM_FUND__C", "LLC_BI__lookupKey__c", "LLC_BI__STATUS__C", "LLC_BI__STAGE__C", "LLC_BI__Product__c"]
    )

    df = df[
        (~df['LLC_BI__STATUS__C'].isin(['Declined', 'Withdrawn', 'Superseded'])) &
        (df['LLC_BI__STAGE__C'] != 'Complete') &
        (df['LLC_BI__PRODUCT__C'] != 'Main') &
        (df['CM_FUND__C'] == 'Fund III')
    ]

    df = df.sort_values(by='NAME', ascending=True)
    all_loans = df.to_dict('records')

    all_results = []
    i = 0
    for loan in all_loans:
        loan_id = loan['ID']
        loan_terms = get_loan_terms(loan_id)
        print(f"processing ID: {loan['ID']} ({loan['NAME']})")
        validator_warning_buffer, validator_error_buffer = validate_loan_terms(loan_terms)
        o = {}
        o['NAME'] = loan['NAME']
        o['ID'] = loan['ID']
        o['ERRORS'] = validator_error_buffer

        all_results.append(o)
        with open("data_file.json", "w") as write_file:
            json.dump(all_results, write_file, indent=4)

        print("Errors: \n", validator_error_buffer, "\n= = = = = = = = = = = = = = = = = = = = = = = = = =\n\n\n")

    return {}


@app.route('/')
def home():
    """Health check endpoint."""
    return 'Welcome to the Amortization Engine'


# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
