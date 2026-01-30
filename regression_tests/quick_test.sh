#!/bin/bash
#
# Quick Test - Demonstrates output folder structure
# Uses core validator directly (no need for function app)
#

OUTPUT_DIR="regression_tests/output"

echo "========================================================================"
echo "Quick Regression Test (using core validator)"
echo "========================================================================"
echo "Output: $OUTPUT_DIR"
echo ""

mkdir -p "$OUTPUT_DIR"

# Test 1: Clean Mezzanine loan
echo "Test 1: Canyon Valley - Mezz (Clean)"
python -m core.json_driven_validator a0iVy00000ETkIkIAL 2>/dev/null | \
  grep -A 1000 "^{" > "$OUTPUT_DIR/test_01_canyon_mezz.json"
echo "✓ Saved to $OUTPUT_DIR/test_01_canyon_mezz.json"

# Test 2: Senior with warnings
echo "Test 2: Canyon Valley - Senior"
python -m core.json_driven_validator a0iVy00000Gb9RJIAZ 2>/dev/null | \
  grep -A 1000 "^{" > "$OUTPUT_DIR/test_02_canyon_senior.json"
echo "✓ Saved to $OUTPUT_DIR/test_02_canyon_senior.json"

# Test 3: Mezzanine with errors
echo "Test 3: Vantage 6 Portfolio - Mezz (Has errors)"
python -m core.json_driven_validator a0ial00000364X3AAI 2>/dev/null | \
  grep -A 1000 "^{" > "$OUTPUT_DIR/test_03_vantage_mezz.json"
echo "✓ Saved to $OUTPUT_DIR/test_03_vantage_mezz.json"

echo ""
echo "========================================================================"
echo "✓ Test complete! Results in $OUTPUT_DIR"
echo "========================================================================"
echo ""
echo "View results:"
echo "  ls -lh $OUTPUT_DIR"
echo "  cat $OUTPUT_DIR/test_01_canyon_mezz.json | jq '.'"
