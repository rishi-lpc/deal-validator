"""
Azure Function App for Deal Validation
======================================
Wrapper for core validation functionality.
Exposes HTTP endpoints for validation, search, and health checks.
"""

import json
import logging
import azure.functions as func
from core.json_driven_validator import JSONValidator
from core.salesforce_fetcher import SalesforceFetcher
from core.config import SALESFORCE_CREDENTIALS

# Initialize Function App
app = func.FunctionApp()

# Initialize services (reuse across function invocations)
fetcher = SalesforceFetcher(**SALESFORCE_CREDENTIALS)
validator = JSONValidator()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    logger.info('Health check endpoint called')

    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "service": "Deal Validator",
            "version": "1.0"
        }),
        mimetype="application/json",
        status_code=200
    )


@app.route(route="validate/id/{loan_id}", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def validate_by_id(req: func.HttpRequest) -> func.HttpResponse:
    """
    Validate loan by ID.

    URL: /api/validate/id/{loan_id}
    Method: GET
    """
    logger.info('Validate by ID endpoint called')

    try:
        # Get loan ID from route parameter
        loan_id = req.route_params.get('loan_id')

        if not loan_id:
            return func.HttpResponse(
                json.dumps({"error": "loan_id is required"}),
                mimetype="application/json",
                status_code=400
            )

        # Fetch loan
        logger.info(f'Fetching loan ID: {loan_id}')
        loan_terms = fetcher.get_loan_terms_by_id(loan_id)

        # Validate
        logger.info(f'Validating loan: {loan_terms["NAME"]}')
        warnings, errors = validator.validate(loan_terms)

        # Build response
        result = {
            "LOAN_NAME": loan_terms['NAME'],
            "LOAN_ID": loan_terms['ID'],
            "LOAN_AMOUNT": loan_terms.get('LLC_BI__AMOUNT__C'),
            "CLOSE_DATE": loan_terms.get('LLC_BI__CLOSEDATE__C'),
            "WARNINGS": warnings,
            "ERRORS": errors,
            "validation_passed": len(errors) == 0
        }

        logger.info(f'Validation complete: {len(errors)} errors, {len(warnings)} warnings')

        return func.HttpResponse(
            json.dumps(result, indent=2, default=str),
            mimetype="application/json",
            status_code=200
        )

    except ValueError as e:
        logger.error(f'ValueError: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=404
        )
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}', exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="validate/name", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def validate_by_name(req: func.HttpRequest) -> func.HttpResponse:
    """
    Validate loan by name.

    URL: /api/validate/name
    Method: POST
    Body: {"loan_name": "Canyon Valley - Mezz", "exact_match": true}
    """
    logger.info('Validate by name endpoint called')

    try:
        # Parse request body
        req_body = req.get_json()
        loan_name = req_body.get('loan_name')
        exact_match = req_body.get('exact_match', True)

        if not loan_name:
            return func.HttpResponse(
                json.dumps({"error": "loan_name is required in request body"}),
                mimetype="application/json",
                status_code=400
            )

        # Fetch loan
        logger.info(f'Fetching loan by name: {loan_name} (exact_match={exact_match})')
        loan_terms = fetcher.get_loan_terms_by_name(loan_name, exact_match=exact_match)

        # Validate
        logger.info(f'Validating loan: {loan_terms["NAME"]}')
        warnings, errors = validator.validate(loan_terms)

        # Build response
        result = {
            "LOAN_NAME": loan_terms['NAME'],
            "LOAN_ID": loan_terms['ID'],
            "LOAN_AMOUNT": loan_terms.get('LLC_BI__AMOUNT__C'),
            "CLOSE_DATE": loan_terms.get('LLC_BI__CLOSEDATE__C'),
            "WARNINGS": warnings,
            "ERRORS": errors,
            "validation_passed": len(errors) == 0
        }

        logger.info(f'Validation complete: {len(errors)} errors, {len(warnings)} warnings')

        return func.HttpResponse(
            json.dumps(result, indent=2, default=str),
            mimetype="application/json",
            status_code=200
        )

    except ValueError as e:
        logger.error(f'ValueError: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=404
        )
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}', exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="search", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def search_loans(req: func.HttpRequest) -> func.HttpResponse:
    """
    Search for loans by name prefix.

    URL: /api/search?prefix=Canyon
    Method: GET
    Query Params: prefix (required)
    """
    logger.info('Search loans endpoint called')

    try:
        # Get search prefix from query params
        prefix = req.params.get('prefix')

        if not prefix:
            return func.HttpResponse(
                json.dumps({"error": "prefix query parameter is required"}),
                mimetype="application/json",
                status_code=400
            )

        # Search loans
        logger.info(f'Searching for loans with prefix: {prefix}')
        loans = fetcher.search_loans(name_prefix=prefix)

        result = {
            "search_prefix": prefix,
            "count": len(loans),
            "loans": [
                {
                    "NAME": loan['NAME'],
                    "ID": loan['ID']
                }
                for loan in loans
            ]
        }

        logger.info(f'Found {len(loans)} loans')

        return func.HttpResponse(
            json.dumps(result, indent=2),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}', exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="validate/batch", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def validate_batch(req: func.HttpRequest) -> func.HttpResponse:
    """
    Validate multiple loans in batch.

    URL: /api/validate/batch
    Method: POST
    Body: {"loan_ids": ["a0ial00000364X3AAI", "a0iVy00000ETkIkIAL"]}
    """
    logger.info('Batch validation endpoint called')

    try:
        # Parse request body
        req_body = req.get_json()
        loan_ids = req_body.get('loan_ids', [])

        if not loan_ids or not isinstance(loan_ids, list):
            return func.HttpResponse(
                json.dumps({"error": "loan_ids array is required in request body"}),
                mimetype="application/json",
                status_code=400
            )

        results = []

        for loan_id in loan_ids:
            try:
                logger.info(f'Validating loan ID: {loan_id}')

                # Fetch and validate
                loan_terms = fetcher.get_loan_terms_by_id(loan_id)
                warnings, errors = validator.validate(loan_terms)

                results.append({
                    "LOAN_NAME": loan_terms['NAME'],
                    "LOAN_ID": loan_terms['ID'],
                    "WARNINGS": warnings,
                    "ERRORS": errors,
                    "validation_passed": len(errors) == 0
                })

            except Exception as e:
                logger.error(f'Error validating loan {loan_id}: {str(e)}')
                results.append({
                    "LOAN_ID": loan_id,
                    "error": str(e),
                    "validation_passed": False
                })

        response = {
            "total_loans": len(loan_ids),
            "results": results
        }

        logger.info(f'Batch validation complete: {len(results)} loans processed')

        return func.HttpResponse(
            json.dumps(response, indent=2, default=str),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}', exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )
