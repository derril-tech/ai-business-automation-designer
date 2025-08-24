"""
Mock Data Provider for Simulation

Generates realistic test data for different workflow step types
during simulation and testing.
"""

import json
import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

import structlog
from faker import Faker

logger = structlog.get_logger(__name__)

# Initialize Faker for generating realistic data
fake = Faker()


class MockDataProvider:
    """Provides mock data for workflow simulation"""
    
    def __init__(self):
        self.fake = Faker()
        self._setup_mock_data_templates()
    
    def _setup_mock_data_templates(self):
        """Setup predefined mock data templates"""
        self.mock_templates = {
            "connector": {
                "http": {
                    "url": "https://api.example.com/users",
                    "method": "GET",
                    "headers": {"Authorization": "Bearer mock_token_123"},
                    "params": {"limit": 10, "offset": 0},
                    "body": None
                },
                "database": {
                    "connection_string": "postgresql://user:pass@localhost:5432/testdb",
                    "query": "SELECT * FROM users WHERE status = 'active'",
                    "parameters": {"status": "active"}
                },
                "email": {
                    "to": ["user@example.com"],
                    "subject": "Test Email",
                    "body": "This is a test email from workflow simulation",
                    "from": "noreply@example.com"
                },
                "slack": {
                    "channel": "#general",
                    "message": "Test message from workflow simulation",
                    "webhook_url": "https://hooks.slack.com/services/mock/webhook"
                },
                "salesforce": {
                    "object": "Contact",
                    "action": "create",
                    "data": {
                        "FirstName": "John",
                        "LastName": "Doe",
                        "Email": "john.doe@example.com"
                    }
                }
            },
            "transform": {
                "map": {
                    "data": [
                        {"id": 1, "name": "John Doe", "email": "john@example.com"},
                        {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
                    ],
                    "mapping": {
                        "user_id": "id",
                        "full_name": "name",
                        "contact_email": "email"
                    }
                },
                "filter": {
                    "data": [
                        {"id": 1, "status": "active", "value": 100},
                        {"id": 2, "status": "inactive", "value": 50},
                        {"id": 3, "status": "active", "value": 200}
                    ],
                    "condition": "status == 'active'"
                },
                "aggregate": {
                    "data": [
                        {"category": "A", "value": 100},
                        {"category": "A", "value": 150},
                        {"category": "B", "value": 200}
                    ],
                    "group_by": "category",
                    "aggregations": ["sum", "count", "avg"]
                }
            },
            "condition": {
                "if_else": {
                    "condition": "value > 100",
                    "true_value": "high",
                    "false_value": "low",
                    "test_data": {"value": 150}
                },
                "switch": {
                    "value": "status",
                    "cases": {
                        "active": "user_active",
                        "inactive": "user_inactive",
                        "pending": "user_pending"
                    },
                    "default": "unknown",
                    "test_data": {"status": "active"}
                }
            },
            "webhook": {
                "outgoing": {
                    "url": "https://webhook.site/mock-endpoint",
                    "method": "POST",
                    "headers": {"Content-Type": "application/json"},
                    "body": {"event": "workflow_completed", "timestamp": "2024-01-01T00:00:00Z"}
                },
                "incoming": {
                    "endpoint": "/webhook/mock",
                    "secret": "mock_webhook_secret",
                    "expected_payload": {"event": "data_received"}
                }
            },
            "delay": {
                "fixed": {
                    "duration_seconds": 5,
                    "description": "Wait for 5 seconds"
                },
                "dynamic": {
                    "duration_expression": "{{delay_minutes}} * 60",
                    "variables": {"delay_minutes": 2}
                }
            }
        }
    
    async def get_mock_data(
        self,
        step_type: str,
        step_config: Dict[str, Any],
        mock_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get mock data for a specific step type and configuration"""
        
        try:
            if step_type == "connector":
                return await self._get_connector_mock_data(step_config, mock_config)
            elif step_type == "transform":
                return await self._get_transform_mock_data(step_config, mock_config)
            elif step_type == "condition":
                return await self._get_condition_mock_data(step_config, mock_config)
            elif step_type == "webhook":
                return await self._get_webhook_mock_data(step_config, mock_config)
            elif step_type == "delay":
                return await self._get_delay_mock_data(step_config, mock_config)
            else:
                return await self._get_generic_mock_data(step_type, step_config, mock_config)
        
        except Exception as e:
            logger.warning(f"Failed to generate mock data for {step_type}: {e}")
            return {}
    
    async def _get_connector_mock_data(
        self,
        step_config: Dict[str, Any],
        mock_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate mock data for connector steps"""
        
        connector_type = step_config.get("connector_type", "http")
        
        if connector_type == "http":
            return {
                "url": step_config.get("url", "https://api.example.com/mock"),
                "method": step_config.get("method", "GET"),
                "headers": step_config.get("headers", {"Content-Type": "application/json"}),
                "params": step_config.get("params", {}),
                "body": step_config.get("body"),
                "timeout": step_config.get("timeout", 30),
                "mock_response": {
                    "status_code": 200,
                    "headers": {"content-type": "application/json"},
                    "data": self._generate_mock_api_response()
                }
            }
        
        elif connector_type == "database":
            return {
                "connection_string": step_config.get("connection_string", "postgresql://mock"),
                "query": step_config.get("query", "SELECT * FROM mock_table"),
                "parameters": step_config.get("parameters", {}),
                "mock_result": self._generate_mock_database_result()
            }
        
        elif connector_type == "email":
            return {
                "to": step_config.get("to", [self.fake.email()]),
                "subject": step_config.get("subject", "Mock Email Subject"),
                "body": step_config.get("body", "Mock email body content"),
                "from": step_config.get("from", "noreply@example.com"),
                "mock_sent": True
            }
        
        elif connector_type == "slack":
            return {
                "channel": step_config.get("channel", "#general"),
                "message": step_config.get("message", "Mock Slack message"),
                "webhook_url": step_config.get("webhook_url", "https://hooks.slack.com/mock"),
                "mock_sent": True
            }
        
        elif connector_type == "salesforce":
            return {
                "object": step_config.get("object", "Contact"),
                "action": step_config.get("action", "create"),
                "data": step_config.get("data", self._generate_mock_salesforce_data()),
                "mock_result": {"success": True, "id": str(uuid4())}
            }
        
        else:
            return {"mock_data": True}
    
    async def _get_transform_mock_data(
        self,
        step_config: Dict[str, Any],
        mock_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate mock data for transform steps"""
        
        transform_type = step_config.get("transform_type", "map")
        
        if transform_type == "map":
            return {
                "data": step_config.get("data", self._generate_mock_array_data()),
                "mapping": step_config.get("mapping", {"id": "user_id", "name": "full_name"}),
                "mock_transformed": self._generate_mock_transformed_data()
            }
        
        elif transform_type == "filter":
            return {
                "data": step_config.get("data", self._generate_mock_array_data()),
                "condition": step_config.get("condition", "status == 'active'"),
                "mock_filtered": self._generate_mock_filtered_data()
            }
        
        elif transform_type == "aggregate":
            return {
                "data": step_config.get("data", self._generate_mock_aggregate_data()),
                "group_by": step_config.get("group_by", "category"),
                "aggregations": step_config.get("aggregations", ["sum", "count"]),
                "mock_aggregated": self._generate_mock_aggregated_data()
            }
        
        else:
            return {"mock_transformed": True}
    
    async def _get_condition_mock_data(
        self,
        step_config: Dict[str, Any],
        mock_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate mock data for condition steps"""
        
        condition_type = step_config.get("condition_type", "if_else")
        
        if condition_type == "if_else":
            return {
                "condition": step_config.get("condition", "value > 100"),
                "true_value": step_config.get("true_value", "high"),
                "false_value": step_config.get("false_value", "low"),
                "test_data": step_config.get("test_data", {"value": 150}),
                "mock_result": True
            }
        
        elif condition_type == "switch":
            return {
                "value": step_config.get("value", "status"),
                "cases": step_config.get("cases", {"active": "user_active", "inactive": "user_inactive"}),
                "default": step_config.get("default", "unknown"),
                "test_data": step_config.get("test_data", {"status": "active"}),
                "mock_result": "user_active"
            }
        
        else:
            return {"mock_condition_result": True}
    
    async def _get_webhook_mock_data(
        self,
        step_config: Dict[str, Any],
        mock_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate mock data for webhook steps"""
        
        webhook_type = step_config.get("webhook_type", "outgoing")
        
        if webhook_type == "outgoing":
            return {
                "url": step_config.get("url", "https://webhook.site/mock"),
                "method": step_config.get("method", "POST"),
                "headers": step_config.get("headers", {"Content-Type": "application/json"}),
                "body": step_config.get("body", {"event": "mock_event"}),
                "mock_sent": True,
                "mock_response": {"status_code": 200}
            }
        
        elif webhook_type == "incoming":
            return {
                "endpoint": step_config.get("endpoint", "/webhook/mock"),
                "secret": step_config.get("secret", "mock_secret"),
                "expected_payload": step_config.get("expected_payload", {"event": "mock_event"}),
                "mock_received": True
            }
        
        else:
            return {"mock_webhook": True}
    
    async def _get_delay_mock_data(
        self,
        step_config: Dict[str, Any],
        mock_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate mock data for delay steps"""
        
        delay_type = step_config.get("delay_type", "fixed")
        
        if delay_type == "fixed":
            return {
                "duration_seconds": step_config.get("duration_seconds", 5),
                "description": step_config.get("description", "Mock delay"),
                "mock_completed": True
            }
        
        elif delay_type == "dynamic":
            return {
                "duration_expression": step_config.get("duration_expression", "{{delay_minutes}} * 60"),
                "variables": step_config.get("variables", {"delay_minutes": 2}),
                "mock_completed": True
            }
        
        else:
            return {"mock_delay": True}
    
    async def _get_generic_mock_data(
        self,
        step_type: str,
        step_config: Dict[str, Any],
        mock_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate generic mock data for unknown step types"""
        
        return {
            "step_type": step_type,
            "config": step_config,
            "mock_data": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _generate_mock_api_response(self) -> Dict[str, Any]:
        """Generate a realistic mock API response"""
        
        response_types = [
            {"users": [{"id": 1, "name": self.fake.name(), "email": self.fake.email()}]},
            {"data": {"count": random.randint(1, 100), "items": [{"id": i, "value": random.randint(1, 1000)} for i in range(5)]}},
            {"status": "success", "message": "Operation completed successfully"},
            {"result": {"processed": random.randint(1, 50), "failed": 0, "total": random.randint(50, 100)}}
        ]
        
        return random.choice(response_types)
    
    def _generate_mock_database_result(self) -> List[Dict[str, Any]]:
        """Generate mock database query results"""
        
        return [
            {
                "id": i,
                "name": self.fake.name(),
                "email": self.fake.email(),
                "status": random.choice(["active", "inactive", "pending"]),
                "created_at": self.fake.date_time().isoformat()
            }
            for i in range(random.randint(1, 10))
        ]
    
    def _generate_mock_salesforce_data(self) -> Dict[str, Any]:
        """Generate mock Salesforce object data"""
        
        return {
            "FirstName": self.fake.first_name(),
            "LastName": self.fake.last_name(),
            "Email": self.fake.email(),
            "Phone": self.fake.phone_number(),
            "Company": self.fake.company()
        }
    
    def _generate_mock_array_data(self) -> List[Dict[str, Any]]:
        """Generate mock array data for transformations"""
        
        return [
            {
                "id": i,
                "name": self.fake.name(),
                "email": self.fake.email(),
                "status": random.choice(["active", "inactive"]),
                "value": random.randint(1, 1000)
            }
            for i in range(random.randint(3, 10))
        ]
    
    def _generate_mock_transformed_data(self) -> List[Dict[str, Any]]:
        """Generate mock transformed data"""
        
        return [
            {
                "user_id": i,
                "full_name": self.fake.name(),
                "contact_email": self.fake.email()
            }
            for i in range(random.randint(3, 10))
        ]
    
    def _generate_mock_filtered_data(self) -> List[Dict[str, Any]]:
        """Generate mock filtered data"""
        
        return [
            {
                "id": i,
                "name": self.fake.name(),
                "status": "active",
                "value": random.randint(1, 1000)
            }
            for i in range(random.randint(1, 5))
        ]
    
    def _generate_mock_aggregate_data(self) -> List[Dict[str, Any]]:
        """Generate mock data for aggregation"""
        
        categories = ["A", "B", "C", "D"]
        return [
            {
                "category": random.choice(categories),
                "value": random.randint(10, 500),
                "date": self.fake.date().isoformat()
            }
            for _ in range(random.randint(10, 20))
        ]
    
    def _generate_mock_aggregated_data(self) -> Dict[str, Any]:
        """Generate mock aggregated results"""
        
        return {
            "A": {"sum": 1500, "count": 5, "avg": 300},
            "B": {"sum": 2200, "count": 4, "avg": 550},
            "C": {"sum": 800, "count": 3, "avg": 267},
            "D": {"sum": 1200, "count": 2, "avg": 600}
        }
    
    def generate_test_scenarios(self, step_type: str) -> List[Dict[str, Any]]:
        """Generate multiple test scenarios for a step type"""
        
        scenarios = []
        
        if step_type == "connector":
            scenarios = [
                {"name": "Successful API Call", "config": {"connector_type": "http", "method": "GET"}, "expected": "success"},
                {"name": "Database Query", "config": {"connector_type": "database", "query": "SELECT * FROM users"}, "expected": "success"},
                {"name": "Email Send", "config": {"connector_type": "email", "to": ["test@example.com"]}, "expected": "success"},
                {"name": "API Error", "config": {"connector_type": "http", "method": "POST"}, "expected": "error"}
            ]
        
        elif step_type == "transform":
            scenarios = [
                {"name": "Data Mapping", "config": {"transform_type": "map"}, "expected": "success"},
                {"name": "Data Filtering", "config": {"transform_type": "filter"}, "expected": "success"},
                {"name": "Data Aggregation", "config": {"transform_type": "aggregate"}, "expected": "success"}
            ]
        
        elif step_type == "condition":
            scenarios = [
                {"name": "If-Else Condition", "config": {"condition_type": "if_else"}, "expected": "success"},
                {"name": "Switch Condition", "config": {"condition_type": "switch"}, "expected": "success"}
            ]
        
        return scenarios
