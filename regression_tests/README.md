# Regression Tests - API Endpoint Tests

Simple curl-based regression tests for the Deal Validator API endpoints.

## Overview

These tests hit the actual HTTP endpoints and save the JSON responses. No comparison with expected values - just direct API testing to verify endpoints work correctly.

## Test Structure

```
regression_tests/
├── test_by_id.sh          # Test GET /api/validate/id/{loan_id}
├── test_by_name.sh        # Test POST /api/validate/name
├── test_batch.sh          # Test POST /api/validate/batch
├── run_all_tests.sh       # Run all tests
│
├── test_data/             # Reference data
│   └── loan_ids.json      # Test loan IDs and descriptions
│
└── results/               # Test results (gitignored)
    └── YYYYMMDD_HHMMSS/   # Timestamped results
```

## Prerequisites

1. **Start the function app locally:**
   ```bash
   func start
   ```
   Or set `BASE_URL` to your Azure deployment:
   ```bash
   export BASE_URL=https://your-app.azurewebsites.net
   ```

2. **Install jq (for JSON formatting):**
   ```bash
   # macOS
   brew install jq

   # Linux
   sudo apt-get install jq
   ```

## Running Tests

### Run All Tests

```bash
./regression_tests/run_all_tests.sh
```

This will:
- Test health check endpoint
- Test search endpoint
- Run all validation tests (by ID, by name, batch)
- Save timestamped results to `regression_tests/results/YYYYMMDD_HHMMSS/`

### Run Individual Test Suites

```bash
# Test validate by ID endpoint (10 loans)
./regression_tests/test_by_id.sh

# Test validate by name endpoint (5 loans)
./regression_tests/test_by_name.sh

# Test batch validation endpoint (6 batches)
./regression_tests/test_batch.sh
```

### Test Against Azure Deployment

```bash
# Set your Azure function app URL
export BASE_URL=https://your-app.azurewebsites.net

# Add function key if needed
export FUNCTION_KEY=your-function-key

# Run tests
./regression_tests/run_all_tests.sh
```

## Test Coverage

### Test by ID (10 loans)
Tests `GET /api/validate/id/{loan_id}`

| Test | Loan | Type | Payment | Expected |
|------|------|------|---------|----------|
| 1 | Canyon Valley - Mezz | Mezzanine | IO | Clean |
| 2 | Canyon Valley - Senior | Senior | P&I | Clean |
| 3 | Vantage - Mezz | Mezzanine | IO | Has errors |
| 4 | Vantage - Senior | Senior | P&I | Has errors |
| 5 | Vitalia - Preferred | Preferred | IO | Clean |
| 6 | Vicinia - A-Tranche | A-Tranche | IO | Clean |
| 7 | Vicinia - B-Tranche | B-Tranche | Mixed | Has errors |
| 8 | Vibrance - Preferred | Preferred | None | Many errors |
| 9 | Vibrance - Senior | Senior | None | Many errors |
| 10 | Canyon View - Mezz | Mezzanine | None | Has errors |

### Test by Name (5 tests)
Tests `POST /api/validate/name`

- Exact match: Canyon Valley - Mezz
- Exact match: Canyon Valley - Senior
- Exact match: Vitalia Stow - Preferred Equity
- Partial match: Vantage (should find first match)
- Exact match: Vicinia Gardens - A-Tranche

### Batch Validation (6 batches)
Tests `POST /api/validate/batch`

- Batch 1: 3 mixed types (Preferred, Senior, Mezz)
- Batch 2: 3 Mezzanine loans
- Batch 3: 2 Tranches (A and B)
- Batch 4: 5 diverse loans
- Batch 5: 3 clean loans (no errors)
- Batch 6: 3 problematic loans (with errors)

## Output Format

Each test saves a JSON file to `regression_tests/results/`:

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

## Reviewing Results

### View All Results

```bash
cd regression_tests/results/20260130_120000/
ls -lh
```

### View Specific Test

```bash
cat regression_tests/results/20260130_120000/01_mezz_io_canyon.json | jq '.'
```

### Check for Errors

```bash
# Find all tests with errors
cd regression_tests/results/20260130_120000/
grep -l '"ERRORS": \[' *.json | grep -v '"ERRORS": \[\]'
```

