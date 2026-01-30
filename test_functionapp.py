#!/usr/bin/env python
"""
Test script to verify functionapp.py can import and use core modules.
This simulates what happens when Azure Functions loads the function app.
"""

import json
import sys

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")

    try:
        from core.json_driven_validator import JSONValidator
        from core.salesforce_fetcher import SalesforceFetcher
        from core.config import SALESFORCE_CREDENTIALS
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_validator():
    """Test validator functionality."""
    print("\nTesting validator...")

    try:
        from core.json_driven_validator import JSONValidator
        from core.salesforce_fetcher import SalesforceFetcher
        from core.config import SALESFORCE_CREDENTIALS

        # Initialize
        fetcher = SalesforceFetcher(**SALESFORCE_CREDENTIALS)
        validator = JSONValidator()

        # Fetch a loan
        loan_id = "a0ial00000554ePAAQ"
        print(f"  Fetching loan: {loan_id}")
        loan_terms = fetcher.get_loan_terms_by_id(loan_id)
        print(f"  ✓ Fetched: {loan_terms['NAME']}")

        # Validate
        print(f"  Validating...")
        warnings, errors = validator.validate(loan_terms)
        print(f"  ✓ Validation complete: {len(errors)} errors, {len(warnings)} warnings")

        # Build result (like function app does)
        result = {
            "LOAN_NAME": loan_terms['NAME'],
            "LOAN_ID": loan_terms['ID'],
            "WARNINGS": warnings,
            "ERRORS": errors,
            "validation_passed": len(errors) == 0
        }

        print("\n  Result preview:")
        print(f"    Loan: {result['LOAN_NAME']}")
        print(f"    Errors: {len(result['ERRORS'])}")
        print(f"    Warnings: {len(result['WARNINGS'])}")
        print(f"    Passed: {result['validation_passed']}")

        return True

    except Exception as e:
        print(f"❌ Validator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search():
    """Test search functionality."""
    print("\nTesting search...")

    try:
        from core.salesforce_fetcher import SalesforceFetcher
        from core.config import SALESFORCE_CREDENTIALS

        fetcher = SalesforceFetcher(**SALESFORCE_CREDENTIALS)

        # Search
        prefix = "Canyon"
        print(f"  Searching for: {prefix}")
        loans = fetcher.search_loans(name_prefix=prefix)
        print(f"  ✓ Found {len(loans)} loans")

        return True

    except Exception as e:
        print(f"❌ Search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*70)
    print("Function App Integration Test")
    print("="*70)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Validator", test_validator()))
    results.append(("Search", test_search()))

    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {test_name}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print(f"\nResults: {passed_count}/{total_count} tests passed")
    print("="*70)

    sys.exit(0 if passed_count == total_count else 1)
