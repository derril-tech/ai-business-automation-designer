"""
Delay Step Executor

Handles execution of delay and wait steps in workflows.
Supports fixed delays, dynamic delays, and conditional waits.
"""

import asyncio
import json
from typing import Any, Dict, Optional, Union
from datetime import datetime, timezone, timedelta

import structlog
from pydantic import BaseModel

from app.core.execution_engine import StepExecutor, WorkflowStep, ExecutionContext

logger = structlog.get_logger(__name__)


class DelayConfig(BaseModel):
    """Configuration for delay steps"""
    delay_type: str = "fixed"  # fixed, dynamic, conditional
    duration: Optional[Union[int, float]] = None  # seconds
    until_time: Optional[str] = None  # ISO datetime string
    condition: Optional[Dict[str, Any]] = None  # For conditional delays
    max_wait_time: Optional[int] = None  # Maximum wait time in seconds
    check_interval: int = 1  # Check interval for conditional delays


class DelayExecutor(StepExecutor):
    """Executor for delay steps"""
    
    async def execute(self, step: WorkflowStep, context: ExecutionContext) -> Dict[str, Any]:
        """Execute a delay step"""
        config = DelayConfig(**step.config)
        
        logger.info(
            "Executing delay step",
            step_id=step.id,
            delay_type=config.delay_type
        )
        
        # Resolve variables in inputs
        resolved_inputs = self._resolve_variables(step.inputs, context.variables)
        
        # Execute based on delay type
        if config.delay_type == "fixed":
            result = await self._execute_fixed_delay(config, resolved_inputs)
        elif config.delay_type == "dynamic":
            result = await self._execute_dynamic_delay(config, resolved_inputs)
        elif config.delay_type == "conditional":
            result = await self._execute_conditional_delay(config, resolved_inputs)
        else:
            raise ValueError(f"Unsupported delay type: {config.delay_type}")
        
        # Add metadata
        result.update({
            "delay_type": config.delay_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    
    async def _execute_fixed_delay(self, config: DelayConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fixed delay"""
        duration = config.duration or inputs.get("duration", 1)
        
        if not isinstance(duration, (int, float)) or duration < 0:
            raise ValueError("Fixed delay requires positive numeric duration")
        
        start_time = datetime.now(timezone.utc)
        
        logger.info(f"Starting fixed delay for {duration} seconds")
        
        # Sleep for the specified duration
        await asyncio.sleep(duration)
        
        end_time = datetime.now(timezone.utc)
        actual_duration = (end_time - start_time).total_seconds()
        
        logger.info(f"Fixed delay completed after {actual_duration} seconds")
        
        return {
            "status": "success",
            "delay_type": "fixed",
            "requested_duration": duration,
            "actual_duration": actual_duration,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    
    async def _execute_dynamic_delay(self, config: DelayConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute dynamic delay (delay until specific time)"""
        until_time_str = config.until_time or inputs.get("until_time")
        
        if not until_time_str:
            raise ValueError("Dynamic delay requires until_time")
        
        try:
            # Parse the target time
            if until_time_str.endswith('Z'):
                until_time_str = until_time_str[:-1] + '+00:00'
            
            target_time = datetime.fromisoformat(until_time_str.replace('Z', '+00:00'))
            
            # Ensure timezone awareness
            if target_time.tzinfo is None:
                target_time = target_time.replace(tzinfo=timezone.utc)
            
        except ValueError as e:
            raise ValueError(f"Invalid datetime format: {until_time_str}") from e
        
        start_time = datetime.now(timezone.utc)
        
        # Calculate delay duration
        delay_duration = (target_time - start_time).total_seconds()
        
        if delay_duration <= 0:
            logger.info("Target time has already passed, no delay needed")
            return {
                "status": "success",
                "delay_type": "dynamic",
                "target_time": target_time.isoformat(),
                "actual_delay": 0,
                "start_time": start_time.isoformat(),
                "end_time": start_time.isoformat()
            }
        
        logger.info(f"Starting dynamic delay until {target_time.isoformat()} ({delay_duration} seconds)")
        
        # Sleep until target time
        await asyncio.sleep(delay_duration)
        
        end_time = datetime.now(timezone.utc)
        actual_delay = (end_time - start_time).total_seconds()
        
        logger.info(f"Dynamic delay completed after {actual_delay} seconds")
        
        return {
            "status": "success",
            "delay_type": "dynamic",
            "target_time": target_time.isoformat(),
            "requested_delay": delay_duration,
            "actual_delay": actual_delay,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    
    async def _execute_conditional_delay(self, config: DelayConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conditional delay (wait until condition is met)"""
        condition = config.condition or inputs.get("condition")
        
        if not condition:
            raise ValueError("Conditional delay requires condition")
        
        max_wait_time = config.max_wait_time or inputs.get("max_wait_time", 300)  # 5 minutes default
        check_interval = config.check_interval or inputs.get("check_interval", 1)
        
        start_time = datetime.now(timezone.utc)
        check_count = 0
        
        logger.info(f"Starting conditional delay with max wait time of {max_wait_time} seconds")
        
        while True:
            check_count += 1
            
            # Check if condition is met
            if self._evaluate_condition(condition, inputs):
                end_time = datetime.now(timezone.utc)
                total_wait_time = (end_time - start_time).total_seconds()
                
                logger.info(f"Condition met after {total_wait_time} seconds ({check_count} checks)")
                
                return {
                    "status": "success",
                    "delay_type": "conditional",
                    "condition": condition,
                    "total_wait_time": total_wait_time,
                    "check_count": check_count,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }
            
            # Check if max wait time exceeded
            elapsed_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            if elapsed_time >= max_wait_time:
                end_time = datetime.now(timezone.utc)
                total_wait_time = (end_time - start_time).total_seconds()
                
                logger.warning(f"Conditional delay timed out after {total_wait_time} seconds")
                
                return {
                    "status": "timeout",
                    "delay_type": "conditional",
                    "condition": condition,
                    "total_wait_time": total_wait_time,
                    "check_count": check_count,
                    "max_wait_time": max_wait_time,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }
            
            # Wait before next check
            await asyncio.sleep(check_interval)
    
    def _evaluate_condition(self, condition: Dict[str, Any], inputs: Dict[str, Any]) -> bool:
        """Evaluate a condition against current inputs"""
        condition_type = condition.get("type", "equals")
        field = condition.get("field")
        value = condition.get("value")
        
        if not field:
            return False
        
        # Get the current value of the field
        current_value = self._get_nested_value(inputs, field)
        
        # Evaluate based on condition type
        if condition_type == "equals":
            return current_value == value
        elif condition_type == "not_equals":
            return current_value != value
        elif condition_type == "contains":
            return value in str(current_value) if current_value else False
        elif condition_type == "not_contains":
            return value not in str(current_value) if current_value else True
        elif condition_type == "greater_than":
            return isinstance(current_value, (int, float)) and current_value > value
        elif condition_type == "less_than":
            return isinstance(current_value, (int, float)) and current_value < value
        elif condition_type == "is_empty":
            return not current_value or (isinstance(current_value, str) and not current_value.strip())
        elif condition_type == "is_not_empty":
            return bool(current_value) and (not isinstance(current_value, str) or current_value.strip())
        elif condition_type == "is_null":
            return current_value is None
        elif condition_type == "is_not_null":
            return current_value is not None
        else:
            logger.warning(f"Unknown condition type: {condition_type}")
            return False
    
    def _get_nested_value(self, data: Any, field_path: str) -> Any:
        """Get nested value using dot notation (e.g., 'user.name')"""
        if not field_path:
            return data
        
        parts = field_path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                index = int(part)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                return None
        
        return current
    
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
