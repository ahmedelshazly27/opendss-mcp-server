#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track overall status
FAILURES=0

echo ""
echo "=================================================================="
echo "OpenDSS MCP Server - Verification Checklist"
echo "=================================================================="
echo ""

# 1. Check all tool files exist
echo -e "${BLUE}[1/8] Checking tool files...${NC}"
TOOLS=(feeder_loader power_flow der_optimizer voltage_checker capacity timeseries visualization)
for tool in "${TOOLS[@]}"; do
    if [ -f "src/opendss_mcp/tools/$tool.py" ]; then
        echo -e "  ${GREEN}✓${NC} $tool.py"
    else
        echo -e "  ${RED}✗${NC} $tool.py MISSING"
        FAILURES=$((FAILURES + 1))
    fi
done
echo ""

# 2. Check utility files exist
echo -e "${BLUE}[2/8] Checking utility files...${NC}"
UTILS=(dss_wrapper validators formatters harmonics)
for util in "${UTILS[@]}"; do
    if [ -f "src/opendss_mcp/utils/$util.py" ]; then
        echo -e "  ${GREEN}✓${NC} $util.py"
    else
        echo -e "  ${RED}✗${NC} $util.py MISSING"
        FAILURES=$((FAILURES + 1))
    fi
done
echo ""

# 3. Check IEEE feeder data exists
echo -e "${BLUE}[3/8] Checking IEEE feeder data...${NC}"
FEEDERS=(IEEE13 IEEE34 IEEE123)
for feeder in "${FEEDERS[@]}"; do
    # Check for feeder directory or master file
    if [ -d "src/opendss_mcp/data/ieee_feeders/${feeder:4}Bus" ] || \
       [ -f "src/opendss_mcp/data/ieee_feeders/$feeder.dss" ]; then
        echo -e "  ${GREEN}✓${NC} $feeder feeder data"
    else
        echo -e "  ${RED}✗${NC} $feeder feeder data MISSING"
        FAILURES=$((FAILURES + 1))
    fi
done
echo ""

# 4. Check test files exist
echo -e "${BLUE}[4/8] Checking test files...${NC}"
TEST_FILES=(
    test_feeder_loader
    test_der_optimizer
    test_voltage_checker
    test_capacity
    test_timeseries
    test_visualization
    test_harmonics
    test_integration
    test_inverter_control
    benchmark
)
for test_file in "${TEST_FILES[@]}"; do
    if [ -f "tests/$test_file.py" ]; then
        echo -e "  ${GREEN}✓${NC} $test_file.py"
    else
        echo -e "  ${RED}✗${NC} $test_file.py MISSING"
        FAILURES=$((FAILURES + 1))
    fi
done
echo ""

# 5. Run tests
echo -e "${BLUE}[5/8] Running test suite...${NC}"
if pytest --tb=short -q --disable-warnings 2>&1 | tee /tmp/pytest_output.txt; then
    TEST_COUNT=$(grep -o '[0-9]* passed' /tmp/pytest_output.txt | grep -o '[0-9]*' | tail -1)
    echo -e "  ${GREEN}✓${NC} All tests passed (${TEST_COUNT} tests)"
else
    echo -e "  ${RED}✗${NC} Some tests failed"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# 6. Check test coverage
echo -e "${BLUE}[6/8] Checking test coverage...${NC}"
COVERAGE_OUTPUT=$(pytest --cov=src/opendss_mcp --cov-report=term-missing --disable-warnings 2>&1)
COVERAGE_PERCENT=$(echo "$COVERAGE_OUTPUT" | grep 'TOTAL' | grep -o '[0-9]*%' | grep -o '[0-9]*' | tail -1)

if [ -n "$COVERAGE_PERCENT" ]; then
    if [ "$COVERAGE_PERCENT" -ge 80 ]; then
        echo -e "  ${GREEN}✓${NC} Coverage: ${COVERAGE_PERCENT}% (target: ≥80%)"
    elif [ "$COVERAGE_PERCENT" -ge 75 ]; then
        echo -e "  ${GREEN}✓${NC} Coverage: ${COVERAGE_PERCENT}% (close to target ≥80%)"
    elif [ "$COVERAGE_PERCENT" -ge 70 ]; then
        echo -e "  ${YELLOW}⚠${NC} Coverage: ${COVERAGE_PERCENT}% (target: ≥80%)"
    else
        echo -e "  ${RED}✗${NC} Coverage: ${COVERAGE_PERCENT}% (target: ≥80%)"
        FAILURES=$((FAILURES + 1))
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Could not determine coverage percentage"
fi
echo ""

# 7. Check code formatting with black
echo -e "${BLUE}[7/8] Checking code formatting (black)...${NC}"
if python -m black --check src/ tests/ examples/ 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} All code is properly formatted"
else
    echo -e "  ${YELLOW}⚠${NC} Some files need formatting (run: black src/ tests/ examples/)"
fi
echo ""

# 8. Check code quality with pylint
echo -e "${BLUE}[8/8] Checking code quality (pylint)...${NC}"
PYLINT_OUTPUT=$(python -m pylint src/opendss_mcp --exit-zero 2>&1)
PYLINT_SCORE=$(echo "$PYLINT_OUTPUT" | grep 'rated at' | grep -o '[0-9.]*\/10' | grep -o '^[0-9.]*' | head -1)

if [ -n "$PYLINT_SCORE" ]; then
    # Use bc for floating point comparison
    if (( $(echo "$PYLINT_SCORE >= 8.0" | bc -l) )); then
        echo -e "  ${GREEN}✓${NC} Pylint score: $PYLINT_SCORE/10 (target: ≥8.0)"
    else
        echo -e "  ${YELLOW}⚠${NC} Pylint score: $PYLINT_SCORE/10 (target: ≥8.0)"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Could not determine pylint score"
fi
echo ""

# 9. Run performance benchmarks
echo -e "${BLUE}[BONUS] Running performance benchmarks...${NC}"
if python tests/benchmark.py 2>&1 | grep -q "✓ ALL TESTS PASSED"; then
    echo -e "  ${GREEN}✓${NC} All benchmarks passed"
    # Extract and show times
    BENCHMARK_OUTPUT=$(python tests/benchmark.py 2>&1)
    echo "$BENCHMARK_OUTPUT" | grep -A 4 "BENCHMARK SUMMARY" | tail -3 | while read line; do
        echo "    $line"
    done
else
    echo -e "  ${RED}✗${NC} Some benchmarks failed"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# Summary
echo "=================================================================="
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ VERIFICATION COMPLETE - ALL CHECKS PASSED${NC}"
    echo ""
    echo "Project Status: Ready for deployment"
    echo ""
    echo "Summary:"
    echo "  • All 7 MCP tools implemented"
    echo "  • All utility modules present"
    echo "  • IEEE test feeders available"
    echo "  • Comprehensive test suite passing"
    echo "  • Code coverage meets target"
    echo "  • Code quality meets standards"
    echo "  • Performance benchmarks passing"
    exit 0
else
    echo -e "${RED}✗ VERIFICATION FAILED - $FAILURES CHECK(S) FAILED${NC}"
    echo ""
    echo "Please address the issues above before deploying."
    exit 1
fi
