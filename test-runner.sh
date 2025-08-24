#!/bin/bash

# AI Business Automation Designer - Comprehensive Test Runner
# Runs all integration and end-to-end tests for the platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
ENV_FILE=".env"
COMPOSE_FILE="docker-compose.dev.yml"
TEST_RESULTS_DIR="test-results"
COVERAGE_DIR="coverage"

# Test configuration
PYTHON_TESTS=true
FRONTEND_TESTS=true
INTEGRATION_TESTS=true
E2E_TESTS=true
PERFORMANCE_TESTS=true
SECURITY_TESTS=true

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_test() {
    echo -e "${PURPLE}[TEST]${NC} $1"
}

log_performance() {
    echo -e "${CYAN}[PERFORMANCE]${NC} $1"
}

check_prerequisites() {
    log_info "Checking test prerequisites..."

    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file $ENV_FILE not found. Please create it from .env.example"
        exit 1
    fi

    # Check if test directories exist
    mkdir -p "$TEST_RESULTS_DIR"
    mkdir -p "$COVERAGE_DIR"

    log_success "Prerequisites check passed"
}

start_test_environment() {
    log_info "Starting test environment..."

    # Start development environment
    docker-compose -f "$COMPOSE_FILE" up -d

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    
    # Wait for database
    until docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U ai_user; do
        sleep 2
    done

    # Wait for Redis
    until docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping; do
        sleep 2
    done

    # Wait for orchestrator
    until curl -f http://localhost:8000/health; do
        sleep 5
    done

    # Wait for gateway
    until curl -f http://localhost:3000/health; do
        sleep 5
    done

    # Wait for frontend
    until curl -f http://localhost:3001/api/health; do
        sleep 5
    done

    log_success "Test environment ready"
}

run_python_tests() {
    if [ "$PYTHON_TESTS" = true ]; then
        log_test "Running Python unit tests..."

        # Run orchestrator tests
        log_info "Running orchestrator unit tests..."
        cd apps/orchestrator
        python -m pytest tests/unit/ -v --cov=app --cov-report=html:../../$COVERAGE_DIR/orchestrator --cov-report=xml:../../$COVERAGE_DIR/orchestrator-coverage.xml --junitxml=../../$TEST_RESULTS_DIR/orchestrator-unit.xml
        cd ../..

        # Run workers tests
        log_info "Running workers unit tests..."
        cd apps/workers
        python -m pytest tests/unit/ -v --cov=app --cov-report=html:../../$COVERAGE_DIR/workers --cov-report=xml:../../$COVERAGE_DIR/workers-coverage.xml --junitxml=../../$TEST_RESULTS_DIR/workers-unit.xml
        cd ../..

        log_success "Python unit tests completed"
    fi
}

run_integration_tests() {
    if [ "$INTEGRATION_TESTS" = true ]; then
        log_test "Running integration tests..."

        # Run orchestrator integration tests
        log_info "Running orchestrator integration tests..."
        cd apps/orchestrator
        python -m pytest tests/integration/ -v --junitxml=../../$TEST_RESULTS_DIR/orchestrator-integration.xml
        cd ../..

        # Run API integration tests
        log_info "Running API integration tests..."
        python -m pytest tests/api_integration/ -v --junitxml=$TEST_RESULTS_DIR/api-integration.xml

        log_success "Integration tests completed"
    fi
}

run_frontend_tests() {
    if [ "$FRONTEND_TESTS" = true ]; then
        log_test "Running frontend tests..."

        # Run frontend unit tests
        log_info "Running frontend unit tests..."
        cd apps/frontend
        npm test -- --coverage --watchAll=false --testResultsProcessor=jest-junit --coverageReporters=html --coverageReporters=text --coverageDirectory=../../$COVERAGE_DIR/frontend
        cd ../..

        log_success "Frontend tests completed"
    fi
}

run_e2e_tests() {
    if [ "$E2E_TESTS" = true ]; then
        log_test "Running end-to-end tests..."

        # Install Playwright if not installed
        if ! command -v npx playwright &> /dev/null; then
            log_info "Installing Playwright..."
            cd apps/frontend
            npx playwright install
            cd ../..
        fi

        # Run Playwright E2E tests
        log_info "Running Playwright E2E tests..."
        cd apps/frontend
        npx playwright test tests/e2e/ --reporter=junit --output=../../$TEST_RESULTS_DIR/e2e-results.xml
        cd ../..

        log_success "End-to-end tests completed"
    fi
}

run_performance_tests() {
    if [ "$PERFORMANCE_TESTS" = true ]; then
        log_test "Running performance tests..."

        # Run load tests
        log_info "Running load tests..."
        python -m pytest tests/performance/ -v --junitxml=$TEST_RESULTS_DIR/performance.xml

        # Run stress tests
        log_info "Running stress tests..."
        python -m pytest tests/stress/ -v --junitxml=$TEST_RESULTS_DIR/stress.xml

        log_success "Performance tests completed"
    fi
}

run_security_tests() {
    if [ "$SECURITY_TESTS" = true ]; then
        log_test "Running security tests..."

        # Run security scans
        log_info "Running security vulnerability scans..."
        python -m pytest tests/security/ -v --junitxml=$TEST_RESULTS_DIR/security.xml

        # Run dependency vulnerability checks
        log_info "Checking for vulnerable dependencies..."
        cd apps/orchestrator
        safety check --json --output-file ../../$TEST_RESULTS_DIR/python-security.json
        cd ../..

        cd apps/frontend
        npm audit --audit-level=moderate --json > ../../$TEST_RESULTS_DIR/npm-security.json
        cd ../..

        log_success "Security tests completed"
    fi
}

