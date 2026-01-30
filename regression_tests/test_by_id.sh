#!/bin/bash
#
# Regression Test: Validate by Loan ID
# Tests the GET /api/validate/id/{loan_id} endpoint
#

BASE_URL="${BASE_URL:-http://localhost:7071}"
OUTPUT_DIR="regression_tests/output"

echo "========================================================================"
echo "Regression Test: Validate by Loan ID"
echo "========================================================================"
echo "Base URL: $BASE_URL"
echo "Output: $OUTPUT_DIR"
echo ""

mkdir -p "$OUTPUT_DIR"

# Test 1: Mezzanine with IO - Clean
echo "Test 1: Canyon Valley - Mezz (Mezzanine with IO)"
curl -s "${BASE_URL}/api/validate/id/a0iVy00000ETkIkIAL" \
  -H "Content-Type: application/json" \
  | jq '.' > "$OUTPUT_DIR/01_mezz_io_canyon.json"
echo "✓ Saved to $OUTPUT_DIR/01_mezz_io_canyon.json"
echo ""

# Test 2: Senior with P&I
echo "Test 2: Canyon Valley - Senior (Senior with P&I)"
curl -s "${BASE_URL}/api/validate/id/a0iVy00000Gb9RJIAZ" \
  -H "Content-Type: application/json" \
  | jq '.' > "$OUTPUT_DIR/02_senior_pi_canyon.json"
echo "✓ Saved to $OUTPUT_DIR/02_senior_pi_canyon.json"
echo ""

# Test 3: Mezzanine with errors
echo "Test 3: Vantage 6 Portfolio - Mezz (Mezzanine with validation errors)"
curl -s "${BASE_URL}/api/validate/id/a0ial00000364X3AAI" \
  -H "Content-Type: application/json" \
  | jq '.' > "$OUTPUT_DIR/03_mezz_io_vantage.json"
echo "✓ Saved to $OUTPUT_DIR/03_mezz_io_vantage.json"
echo ""

# Test 4: Senior with errors
echo "Test 4: Vantage 6 Portfolio - Senior (Senior with validation errors)"
curl -s "${BASE_URL}/api/validate/id/a0ial00000362BuAAI" \
  -H "Content-Type: application/json" \
  | jq '.' > "$OUTPUT_DIR/04_senior_pi_vantage.json"
echo "✓ Saved to $OUTPUT_DIR/04_senior_pi_vantage.json"
echo ""

# Test 5: Preferred Equity
echo "Test 5: Vitalia Stow - Preferred Equity"
curl -s "${BASE_URL}/api/validate/id/a0ial000003EBTKAA4" \
  -H "Content-Type: application/json" \
  | jq '.' > "$OUTPUT_DIR/05_preferred_io_vitalia.json"
echo "✓ Saved to $OUTPUT_DIR/05_preferred_io_vitalia.json"
echo ""

# Test 6: A-Tranche
echo "Test 6: Vicinia Gardens - A-Tranche"
curl -s "${BASE_URL}/api/validate/id/a0iVy00000FFualIAD" \
  -H "Content-Type: application/json" \
  | jq '.' > "$OUTPUT_DIR/06_tranche_a_io.json"
echo "✓ Saved to $OUTPUT_DIR/06_tranche_a_io.json"
echo ""

# Test 7: B-Tranche with mixed payments
echo "Test 7: Vicinia Gardens - B-Tranche (Mixed IO and P&I)"
curl -s "${BASE_URL}/api/validate/id/a0iVy00000FFuakIAD" \
  -H "Content-Type: application/json" \
  | jq '.' > "$OUTPUT_DIR/07_tranche_b_mixed.json"
echo "✓ Saved to $OUTPUT_DIR/07_tranche_b_mixed.json"
echo ""

# Test 8: Minimal data - many errors
echo "Test 8: Vibrance At Park Hill - Preferred (Minimal data)"
curl -s "${BASE_URL}/api/validate/id/a0iVy00000HnhObIAJ" \
  -H "Content-Type: application/json" \
  | jq '.' > "$OUTPUT_DIR/08_preferred_minimal.json"
echo "✓ Saved to $OUTPUT_DIR/08_preferred_minimal.json"
echo ""

# Test 9: Senior with minimal data
echo "Test 9: Vibrance At Park Hill - Senior (Minimal data)"
curl -s "${BASE_URL}/api/validate/id/a0iVy00000Hnh8TIAR" \
  -H "Content-Type: application/json" \
  | jq '.' > "$OUTPUT_DIR/09_senior_minimal.json"
echo "✓ Saved to $OUTPUT_DIR/09_senior_minimal.json"
echo ""

# Test 10: Fees only
echo "Test 10: Canyon View - Mezz A (Fees only, no pricing/payment)"
curl -s "${BASE_URL}/api/validate/id/a0iVy000003nN0AIAU" \
  -H "Content-Type: application/json" \
  | jq '.' > "$OUTPUT_DIR/10_mezz_fees_only.json"
echo "✓ Saved to $OUTPUT_DIR/10_mezz_fees_only.json"
echo ""

echo "========================================================================"
echo "✓ All tests complete! Results saved to $OUTPUT_DIR"
echo "========================================================================"
