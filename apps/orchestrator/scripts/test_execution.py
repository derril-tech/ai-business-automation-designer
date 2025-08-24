#!/usr/bin/env python3
"""
Test Execution Engine

This script demonstrates the core workflow execution engine functionality.
It creates sample workflows and executes them to show the system in action.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.execution_engine import execution_engine, ExecutionStatus
from app.chains.design_chain import DesignChain


async def test_simple_workflow():
    """Test a simple workflow with basic steps"""
    print("\n=== Testing Simple Workflow ===")
    
    # Create a simple workflow definition
    workflow_definition = {
        "name": "Simple Test Workflow",
        "description": "A simple workflow to test the execution engine",
        "steps": [
            {
                "id": "step1",
                "name": "HTTP Request",
                "type": "connector",
                "config": {
                    "connector_type": "http",
                    "method": "GET",
                    "endpoint": "https://httpbin.org/json"
                },
                "inputs": {},
                "outputs": {},
                "dependencies": []
            },
            {
                "id": "step2",
                "name": "Transform Data",
                "type": "transform",
                "config": {
                    "transform_type": "map",
                    "field_mappings": {
                        "body.slideshow.author": "author",
                        "body.slideshow.title": "title"
                    }
                },
                "inputs": {
                    "data": "{{step1_output}}"
                },
                "outputs": {},
                "dependencies": ["step1"]
            },
            {
                "id": "step3",
                "name": "Condition Check",
                "type": "condition",
                "config": {
                    "condition_type": "if",
                    "operator": "is_not_empty",
                    "field": "author"
                },
                "inputs": {
                    "author": "{{step2_output.author}}"
                },
                "outputs": {},
                "dependencies": ["step2"]
            }
        ]
    }
    
    # Execute the workflow
    execution_id = await execution_engine.execute_workflow(
        workflow_id="test-simple-workflow",
        workflow_definition=workflow_definition,
        initial_variables={}
    )
    
    print(f"Workflow execution started: {execution_id}")
    
    # Wait a bit for execution to complete
    await asyncio.sleep(3)
    
    # Check execution status
    execution = execution_engine.get_execution_status(execution_id)
    if execution:
        print(f"Execution status: {execution.status}")
        print(f"Steps completed: {len(execution.step_results)}")
        for step_id, result in execution.step_results.items():
            print(f"  {step_id}: {result.status} ({result.execution_time:.2f}s)")
            if result.output:
                print(f"    Output: {json.dumps(result.output, indent=2)}")


async def test_conditional_workflow():
    """Test a workflow with conditional logic"""
    print("\n=== Testing Conditional Workflow ===")
    
    workflow_definition = {
        "name": "Conditional Test Workflow",
        "description": "A workflow with conditional branching",
        "steps": [
            {
                "id": "step1",
                "name": "Generate Number",
                "type": "transform",
                "config": {
                    "transform_type": "custom",
                    "custom_function": "42"
                },
                "inputs": {},
                "outputs": {},
                "dependencies": []
            },
            {
                "id": "step2",
                "name": "Check if Even",
                "type": "condition",
                "config": {
                    "condition_type": "if",
                    "operator": "equals",
                    "value": 0,
                    "field": "remainder"
                },
                "inputs": {
                    "number": "{{step1_output}}",
                    "remainder": "{{step1_output % 2}}"
                },
                "outputs": {},
                "dependencies": ["step1"]
            },
            {
                "id": "step3",
                "name": "Even Number Action",
                "type": "transform",
                "config": {
                    "transform_type": "format",
                    "format_template": "The number {{number}} is even!"
                },
                "inputs": {
                    "number": "{{step1_output}}"
                },
                "outputs": {},
                "dependencies": ["step2"]
            }
        ]
    }
    
    # Execute the workflow
    execution_id = await execution_engine.execute_workflow(
        workflow_id="test-conditional-workflow",
        workflow_definition=workflow_definition,
        initial_variables={}
    )
    
    print(f"Conditional workflow execution started: {execution_id}")
    
    # Wait for execution to complete
    await asyncio.sleep(2)
    
    # Check execution status
    execution = execution_engine.get_execution_status(execution_id)
    if execution:
        print(f"Execution status: {execution.status}")
        for step_id, result in execution.step_results.items():
            print(f"  {step_id}: {result.status}")
            if result.output:
                print(f"    Output: {result.output}")


async def test_delay_workflow():
    """Test a workflow with delay steps"""
    print("\n=== Testing Delay Workflow ===")
    
    workflow_definition = {
        "name": "Delay Test Workflow",
        "description": "A workflow with delay steps",
        "steps": [
            {
                "id": "step1",
                "name": "Start",
                "type": "transform",
                "config": {
                    "transform_type": "format",
                    "format_template": "Workflow started at {{timestamp}}"
                },
                "inputs": {
                    "timestamp": "{{datetime.now().isoformat()}}"
                },
                "outputs": {},
                "dependencies": []
            },
            {
                "id": "step2",
                "name": "Wait 2 seconds",
                "type": "delay",
                "config": {
                    "delay_type": "fixed",
                    "duration": 2
                },
                "inputs": {},
                "outputs": {},
                "dependencies": ["step1"]
            },
            {
                "id": "step3",
                "name": "End",
                "type": "transform",
                "config": {
                    "transform_type": "format",
                    "format_template": "Workflow completed at {{timestamp}}"
                },
                "inputs": {
                    "timestamp": "{{datetime.now().isoformat()}}"
                },
                "outputs": {},
                "dependencies": ["step2"]
            }
        ]
    }
    
    # Execute the workflow
    execution_id = await execution_engine.execute_workflow(
        workflow_id="test-delay-workflow",
        workflow_definition=workflow_definition,
        initial_variables={}
    )
    
    print(f"Delay workflow execution started: {execution_id}")
    
    # Wait for execution to complete (including the 2-second delay)
    await asyncio.sleep(4)
    
    # Check execution status
    execution = execution_engine.get_execution_status(execution_id)
    if execution:
        print(f"Execution status: {execution.status}")
        for step_id, result in execution.step_results.items():
            print(f"  {step_id}: {result.status} ({result.execution_time:.2f}s)")


async def test_ai_designed_workflow():
    """Test workflow design and execution using CrewAI"""
    print("\n=== Testing AI-Designed Workflow ===")
    
    try:
        # Design a workflow using CrewAI
        design_chain = DesignChain()
        goal = "Create a workflow that fetches weather data for a city and sends a notification if it's raining"
        
        print(f"Designing workflow for goal: {goal}")
        design_result = await design_chain.design_workflow(goal)
        
        if design_result and design_result.get("workflow_definition"):
            print("Workflow designed successfully!")
            print(f"Workflow name: {design_result.get('workflow_name', 'Unknown')}")
            print(f"Number of steps: {len(design_result['workflow_definition'].get('steps', []))}")
            
            # Execute the designed workflow
            workflow_id = f"ai-designed-{datetime.now(timezone.utc).timestamp()}"
            execution_id = await execution_engine.execute_workflow(
                workflow_id=workflow_id,
                workflow_definition=design_result["workflow_definition"],
                initial_variables={"city": "New York"}
            )
            
            print(f"AI-designed workflow execution started: {execution_id}")
            
            # Wait for execution to complete
            await asyncio.sleep(5)
            
            # Check execution status
            execution = execution_engine.get_execution_status(execution_id)
            if execution:
                print(f"Execution status: {execution.status}")
                print(f"Steps completed: {len(execution.step_results)}")
        else:
            print("Failed to design workflow with CrewAI")
            
    except Exception as e:
        print(f"Error testing AI-designed workflow: {e}")


async def test_execution_metrics():
    """Test execution metrics and statistics"""
    print("\n=== Testing Execution Metrics ===")
    
    # Get all executions
    all_executions = list(execution_engine.active_executions.values()) + list(execution_engine.execution_history.values())
    
    print(f"Total executions: {len(all_executions)}")
    print(f"Active executions: {len(execution_engine.active_executions)}")
    print(f"Completed executions: {len([e for e in all_executions if e.status == ExecutionStatus.COMPLETED])}")
    print(f"Failed executions: {len([e for e in all_executions if e.status == ExecutionStatus.FAILED])}")
    
    # Calculate success rate
    completed = len([e for e in all_executions if e.status == ExecutionStatus.COMPLETED])
    failed = len([e for e in all_executions if e.status == ExecutionStatus.FAILED])
    total = completed + failed
    
    if total > 0:
        success_rate = (completed / total) * 100
        print(f"Success rate: {success_rate:.1f}%")


async def main():
    """Main test function"""
    print("🚀 Testing AI Business Automation Designer - Execution Engine")
    print("=" * 60)
    
    try:
        # Test simple workflow
        await test_simple_workflow()
        
        # Test conditional workflow
        await test_conditional_workflow()
        
        # Test delay workflow
        await test_delay_workflow()
        
        # Test AI-designed workflow
        await test_ai_designed_workflow()
        
        # Test execution metrics
        await test_execution_metrics()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Set up environment variables for testing
    os.environ.setdefault("OPENAI_API_KEY", "test-key")
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
    
    # Run the tests
    asyncio.run(main())
