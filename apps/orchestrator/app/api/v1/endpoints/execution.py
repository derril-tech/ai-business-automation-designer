"""
Execution API Endpoints

Handles workflow execution operations including starting, monitoring, and managing executions.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from app.core.execution_engine import execution_engine, ExecutionStatus, WorkflowExecution
from app.chains.design_chain import DesignChain

router = APIRouter()


class ExecuteWorkflowRequest(BaseModel):
    """Request model for executing a workflow"""
    workflow_id: str = Field(..., description="Workflow identifier")
    workflow_definition: Dict[str, Any] = Field(..., description="Workflow definition")
    initial_variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Initial variables")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Execution metadata")


class ExecuteWorkflowResponse(BaseModel):
    """Response model for workflow execution"""
    execution_id: str = Field(..., description="Execution identifier")
    status: str = Field(..., description="Execution status")
    message: str = Field(..., description="Response message")
    timestamp: str = Field(..., description="Response timestamp")


class ExecutionStatusResponse(BaseModel):
    """Response model for execution status"""
    execution_id: str = Field(..., description="Execution identifier")
    workflow_id: str = Field(..., description="Workflow identifier")
    status: ExecutionStatus = Field(..., description="Execution status")
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="Workflow steps")
    step_results: Dict[str, Any] = Field(default_factory=dict, description="Step execution results")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Current variables")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata")
    created_at: str = Field(..., description="Creation timestamp")
    started_at: Optional[str] = Field(None, description="Start timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")


class CancelExecutionResponse(BaseModel):
    """Response model for execution cancellation"""
    execution_id: str = Field(..., description="Execution identifier")
    cancelled: bool = Field(..., description="Whether execution was cancelled")
    message: str = Field(..., description="Response message")
    timestamp: str = Field(..., description="Response timestamp")


@router.post("/execute", response_model=ExecuteWorkflowResponse)
async def execute_workflow(request: ExecuteWorkflowRequest):
    """
    Execute a workflow with the given definition
    
    This endpoint starts a new workflow execution based on the provided definition.
    The execution runs asynchronously and can be monitored using the status endpoint.
    """
    try:
        # Start workflow execution
        execution_id = await execution_engine.execute_workflow(
            workflow_id=request.workflow_id,
            workflow_definition=request.workflow_definition,
            initial_variables=request.initial_variables
        )
        
        return ExecuteWorkflowResponse(
            execution_id=execution_id,
            status="started",
            message=f"Workflow execution started with ID: {execution_id}",
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start workflow execution: {str(e)}"
        )


@router.get("/status/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(execution_id: str):
    """
    Get the status of a workflow execution
    
    Returns detailed information about the execution including step results,
    variables, and timing information.
    """
    execution = execution_engine.get_execution_status(execution_id)
    
    if not execution:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found: {execution_id}"
        )
    
    # Convert step results to serializable format
    step_results = {}
    for step_id, result in execution.step_results.items():
        step_results[step_id] = {
            "status": result.status.value,
            "output": result.output,
            "error": result.error,
            "execution_time": result.execution_time,
            "retry_count": result.retry_count,
            "metadata": result.metadata
        }
    
    # Convert steps to serializable format
    steps = []
    for step in execution.steps:
        steps.append({
            "id": step.id,
            "name": step.name,
            "type": step.type,
            "config": step.config,
            "inputs": step.inputs,
            "outputs": step.outputs,
            "dependencies": step.dependencies,
            "retry_policy": step.retry_policy,
            "timeout": step.timeout
        })
    
    return ExecutionStatusResponse(
        execution_id=execution.id,
        workflow_id=execution.workflow_id,
        status=execution.status,
        steps=steps,
        step_results=step_results,
        variables=execution.variables,
        metadata=execution.metadata,
        created_at=execution.created_at.isoformat(),
        started_at=execution.started_at.isoformat() if execution.started_at else None,
        completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
        error=execution.error
    )


@router.post("/cancel/{execution_id}", response_model=CancelExecutionResponse)
async def cancel_execution(execution_id: str):
    """
    Cancel an active workflow execution
    
    Only active executions can be cancelled. Completed or failed executions
    cannot be cancelled.
    """
    cancelled = execution_engine.cancel_execution(execution_id)
    
    if not cancelled:
        raise HTTPException(
            status_code=404,
            detail=f"Active execution not found: {execution_id}"
        )
    
    return CancelExecutionResponse(
        execution_id=execution_id,
        cancelled=True,
        message=f"Execution {execution_id} cancelled successfully",
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/list", response_model=List[Dict[str, Any]])
async def list_executions(
    status: Optional[ExecutionStatus] = Query(None, description="Filter by execution status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of executions to return"),
    offset: int = Query(0, ge=0, description="Number of executions to skip")
):
    """
    List workflow executions
    
    Returns a list of executions with optional filtering by status.
    Results are paginated using limit and offset parameters.
    """
    # Get all executions (active + history)
    all_executions = list(execution_engine.active_executions.values()) + list(execution_engine.execution_history.values())
    
    # Filter by status if specified
    if status:
        all_executions = [e for e in all_executions if e.status == status]
    
    # Sort by creation time (newest first)
    all_executions.sort(key=lambda e: e.created_at, reverse=True)
    
    # Apply pagination
    paginated_executions = all_executions[offset:offset + limit]
    
    # Convert to response format
    executions = []
    for execution in paginated_executions:
        executions.append({
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "created_at": execution.created_at.isoformat(),
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "error": execution.error,
            "step_count": len(execution.steps),
            "completed_steps": len([r for r in execution.step_results.values() if r.status.value == "completed"]),
            "failed_steps": len([r for r in execution.step_results.values() if r.status.value == "failed"])
        })
    
    return executions


@router.post("/execute-from-design")
async def execute_from_design(
    goal: str = Query(..., description="Workflow goal description"),
    initial_variables: Optional[Dict[str, Any]] = None
):
    """
    Design and execute a workflow from a natural language goal
    
    This endpoint combines the design and execution phases:
    1. Uses CrewAI to design a workflow from the goal
    2. Immediately executes the designed workflow
    """
    try:
        # Design the workflow using CrewAI
        design_chain = DesignChain()
        design_result = await design_chain.design_workflow(goal)
        
        if not design_result or not design_result.get("workflow_definition"):
            raise HTTPException(
                status_code=400,
                detail="Failed to design workflow from goal"
            )
        
        # Generate workflow ID
        workflow_id = f"auto-generated-{datetime.utcnow().timestamp()}"
        
        # Execute the designed workflow
        execution_id = await execution_engine.execute_workflow(
            workflow_id=workflow_id,
            workflow_definition=design_result["workflow_definition"],
            initial_variables=initial_variables or {}
        )
        
        return {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "design_result": design_result,
            "status": "started",
            "message": f"Workflow designed and executed with ID: {execution_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to design and execute workflow: {str(e)}"
        )


@router.get("/metrics")
async def get_execution_metrics():
    """
    Get execution metrics and statistics
    
    Returns aggregated metrics about workflow executions including
    success rates, average execution times, and step performance.
    """
    # Get all executions
    all_executions = list(execution_engine.active_executions.values()) + list(execution_engine.execution_history.values())
    
    if not all_executions:
        return {
            "total_executions": 0,
            "active_executions": 0,
            "completed_executions": 0,
            "failed_executions": 0,
            "success_rate": 0.0,
            "average_execution_time": 0.0
        }
    
    # Calculate metrics
    total_executions = len(all_executions)
    active_executions = len(execution_engine.active_executions)
    completed_executions = len([e for e in all_executions if e.status == ExecutionStatus.COMPLETED])
    failed_executions = len([e for e in all_executions if e.status == ExecutionStatus.FAILED])
    
    # Calculate success rate
    success_rate = completed_executions / (completed_executions + failed_executions) if (completed_executions + failed_executions) > 0 else 0.0
    
    # Calculate average execution time
    execution_times = []
    for execution in all_executions:
        if execution.started_at and execution.completed_at:
            duration = (execution.completed_at - execution.started_at).total_seconds()
            execution_times.append(duration)
    
    average_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
    
    # Step type statistics
    step_types = {}
    for execution in all_executions:
        for step in execution.steps:
            step_type = step.type
            if step_type not in step_types:
                step_types[step_type] = {"total": 0, "completed": 0, "failed": 0}
            
            step_types[step_type]["total"] += 1
            
            if step.id in execution.step_results:
                result = execution.step_results[step.id]
                if result.status.value == "completed":
                    step_types[step_type]["completed"] += 1
                elif result.status.value == "failed":
                    step_types[step_type]["failed"] += 1
    
    return {
        "total_executions": total_executions,
        "active_executions": active_executions,
        "completed_executions": completed_executions,
        "failed_executions": failed_executions,
        "success_rate": round(success_rate * 100, 2),
        "average_execution_time": round(average_execution_time, 2),
        "step_types": step_types
    }
