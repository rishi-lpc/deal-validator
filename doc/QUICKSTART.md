# Quick Start Guide

## Directory Structure

```
deal-validator/
├── core/                              # Business logic (deployed)
│   ├── config.py                      # Salesforce credentials
│   ├── salesforce_fetcher.py          # Salesforce connector
│   ├── json_driven_validator.py       # Validation engine
│   └── validation_rules.json          # Validation rules
│
├── regression_tests/                  # API endpoint tests
│   ├── test_by_id.sh                  # Test by ID endpoint
│   ├── test_by_name.sh                # Test by name endpoint
│   ├── test_batch.sh                  # Test batch endpoint
│   └── run_all_tests.sh               # Run all tests
│
├── functionapp.py                     # Azure Functions wrapper
└── test_functionapp.py                # Integration tests
```

## Local Testing (Without Azure Functions)

Test the core validator directly:

```bash
# Validate by loan ID
python -m core.json_driven_validator a0ial00000554ePAAQ

# Validate by loan name
python -m core.json_driven_validator "Canyon Valley - Mezz"

# Search for loans
python -m core.json_driven_validator --search Canyon
```

## Testing with Azure Functions Locally

### 1. Start the Function App

```bash
func start
```

### 2. Test Endpoints Manually

```bash
# Health check
curl http://localhost:7071/api/health

# Search loans
curl "http://localhost:7071/api/search?prefix=Canyon"

# Validate by ID
curl http://localhost:7071/api/validate/id/a0ial00000554ePAAQ

# Validate by name
curl -X POST http://localhost:7071/api/validate/name \
  -H "Content-Type: application/json" \
  -d '{"loan_name": "Canyon Valley - Mezz", "exact_match": true}'

# Batch validation
curl -X POST http://localhost:7071/api/validate/batch \
  -H "Content-Type: application/json" \
  -d '{"loan_ids": ["a0iVy00000ETkIkIAL", "a0iVy00000Gb9RJIAZ"]}'
```

### 3. Run Regression Tests

```bash
# Run all regression tests
./regression_tests/run_all_tests.sh

# Or run individual test suites
./regression_tests/test_by_id.sh
./regression_tests/test_by_name.sh
./regression_tests/test_batch.sh
```

Results are saved to `regression_tests/results/YYYYMMDD_HHMMSS/`

## Integration Tests

Test that the function app can import and use core modules:

```bash
python test_functionapp.py
```

## Test Loan IDs

Quick reference for testing:

| Loan ID | Name | Type | Status |
|---------|------|------|--------|
| a0iVy00000ETkIkIAL | Canyon Valley - Mezz | Mezzanine | Clean |
| a0iVy00000Gb9RJIAZ | Canyon Valley - Senior | Senior | Clean |
| a0ial00000364X3AAI | Vantage - Mezz | Mezzanine | Has errors |
| a0ial00000362BuAAI | Vantage - Senior | Senior | Has errors |
| a0ial000003EBTKAA4 | Vitalia - Preferred | Preferred | Clean |

See [regression_tests/test_data/loan_ids.json](regression_tests/test_data/loan_ids.json) for complete list.

## Next Steps

1. **Test locally**: `python -m core.json_driven_validator <loan_id>`
2. **Start function app**: `func start`
3. **Run regression tests**: `./regression_tests/run_all_tests.sh`
4. **Deploy to Azure**: See [README.md](README.md)
