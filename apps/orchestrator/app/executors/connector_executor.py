"""
Connector Step Executor

Handles execution of connector steps that integrate with external systems.
Supports various connector types like HTTP APIs, databases, file systems, etc.
"""

import asyncio
import json
from typing import Any, Dict, Optional
from datetime import datetime, timezone

import httpx
import structlog
from pydantic import BaseModel

from app.core.execution_engine import StepExecutor, WorkflowStep, ExecutionContext

logger = structlog.get_logger(__name__)


class ConnectorConfig(BaseModel):
    """Configuration for connector steps"""
    connector_type: str
    endpoint: Optional[str] = None
    method: str = "GET"
    headers: Dict[str, str] = {}
    body: Optional[Dict[str, Any]] = None
    timeout: int = 30
    retry_on_failure: bool = True
    max_retries: int = 3
    retry_delay: int = 1


class ConnectorExecutor(StepExecutor):
    """Executor for connector steps"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def execute(self, step: WorkflowStep, context: ExecutionContext) -> Dict[str, Any]:
        """Execute a connector step"""
        config = ConnectorConfig(**step.config)
        
        logger.info(
            "Executing connector step",
            step_id=step.id,
            connector_type=config.connector_type,
            endpoint=config.endpoint
        )
        
        # Resolve variables in inputs
        resolved_inputs = self._resolve_variables(step.inputs, context.variables)
        
        # Execute based on connector type
        if config.connector_type == "http":
            return await self._execute_http_connector(config, resolved_inputs)
        elif config.connector_type == "database":
            return await self._execute_database_connector(config, resolved_inputs)
        elif config.connector_type == "file":
            return await self._execute_file_connector(config, resolved_inputs)
        elif config.connector_type == "email":
            return await self._execute_email_connector(config, resolved_inputs)
        elif config.connector_type == "slack":
            return await self._execute_slack_connector(config, resolved_inputs)
        elif config.connector_type == "salesforce":
            return await self._execute_salesforce_connector(config, resolved_inputs)
        else:
            # Generic connector execution
            return await self._execute_generic_connector(config, resolved_inputs)
    
    async def _execute_http_connector(self, config: ConnectorConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP connector"""
        url = config.endpoint or inputs.get("url")
        if not url:
            raise ValueError("HTTP connector requires endpoint or url in inputs")
        
        # Prepare request
        method = config.method.upper()
        headers = {**config.headers, **inputs.get("headers", {})}
        body = config.body or inputs.get("body")
        
        # Make request
        try:
            response = await self.http_client.request(
                method=method,
                url=url,
                headers=headers,
                json=body if body else None,
                timeout=config.timeout
            )
            
            response.raise_for_status()
            
            return {
                "status": "success",
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP connector failed",
                status_code=e.response.status_code,
                error=str(e)
            )
            raise Exception(f"HTTP request failed: {e.response.status_code} - {e.response.text}")
        
        except Exception as e:
            logger.error("HTTP connector error", error=str(e))
            raise
    
    async def _execute_database_connector(self, config: ConnectorConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute database connector"""
        # Mock implementation for now
        logger.info("Executing database connector", inputs=inputs)
        
        return {
            "status": "success",
            "operation": inputs.get("operation", "query"),
            "rows_affected": inputs.get("rows_affected", 0),
            "result": inputs.get("result", []),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _execute_file_connector(self, config: ConnectorConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file connector"""
        # Mock implementation for now
        logger.info("Executing file connector", inputs=inputs)
        
        return {
            "status": "success",
            "operation": inputs.get("operation", "read"),
            "file_path": inputs.get("file_path", ""),
            "content": inputs.get("content", ""),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _execute_email_connector(self, config: ConnectorConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email connector"""
        # Mock implementation for now
        logger.info("Executing email connector", inputs=inputs)
        
        return {
            "status": "success",
            "to": inputs.get("to", []),
            "subject": inputs.get("subject", ""),
            "message_id": f"mock-{datetime.now(timezone.utc).timestamp()}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _execute_slack_connector(self, config: ConnectorConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Slack connector"""
        # Mock implementation for now
        logger.info("Executing Slack connector", inputs=inputs)
        
        return {
            "status": "success",
            "channel": inputs.get("channel", ""),
            "message": inputs.get("message", ""),
            "ts": f"{datetime.now(timezone.utc).timestamp()}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _execute_salesforce_connector(self, config: ConnectorConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Salesforce connector"""
        # Mock implementation for now
        logger.info("Executing Salesforce connector", inputs=inputs)
        
        return {
            "status": "success",
            "object": inputs.get("object", ""),
            "operation": inputs.get("operation", "query"),
            "record_id": inputs.get("record_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _execute_generic_connector(self, config: ConnectorConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generic connector"""
        logger.info(
            "Executing generic connector",
            connector_type=config.connector_type,
            inputs=inputs
        )
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        return {
            "status": "success",
            "connector_type": config.connector_type,
            "processed_data": inputs.get("data", {}),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _resolve_variables(self, inputs: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve variables in inputs using context variables"""
        resolved = {}
        
        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                # Variable reference
                var_name = value[2:-2].strip()
                resolved[key] = variables.get(var_name, value)
            elif isinstance(value, dict):
                # Recursively resolve nested dictionaries
                resolved[key] = self._resolve_variables(value, variables)
            elif isinstance(value, list):
                # Resolve variables in list items
                resolved[key] = [
                    self._resolve_variables(item, variables) if isinstance(item, dict)
                    else variables.get(item[2:-2].strip(), item) if isinstance(item, str) and item.startswith("{{") and item.endswith("}}")
                    else item
                    for item in value
                ]
            else:
                resolved[key] = value
        
        return resolved
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
