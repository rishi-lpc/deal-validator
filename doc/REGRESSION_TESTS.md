# Regression Tests - Simplified Curl-Based Tests

## Overview

Simple curl-based API endpoint tests that hit the actual HTTP endpoints and save JSON responses. No comparison with expected values - just direct API smoke testing.

## Structure

```
regression_tests/
├── test_by_id.sh          # 10 tests - GET /api/validate/id/{loan_id}
├── test_by_name.sh        #  5 tests - POST /api/validate/name
├── test_batch.sh          #  6 tests - POST /api/validate/batch
├── run_all_tests.sh       # Run all tests (21 total)
│
├── test_data/             # Reference data
│   └── loan_ids.json      # Test loan IDs and descriptions
│
└── results/               # Test results (timestamped folders)
    └── YYYYMMDD_HHMMSS/   # Each test run creates timestamped folder
```

## Quick Start

### 1. Start Function App

```bash
func start
```

### 2. Run All Tests

```bash
./regression_tests/run_all_tests.sh
```

Output saved to: `regression_tests/results/YYYYMMDD_HHMMSS/`

### 3. Review Results

```bash
# List all result files
ls -lh regression_tests/results/20260130_120000/

# View specific test
cat regression_tests/results/20260130_120000/01_mezz_io_canyon.json | jq '.'

# Find tests with errors
grep -l '"ERRORS": \[' regression_tests/results/20260130_120000/*.json | grep -v '\[\]'
```

## Test Coverage

### Test by ID (10 loans)
- **Test 1**: Canyon Valley - Mezz (Mezzanine, IO, Clean)
- **Test 2**: Canyon Valley - Senior (Senior, P&I, Clean)
- **Test 3**: Vantage - Mezz (Mezzanine, IO, Has errors)
- **Test 4**: Vantage - Senior (Senior, P&I, Has errors)
- **Test 5**: Vitalia - Preferred (Preferred, IO, Clean)
- **Test 6**: Vicinia - A-Tranche (A-Tranche, IO, Clean)
- **Test 7**: Vicinia - B-Tranche (B-Tranche, Mixed, Has errors)
- **Test 8**: Vibrance - Preferred (Preferred, Minimal, Many errors)
- **Test 9**: Vibrance - Senior (Senior, Minimal, Many errors)
- **Test 10**: Canyon View - Mezz (Mezzanine, Fees only, Has errors)

### Test by Name (5 tests)
- Exact match: Canyon Valley - Mezz
- Exact match: Canyon Valley - Senior
- Exact match: Vitalia Stow - Preferred Equity
- Partial match: Vantage
- Exact match: Vicinia Gardens - A-Tranche

### Batch Validation (6 tests)
- Batch 1: 3 mixed types (Preferred, Senior, Mezz)
- Batch 2: 3 Mezzanine loans
- Batch 3: 2 Tranches (A and B)
- Batch 4: 5 diverse loans
- Batch 5: 3 clean loans
- Batch 6: 3 problematic loans

## Sample Output

Each test produces a JSON file like:

```json
{
  "LOAN_NAME": "Canyon Valley - Mezz",
  "LOAN_ID": "a0iVy00000ETkIkIAL",
  "LOAN_AMOUNT": 7000000.0,
  "CLOSE_DATE": "2024-12-24",
  "WARNINGS": [
    {
      "TABLE": "DRAW",
      "ID": null,
      "FIELD": null,
      "MESSAGE": "Total draw amounts do not match..."
    }
  ],
  "ERRORS": [],
  "validation_passed": true
}
```

## Running Against Azure

```bash
# Set Azure URL
export BASE_URL=https://your-app.azurewebsites.net

# Run tests
./regression_tests/run_all_tests.sh
```

## Benefits

1. **Simple**: Just curl commands, no Python test framework
2. **Direct**: Tests actual HTTP endpoints
3. **Visual**: JSON responses saved for inspection
4. **Fast**: All 21 tests run in seconds
5. **Portable**: Works locally or against Azure
6. **CI/CD Ready**: Easy to integrate

## Files Created

After running, you'll have:

```
regression_tests/results/20260130_120000/
├── 00_health_check.json            # Health check
├── 00_search_canyon.json           # Search test
├── 01_mezz_io_canyon.json          # Test by ID #1
├── 02_senior_pi_canyon.json        # Test by ID #2
├── ...
├── 10_mezz_fees_only.json          # Test by ID #10
├── name_01_canyon_mezz.json        # Test by name #1
├── ...
├── name_05_vicinia_a.json          # Test by name #5
├── batch_01_mixed_3.json           # Batch test #1
├── ...
└── batch_06_errors_3.json          # Batch test #6
```

## Total Test Count

- **21 API endpoint tests**
- **10 diverse loan types**
- **3 test suites** (by ID, by name, batch)
- **All major endpoints covered**

See [regression_tests/README.md](regression_tests/README.md) for detailed documentation.
