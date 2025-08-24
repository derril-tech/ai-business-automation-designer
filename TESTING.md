# AI Business Automation Designer - Testing Guide

This guide covers all aspects of testing for the AI Business Automation Designer platform, from unit tests to end-to-end testing and performance validation.

## Table of Contents

1. [Testing Strategy](#testing-strategy)
2. [Test Types](#test-types)
3. [Running Tests](#running-tests)
4. [Test Environment](#test-environment)
5. [Test Coverage](#test-coverage)
6. [Continuous Integration](#continuous-integration)
7. [Performance Testing](#performance-testing)
8. [Security Testing](#security-testing)
9. [Troubleshooting](#troubleshooting)

## Testing Strategy

### 🎯 Testing Philosophy

Our testing strategy follows these principles:

- **Comprehensive Coverage**: Test all components, services, and integrations
- **Automated Testing**: Minimize manual testing through comprehensive automation
- **Continuous Validation**: Run tests continuously to catch issues early
- **Performance Focus**: Ensure system meets performance requirements
- **Security First**: Validate security measures and vulnerability prevention
- **User-Centric**: Test complete user journeys and experiences

### 🏗️ Testing Pyramid

```
    E2E Tests (Few, Critical Paths)
         /\
        /  \
   Integration Tests (Service Boundaries)
      /        \
     /          \
Unit Tests (Many, Fast, Isolated)
```

## Test Types

### 1. Unit Tests

**Purpose**: Test individual components in isolation

**Coverage**:
- **Orchestrator**: Services, models, utilities, executors
- **Workers**: Task handlers, utilities, configurations
- **Frontend**: Components, hooks, utilities, stores
- **Gateway**: Controllers, services, middleware

**Location**:
```
apps/orchestrator/tests/unit/
apps/workers/tests/unit/
apps/frontend/tests/unit/
apps/gateway/tests/unit/
```

**Example**:
```python
# apps/orchestrator/tests/unit/test_design_service.py
def test_ai_design_workflow():
    service = DesignService()
    result = service.create_workflow("Process emails")
    assert result.confidence > 0.8
    assert len(result.steps) > 0
```

### 2. Integration Tests

**Purpose**: Test interactions between components and services

**Coverage**:
- Service-to-service communication
- Database interactions
- API endpoint integration
- Message queue operations
- External service integrations

**Location**:
```
apps/orchestrator/tests/integration/
tests/api_integration/
tests/database/
```

**Example**:
```python
# apps/orchestrator/tests/integration/test_integration.py
def test_complete_workflow_integration():
    # Test AI design → workflow creation → execution
    design = create_ai_design()
    workflow = create_workflow(design)
    execution = execute_workflow(workflow)
    assert execution.status == "completed"
```

### 3. End-to-End Tests

**Purpose**: Test complete user journeys from start to finish

**Coverage**:
- Complete workflow design process
- AI-assisted workflow generation
- Visual flow builder interactions
- Workflow execution and monitoring
- Error handling and recovery

**Location**:
```
apps/frontend/tests/e2e/
tests/e2e/
```

**Example**:
```typescript
// apps/frontend/tests/e2e/flow-builder.test.ts
test('should create complete workflow using AI design', async () => {
  await page.click('[data-testid="ai-design-button"]');
  await page.fill('[data-testid="goal-input"]', 'Process emails');
  await page.click('[data-testid="generate-workflow-button"]');
  await expect(page.locator('[data-testid="workflow-preview"]')).toBeVisible();
});
```

### 4. API Tests

**Purpose**: Test API endpoints and data flow

**Coverage**:
- REST API endpoints
- Request/response validation
- Authentication and authorization
- Error handling
- Rate limiting

**Location**:
```
tests/api/
```

### 5. Performance Tests

**Purpose**: Validate system performance under load

**Coverage**:
- Load testing
- Stress testing
- Scalability validation
- Response time measurement
- Resource usage monitoring

**Location**:
```
tests/performance/
tests/stress/
```

### 6. Security Tests

**Purpose**: Validate security measures and vulnerability prevention

**Coverage**:
- Authentication testing
- Authorization validation
- Input validation
- Dependency vulnerability scanning
- Penetration testing

**Location**:
```
tests/security/
```

## Running Tests

### Quick Start

```bash
# Run all tests
./test-runner.sh

# Run specific test types
./test-runner.sh --no-e2e --no-performance

# Run individual test suites
cd apps/orchestrator && python -m pytest tests/
cd apps/frontend && npm test
```

### Test Runner Options

```bash
./test-runner.sh [options]

Options:
  --no-python      Skip Python unit tests
  --no-frontend    Skip frontend tests
  --no-integration Skip integration tests
  --no-e2e         Skip end-to-end tests
  --no-performance Skip performance tests
  --no-security    Skip security tests
  --help           Show this help message
```

### Individual Test Commands

#### Python Tests (Orchestrator & Workers)

```bash
# Run all tests
cd apps/orchestrator
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html

# Run specific test file
python -m pytest tests/unit/test_design_service.py -v

# Run specific test function
python -m pytest tests/unit/test_design_service.py::test_ai_design -v
```

#### Frontend Tests

```bash
# Run unit tests
cd apps/frontend
npm test

# Run with coverage
npm test -- --coverage

# Run E2E tests
npx playwright test tests/e2e/

# Run specific E2E test
npx playwright test tests/e2e/flow-builder.test.ts
```

#### Integration Tests

```bash
# Run API integration tests
python -m pytest tests/api_integration/ -v

# Run database tests
python -m pytest tests/database/ -v

# Run monitoring tests
python -m pytest tests/monitoring/ -v
```

## Test Environment

### Prerequisites

1. **Docker & Docker Compose**: For running test environment
2. **Python 3.11+**: For backend tests
3. **Node.js 18+**: For frontend tests
4. **Playwright**: For E2E tests
5. **Environment Variables**: Configured `.env` file

### Environment Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd ai-business-automation-designer

# 2. Set up environment
cp .env.example .env
# Edit .env with test configuration

# 3. Install dependencies
cd apps/orchestrator && pip install -r requirements.txt
cd ../frontend && npm install
cd ../..

# 4. Install Playwright
cd apps/frontend && npx playwright install
cd ../..
```

### Test Database

The test environment uses a separate test database:

```yaml
# docker-compose.dev.yml
services:
  postgres:
    environment:
      POSTGRES_DB: ai_automation_test
```

### Test Data

Test data is automatically generated and cleaned up:

```python
# Test fixtures
@pytest.fixture
def sample_workflow():
    return {
        "name": "Test Workflow",
        "description": "Test workflow for testing",
        "definition": {"steps": []}
    }
```

## Test Coverage

### Coverage Reports

Coverage reports are generated automatically:

```bash
# View coverage reports
open coverage/orchestrator/index.html
open coverage/workers/index.html
open coverage/frontend/lcov-report/index.html
```

### Coverage Targets

- **Unit Tests**: >90% line coverage
- **Integration Tests**: >80% integration coverage
- **E2E Tests**: 100% critical path coverage

### Coverage Configuration

```python
# pytest.ini
[tool:pytest]
addopts = 
    --cov=app
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=90
```

## Continuous Integration

### GitHub Actions

Tests run automatically on every commit:

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Tests
        run: ./test-runner.sh
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

Automated checks before commits:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Performance Testing

### Load Testing

```bash
# Run load tests
python -m pytest tests/performance/test_load.py -v

# Custom load test
python -m pytest tests/performance/test_load.py::test_workflow_execution_load -v
```

### Stress Testing

```bash
# Run stress tests
python -m pytest tests/stress/test_stress.py -v

# Memory leak testing
python -m pytest tests/stress/test_memory_leaks.py -v
```

### Performance Benchmarks

```python
# tests/performance/test_benchmarks.py
def test_workflow_execution_performance():
    start_time = time.time()
    result = execute_workflow(complex_workflow)
    execution_time = time.time() - start_time
    
    assert execution_time < 5.0  # Should complete within 5 seconds
    assert result.status == "completed"
```

## Security Testing

### Vulnerability Scanning

```bash
# Python dependencies
cd apps/orchestrator
safety check

# Node.js dependencies
cd apps/frontend
npm audit
```

### Security Tests

```python
# tests/security/test_authentication.py
def test_jwt_token_validation():
    # Test JWT token validation
    token = create_test_token()
    result = validate_token(token)
    assert result.is_valid == True
```

### Penetration Testing

```python
# tests/security/test_penetration.py
def test_sql_injection_prevention():
    # Test SQL injection prevention
    malicious_input = "'; DROP TABLE users; --"
    result = process_user_input(malicious_input)
    assert "DROP TABLE" not in result.query
```

## Test Data Management

### Fixtures

```python
# conftest.py
@pytest.fixture(scope="session")
def test_db():
    """Create test database session."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_user(test_db):
    """Create sample user for testing."""
    user = User(email="test@example.com", username="testuser")
    test_db.add(user)
    test_db.commit()
    return user
```

### Mock Data

```python
# tests/fixtures/mock_data.py
MOCK_WORKFLOW = {
    "name": "Test Workflow",
    "description": "Test workflow",
    "definition": {
        "steps": [
            {
                "id": "step1",
                "type": "connector",
                "name": "HTTP Request",
                "config": {"url": "https://httpbin.org/get"}
            }
        ]
    }
}
```

## Troubleshooting

### Common Issues

#### 1. Test Environment Not Starting

```bash
# Check Docker status
docker info

# Check port conflicts
netstat -tulpn | grep :8000

# Restart Docker
sudo systemctl restart docker
```

#### 2. Database Connection Issues

```bash
# Check database status
docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U ai_user

# Reset test database
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

#### 3. Frontend Tests Failing

```bash
# Clear node modules
cd apps/frontend
rm -rf node_modules package-lock.json
npm install

# Clear Playwright cache
npx playwright install --force
```

#### 4. E2E Tests Timing Out

```bash
# Increase timeout
npx playwright test --timeout=60000

# Run in headed mode for debugging
npx playwright test --headed
```

### Debug Mode

Enable debug logging:

```bash
# Python tests
python -m pytest tests/ -v -s --log-cli-level=DEBUG

# Frontend tests
npm test -- --verbose

# E2E tests
DEBUG=pw:api npx playwright test
```

### Test Reports

View detailed test reports:

```bash
# HTML report
open test-results/test-report.html

# JUnit XML reports
open test-results/orchestrator-unit.xml
open test-results/e2e-results.xml
```

## Best Practices

### Writing Tests

1. **Test Naming**: Use descriptive test names
2. **Arrange-Act-Assert**: Structure tests clearly
3. **Isolation**: Each test should be independent
4. **Mocking**: Mock external dependencies
5. **Data Cleanup**: Clean up test data after tests

### Test Maintenance

1. **Regular Updates**: Keep tests up to date with code changes
2. **Refactoring**: Refactor tests when code changes
3. **Performance**: Keep tests fast and efficient
4. **Documentation**: Document complex test scenarios

### Continuous Improvement

1. **Coverage Analysis**: Monitor and improve test coverage
2. **Performance Monitoring**: Track test execution time
3. **Flaky Test Detection**: Identify and fix flaky tests
4. **Test Automation**: Automate test execution and reporting

## Support

For testing support:

1. Check the [GitHub Issues](https://github.com/your-repo/issues)
2. Review the [Test Documentation](https://docs.your-domain.com/testing)
3. Contact the testing team

## License

This testing guide is part of the AI Business Automation Designer project and is licensed under the MIT License.
