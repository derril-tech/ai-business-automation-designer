"""
Simulation API Endpoints

Provides endpoints for testing workflows with mock data and
getting detailed execution results.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.workflow import Workflow
from app.simulation.engine import (
    SimulationEngine, SimulationConfig, SimulationResult, simulation_engine
)
from app.simulation.mock_data import MockDataProvider
from app.simulation.validators import WorkflowValidator
from app.services.workflow_service import WorkflowService

router = APIRouter()
mock_provider = MockDataProvider()
workflow_validator = WorkflowValidator()


class SimulationRequest(BaseModel):
    """Request model for workflow simulation"""
    workflow_id: str
    config: Optional[SimulationConfig] = None
    initial_variables: Optional[Dict[str, Any]] = None
    mock_data_config: Optional[Dict[str, Any]] = None


class SimulationResponse(BaseModel):
    """Response model for simulation results"""
    simulation_id: str
    workflow_id: str
    workflow_name: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    duration_ms: Optional[int] = None
    step_count: int
    error_count: int
    warning_count: int
    execution_path: List[str] = []
    validation_errors: List[str] = []


class SimulationStepResponse(BaseModel):
    """Response model for simulation step details"""
    step_id: str
    step_type: str
    name: str
    status: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_ms: Optional[int] = None
    inputs: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}
    error: Optional[str] = None
    mock_data_used: Dict[str, Any] = {}


class SimulationDetailResponse(BaseModel):
    """Detailed simulation response with step information"""
    simulation_id: str
    workflow_id: str
    workflow_name: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    duration_ms: Optional[int] = None
    steps: List[SimulationStepResponse] = []
    variables: Dict[str, Any] = {}
    mock_data_config: Dict[str, Any] = {}
    validation_errors: List[str] = []
    execution_path: List[str] = []
    performance_metrics: Dict[str, Any] = {}


class ValidationRequest(BaseModel):
    """Request model for workflow validation"""
    workflow_id: str


class ValidationResponse(BaseModel):
    """Response model for validation results"""
    is_valid: bool
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    info: List[Dict[str, Any]] = []
    error_count: int
    warning_count: int
    info_count: int


class MockDataRequest(BaseModel):
    """Request model for mock data generation"""
    step_type: str
    step_config: Dict[str, Any]
    mock_config: Optional[Dict[str, Any]] = None


class MockDataResponse(BaseModel):
    """Response model for mock data"""
    mock_data: Dict[str, Any]
    scenarios: List[Dict[str, Any]] = []


@router.post("/simulate", response_model=SimulationResponse)
async def simulate_workflow(
    request: SimulationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> SimulationResponse:
    """
    Simulate a workflow execution with mock data
    
    This endpoint allows testing workflows in a safe environment with:
    - Mock data generation for different step types
    - Step-by-step execution tracking
    - Performance metrics
    - Validation checks
    """
    
    try:
        # Get workflow
        workflow_service = WorkflowService()
        workflow = await workflow_service.get_workflow(request.workflow_id, current_user.id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Prepare simulation config
        config = request.config or SimulationConfig()
        if request.mock_data_config:
            config.mock_data_config = request.mock_data_config
        
        # Start simulation
        simulation = await simulation_engine.simulate_workflow(
            workflow=workflow,
            config=config,
            initial_variables=request.initial_variables
        )
        
        # Convert to response model
        step_count = len(simulation.steps)
        error_count = len([s for s in simulation.steps if s.status == "failed"])
        warning_count = len([s for s in simulation.steps if s.status == "skipped"])
        
        return SimulationResponse(
            simulation_id=simulation.simulation_id,
            workflow_id=simulation.workflow_id,
            workflow_name=simulation.workflow_name,
            status=simulation.status,
            start_time=simulation.start_time.isoformat(),
            end_time=simulation.end_time.isoformat() if simulation.end_time else None,
            duration_ms=simulation.duration_ms,
            step_count=step_count,
            error_count=error_count,
            warning_count=warning_count,
            execution_path=simulation.execution_path,
            validation_errors=simulation.validation_errors
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.get("/simulate/{simulation_id}", response_model=SimulationDetailResponse)
async def get_simulation_result(
    simulation_id: str,
    current_user: User = Depends(get_current_user)
) -> SimulationDetailResponse:
    """
    Get detailed results of a simulation
    
    Returns comprehensive information about the simulation including:
    - Step-by-step execution details
    - Input/output data for each step
    - Performance metrics
    - Mock data used
    """
    
    # Get simulation result
    simulation = simulation_engine.get_simulation_status(simulation_id)
    
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    # Convert steps to response model
    steps = []
    for step in simulation.steps:
        steps.append(SimulationStepResponse(
            step_id=step.step_id,
            step_type=step.step_type,
            name=step.name,
            status=step.status,
            start_time=step.start_time.isoformat() if step.start_time else None,
            end_time=step.end_time.isoformat() if step.end_time else None,
            duration_ms=step.duration_ms,
            inputs=step.inputs,
            outputs=step.outputs,
            error=step.error,
            mock_data_used=step.mock_data_used
        ))
    
    return SimulationDetailResponse(
        simulation_id=simulation.simulation_id,
        workflow_id=simulation.workflow_id,
        workflow_name=simulation.workflow_name,
        status=simulation.status,
        start_time=simulation.start_time.isoformat(),
        end_time=simulation.end_time.isoformat() if simulation.end_time else None,
        duration_ms=simulation.duration_ms,
        steps=steps,
        variables=simulation.variables,
        mock_data_config=simulation.mock_data_config,
        validation_errors=simulation.validation_errors,
        execution_path=simulation.execution_path,
        performance_metrics=simulation.performance_metrics
    )


@router.post("/simulate/{simulation_id}/cancel")
async def cancel_simulation(
    simulation_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Cancel an active simulation
    
    Stops the simulation execution and returns the current state.
    """
    
    success = simulation_engine.cancel_simulation(simulation_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Simulation not found or already completed")
    
    return {"message": "Simulation cancelled successfully", "simulation_id": simulation_id}


@router.post("/validate", response_model=ValidationResponse)
async def validate_workflow(
    request: ValidationRequest,
    current_user: User = Depends(get_current_user)
) -> ValidationResponse:
    """
    Validate a workflow configuration
    
    Performs comprehensive validation including:
    - Step configuration validation
    - Connection validation
    - Variable reference validation
    - Performance and security checks
    """
    
    try:
        # Get workflow
        workflow_service = WorkflowService()
        workflow = await workflow_service.get_workflow(request.workflow_id, current_user.id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Validate workflow
        validation_errors = await workflow_validator.validate_workflow(workflow)
        
        # For now, we'll return a simplified validation result
        # In a full implementation, you'd want to return detailed validation results
        is_valid = len(validation_errors) == 0
        
        return ValidationResponse(
            is_valid=is_valid,
            errors=[{"message": error} for error in validation_errors],
            warnings=[],
            info=[],
            error_count=len(validation_errors),
            warning_count=0,
            info_count=0
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.post("/mock-data", response_model=MockDataResponse)
async def generate_mock_data(
    request: MockDataRequest,
    current_user: User = Depends(get_current_user)
) -> MockDataResponse:
    """
    Generate mock data for a specific step type and configuration
    
    Useful for testing individual steps or understanding what data
    will be available during simulation.
    """
    
    try:
        # Generate mock data
        mock_data = await mock_provider.get_mock_data(
            step_type=request.step_type,
            step_config=request.step_config,
            mock_config=request.mock_config
        )
        
        # Generate test scenarios
        scenarios = mock_provider.generate_test_scenarios(request.step_type)
        
        return MockDataResponse(
            mock_data=mock_data,
            scenarios=scenarios
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mock data generation failed: {str(e)}")


@router.get("/mock-data/templates")
async def get_mock_data_templates(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get available mock data templates
    
    Returns predefined templates for different step types that can be used
    as starting points for mock data configuration.
    """
    
    return {
        "templates": mock_provider.mock_templates,
        "step_types": {
            "connector": mock_provider.valid_connector_types,
            "transform": mock_provider.valid_transform_types,
            "condition": mock_provider.valid_condition_types,
            "webhook": mock_provider.valid_webhook_types,
            "delay": mock_provider.valid_delay_types
        }
    }


@router.get("/simulate/{workflow_id}/history")
async def get_simulation_history(
    workflow_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get simulation history for a workflow
    
    Returns a list of previous simulations for the specified workflow.
    Note: This would typically be stored in a database in a real implementation.
    """
    
    # In a real implementation, you'd query the database for simulation history
    # For now, we'll return a placeholder response
    
    return {
        "workflow_id": workflow_id,
        "simulations": [],
        "total_count": 0,
        "limit": limit,
        "offset": offset
    }


@router.post("/simulate/{workflow_id}/dry-run")
async def dry_run_workflow(
    workflow_id: str,
    initial_variables: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user)
) -> SimulationResponse:
    """
    Perform a dry run of a workflow
    
    Executes the workflow without making actual external calls,
    useful for validating the workflow structure and data flow.
    """
    
    try:
        # Get workflow
        workflow_service = WorkflowService()
        workflow = await workflow_service.get_workflow(workflow_id, current_user.id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Configure for dry run
        config = SimulationConfig(
            dry_run=True,
            use_mock_data=True,
            enable_validation=True,
            stop_on_error=False
        )
        
        # Start dry run simulation
        simulation = await simulation_engine.simulate_workflow(
            workflow=workflow,
            config=config,
            initial_variables=initial_variables
        )
        
        # Convert to response model
        step_count = len(simulation.steps)
        error_count = len([s for s in simulation.steps if s.status == "failed"])
        warning_count = len([s for s in simulation.steps if s.status == "skipped"])
        
        return SimulationResponse(
            simulation_id=simulation.simulation_id,
            workflow_id=simulation.workflow_id,
            workflow_name=simulation.workflow_name,
            status=simulation.status,
            start_time=simulation.start_time.isoformat(),
            end_time=simulation.end_time.isoformat() if simulation.end_time else None,
            duration_ms=simulation.duration_ms,
            step_count=step_count,
            error_count=error_count,
            warning_count=warning_count,
            execution_path=simulation.execution_path,
            validation_errors=simulation.validation_errors
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dry run failed: {str(e)}")


@router.get("/simulate/active")
async def get_active_simulations(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get list of active simulations
    
    Returns currently running simulations for the user.
    """
    
    # In a real implementation, you'd filter by user
    active_simulations = list(simulation_engine.active_simulations.values())
    
    return {
        "active_simulations": [
            {
                "simulation_id": sim.simulation_id,
                "workflow_id": sim.workflow_id,
                "workflow_name": sim.workflow_name,
                "status": sim.status,
                "start_time": sim.start_time.isoformat(),
                "step_count": len(sim.steps),
                "completed_steps": len([s for s in sim.steps if s.status == "completed"])
            }
            for sim in active_simulations
        ],
        "total_count": len(active_simulations)
    }
