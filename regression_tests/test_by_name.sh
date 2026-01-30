#!/bin/bash
#
# Regression Test: Validate by Loan Name
# Tests the POST /api/validate/name endpoint
#

BASE_URL="${BASE_URL:-http://localhost:7071}"
OUTPUT_DIR="regression_tests/output"

echo "========================================================================"
echo "Regression Test: Validate by Loan Name"
echo "========================================================================"
echo "Base URL: $BASE_URL"
echo "Output: $OUTPUT_DIR"
echo ""

mkdir -p "$OUTPUT_DIR"

# Test 1: Exact match - Mezzanine
echo "Test 1: Validate 'Canyon Valley - Mezz' (exact match)"
curl -s -X POST "${BASE_URL}/api/validate/name" \
  -H "Content-Type: application/json" \
  -d '{"loan_name": "Canyon Valley - Mezz", "exact_match": true}' \
  | jq '.' > "$OUTPUT_DIR/name_01_canyon_mezz.json"
echo "✓ Saved to $OUTPUT_DIR/name_01_canyon_mezz.json"
echo ""

# Test 2: Exact match - Senior
echo "Test 2: Validate 'Canyon Valley - Senior' (exact match)"
curl -s -X POST "${BASE_URL}/api/validate/name" \
  -H "Content-Type: application/json" \
  -d '{"loan_name": "Canyon Valley - Senior", "exact_match": true}' \
  | jq '.' > "$OUTPUT_DIR/name_02_canyon_senior.json"
echo "✓ Saved to $OUTPUT_DIR/name_02_canyon_senior.json"
echo ""

# Test 3: Exact match - Preferred
echo "Test 3: Validate 'Vitalia Stow - Preferred Equity' (exact match)"
curl -s -X POST "${BASE_URL}/api/validate/name" \
  -H "Content-Type: application/json" \
  -d '{"loan_name": "Vitalia Stow - Preferred Equity", "exact_match": true}' \
  | jq '.' > "$OUTPUT_DIR/name_03_vitalia_preferred.json"
echo "✓ Saved to $OUTPUT_DIR/name_03_vitalia_preferred.json"
echo ""

# Test 4: Partial match
echo "Test 4: Validate 'Vantage' (partial match)"
curl -s -X POST "${BASE_URL}/api/validate/name" \
  -H "Content-Type: application/json" \
  -d '{"loan_name": "Vantage", "exact_match": false}' \
  | jq '.' > "$OUTPUT_DIR/name_04_vantage_partial.json"
echo "✓ Saved to $OUTPUT_DIR/name_04_vantage_partial.json"
echo ""

# Test 5: A-Tranche
echo "Test 5: Validate 'Vicinia Gardens - A-Tranche' (exact match)"
curl -s -X POST "${BASE_URL}/api/validate/name" \
  -H "Content-Type: application/json" \
  -d '{"loan_name": "Vicinia Gardens - A-Tranche", "exact_match": true}' \
  | jq '.' > "$OUTPUT_DIR/name_05_vicinia_a.json"
echo "✓ Saved to $OUTPUT_DIR/name_05_vicinia_a.json"
echo ""

echo "========================================================================"
echo "✓ All tests complete! Results saved to $OUTPUT_DIR"
echo "========================================================================"
