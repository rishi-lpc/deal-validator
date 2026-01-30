#!/bin/bash
#
# Run All Regression Tests (Direct Core Validator)
# Uses core validator directly instead of HTTP endpoints
#

OUTPUT_DIR="regression_tests/output"

echo "========================================================================"
echo "REGRESSION TEST SUITE - Direct Core Validator"
echo "========================================================================"
echo "Output Directory: $OUTPUT_DIR"
echo ""

# Clear and create output directory
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Function to extract JSON from validator output
extract_json() {
    awk '/^{/,/^}/'
}

echo "========================================================================"
echo "Test Suite 1: Validate by ID (10 tests)"
echo "========================================================================"

# Test 1
echo "Test 1: Canyon Valley - Mezz (Mezzanine with IO)"
python -m core.json_driven_validator a0iVy00000ETkIkIAL 2>/dev/null | extract_json > "$OUTPUT_DIR/01_mezz_io_canyon.json"
echo "✓ Saved to $OUTPUT_DIR/01_mezz_io_canyon.json"

# Test 2
echo "Test 2: Canyon Valley - Senior (Senior with P&I)"
python -m core.json_driven_validator a0iVy00000Gb9RJIAZ 2>/dev/null | extract_json > "$OUTPUT_DIR/02_senior_pi_canyon.json"
echo "✓ Saved to $OUTPUT_DIR/02_senior_pi_canyon.json"

# Test 3
echo "Test 3: Vantage 6 Portfolio - Mezz (Mezzanine with validation errors)"
python -m core.json_driven_validator a0ial00000364X3AAI 2>/dev/null | extract_json > "$OUTPUT_DIR/03_mezz_io_vantage.json"
echo "✓ Saved to $OUTPUT_DIR/03_mezz_io_vantage.json"

# Test 4
echo "Test 4: Vantage 6 Portfolio - Senior (Senior with validation errors)"
python -m core.json_driven_validator a0ial00000362BuAAI 2>/dev/null | extract_json > "$OUTPUT_DIR/04_senior_pi_vantage.json"
echo "✓ Saved to $OUTPUT_DIR/04_senior_pi_vantage.json"

# Test 5
echo "Test 5: Vitalia Stow - Preferred Equity"
python -m core.json_driven_validator a0ial000003EBTKAA4 2>/dev/null | extract_json > "$OUTPUT_DIR/05_preferred_io_vitalia.json"
echo "✓ Saved to $OUTPUT_DIR/05_preferred_io_vitalia.json"

# Test 6
echo "Test 6: Vicinia Gardens - A-Tranche"
python -m core.json_driven_validator a0iVy00000FFualIAD 2>/dev/null | extract_json > "$OUTPUT_DIR/06_tranche_a_io.json"
echo "✓ Saved to $OUTPUT_DIR/06_tranche_a_io.json"

# Test 7
echo "Test 7: Vicinia Gardens - B-Tranche (Mixed IO and P&I)"
python -m core.json_driven_validator a0iVy00000FFuakIAD 2>/dev/null | extract_json > "$OUTPUT_DIR/07_tranche_b_mixed.json"
echo "✓ Saved to $OUTPUT_DIR/07_tranche_b_mixed.json"

# Test 8
echo "Test 8: Vibrance At Park Hill - Preferred (Minimal data)"
python -m core.json_driven_validator a0iVy00000HnhObIAJ 2>/dev/null | extract_json > "$OUTPUT_DIR/08_preferred_minimal.json"
echo "✓ Saved to $OUTPUT_DIR/08_preferred_minimal.json"

# Test 9
echo "Test 9: Vibrance At Park Hill - Senior (Minimal data)"
python -m core.json_driven_validator a0iVy00000Hnh8TIAR 2>/dev/null | extract_json > "$OUTPUT_DIR/09_senior_minimal.json"
echo "✓ Saved to $OUTPUT_DIR/09_senior_minimal.json"

# Test 10
echo "Test 10: Canyon View - Mezz A (Fees only, no pricing/payment)"
python -m core.json_driven_validator a0iVy000003nN0AIAU 2>/dev/null | extract_json > "$OUTPUT_DIR/10_mezz_fees_only.json"
echo "✓ Saved to $OUTPUT_DIR/10_mezz_fees_only.json"

echo ""
echo "========================================================================"
echo "Test Suite 2: Search Tests (5 tests)"
echo "========================================================================"

