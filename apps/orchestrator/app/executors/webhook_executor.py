"""
Webhook Step Executor

Handles execution of webhook steps for external integrations.
Supports both incoming and outgoing webhooks with various HTTP methods.
"""

import asyncio
import json
import hmac
import hashlib
from typing import Any, Dict, Optional
from datetime import datetime, timezone

import httpx
import structlog
from pydantic import BaseModel

from app.core.execution_engine import StepExecutor, WorkflowStep, ExecutionContext

logger = structlog.get_logger(__name__)


class WebhookConfig(BaseModel):
    """Configuration for webhook steps"""
    webhook_type: str = "outgoing"  # outgoing, incoming
    url: Optional[str] = None
    method: str = "POST"
    headers: Dict[str, str] = {}
    body: Optional[Dict[str, Any]] = None
    timeout: int = 30
    retry_on_failure: bool = True
    max_retries: int = 3
    retry_delay: int = 1
    secret: Optional[str] = None  # For signature verification
    signature_header: str = "X-Webhook-Signature"


class WebhookExecutor(StepExecutor):
    """Executor for webhook steps"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def execute(self, step: WorkflowStep, context: ExecutionContext) -> Dict[str, Any]:
        """Execute a webhook step"""
        config = WebhookConfig(**step.config)
        
        logger.info(
            "Executing webhook step",
            step_id=step.id,
            webhook_type=config.webhook_type,
            url=config.url
        )
        
        # Resolve variables in inputs
        resolved_inputs = self._resolve_variables(step.inputs, context.variables)
        
        # Execute based on webhook type
        if config.webhook_type == "outgoing":
            return await self._execute_outgoing_webhook(config, resolved_inputs)
        elif config.webhook_type == "incoming":
            return await self._execute_incoming_webhook(config, resolved_inputs)
        else:
            raise ValueError(f"Unsupported webhook type: {config.webhook_type}")
    
    async def _execute_outgoing_webhook(self, config: WebhookConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute outgoing webhook (send webhook to external system)"""
        url = config.url or inputs.get("url")
        if not url:
            raise ValueError("Outgoing webhook requires url in config or inputs")
        
        # Prepare request
        method = config.method.upper()
        headers = {**config.headers, **inputs.get("headers", {})}
        body = config.body or inputs.get("body") or inputs.get("data", {})
        
        # Add webhook signature if secret is provided
        if config.secret and body:
            signature = self._generate_signature(body, config.secret)
            headers[config.signature_header] = signature
        
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
            
            logger.info(
                "Outgoing webhook sent successfully",
                url=url,
                method=method,
                status_code=response.status_code
            )
            
            return {
                "status": "success",
                "webhook_type": "outgoing",
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "response_body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "Outgoing webhook failed",
                url=url,
                status_code=e.response.status_code,
                error=str(e)
            )
            raise Exception(f"Webhook request failed: {e.response.status_code} - {e.response.text}")
        
        except Exception as e:
            logger.error("Outgoing webhook error", url=url, error=str(e))
            raise
    
    async def _execute_incoming_webhook(self, config: WebhookConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute incoming webhook (receive webhook from external system)"""
        # For incoming webhooks, we typically validate and process the incoming data
        webhook_data = inputs.get("webhook_data", {})
        headers = inputs.get("headers", {})
        
        # Validate webhook signature if secret is provided
        if config.secret:
            signature = headers.get(config.signature_header)
            if not signature:
                raise Exception("Webhook signature header not found")
            
            if not self._verify_signature(webhook_data, config.secret, signature):
                raise Exception("Invalid webhook signature")
        
        logger.info(
            "Incoming webhook processed successfully",
            data_keys=list(webhook_data.keys()) if isinstance(webhook_data, dict) else "non-dict"
        )
        
        return {
            "status": "success",
            "webhook_type": "incoming",
            "webhook_data": webhook_data,
            "headers": headers,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _generate_signature(self, data: Any, secret: str) -> str:
        """Generate HMAC signature for webhook data"""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        signature = hmac.new(
            secret.encode('utf-8'),
            data_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    def _verify_signature(self, data: Any, secret: str, signature: str) -> bool:
        """Verify HMAC signature for webhook data"""
        expected_signature = self._generate_signature(data, secret)
        return hmac.compare_digest(signature, expected_signature)
    
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
