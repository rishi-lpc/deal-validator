#!/bin/bash
#
# Regression Test: Batch Validation
# Tests the POST /api/validate/batch endpoint
#

BASE_URL="${BASE_URL:-http://localhost:7071}"
OUTPUT_DIR="regression_tests/output"

echo "========================================================================"
echo "Regression Test: Batch Validation"
echo "========================================================================"
echo "Base URL: $BASE_URL"
echo "Output: $OUTPUT_DIR"
echo ""

mkdir -p "$OUTPUT_DIR"

# Test 1: Small batch - Mixed types
echo "Test 1: Batch of 3 loans (Preferred, Senior, Mezz)"
curl -s -X POST "${BASE_URL}/api/validate/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "loan_ids": [
      "a0ial000003EBTKAA4",
      "a0iVy00000Gb9RJIAZ",
      "a0iVy00000ETkIkIAL"
    ]
  }' \
  | jq '.' > "$OUTPUT_DIR/batch_01_mixed_3.json"
echo "✓ Saved to $OUTPUT_DIR/batch_01_mixed_3.json"
echo ""

# Test 2: Medium batch - All Mezzanine
echo "Test 2: Batch of 3 Mezzanine loans"
curl -s -X POST "${BASE_URL}/api/validate/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "loan_ids": [
      "a0iVy00000ETkIkIAL",
      "a0ial00000364X3AAI",
      "a0iVy000003nN0AIAU"
    ]
  }' \
  | jq '.' > "$OUTPUT_DIR/batch_02_mezz_3.json"
echo "✓ Saved to $OUTPUT_DIR/batch_02_mezz_3.json"
echo ""

# Test 3: Tranches batch
echo "Test 3: Batch of A and B Tranches"
curl -s -X POST "${BASE_URL}/api/validate/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "loan_ids": [
      "a0iVy00000FFualIAD",
      "a0iVy00000FFuakIAD"
    ]
  }' \
  | jq '.' > "$OUTPUT_DIR/batch_03_tranches_2.json"
echo "✓ Saved to $OUTPUT_DIR/batch_03_tranches_2.json"
echo ""

# Test 4: Larger batch - Diverse loans
echo "Test 4: Batch of 5 diverse loans"
curl -s -X POST "${BASE_URL}/api/validate/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "loan_ids": [
      "a0ial000003EBTKAA4",
      "a0iVy00000Gb9RJIAZ",
      "a0iVy00000ETkIkIAL",
      "a0ial00000364X3AAI",
      "a0iVy00000FFualIAD"
    ]
  }' \
  | jq '.' > "$OUTPUT_DIR/batch_04_diverse_5.json"
echo "✓ Saved to $OUTPUT_DIR/batch_04_diverse_5.json"
echo ""

# Test 5: Clean loans (no errors expected)
echo "Test 5: Batch of loans with clean validation"
curl -s -X POST "${BASE_URL}/api/validate/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "loan_ids": [
      "a0iVy00000ETkIkIAL",
      "a0iVy00000Gb9RJIAZ",
      "a0ial000003EBTKAA4"
    ]
  }' \
  | jq '.' > "$OUTPUT_DIR/batch_05_clean_3.json"
echo "✓ Saved to $OUTPUT_DIR/batch_05_clean_3.json"
echo ""

# Test 6: Problematic loans (errors expected)
echo "Test 6: Batch of loans with validation errors"
curl -s -X POST "${BASE_URL}/api/validate/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "loan_ids": [
      "a0ial00000364X3AAI",
      "a0iVy00000HnhObIAJ",
      "a0iVy00000Hnh8TIAR"
    ]
  }' \
  | jq '.' > "$OUTPUT_DIR/batch_06_errors_3.json"
echo "✓ Saved to $OUTPUT_DIR/batch_06_errors_3.json"
echo ""

echo "========================================================================"
echo "✓ All tests complete! Results saved to $OUTPUT_DIR"
echo "========================================================================"