### Count Errors/Warnings

```bash
# Count errors in a specific test
cat 03_mezz_io_vantage.json | jq '.ERRORS | length'

# Count warnings
cat 03_mezz_io_vantage.json | jq '.WARNINGS | length'
```

### Compare Two Test Runs

```bash
# Compare results from different runs
diff -u results/20260130_120000/01_mezz_io_canyon.json \
        results/20260130_130000/01_mezz_io_canyon.json
```

## Test Loan Reference

See [test_data/loan_ids.json](test_data/loan_ids.json) for complete list of test loans with descriptions.

### Quick Reference

- **Clean Loans** (0 errors): Tests 1, 2, 5, 6
- **With Errors**: Tests 3, 4, 7, 8, 9, 10
- **Mezzanine**: Tests 1, 3, 10
- **Senior**: Tests 2, 4, 9
- **Preferred**: Tests 5, 8
- **Tranches**: Tests 6, 7

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Regression Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          sudo apt-get install -y jq

      - name: Start Function App
        run: |
          func start &
          sleep 10

      - name: Run Regression Tests
        run: ./regression_tests/run_all_tests.sh

      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: regression_tests/results/
```

## Adding New Tests

### Add to test_by_id.sh

```bash
echo "Test 11: Your Loan Name"
curl -s "${BASE_URL}/api/validate/id/YOUR_LOAN_ID" \
  -H "Content-Type: application/json" \
  | jq '.' > "$OUTPUT_DIR/11_your_test.json"
echo "✓ Saved to $OUTPUT_DIR/11_your_test.json"
```

### Add to test_by_name.sh

```bash
echo "Test 6: Your loan name test"
curl -s -X POST "${BASE_URL}/api/validate/name" \
  -H "Content-Type: application/json" \
  -d '{"loan_name": "Your Loan Name", "exact_match": true}' \
  | jq '.' > "$OUTPUT_DIR/name_06_your_test.json"
echo "✓ Saved"
```

### Add to test_batch.sh

```bash
echo "Test 7: Your batch description"
curl -s -X POST "${BASE_URL}/api/validate/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "loan_ids": [
      "YOUR_ID_1",
      "YOUR_ID_2"
    ]
  }' \
  | jq '.' > "$OUTPUT_DIR/batch_07_your_test.json"
echo "✓ Saved"
```

## Troubleshooting

### Function App Not Running

```bash
# Check if function app is running
curl http://localhost:7071/api/health

# If not running, start it
func start
```

### jq Not Installed

```bash
# macOS
brew install jq

# Linux
sudo apt-get install jq

# Or run tests without jq (no formatting)
# Edit test scripts and remove | jq '.'
```

### Permission Denied

```bash
# Make scripts executable
chmod +x regression_tests/*.sh
```

### Results Directory Not Created

```bash
# Create manually
mkdir -p regression_tests/results
```

## What Gets Tested

✅ **Endpoints tested:**
- `GET /api/health` - Health check
- `GET /api/search?prefix=X` - Search loans
- `GET /api/validate/id/{loan_id}` - Validate by ID
- `POST /api/validate/name` - Validate by name
- `POST /api/validate/batch` - Batch validation

✅ **Loan types tested:**
- Preferred Equity
- Senior Debt
- Mezzanine
- A/B Tranches

✅ **Payment types tested:**
- Interest Only (IO)
- Principal & Interest (P&I)
- Mixed payments
- Minimal/no data

✅ **Validation scenarios:**
- Clean loans (no errors)
- Loans with warnings
- Loans with validation errors
- Loans with minimal data

## Benefits

1. **Simple**: Just curl commands, no complex test framework
2. **Direct**: Tests actual HTTP endpoints
3. **Visual**: JSON responses saved for inspection
4. **Timestamped**: Results organized by run time
5. **Portable**: Works locally or against Azure deployment
6. **Fast**: Tests run in seconds
7. **CI/CD Ready**: Easy to integrate into pipelines

## Summary

- **21 individual tests** across 3 test suites
- **10 diverse loan types** from Salesforce
- **All major endpoints** covered
- **Results saved as JSON** for easy review
- **Timestamped output** for comparison over time
