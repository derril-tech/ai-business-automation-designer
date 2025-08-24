"""
Core Workflow Execution Engine

This module provides the core execution engine for running AI-designed workflows.
It handles workflow state management, step execution, error handling, and recovery.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

import structlog
from pydantic import BaseModel, Field

from app.core.config import settings
from app.executors import (
    ConnectorExecutor,
    ConditionExecutor,
    TransformExecutor,
    WebhookExecutor,
    DelayExecutor
)

logger = structlog.get_logger(__name__)


class ExecutionStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(str, Enum):
    """Individual step execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class ExecutionContext:
    """Context for workflow execution"""
    workflow_id: str
    execution_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class StepResult:
    """Result of a step execution"""
    step_id: str
    status: StepStatus
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: Optional[float] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowStep(BaseModel):
    """Represents a step in a workflow"""
    id: str = Field(..., description="Unique step identifier")
    name: str = Field(..., description="Human-readable step name")
    type: str = Field(..., description="Step type (connector, condition, transform, etc.)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Step configuration")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Step inputs")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="Expected outputs")
    dependencies: List[str] = Field(default_factory=list, description="Step dependencies")
    retry_policy: Dict[str, Any] = Field(default_factory=dict, description="Retry configuration")
    timeout: Optional[int] = Field(None, description="Step timeout in seconds")


