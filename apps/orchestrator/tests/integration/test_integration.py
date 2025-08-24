"""
Integration tests for the AI Business Automation Designer orchestrator.
Tests complete workflows from AI design to execution.
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.config import settings
from app.core.database import get_db, Base
from app.models.workflow import Workflow, WorkflowExecution
from app.models.user import User
from app.services.design_service import DesignService
from app.services.execution_service import ExecutionService
from app.services.simulation_service import SimulationService


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_workflow(db_session, sample_user):
    """Create a sample workflow for testing."""
    workflow = Workflow(
        name="Test Workflow",
        description="A test workflow for integration testing",
        definition={
            "steps": [
                {
                    "id": "step1",
                    "type": "connector",
                    "name": "HTTP Request",
                    "config": {
                        "method": "GET",
                        "url": "https://httpbin.org/get",
                        "headers": {"Content-Type": "application/json"}
                    }
                },
                {
                    "id": "step2",
                    "type": "transform",
                    "name": "Process Response",
                    "config": {
                        "operation": "map",
                        "mapping": {
                            "status": "{{step1.status_code}}",
                            "data": "{{step1.body}}"
                        }
                    },
                    "dependencies": ["step1"]
                }
            ]
        },
        user_id=sample_user.id
    )
    db_session.add(workflow)
    db_session.commit()
    db_session.refresh(workflow)
    return workflow


class TestCompleteWorkflowIntegration:
    """Test complete workflow integration from design to execution."""

    @patch('app.services.design_service.DesignService._call_crewai_chain')
    def test_ai_design_to_execution_flow(self, mock_crewai, client, db_session, sample_user):
        """Test complete flow from AI design to workflow execution."""
        # Mock CrewAI response
        mock_crewai.return_value = {
            "workflow": {
                "name": "Email Processing Workflow",
                "description": "Process incoming emails and send notifications",
                "steps": [
                    {
                        "id": "step1",
                        "type": "connector",
                        "name": "Check Email",
                        "config": {
                            "connector": "email",
                            "action": "check_inbox",
                            "filters": {"unread": True}
                        }
                    },
                    {
                        "id": "step2",
                        "type": "condition",
                        "name": "Check Priority",
                        "config": {
                            "condition": "{{step1.priority == 'high'}}",
                            "true_steps": ["step3"],
                            "false_steps": ["step4"]
                        },
                        "dependencies": ["step1"]
                    },
                    {
                        "id": "step3",
                        "type": "connector",
                        "name": "Send Slack Alert",
                        "config": {
                            "connector": "slack",
                            "action": "send_message",
                            "channel": "#alerts",
                            "message": "High priority email received: {{step1.subject}}"
                        },
                        "dependencies": ["step2"]
                    },
                    {
                        "id": "step4",
                        "type": "transform",
                        "name": "Log Email",
                        "config": {
                            "operation": "log",
                            "message": "Email processed: {{step1.subject}}"
                        },
                        "dependencies": ["step2"]
                    }
                ]
            },
            "confidence": 0.95,
            "recommendations": ["Consider adding email filtering rules"]
        }

        # 1. Test AI Design
        design_response = client.post(
            "/api/v1/design/ai-design",
            json={
                "goal": "Create a workflow to process incoming emails and send Slack notifications for high priority emails",
                "constraints": ["Use email and Slack connectors", "Handle high priority emails differently"],
                "preferences": {"notification_channel": "slack"}
            }
        )
        assert design_response.status_code == 200
        design_data = design_response.json()
        assert "workflow" in design_data
        assert design_data["confidence"] > 0.8

        # 2. Test Workflow Creation
        workflow_response = client.post(
            "/api/v1/workflows/",
            json={
                "name": design_data["workflow"]["name"],
                "description": design_data["workflow"]["description"],
                "definition": design_data["workflow"]
            }
        )
        assert workflow_response.status_code == 201
        workflow_data = workflow_response.json()
        workflow_id = workflow_data["id"]

        # 3. Test Workflow Validation
        validation_response = client.post(
            f"/api/v1/workflows/{workflow_id}/validate"
        )
        assert validation_response.status_code == 200
        validation_data = validation_response.json()
        assert validation_data["is_valid"] == True

        # 4. Test Workflow Simulation
        simulation_response = client.post(
            f"/api/v1/simulation/start",
            json={
                "workflow_id": workflow_id,
                "initial_variables": {
                    "test_email": {
                        "subject": "Test High Priority Email",
                        "priority": "high",
                        "body": "This is a test email"
                    }
                }
            }
        )
        assert simulation_response.status_code == 200
        simulation_data = simulation_response.json()
        simulation_id = simulation_data["simulation_id"]

        # 5. Test Simulation Results
        simulation_results = client.get(f"/api/v1/simulation/{simulation_id}")
        assert simulation_results.status_code == 200
        results_data = simulation_results.json()
        assert results_data["status"] in ["completed", "running"]

        # 6. Test Workflow Execution
        execution_response = client.post(
            f"/api/v1/execution/start",
            json={
                "workflow_id": workflow_id,
                "initial_variables": {
                    "test_mode": True
                }
            }
        )
        assert execution_response.status_code == 200
        execution_data = execution_response.json()
        execution_id = execution_data["execution_id"]

        # 7. Test Execution Status
        execution_status = client.get(f"/api/v1/execution/{execution_id}")
        assert execution_status.status_code == 200
        status_data = execution_status.json()
        assert status_data["workflow_id"] == workflow_id

    def test_error_handling_and_recovery(self, client, db_session, sample_user):
        """Test error handling and recovery mechanisms."""
        # Create a workflow with potential errors
        workflow_response = client.post(
            "/api/v1/workflows/",
            json={
                "name": "Error Test Workflow",
                "description": "Test error handling",
                "definition": {
                    "steps": [
                        {
                            "id": "step1",
                            "type": "connector",
                            "name": "Failing HTTP Request",
                            "config": {
                                "method": "GET",
                                "url": "https://invalid-url-that-will-fail.com",
                                "timeout": 5
                            }
                        },
                        {
                            "id": "step2",
                            "type": "transform",
                            "name": "Process Data",
                            "config": {
                                "operation": "map",
                                "mapping": {"result": "{{step1.data}}"}
                            },
                            "dependencies": ["step1"]
                        }
                    ]
                }
            }
        )
        assert workflow_response.status_code == 201
        workflow_id = workflow_response.json()["id"]

        # Test execution with error handling
        execution_response = client.post(
            f"/api/v1/execution/start",
            json={
                "workflow_id": workflow_id,
                "initial_variables": {},
                "error_handling": {
                    "retry_policy": {
                        "max_retries": 2,
                        "backoff_factor": 1.5
                    },
                    "continue_on_error": True
                }
            }
        )
        assert execution_response.status_code == 200

        # Check execution status
        execution_id = execution_response.json()["execution_id"]
        status_response = client.get(f"/api/v1/execution/{execution_id}")
        assert status_response.status_code == 200

    def test_variable_resolution_across_steps(self, client, db_session, sample_user):
        """Test variable resolution across workflow steps."""
        workflow_response = client.post(
            "/api/v1/workflows/",
            json={
                "name": "Variable Test Workflow",
                "description": "Test variable resolution",
                "definition": {
                    "steps": [
                        {
                            "id": "step1",
                            "type": "transform",
                            "name": "Generate Data",
                            "config": {
                                "operation": "set",
                                "variables": {
                                    "user_id": "12345",
                                    "timestamp": "{{now()}}",
                                    "status": "active"
                                }
                            }
                        },
                        {
                            "id": "step2",
                            "type": "transform",
                            "name": "Process User",
                            "config": {
                                "operation": "map",
                                "mapping": {
                                    "processed_user": {
                                        "id": "{{step1.user_id}}",
                                        "created_at": "{{step1.timestamp}}",
                                        "status": "{{step1.status}}"
                                    }
                                }
                            },
                            "dependencies": ["step1"]
                        },
                        {
                            "id": "step3",
                            "type": "transform",
                            "name": "Final Result",
                            "config": {
                                "operation": "set",
                                "variables": {
                                    "final_result": "{{step2.processed_user}}",
                                    "summary": "Processed user {{step1.user_id}} at {{step1.timestamp}}"
                                }
                            },
                            "dependencies": ["step2"]
                        }
                    ]
                }
            }
        )
        assert workflow_response.status_code == 201
        workflow_id = workflow_response.json()["id"]

        # Execute workflow
        execution_response = client.post(
            f"/api/v1/execution/start",
            json={
                "workflow_id": workflow_id,
                "initial_variables": {}
            }
        )
        assert execution_response.status_code == 200

        # Check execution results
        execution_id = execution_response.json()["execution_id"]
        status_response = client.get(f"/api/v1/execution/{execution_id}")
        assert status_response.status_code == 200

        # Verify variable resolution
        status_data = status_response.json()
        if status_data["status"] == "completed":
            assert "final_result" in status_data.get("variables", {})
            assert "summary" in status_data.get("variables", {})

    def test_concurrent_executions(self, client, db_session, sample_user):
        """Test handling of concurrent workflow executions."""
        # Create a simple workflow
        workflow_response = client.post(
            "/api/v1/workflows/",
            json={
                "name": "Concurrent Test Workflow",
                "description": "Test concurrent executions",
                "definition": {
                    "steps": [
                        {
                            "id": "step1",
                            "type": "delay",
                            "name": "Wait",
                            "config": {
                                "duration": 2
                            }
                        },
                        {
                            "id": "step2",
                            "type": "transform",
                            "name": "Process",
                            "config": {
                                "operation": "set",
                                "variables": {
                                    "result": "completed"
                                }
                            },
                            "dependencies": ["step1"]
                        }
                    ]
                }
            }
        )
        assert workflow_response.status_code == 201
        workflow_id = workflow_response.json()["id"]

        # Start multiple concurrent executions
        execution_ids = []
        for i in range(3):
            execution_response = client.post(
                f"/api/v1/execution/start",
                json={
                    "workflow_id": workflow_id,
                    "initial_variables": {"execution_number": i}
                }
            )
            assert execution_response.status_code == 200
            execution_ids.append(execution_response.json()["execution_id"])

        # Check all executions are running
        for execution_id in execution_ids:
            status_response = client.get(f"/api/v1/execution/{execution_id}")
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["status"] in ["running", "completed"]

    def test_workflow_cancellation(self, client, db_session, sample_user):
        """Test workflow execution cancellation."""
        # Create a long-running workflow
        workflow_response = client.post(
            "/api/v1/workflows/",
            json={
                "name": "Cancellation Test Workflow",
                "description": "Test workflow cancellation",
                "definition": {
                    "steps": [
                        {
                            "id": "step1",
                            "type": "delay",
                            "name": "Long Wait",
                            "config": {
                                "duration": 30
                            }
                        }
                    ]
                }
            }
        )
        assert workflow_response.status_code == 201
        workflow_id = workflow_response.json()["id"]

        # Start execution
        execution_response = client.post(
            f"/api/v1/execution/start",
            json={
                "workflow_id": workflow_id,
                "initial_variables": {}
            }
        )
        assert execution_response.status_code == 200
        execution_id = execution_response.json()["execution_id"]

        # Cancel execution
        cancel_response = client.post(f"/api/v1/execution/{execution_id}/cancel")
        assert cancel_response.status_code == 200

        # Verify cancellation
        status_response = client.get(f"/api/v1/execution/{execution_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "cancelled"


class TestAPIIntegration:
    """Test API integration and data flow."""

    def test_health_check_integration(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_metrics_endpoint_integration(self, client):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        # Verify Prometheus metrics format
        content = response.text
        assert "http_requests_total" in content
        assert "workflow_executions_total" in content

    def test_database_integration(self, client, db_session, sample_user):
        """Test database integration and data persistence."""
        # Create workflow
        workflow_data = {
            "name": "Database Test Workflow",
            "description": "Test database integration",
            "definition": {"steps": []}
        }
        
        response = client.post("/api/v1/workflows/", json=workflow_data)
        assert response.status_code == 201
        
        # Verify data persistence
        workflow_id = response.json()["id"]
        get_response = client.get(f"/api/v1/workflows/{workflow_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == workflow_data["name"]

    def test_error_response_format(self, client):
        """Test error response format and handling."""
        # Test invalid endpoint
        response = client.get("/api/v1/invalid-endpoint")
        assert response.status_code == 404
        error_data = response.json()
        assert "error" in error_data
        assert "detail" in error_data

        # Test invalid workflow ID
        response = client.get("/api/v1/workflows/invalid-id")
        assert response.status_code == 422


class TestPerformanceIntegration:
    """Test performance and scalability aspects."""

    def test_workflow_execution_performance(self, client, db_session, sample_user):
        """Test workflow execution performance."""
        # Create a simple workflow for performance testing
        workflow_response = client.post(
            "/api/v1/workflows/",
            json={
                "name": "Performance Test Workflow",
                "description": "Test execution performance",
                "definition": {
                    "steps": [
                        {
                            "id": "step1",
                            "type": "transform",
                            "name": "Quick Process",
                            "config": {
                                "operation": "set",
                                "variables": {"result": "success"}
                            }
                        }
                    ]
                }
            }
        )
        assert workflow_response.status_code == 201
        workflow_id = workflow_response.json()["id"]

        # Execute and measure performance
        import time
        start_time = time.time()
        
        execution_response = client.post(
            f"/api/v1/execution/start",
            json={
                "workflow_id": workflow_id,
                "initial_variables": {}
            }
        )
        assert execution_response.status_code == 200
        
        execution_time = time.time() - start_time
        # Execution should complete quickly (under 5 seconds)
        assert execution_time < 5.0

    def test_concurrent_api_requests(self, client, db_session, sample_user):
        """Test handling of concurrent API requests."""
        import threading
        import time

        # Create a simple workflow
        workflow_response = client.post(
            "/api/v1/workflows/",
            json={
                "name": "Concurrent API Test",
                "description": "Test concurrent API requests",
                "definition": {"steps": []}
            }
        )
        assert workflow_response.status_code == 201
        workflow_id = workflow_response.json()["id"]

        # Test concurrent GET requests
        def make_request():
            response = client.get(f"/api/v1/workflows/{workflow_id}")
            assert response.status_code == 200

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