# Search tests - create simple JSON output
echo "Test 11: Search 'Canyon'"
python -m core.json_driven_validator --search Canyon 2>/dev/null | tail -n +5 | head -n -1 > /tmp/search_canyon.txt
{
  echo '{'
  echo '  "search_prefix": "Canyon",'
  echo '  "results": ['
  grep "ID:" /tmp/search_canyon.txt | awk '{print "    {\"ID\": \""$NF"\"},"}' | sed '$ s/,$//'
  echo '  ]'
  echo '}'
} > "$OUTPUT_DIR/11_search_canyon.json"
echo "✓ Saved to $OUTPUT_DIR/11_search_canyon.json"

echo "Test 12: Validate 'Canyon Valley - Mezz' (exact match)"
python -m core.json_driven_validator "Canyon Valley - Mezz" 2>/dev/null | extract_json > "$OUTPUT_DIR/12_name_canyon_mezz.json"
echo "✓ Saved to $OUTPUT_DIR/12_name_canyon_mezz.json"

echo "Test 13: Validate 'Canyon Valley - Senior' (exact match)"
python -m core.json_driven_validator "Canyon Valley - Senior" 2>/dev/null | extract_json > "$OUTPUT_DIR/13_name_canyon_senior.json"
echo "✓ Saved to $OUTPUT_DIR/13_name_canyon_senior.json"

echo "Test 14: Validate 'Vitalia Stow - Preferred Equity' (exact match)"
python -m core.json_driven_validator "Vitalia Stow - Preferred Equity" 2>/dev/null | extract_json > "$OUTPUT_DIR/14_name_vitalia_preferred.json"
echo "✓ Saved to $OUTPUT_DIR/14_name_vitalia_preferred.json"

echo "Test 15: Validate 'Vicinia Gardens - A-Tranche' (exact match)"
python -m core.json_driven_validator "Vicinia Gardens - A-Tranche" 2>/dev/null | extract_json > "$OUTPUT_DIR/15_name_vicinia_a.json"
echo "✓ Saved to $OUTPUT_DIR/15_name_vicinia_a.json"

echo ""
echo "========================================================================"
echo "Test Suite 3: Additional Validation Tests (6 tests)"
echo "========================================================================"

# Test more diverse loans
echo "Test 16: Vicinia Gardens - B-Tranche"
python -m core.json_driven_validator "Vicinia Gardens - B-Tranche" 2>/dev/null | extract_json > "$OUTPUT_DIR/16_vicinia_b_tranche.json"
echo "✓ Saved to $OUTPUT_DIR/16_vicinia_b_tranche.json"

echo "Test 17: Vantage 6 Portfolio - Senior"
python -m core.json_driven_validator a0ial00000362BuAAI 2>/dev/null | extract_json > "$OUTPUT_DIR/17_vantage_senior.json"
echo "✓ Saved to $OUTPUT_DIR/17_vantage_senior.json"

echo "Test 18: Vibrance At Park Hill - Preferred"
python -m core.json_driven_validator a0iVy00000HnhObIAJ 2>/dev/null | extract_json > "$OUTPUT_DIR/18_vibrance_preferred.json"
echo "✓ Saved to $OUTPUT_DIR/18_vibrance_preferred.json"

echo "Test 19: Vibrance At Park Hill - Senior"
python -m core.json_driven_validator a0iVy00000Hnh8TIAR 2>/dev/null | extract_json > "$OUTPUT_DIR/19_vibrance_senior.json"
echo "✓ Saved to $OUTPUT_DIR/19_vibrance_senior.json"

echo "Test 20: Canyon View - Mezz A"
python -m core.json_driven_validator a0iVy000003nN0AIAU 2>/dev/null | extract_json > "$OUTPUT_DIR/20_canyon_view_mezz.json"
echo "✓ Saved to $OUTPUT_DIR/20_canyon_view_mezz.json"

echo "Test 21: Vitalia Stow - Preferred Equity (retest)"
python -m core.json_driven_validator a0ial000003EBTKAA4 2>/dev/null | extract_json > "$OUTPUT_DIR/21_vitalia_preferred_retest.json"
echo "✓ Saved to $OUTPUT_DIR/21_vitalia_preferred_retest.json"

echo ""
echo "========================================================================"
echo "TEST SUMMARY"
echo "========================================================================"
echo "Results saved to: $OUTPUT_DIR"
echo ""
echo "Test Files Created:"
ls -1 "$OUTPUT_DIR" | wc -l | xargs echo "  Total files:"
echo ""
echo "File List:"
ls -lh "$OUTPUT_DIR"
echo ""
echo "========================================================================"
echo "✓ All 21 regression tests complete!"
echo "========================================================================"
echo ""
echo "To review results:"
echo "  cd $OUTPUT_DIR"
echo "  ls -lh"
echo ""
echo "To view specific test:"
echo "  cat $OUTPUT_DIR/01_mezz_io_canyon.json"
