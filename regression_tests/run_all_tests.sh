#!/bin/bash
#
# Run All Regression Tests
# Executes all test suites and saves results
#

set -e  # Exit on error

BASE_URL="${BASE_URL:-http://localhost:7071}"
OUTPUT_DIR="regression_tests/output"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "========================================================================"
echo "REGRESSION TEST SUITE - API ENDPOINT TESTS"
echo "========================================================================"
echo "Base URL: $BASE_URL"
echo "Timestamp: $TIMESTAMP"
echo "Output Directory: $OUTPUT_DIR"
echo ""

# Clear and create output directory
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Set output directory for test scripts
export OUTPUT_DIR

# Test 1: Health Check
echo "========================================================================"
echo "Testing Health Check Endpoint"
echo "========================================================================"
curl -s "${BASE_URL}/api/health" | jq '.' > "$OUTPUT_DIR/00_health_check.json"
echo "✓ Health check complete"
echo ""

# Test 2: Search Endpoint
echo "========================================================================"
echo "Testing Search Endpoint"
echo "========================================================================"
echo "Searching for 'Canyon'..."
curl -s "${BASE_URL}/api/search?prefix=Canyon" | jq '.' > "$OUTPUT_DIR/00_search_canyon.json"
echo "✓ Search test complete"
echo ""

# Test 3: Validate by ID
echo "========================================================================"
echo "Running Test Suite: Validate by ID"
echo "========================================================================"
bash regression_tests/test_by_id.sh
echo ""

# Test 4: Validate by Name
echo "========================================================================"
echo "Running Test Suite: Validate by Name"
echo "========================================================================"
bash regression_tests/test_by_name.sh
echo ""

# Test 5: Batch Validation
echo "========================================================================"
echo "Running Test Suite: Batch Validation"
echo "========================================================================"
bash regression_tests/test_batch.sh
echo ""

# Create summary
echo "========================================================================"
echo "TEST SUMMARY"
echo "========================================================================"
echo "Base URL: $BASE_URL"
echo "Timestamp: $TIMESTAMP"
echo ""
echo "Results saved to: $OUTPUT_DIR"
echo ""
echo "Test Files Created:"
ls -1 "$OUTPUT_DIR" | wc -l | xargs echo "  Total files:"
echo ""
echo "File List:"
ls -lh "$OUTPUT_DIR" | tail -n +2
echo ""
echo "========================================================================"
echo "✓ All regression tests complete!"
echo "========================================================================"
echo ""
echo "To review results:"
echo "  cd $OUTPUT_DIR"
echo "  ls -lh"
echo ""
echo "To view specific test:"
echo "  cat $OUTPUT_DIR/01_mezz_io_canyon.json | jq '.'"