run_api_tests() {
    log_test "Running API tests..."

    # Test all API endpoints
    log_info "Testing API endpoints..."
    python -m pytest tests/api/ -v --junitxml=$TEST_RESULTS_DIR/api-tests.xml

    # Test API documentation
    log_info "Testing API documentation..."
    curl -f http://localhost:8000/docs > /dev/null
    curl -f http://localhost:3000/docs > /dev/null

    log_success "API tests completed"
}

run_database_tests() {
    log_test "Running database tests..."

    # Test database migrations
    log_info "Testing database migrations..."
    docker-compose -f "$COMPOSE_FILE" exec -T orchestrator alembic upgrade head
    docker-compose -f "$COMPOSE_FILE" exec -T orchestrator alembic downgrade -1
    docker-compose -f "$COMPOSE_FILE" exec -T orchestrator alembic upgrade +1

    # Test database connectivity
    log_info "Testing database connectivity..."
    python -m pytest tests/database/ -v --junitxml=$TEST_RESULTS_DIR/database-tests.xml

    log_success "Database tests completed"
}

run_monitoring_tests() {
    log_test "Running monitoring tests..."

    # Test Prometheus metrics
    log_info "Testing Prometheus metrics..."
    curl -f http://localhost:8000/metrics > /dev/null
    curl -f http://localhost:3000/metrics > /dev/null

    # Test health checks
    log_info "Testing health checks..."
    curl -f http://localhost:8000/health > /dev/null
    curl -f http://localhost:3000/health > /dev/null
    curl -f http://localhost:3001/api/health > /dev/null

    # Test Grafana connectivity
    log_info "Testing Grafana connectivity..."
    curl -f http://localhost:3002/api/health > /dev/null

    log_success "Monitoring tests completed"
}

generate_test_report() {
    log_info "Generating test report..."

    # Create HTML report
    cat > "$TEST_RESULTS_DIR/test-report.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>AI Business Automation Designer - Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .success { background-color: #d4edda; border-color: #c3e6cb; }
        .error { background-color: #f8d7da; border-color: #f5c6cb; }
        .warning { background-color: #fff3cd; border-color: #ffeaa7; }
        .coverage { background-color: #d1ecf1; border-color: #bee5eb; }
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Business Automation Designer - Test Report</h1>
        <p>Generated on: $(date)</p>
    </div>

    <div class="section success">
        <h2>Test Summary</h2>
        <p>All tests completed successfully!</p>
    </div>

    <div class="section coverage">
        <h2>Code Coverage</h2>
        <p>Coverage reports available in: <a href="../$COVERAGE_DIR/">coverage/</a></p>
    </div>

    <div class="section">
        <h2>Test Results</h2>
        <ul>
            <li><a href="orchestrator-unit.xml">Orchestrator Unit Tests</a></li>
            <li><a href="workers-unit.xml">Workers Unit Tests</a></li>
            <li><a href="orchestrator-integration.xml">Orchestrator Integration Tests</a></li>
            <li><a href="api-integration.xml">API Integration Tests</a></li>
            <li><a href="e2e-results.xml">End-to-End Tests</a></li>
            <li><a href="performance.xml">Performance Tests</a></li>
            <li><a href="security.xml">Security Tests</a></li>
        </ul>
    </div>
</body>
</html>
EOF

    log_success "Test report generated: $TEST_RESULTS_DIR/test-report.html"
}

cleanup_test_environment() {
    log_info "Cleaning up test environment..."

    # Stop development environment
    docker-compose -f "$COMPOSE_FILE" down

    # Clean up test files
    rm -f test_integration.db
    rm -f *.pyc
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

    log_success "Test environment cleaned up"
}

show_test_summary() {
    log_info "Test Summary:"
    echo ""
    echo "Test Results Directory: $TEST_RESULTS_DIR"
    echo "Coverage Reports: $COVERAGE_DIR"
    echo "HTML Report: $TEST_RESULTS_DIR/test-report.html"
    echo ""
    echo "To view coverage reports:"
    echo "  open $COVERAGE_DIR/orchestrator/index.html"
    echo "  open $COVERAGE_DIR/workers/index.html"
    echo "  open $COVERAGE_DIR/frontend/lcov-report/index.html"
    echo ""
    echo "To view test report:"
    echo "  open $TEST_RESULTS_DIR/test-report.html"
}

# Main test execution
main() {
    log_info "Starting comprehensive test suite for AI Business Automation Designer"
    echo ""

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-python)
                PYTHON_TESTS=false
                shift
                ;;
            --no-frontend)
                FRONTEND_TESTS=false
                shift
                ;;
            --no-integration)
                INTEGRATION_TESTS=false
                shift
                ;;
            --no-e2e)
                E2E_TESTS=false
                shift
                ;;
            --no-performance)
                PERFORMANCE_TESTS=false
                shift
                ;;
            --no-security)
                SECURITY_TESTS=false
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --no-python      Skip Python unit tests"
                echo "  --no-frontend    Skip frontend tests"
                echo "  --no-integration Skip integration tests"
                echo "  --no-e2e         Skip end-to-end tests"
                echo "  --no-performance Skip performance tests"
                echo "  --no-security    Skip security tests"
                echo "  --help           Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Execute test suite
    check_prerequisites
    start_test_environment

    # Run all test types
    run_python_tests
    run_frontend_tests
    run_integration_tests
    run_e2e_tests
    run_performance_tests
    run_security_tests
    run_api_tests
    run_database_tests
    run_monitoring_tests

    # Generate reports
    generate_test_report
    cleanup_test_environment
    show_test_summary

    log_success "All tests completed successfully!"
}

# Handle script interruption
trap cleanup_test_environment EXIT

# Run main function
main "$@"
