"""
Simulation Engine for Workflow Testing

Provides a safe environment to test workflows with mock data,
step-by-step execution, and comprehensive validation.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field

from app.core.config import settings
from app.models.workflow import Workflow, WorkflowStep
from app.executors import get_executor
from app.simulation.mock_data import MockDataProvider
from app.simulation.validators import WorkflowValidator

logger = structlog.get_logger(__name__)


class SimulationStep(BaseModel):
    """Represents a single step in simulation execution"""
    step_id: str
    step_type: str
    name: str
    status: str = "pending"  # pending, running, completed, failed, skipped
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    inputs: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}
    error: Optional[str] = None
    mock_data_used: Dict[str, Any] = {}


class SimulationResult(BaseModel):
    """Complete simulation execution result"""
    simulation_id: str
    workflow_id: str
    workflow_name: str
    status: str = "running"  # running, completed, failed, cancelled
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    steps: List[SimulationStep] = []
    variables: Dict[str, Any] = {}
    mock_data_config: Dict[str, Any] = {}
    validation_errors: List[str] = []
    execution_path: List[str] = []
    performance_metrics: Dict[str, Any] = {}


class SimulationConfig(BaseModel):
    """Configuration for simulation execution"""
    use_mock_data: bool = True
    mock_data_config: Dict[str, Any] = {}
    step_timeout_seconds: int = 30
    max_steps: int = 100
    enable_validation: bool = True
    enable_performance_tracking: bool = True
    stop_on_error: bool = True
    dry_run: bool = False


class SimulationEngine:
    """Main simulation engine for workflow testing"""
    
    def __init__(self):
        self.mock_provider = MockDataProvider()
        self.validator = WorkflowValidator()
        self.active_simulations: Dict[str, SimulationResult] = {}
    
    async def simulate_workflow(
        self,
        workflow: Workflow,
        config: SimulationConfig,
        initial_variables: Optional[Dict[str, Any]] = None
    ) -> SimulationResult:
        """Execute a workflow simulation"""
        
        simulation_id = str(uuid4())
        start_time = datetime.utcnow()
        
        # Initialize simulation result
        simulation = SimulationResult(
            simulation_id=simulation_id,
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            start_time=start_time,
            variables=initial_variables or {},
            mock_data_config=config.mock_data_config
        )
        
        self.active_simulations[simulation_id] = simulation
        
        try:
            logger.info(
                "Starting workflow simulation",
                simulation_id=simulation_id,
                workflow_id=workflow.id,
                workflow_name=workflow.name
            )
            
            # Validate workflow if enabled
            if config.enable_validation:
                validation_errors = await self.validator.validate_workflow(workflow)
                simulation.validation_errors = validation_errors
                
                if validation_errors and config.stop_on_error:
                    simulation.status = "failed"
                    simulation.end_time = datetime.utcnow()
                    simulation.duration_ms = int((simulation.end_time - simulation.start_time).total_seconds() * 1000)
                    return simulation
            
            # Initialize steps
            simulation.steps = [
                SimulationStep(
                    step_id=step.id,
                    step_type=step.type,
                    name=step.name,
                    inputs=step.config.get("inputs", {})
                )
                for step in workflow.steps
            ]
            
            # Execute workflow steps
            await self._execute_simulation_steps(
                workflow, simulation, config
            )
            
            # Calculate final metrics
            simulation.end_time = datetime.utcnow()
            simulation.duration_ms = int((simulation.end_time - simulation.start_time).total_seconds() * 1000)
            
            if simulation.status == "running":
                simulation.status = "completed"
            
            logger.info(
                "Workflow simulation completed",
                simulation_id=simulation_id,
                status=simulation.status,
                duration_ms=simulation.duration_ms
            )
            
        except Exception as e:
            logger.error(
                "Workflow simulation failed",
                simulation_id=simulation_id,
                error=str(e)
            )
            simulation.status = "failed"
            simulation.end_time = datetime.utcnow()
            simulation.duration_ms = int((simulation.end_time - simulation.start_time).total_seconds() * 1000)
        
        finally:
            # Clean up
            if simulation_id in self.active_simulations:
                del self.active_simulations[simulation_id]
        
        return simulation
    
    async def _execute_simulation_steps(
        self,
        workflow: Workflow,
        simulation: SimulationResult,
        config: SimulationConfig
    ):
        """Execute workflow steps in simulation mode"""
        
        step_map = {step.id: step for step in workflow.steps}
        executed_steps = set()
        
        # Find start steps
        start_steps = [step for step in workflow.steps if step.type == "start"]
        
        for start_step in start_steps:
            await self._execute_step_recursive(
                start_step, step_map, simulation, config, executed_steps
            )
    
    async def _execute_step_recursive(
        self,
        step: WorkflowStep,
        step_map: Dict[str, WorkflowStep],
        simulation: SimulationResult,
        config: SimulationConfig,
        executed_steps: set
    ):
        """Recursively execute steps following workflow connections"""
        
        if step.id in executed_steps:
            return
        
        if len(simulation.steps) >= config.max_steps:
            logger.warning("Maximum steps reached in simulation")
            return
        
        # Find simulation step
        sim_step = next(s for s in simulation.steps if s.step_id == step.id)
        if not sim_step:
            return
        
        # Mark as running
        sim_step.status = "running"
        sim_step.start_time = datetime.utcnow()
        
        try:
            # Prepare inputs with mock data if enabled
            inputs = await self._prepare_step_inputs(
                step, simulation.variables, config
            )
            sim_step.inputs = inputs
            
            # Execute step (or simulate if dry run)
            if config.dry_run:
                outputs = await self._simulate_step_execution(step, inputs)
            else:
                outputs = await self._execute_step(step, inputs, config)
            
            sim_step.outputs = outputs
            sim_step.status = "completed"
            
            # Update simulation variables
            simulation.variables.update(outputs)
            simulation.execution_path.append(step.id)
            
            # Execute next steps
            for next_step_id in step.connections:
                if next_step_id in step_map:
                    next_step = step_map[next_step_id]
                    await self._execute_step_recursive(
                        next_step, step_map, simulation, config, executed_steps
                    )
            
            executed_steps.add(step.id)
            
        except Exception as e:
            sim_step.status = "failed"
            sim_step.error = str(e)
            logger.error(
                "Step execution failed in simulation",
                step_id=step.id,
                step_name=step.name,
                error=str(e)
            )
            
            if config.stop_on_error:
                simulation.status = "failed"
                raise
        
        finally:
            sim_step.end_time = datetime.utcnow()
            if sim_step.start_time:
                sim_step.duration_ms = int((sim_step.end_time - sim_step.start_time).total_seconds() * 1000)
    
    async def _prepare_step_inputs(
        self,
        step: WorkflowStep,
        variables: Dict[str, Any],
        config: SimulationConfig
    ) -> Dict[str, Any]:
        """Prepare step inputs with variable resolution and mock data"""
        
        inputs = step.config.get("inputs", {}).copy()
        
        # Resolve variables
        resolved_inputs = {}
        for key, value in inputs.items():
            if isinstance(value, str) and "{{" in value and "}}" in value:
                # Variable resolution
                resolved_value = self._resolve_variables(value, variables)
                resolved_inputs[key] = resolved_value
            else:
                resolved_inputs[key] = value
        
        # Add mock data if enabled
        if config.use_mock_data:
            mock_data = await self.mock_provider.get_mock_data(
                step.type, step.config, config.mock_data_config
            )
            resolved_inputs.update(mock_data)
            
            # Store mock data used for reference
            sim_step = next((s for s in self.active_simulations.values() 
                          if any(ss.step_id == step.id for ss in s.steps)), None)
            if sim_step:
                step_sim = next(ss for ss in sim_step.steps if ss.step_id == step.id)
                step_sim.mock_data_used = mock_data
        
        return resolved_inputs
    
    def _resolve_variables(self, template: str, variables: Dict[str, Any]) -> Any:
        """Resolve variables in template strings"""
        try:
            # Simple variable resolution for simulation
            for var_name, var_value in variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                if placeholder in template:
                    template = template.replace(placeholder, str(var_value))
            return template
        except Exception as e:
            logger.warning(f"Variable resolution failed: {e}")
            return template
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        inputs: Dict[str, Any],
        config: SimulationConfig
    ) -> Dict[str, Any]:
        """Execute a single step with timeout"""
        
        executor = get_executor(step.type)
        if not executor:
            raise ValueError(f"No executor found for step type: {step.type}")
        
        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                executor.execute(step.config, inputs),
                timeout=config.step_timeout_seconds
            )
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Step execution timed out after {config.step_timeout_seconds} seconds")
    
    async def _simulate_step_execution(
        self,
        step: WorkflowStep,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate step execution for dry run mode"""
        
        # Simulate different outputs based on step type
        if step.type == "connector":
            return {
                "status": "success",
                "data": {"message": "Mock API response"},
                "headers": {"content-type": "application/json"},
                "status_code": 200
            }
        elif step.type == "transform":
            return {
                "transformed_data": inputs.get("data", {}),
                "transformation_count": 1
            }
        elif step.type == "condition":
            return {
                "condition_result": True,
                "branch_taken": "true"
            }
        elif step.type == "webhook":
            return {
                "webhook_sent": True,
                "response_status": 200
            }
        elif step.type == "delay":
            return {
                "delay_completed": True,
                "actual_delay_ms": 1000
            }
        else:
            return {"simulated_output": True}
    
    def get_simulation_status(self, simulation_id: str) -> Optional[SimulationResult]:
        """Get current status of a simulation"""
        return self.active_simulations.get(simulation_id)
    
    def cancel_simulation(self, simulation_id: str) -> bool:
        """Cancel an active simulation"""
        if simulation_id in self.active_simulations:
            simulation = self.active_simulations[simulation_id]
            simulation.status = "cancelled"
            simulation.end_time = datetime.utcnow()
            if simulation.start_time:
                simulation.duration_ms = int((simulation.end_time - simulation.start_time).total_seconds() * 1000)
            return True
        return False


# Global simulation engine instance
simulation_engine = SimulationEngine()
