"""
Condition Step Executor

Handles execution of conditional steps that control workflow branching.
Supports various condition types like if/else, switch, and complex logical expressions.
"""

import asyncio
import json
import operator
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone

import structlog
from pydantic import BaseModel

from app.core.execution_engine import StepExecutor, WorkflowStep, ExecutionContext

logger = structlog.get_logger(__name__)


class ConditionConfig(BaseModel):
    """Configuration for condition steps"""
    condition_type: str = "if"  # if, switch, all, any
    operator: str = "equals"  # equals, not_equals, greater_than, less_than, contains, etc.
    value: Any = None
    field: Optional[str] = None
    conditions: Optional[List[Dict[str, Any]]] = None  # For complex conditions
    default_branch: Optional[str] = None


class ConditionExecutor(StepExecutor):
    """Executor for condition steps"""
    
    # Supported operators
    OPERATORS = {
        "equals": operator.eq,
        "not_equals": operator.ne,
        "greater_than": operator.gt,
        "greater_than_or_equal": operator.ge,
        "less_than": operator.lt,
        "less_than_or_equal": operator.le,
        "contains": lambda x, y: y in x if hasattr(x, '__contains__') else False,
        "not_contains": lambda x, y: y not in x if hasattr(x, '__contains__') else True,
        "starts_with": lambda x, y: str(x).startswith(str(y)),
        "ends_with": lambda x, y: str(x).endswith(str(y)),
        "is_empty": lambda x: not x or (isinstance(x, str) and not x.strip()),
        "is_not_empty": lambda x: bool(x) and (not isinstance(x, str) or x.strip()),
        "is_null": lambda x: x is None,
        "is_not_null": lambda x: x is not None,
        "regex_match": lambda x, y: bool(re.match(y, str(x))) if hasattr(re, 'match') else False,
    }
    
    async def execute(self, step: WorkflowStep, context: ExecutionContext) -> Dict[str, Any]:
        """Execute a condition step"""
        config = ConditionConfig(**step.config)
        
        logger.info(
            "Executing condition step",
            step_id=step.id,
            condition_type=config.condition_type,
            operator=config.operator
        )
        
        # Resolve variables in inputs
        resolved_inputs = self._resolve_variables(step.inputs, context.variables)
        
        # Execute based on condition type
        if config.condition_type == "if":
            result = await self._execute_if_condition(config, resolved_inputs)
        elif config.condition_type == "switch":
            result = await self._execute_switch_condition(config, resolved_inputs)
        elif config.condition_type == "all":
            result = await self._execute_all_condition(config, resolved_inputs)
        elif config.condition_type == "any":
            result = await self._execute_any_condition(config, resolved_inputs)
        else:
            raise ValueError(f"Unsupported condition type: {config.condition_type}")
        
        # Add metadata
        result.update({
            "condition_type": config.condition_type,
            "operator": config.operator,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    
    async def _execute_if_condition(self, config: ConditionConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute if condition"""
        # Get the value to test
        test_value = self._get_test_value(config, inputs)
        expected_value = config.value
        
        # Get the operator function
        op_func = self.OPERATORS.get(config.operator)
        if not op_func:
            raise ValueError(f"Unsupported operator: {config.operator}")
        
        # Evaluate condition
        try:
            condition_result = op_func(test_value, expected_value)
        except Exception as e:
            logger.error(
                "Condition evaluation failed",
                operator=config.operator,
                test_value=test_value,
                expected_value=expected_value,
                error=str(e)
            )
            condition_result = False
        
        logger.info(
            "If condition evaluated",
            test_value=test_value,
            expected_value=expected_value,
            operator=config.operator,
            result=condition_result
        )
        
        return {
            "status": "success",
            "condition_result": condition_result,
            "branch": "true" if condition_result else "false",
            "test_value": test_value,
            "expected_value": expected_value
        }
    
    async def _execute_switch_condition(self, config: ConditionConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute switch condition"""
        # Get the value to test
        test_value = self._get_test_value(config, inputs)
        
        # Find matching case
        matched_case = None
        matched_value = None
        
        for case in config.conditions or []:
            case_value = case.get("value")
            if test_value == case_value:
                matched_case = case
                matched_value = case_value
                break
        
        # Use default if no match
        if not matched_case and config.default_branch:
            matched_case = {"branch": config.default_branch}
        
        logger.info(
            "Switch condition evaluated",
            test_value=test_value,
            matched_value=matched_value,
            matched_case=matched_case
        )
        
        return {
            "status": "success",
            "condition_result": matched_case is not None,
            "branch": matched_case.get("branch") if matched_case else None,
            "test_value": test_value,
            "matched_value": matched_value
        }
    
    async def _execute_all_condition(self, config: ConditionConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all condition (all conditions must be true)"""
        if not config.conditions:
            raise ValueError("All condition requires conditions list")
        
        results = []
        all_true = True
        
        for condition in config.conditions:
            condition_config = ConditionConfig(**condition)
            result = await self._execute_if_condition(condition_config, inputs)
            results.append(result)
            
            if not result["condition_result"]:
                all_true = False
        
        logger.info(
            "All condition evaluated",
            total_conditions=len(config.conditions),
            passed_conditions=sum(1 for r in results if r["condition_result"]),
            all_true=all_true
        )
        
        return {
            "status": "success",
            "condition_result": all_true,
            "branch": "true" if all_true else "false",
            "results": results,
            "total_conditions": len(config.conditions),
            "passed_conditions": sum(1 for r in results if r["condition_result"])
        }
    
    async def _execute_any_condition(self, config: ConditionConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute any condition (at least one condition must be true)"""
        if not config.conditions:
            raise ValueError("Any condition requires conditions list")
        
        results = []
        any_true = False
        
        for condition in config.conditions:
            condition_config = ConditionConfig(**condition)
            result = await self._execute_if_condition(condition_config, inputs)
            results.append(result)
            
            if result["condition_result"]:
                any_true = True
        
        logger.info(
            "Any condition evaluated",
            total_conditions=len(config.conditions),
            passed_conditions=sum(1 for r in results if r["condition_result"]),
            any_true=any_true
        )
        
        return {
            "status": "success",
            "condition_result": any_true,
            "branch": "true" if any_true else "false",
            "results": results,
            "total_conditions": len(config.conditions),
            "passed_conditions": sum(1 for r in results if r["condition_result"])
        }
    
    def _get_test_value(self, config: ConditionConfig, inputs: Dict[str, Any]) -> Any:
        """Get the value to test from inputs"""
        if config.field:
            # Use specified field
            return inputs.get(config.field)
        else:
            # Use the first input value
            return next(iter(inputs.values())) if inputs else None
    
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
