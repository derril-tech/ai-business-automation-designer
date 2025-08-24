"""
Workflow Validation for Simulation

Validates workflow configurations and identifies potential issues
before execution or simulation.
"""

import re
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

import structlog
from pydantic import BaseModel, ValidationError

from app.models.workflow import Workflow, WorkflowStep
from app.executors import get_executor

logger = structlog.get_logger(__name__)


class ValidationError(BaseModel):
    """Represents a validation error"""
    step_id: Optional[str] = None
    step_name: Optional[str] = None
    error_type: str
    message: str
    severity: str = "error"  # error, warning, info
    field: Optional[str] = None


class ValidationResult(BaseModel):
    """Result of workflow validation"""
    is_valid: bool
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []
    info: List[ValidationError] = []
    
    @property
    def all_issues(self) -> List[ValidationError]:
        """Get all validation issues"""
        return self.errors + self.warnings + self.info


class WorkflowValidator:
    """Validates workflow configurations and identifies issues"""
    
    def __init__(self):
        self.required_fields = {
            "connector": ["connector_type"],
            "transform": ["transform_type"],
            "condition": ["condition_type"],
            "webhook": ["webhook_type"],
            "delay": ["delay_type"]
        }
        
        self.valid_connector_types = ["http", "database", "email", "slack", "salesforce"]
        self.valid_transform_types = ["map", "filter", "aggregate", "format", "split", "join"]
        self.valid_condition_types = ["if_else", "switch", "all", "any"]
        self.valid_webhook_types = ["outgoing", "incoming"]
        self.valid_delay_types = ["fixed", "dynamic", "conditional"]
    
    async def validate_workflow(self, workflow: Workflow) -> List[str]:
        """Validate a complete workflow and return error messages"""
        
        result = ValidationResult()
        
        # Basic workflow validation
        self._validate_workflow_basics(workflow, result)
        
        # Step validation
        await self._validate_workflow_steps(workflow, result)
        
        # Connection validation
        self._validate_workflow_connections(workflow, result)
        
        # Variable validation
        self._validate_workflow_variables(workflow, result)
        
        # Performance validation
        self._validate_workflow_performance(workflow, result)
        
        # Security validation
        self._validate_workflow_security(workflow, result)
        
        # Return error messages
        return [error.message for error in result.errors]
    
    def _validate_workflow_basics(self, workflow: Workflow, result: ValidationResult):
        """Validate basic workflow properties"""
        
        if not workflow.name or len(workflow.name.strip()) == 0:
            result.errors.append(ValidationError(
                error_type="missing_name",
                message="Workflow must have a name",
                severity="error"
            ))
        
        if not workflow.steps:
            result.errors.append(ValidationError(
                error_type="no_steps",
                message="Workflow must have at least one step",
                severity="error"
            ))
        
        # Check for start steps
        start_steps = [step for step in workflow.steps if step.type == "start"]
        if not start_steps:
            result.errors.append(ValidationError(
                error_type="no_start_step",
                message="Workflow must have at least one start step",
                severity="error"
            ))
        
        # Check for end steps
        end_steps = [step for step in workflow.steps if step.type == "end"]
        if not end_steps:
            result.warnings.append(ValidationError(
                error_type="no_end_step",
                message="Workflow should have at least one end step",
                severity="warning"
            ))
    
    async def _validate_workflow_steps(self, workflow: Workflow, result: ValidationResult):
        """Validate individual workflow steps"""
        
        step_ids = set()
        
        for step in workflow.steps:
            # Check for duplicate step IDs
            if step.id in step_ids:
                result.errors.append(ValidationError(
                    step_id=step.id,
                    step_name=step.name,
                    error_type="duplicate_step_id",
                    message=f"Duplicate step ID: {step.id}",
                    severity="error"
                ))
            else:
                step_ids.add(step.id)
            
            # Validate step basics
            self._validate_step_basics(step, result)
            
            # Validate step configuration
            await self._validate_step_config(step, result)
            
            # Validate step connections
            self._validate_step_connections(step, workflow, result)
    
    def _validate_step_basics(self, step: WorkflowStep, result: ValidationResult):
        """Validate basic step properties"""
        
        if not step.name or len(step.name.strip()) == 0:
            result.errors.append(ValidationError(
                step_id=step.id,
                error_type="missing_step_name",
                message=f"Step {step.id} must have a name",
                severity="error"
            ))
        
        if not step.type:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="missing_step_type",
                message=f"Step {step.name} must have a type",
                severity="error"
            ))
        
        # Validate step type
        valid_types = ["start", "end", "connector", "transform", "condition", "webhook", "delay"]
        if step.type not in valid_types:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="invalid_step_type",
                message=f"Invalid step type '{step.type}' for step {step.name}",
                severity="error"
            ))
    
    async def _validate_step_config(self, step: WorkflowStep, result: ValidationResult):
        """Validate step configuration"""
        
        if not step.config:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="missing_config",
                message=f"Step {step.name} must have configuration",
                severity="error"
            ))
            return
        
        # Validate based on step type
        if step.type == "connector":
            self._validate_connector_config(step, result)
        elif step.type == "transform":
            self._validate_transform_config(step, result)
        elif step.type == "condition":
            self._validate_condition_config(step, result)
        elif step.type == "webhook":
            self._validate_webhook_config(step, result)
        elif step.type == "delay":
            self._validate_delay_config(step, result)
        
        # Check if executor exists for step type
        executor = get_executor(step.type)
        if not executor:
            result.warnings.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="no_executor",
                message=f"No executor found for step type '{step.type}'",
                severity="warning"
            ))
    
    def _validate_connector_config(self, step: WorkflowStep, result: ValidationResult):
        """Validate connector step configuration"""
        
        config = step.config
        
        # Check required fields
        if "connector_type" not in config:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="missing_connector_type",
                message=f"Connector step {step.name} must specify connector_type",
                severity="error",
                field="connector_type"
            ))
            return
        
        connector_type = config["connector_type"]
        if connector_type not in self.valid_connector_types:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="invalid_connector_type",
                message=f"Invalid connector type '{connector_type}' for step {step.name}",
                severity="error",
                field="connector_type"
            ))
        
        # Validate specific connector types
        if connector_type == "http":
            self._validate_http_connector(step, result)
        elif connector_type == "database":
            self._validate_database_connector(step, result)
        elif connector_type == "email":
            self._validate_email_connector(step, result)
        elif connector_type == "slack":
            self._validate_slack_connector(step, result)
        elif connector_type == "salesforce":
            self._validate_salesforce_connector(step, result)
    
    def _validate_http_connector(self, step: WorkflowStep, result: ValidationResult):
        """Validate HTTP connector configuration"""
        
        config = step.config
        
        if "url" not in config:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="missing_url",
                message=f"HTTP connector {step.name} must specify URL",
                severity="error",
                field="url"
            ))
        else:
            url = config["url"]
            if not self._is_valid_url(url):
                result.errors.append(ValidationError(
                    step_id=step.id,
                    step_name=step.name,
                    error_type="invalid_url",
                    message=f"Invalid URL '{url}' in step {step.name}",
                    severity="error",
                    field="url"
                ))
        
        if "method" in config:
            method = config["method"].upper()
            valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
            if method not in valid_methods:
                result.errors.append(ValidationError(
                    step_id=step.id,
                    step_name=step.name,
                    error_type="invalid_method",
                    message=f"Invalid HTTP method '{method}' in step {step.name}",
                    severity="error",
                    field="method"
                ))
    
    def _validate_database_connector(self, step: WorkflowStep, result: ValidationResult):
        """Validate database connector configuration"""
        
        config = step.config
        
        if "connection_string" not in config:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="missing_connection_string",
                message=f"Database connector {step.name} must specify connection_string",
                severity="error",
                field="connection_string"
            ))
        
        if "query" not in config:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="missing_query",
                message=f"Database connector {step.name} must specify query",
                severity="error",
                field="query"
            ))
    
    def _validate_email_connector(self, step: WorkflowStep, result: ValidationResult):
        """Validate email connector configuration"""
        
        config = step.config
        
        required_fields = ["to", "subject", "body"]
        for field in required_fields:
            if field not in config:
                result.errors.append(ValidationError(
                    step_id=step.id,
                    step_name=step.name,
                    error_type=f"missing_{field}",
                    message=f"Email connector {step.name} must specify {field}",
                    severity="error",
                    field=field
                ))
    
    def _validate_slack_connector(self, step: WorkflowStep, result: ValidationResult):
        """Validate Slack connector configuration"""
        
        config = step.config
        
        if "channel" not in config:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="missing_channel",
                message=f"Slack connector {step.name} must specify channel",
                severity="error",
                field="channel"
            ))
        
        if "message" not in config:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="missing_message",
                message=f"Slack connector {step.name} must specify message",
                severity="error",
                field="message"
            ))
    
    def _validate_salesforce_connector(self, step: WorkflowStep, result: ValidationResult):
        """Validate Salesforce connector configuration"""
        
        config = step.config
        
        if "object" not in config:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="missing_object",
                message=f"Salesforce connector {step.name} must specify object",
                severity="error",
                field="object"
            ))
        
        if "action" not in config:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="missing_action",
                message=f"Salesforce connector {step.name} must specify action",
                severity="error",
                field="action"
            ))
    
    def _validate_transform_config(self, step: WorkflowStep, result: ValidationResult):
        """Validate transform step configuration"""
        
        config = step.config
        
        if "transform_type" not in config:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="missing_transform_type",
                message=f"Transform step {step.name} must specify transform_type",
                severity="error",
                field="transform_type"
            ))
            return
        
        transform_type = config["transform_type"]
        if transform_type not in self.valid_transform_types:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="invalid_transform_type",
                message=f"Invalid transform type '{transform_type}' for step {step.name}",
                severity="error",
                field="transform_type"
            ))
    
    def _validate_condition_config(self, step: WorkflowStep, result: ValidationResult):
        """Validate condition step configuration"""
        
        config = step.config
        
        if "condition_type" not in config:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="missing_condition_type",
                message=f"Condition step {step.name} must specify condition_type",
                severity="error",
                field="condition_type"
            ))
            return
        
        condition_type = config["condition_type"]
        if condition_type not in self.valid_condition_types:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="invalid_condition_type",
                message=f"Invalid condition type '{condition_type}' for step {step.name}",
                severity="error",
                field="condition_type"
            ))
    
    def _validate_webhook_config(self, step: WorkflowStep, result: ValidationResult):
        """Validate webhook step configuration"""
        
        config = step.config
        
        if "webhook_type" not in config:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="missing_webhook_type",
                message=f"Webhook step {step.name} must specify webhook_type",
                severity="error",
                field="webhook_type"
            ))
            return
        
        webhook_type = config["webhook_type"]
        if webhook_type not in self.valid_webhook_types:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="invalid_webhook_type",
                message=f"Invalid webhook type '{webhook_type}' for step {step.name}",
                severity="error",
                field="webhook_type"
            ))
    
    def _validate_delay_config(self, step: WorkflowStep, result: ValidationResult):
        """Validate delay step configuration"""
        
        config = step.config
        
        if "delay_type" not in config:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="missing_delay_type",
                message=f"Delay step {step.name} must specify delay_type",
                severity="error",
                field="delay_type"
            ))
            return
        
        delay_type = config["delay_type"]
        if delay_type not in self.valid_delay_types:
            result.errors.append(ValidationError(
                step_id=step.id,
                step_name=step.name,
                error_type="invalid_delay_type",
                message=f"Invalid delay type '{delay_type}' for step {step.name}",
                severity="error",
                field="delay_type"
            ))
    
    def _validate_step_connections(self, step: WorkflowStep, workflow: Workflow, result: ValidationResult):
        """Validate step connections"""
        
        step_ids = {s.id for s in workflow.steps}
        
        for connection_id in step.connections:
            if connection_id not in step_ids:
                result.errors.append(ValidationError(
                    step_id=step.id,
                    step_name=step.name,
                    error_type="invalid_connection",
                    message=f"Step {step.name} connects to non-existent step {connection_id}",
                    severity="error"
                ))
    
    def _validate_workflow_connections(self, workflow: Workflow, result: ValidationResult):
        """Validate overall workflow connections"""
        
        # Check for cycles
        if self._has_cycles(workflow):
            result.errors.append(ValidationError(
                error_type="workflow_cycle",
                message="Workflow contains cycles which may cause infinite loops",
                severity="error"
            ))
        
        # Check for unreachable steps
        unreachable = self._find_unreachable_steps(workflow)
        if unreachable:
            step_names = [step.name for step in unreachable]
            result.warnings.append(ValidationError(
                error_type="unreachable_steps",
                message=f"Unreachable steps detected: {', '.join(step_names)}",
                severity="warning"
            ))
    
    def _validate_workflow_variables(self, workflow: Workflow, result: ValidationResult):
        """Validate workflow variable usage"""
        
        # Extract all variable references
        variable_refs = set()
        for step in workflow.steps:
            if step.config:
                self._extract_variable_references(step.config, variable_refs)
        
        # Check for undefined variables (basic check)
        # This is a simplified check - in practice, you'd want more sophisticated analysis
        for var_ref in variable_refs:
            if not self._is_likely_defined_variable(var_ref, workflow):
                result.warnings.append(ValidationError(
                    error_type="undefined_variable",
                    message=f"Variable reference '{var_ref}' may be undefined",
                    severity="warning"
                ))
    
    def _validate_workflow_performance(self, workflow: Workflow, result: ValidationResult):
        """Validate workflow performance characteristics"""
        
        # Check for too many steps
        if len(workflow.steps) > 100:
            result.warnings.append(ValidationError(
                error_type="too_many_steps",
                message=f"Workflow has {len(workflow.steps)} steps, consider breaking into smaller workflows",
                severity="warning"
            ))
        
        # Check for potential performance issues
        for step in workflow.steps:
            if step.type == "delay":
                config = step.config or {}
                if config.get("delay_type") == "fixed":
                    duration = config.get("duration_seconds", 0)
                    if duration > 300:  # 5 minutes
                        result.warnings.append(ValidationError(
                            step_id=step.id,
                            step_name=step.name,
                            error_type="long_delay",
                            message=f"Step {step.name} has a long delay ({duration}s)",
                            severity="warning"
                        ))
    
    def _validate_workflow_security(self, workflow: Workflow, result: ValidationResult):
        """Validate workflow security aspects"""
        
        for step in workflow.steps:
            if step.type == "connector":
                config = step.config or {}
                if config.get("connector_type") == "http":
                    url = config.get("url", "")
                    if self._contains_sensitive_data(url):
                        result.warnings.append(ValidationError(
                            step_id=step.id,
                            step_name=step.name,
                            error_type="sensitive_url",
                            message=f"Step {step.name} URL may contain sensitive data",
                            severity="warning"
                        ))
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _has_cycles(self, workflow: Workflow) -> bool:
        """Check if workflow has cycles using DFS"""
        
        def dfs(step_id: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)
            
            step = next((s for s in workflow.steps if s.id == step_id), None)
            if not step:
                return False
            
            for neighbor_id in step.connections:
                if neighbor_id not in visited:
                    if dfs(neighbor_id, visited, rec_stack):
                        return True
                elif neighbor_id in rec_stack:
                    return True
            
            rec_stack.remove(step_id)
            return False
        
        visited = set()
        for step in workflow.steps:
            if step.id not in visited:
                if dfs(step.id, visited, set()):
                    return True
        
        return False
    
    def _find_unreachable_steps(self, workflow: Workflow) -> List[WorkflowStep]:
        """Find steps that cannot be reached from any start step"""
        
        # Find all reachable steps from start steps
        reachable = set()
        start_steps = [step for step in workflow.steps if step.type == "start"]
        
        def mark_reachable(step_id: str):
            if step_id in reachable:
                return
            reachable.add(step_id)
            
            step = next((s for s in workflow.steps if s.id == step_id), None)
            if step:
                for connection_id in step.connections:
                    mark_reachable(connection_id)
        
        for start_step in start_steps:
            mark_reachable(start_step.id)
        
        # Return unreachable steps
        return [step for step in workflow.steps if step.id not in reachable]
    
    def _extract_variable_references(self, obj: Any, refs: Set[str]):
        """Extract variable references from configuration objects"""
        
        if isinstance(obj, str):
            # Find {{variable}} patterns
            matches = re.findall(r'\{\{([^}]+)\}\}', obj)
            refs.update(matches)
        elif isinstance(obj, dict):
            for value in obj.values():
                self._extract_variable_references(value, refs)
        elif isinstance(obj, list):
            for item in obj:
                self._extract_variable_references(item, refs)
    
    def _is_likely_defined_variable(self, var_ref: str, workflow: Workflow) -> bool:
        """Check if a variable is likely to be defined"""
        
        # Common variable names that are typically defined
        common_vars = {
            "workflow_id", "workflow_name", "execution_id", "timestamp",
            "user_id", "user_email", "organization_id"
        }
        
        if var_ref in common_vars:
            return True
        
        # Check if it's an output from a previous step
        for step in workflow.steps:
            if step.config and "outputs" in step.config:
                outputs = step.config["outputs"]
                if isinstance(outputs, dict) and var_ref in outputs:
                    return True
        
        return False
    
    def _contains_sensitive_data(self, url: str) -> bool:
        """Check if URL contains potentially sensitive data"""
        
        sensitive_patterns = [
            r'password=',
            r'token=',
            r'key=',
            r'secret=',
            r'auth=',
            r'api_key='
        ]
        
        for pattern in sensitive_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        return False