class WorkflowExecution(BaseModel):
    """Represents a workflow execution"""
    id: str = Field(..., description="Unique execution identifier")
    workflow_id: str = Field(..., description="Workflow identifier")
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)
    steps: List[WorkflowStep] = Field(default_factory=list)
    step_results: Dict[str, StepResult] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class ExecutionEngine:
    """
    Core workflow execution engine
    
    Handles:
    - Workflow state management
    - Step execution orchestration
    - Error handling and recovery
    - Variable management
    - Execution monitoring
    """
    
    def __init__(self):
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.execution_history: Dict[str, WorkflowExecution] = {}
        self.step_executors: Dict[str, Any] = {}
        
        # Register step executors
        self._register_executors()
    
    def _register_executors(self):
        """Register all step executors"""
        self.step_executors.update({
            "connector": ConnectorExecutor(),
            "condition": ConditionExecutor(),
            "transform": TransformExecutor(),
            "webhook": WebhookExecutor(),
            "delay": DelayExecutor(),
        })
        
    async def execute_workflow(
        self, 
        workflow_id: str, 
        workflow_definition: Dict[str, Any],
        initial_variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Execute a workflow with the given definition
        
        Args:
            workflow_id: Unique workflow identifier
            workflow_definition: Workflow definition from design phase
            initial_variables: Initial variables for the execution
            
        Returns:
            Execution ID for tracking
        """
        execution_id = str(uuid.uuid4())
        
        # Create execution context
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            variables=initial_variables or {},
            metadata=workflow_definition.get("metadata", {})
        )
        
        # Parse workflow definition into steps
        steps = self._parse_workflow_definition(workflow_definition)
        execution.steps = steps
        
        # Store execution
        self.active_executions[execution_id] = execution
        
        logger.info(
            "Starting workflow execution",
            execution_id=execution_id,
            workflow_id=workflow_id,
            step_count=len(steps)
        )
        
        # Start execution asynchronously
        asyncio.create_task(self._run_execution(execution_id))
        
        return execution_id
    
    async def _run_execution(self, execution_id: str):
        """Run the workflow execution"""
        execution = self.active_executions.get(execution_id)
        if not execution:
            logger.error("Execution not found", execution_id=execution_id)
            return
        
        try:
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = datetime.now(timezone.utc)
            
            # Execute steps in dependency order
            await self._execute_steps(execution)
            
            # Mark as completed
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.now(timezone.utc)
            
            logger.info(
                "Workflow execution completed",
                execution_id=execution_id,
                duration=execution.completed_at - execution.started_at
            )
            
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now(timezone.utc)
            
            logger.error(
                "Workflow execution failed",
                execution_id=execution_id,
                error=str(e)
            )
        
        finally:
            # Move to history
            self.execution_history[execution_id] = execution
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
    
    async def _execute_steps(self, execution: WorkflowExecution):
        """Execute all steps in the workflow"""
        # Create execution context
        context = ExecutionContext(
            workflow_id=execution.workflow_id,
            execution_id=execution.id,
            variables=execution.variables,
            metadata=execution.metadata
        )
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(execution.steps)
        
        # Execute steps in topological order
        executed_steps = set()
        
        while len(executed_steps) < len(execution.steps):
            # Find steps ready to execute
            ready_steps = [
                step for step in execution.steps
                if step.id not in executed_steps and
                all(dep in executed_steps for dep in step.dependencies)
            ]
            
            if not ready_steps:
                # Check for circular dependencies
                remaining_steps = [
                    step.id for step in execution.steps
                    if step.id not in executed_steps
                ]
                raise Exception(f"Circular dependency detected in steps: {remaining_steps}")
            
            # Execute ready steps concurrently
            tasks = [
                self._execute_step(step, context, execution)
                for step in ready_steps
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for step, result in zip(ready_steps, results):
                if isinstance(result, Exception):
                    # Step failed
                    step_result = StepResult(
                        step_id=step.id,
                        status=StepStatus.FAILED,
                        error=str(result)
                    )
                    execution.step_results[step.id] = step_result
                    
                    # Check if we should continue or fail
                    if step.config.get("critical", True):
                        raise result
                else:
                    # Step completed successfully
                    executed_steps.add(step.id)
                    
                    # Update context variables
                    if result.output:
                        context.variables.update(result.output)
                        execution.variables.update(result.output)
    
    async def _execute_step(
        self, 
        step: WorkflowStep, 
        context: ExecutionContext,
        execution: WorkflowExecution
    ) -> StepResult:
        """Execute a single step"""
        start_time = datetime.now(timezone.utc)
        
        logger.info(
            "Executing step",
            execution_id=execution.id,
            step_id=step.id,
            step_name=step.name,
            step_type=step.type
        )
        
        # Create step result
        step_result = StepResult(
            step_id=step.id,
            status=StepStatus.RUNNING
        )
        execution.step_results[step.id] = step_result
        
        try:
            # Get step executor
            executor = self._get_step_executor(step.type)
            
            # Execute step
            output = await executor.execute(step, context)
            
            # Update step result
            step_result.status = StepStatus.COMPLETED
            step_result.output = output
            step_result.execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            logger.info(
                "Step completed",
                execution_id=execution.id,
                step_id=step.id,
                execution_time=step_result.execution_time
            )
            
            return step_result
            
        except Exception as e:
            step_result.status = StepStatus.FAILED
            step_result.error = str(e)
            step_result.execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            logger.error(
                "Step failed",
                execution_id=execution.id,
                step_id=step.id,
                error=str(e)
            )
            
            # Handle retries
            if step.retry_policy and step_result.retry_count < step.retry_policy.get("max_retries", 0):
                await self._retry_step(step, context, execution, step_result)
            
            raise e
    
    async def _retry_step(
        self, 
        step: WorkflowStep, 
        context: ExecutionContext,
        execution: WorkflowExecution,
        step_result: StepResult
    ):
        """Retry a failed step"""
        step_result.retry_count += 1
        step_result.status = StepStatus.RETRYING
        
        retry_delay = step.retry_policy.get("delay", 1) * step_result.retry_count
        await asyncio.sleep(retry_delay)
        
        logger.info(
            "Retrying step",
            execution_id=execution.id,
            step_id=step.id,
            retry_count=step_result.retry_count
        )
        
        # Re-execute step
        await self._execute_step(step, context, execution)
    
    def _get_step_executor(self, step_type: str):
        """Get the appropriate executor for a step type"""
        if step_type not in self.step_executors:
            # Return default executor
            return DefaultStepExecutor()
        return self.step_executors[step_type]
    
    def _parse_workflow_definition(self, definition: Dict[str, Any]) -> List[WorkflowStep]:
        """Parse workflow definition into steps"""
        steps = []
        
        for step_def in definition.get("steps", []):
            step = WorkflowStep(
                id=step_def["id"],
                name=step_def["name"],
                type=step_def["type"],
                config=step_def.get("config", {}),
                inputs=step_def.get("inputs", {}),
                outputs=step_def.get("outputs", {}),
                dependencies=step_def.get("dependencies", []),
                retry_policy=step_def.get("retry_policy", {}),
                timeout=step_def.get("timeout")
            )
            steps.append(step)
        
        return steps
    
    def _build_dependency_graph(self, steps: List[WorkflowStep]) -> Dict[str, List[str]]:
        """Build dependency graph for steps"""
        graph = {}
        for step in steps:
            graph[step.id] = step.dependencies
        return graph
    
    def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution status"""
        return self.active_executions.get(execution_id) or self.execution_history.get(execution_id)
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an active execution"""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = ExecutionStatus.CANCELLED
            execution.completed_at = datetime.now(timezone.utc)
            
            # Move to history
            self.execution_history[execution_id] = execution
            del self.active_executions[execution_id]
            
            logger.info("Execution cancelled", execution_id=execution_id)
            return True
        
        return False


class StepExecutor:
    """Base class for step executors"""
    
    async def execute(self, step: WorkflowStep, context: ExecutionContext) -> Dict[str, Any]:
        """Execute a step"""
        raise NotImplementedError


class DefaultStepExecutor(StepExecutor):
    """Default step executor for unknown step types"""
    
    async def execute(self, step: WorkflowStep, context: ExecutionContext) -> Dict[str, Any]:
        """Execute a step with default behavior"""
        logger.warning(
            "Using default executor for unknown step type",
            step_id=step.id,
            step_type=step.type
        )
        
        # Return mock output for now
        return {
            "status": "completed",
            "message": f"Step {step.name} executed with default executor",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global execution engine instance
execution_engine = ExecutionEngine()
