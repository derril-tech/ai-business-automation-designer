"""
Transform Step Executor

Handles execution of data transformation steps.
Supports various transformation types like mapping, filtering, aggregation, etc.
"""

import asyncio
import json
import re
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timezone

import structlog
from pydantic import BaseModel

from app.core.execution_engine import StepExecutor, WorkflowStep, ExecutionContext

logger = structlog.get_logger(__name__)


class TransformConfig(BaseModel):
    """Configuration for transform steps"""
    transform_type: str  # map, filter, aggregate, format, split, join, etc.
    field_mappings: Optional[Dict[str, str]] = None
    filter_conditions: Optional[List[Dict[str, Any]]] = None
    aggregation_rules: Optional[Dict[str, str]] = None
    format_template: Optional[str] = None
    split_delimiter: Optional[str] = None
    join_delimiter: Optional[str] = " "
    custom_function: Optional[str] = None


class TransformExecutor(StepExecutor):
    """Executor for transform steps"""
    
    # Built-in transformation functions
    TRANSFORM_FUNCTIONS = {
        "uppercase": lambda x: str(x).upper() if x else "",
        "lowercase": lambda x: str(x).lower() if x else "",
        "capitalize": lambda x: str(x).capitalize() if x else "",
        "trim": lambda x: str(x).strip() if x else "",
        "length": lambda x: len(str(x)) if x else 0,
        "round": lambda x, decimals=2: round(float(x), decimals) if x else 0,
        "abs": lambda x: abs(float(x)) if x else 0,
        "sum": lambda x: sum(float(i) for i in x) if isinstance(x, (list, tuple)) else float(x) if x else 0,
        "avg": lambda x: sum(float(i) for i in x) / len(x) if isinstance(x, (list, tuple)) and x else 0,
        "min": lambda x: min(x) if isinstance(x, (list, tuple)) and x else x,
        "max": lambda x: max(x) if isinstance(x, (list, tuple)) and x else x,
        "count": lambda x: len(x) if isinstance(x, (list, tuple)) else 1,
        "unique": lambda x: list(set(x)) if isinstance(x, (list, tuple)) else [x],
        "reverse": lambda x: x[::-1] if isinstance(x, (list, tuple, str)) else x,
        "sort": lambda x: sorted(x) if isinstance(x, (list, tuple)) else x,
        "json_parse": lambda x: json.loads(x) if isinstance(x, str) else x,
        "json_stringify": lambda x: json.dumps(x) if x is not None else "",
    }
    
    async def execute(self, step: WorkflowStep, context: ExecutionContext) -> Dict[str, Any]:
        """Execute a transform step"""
        config = TransformConfig(**step.config)
        
        logger.info(
            "Executing transform step",
            step_id=step.id,
            transform_type=config.transform_type
        )
        
        # Resolve variables in inputs
        resolved_inputs = self._resolve_variables(step.inputs, context.variables)
        
        # Execute based on transform type
        if config.transform_type == "map":
            result = await self._execute_map_transform(config, resolved_inputs)
        elif config.transform_type == "filter":
            result = await self._execute_filter_transform(config, resolved_inputs)
        elif config.transform_type == "aggregate":
            result = await self._execute_aggregate_transform(config, resolved_inputs)
        elif config.transform_type == "format":
            result = await self._execute_format_transform(config, resolved_inputs)
        elif config.transform_type == "split":
            result = await self._execute_split_transform(config, resolved_inputs)
        elif config.transform_type == "join":
            result = await self._execute_join_transform(config, resolved_inputs)
        elif config.transform_type == "custom":
            result = await self._execute_custom_transform(config, resolved_inputs)
        else:
            raise ValueError(f"Unsupported transform type: {config.transform_type}")
        
        # Add metadata
        result.update({
            "transform_type": config.transform_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    
    async def _execute_map_transform(self, config: TransformConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute map transform (field mapping and transformation)"""
        if not config.field_mappings:
            raise ValueError("Map transform requires field_mappings")
        
        result = {}
        
        for source_field, target_field in config.field_mappings.items():
            # Get source value
            source_value = self._get_nested_value(inputs, source_field)
            
            # Apply transformations if specified
            if ":" in target_field:
                # Format: target_field:transform1:transform2
                parts = target_field.split(":")
                actual_target_field = parts[0]
                transformations = parts[1:]
                
                transformed_value = source_value
                for transform in transformations:
                    if transform in self.TRANSFORM_FUNCTIONS:
                        transformed_value = self.TRANSFORM_FUNCTIONS[transform](transformed_value)
                    else:
                        logger.warning(f"Unknown transformation: {transform}")
                
                result[actual_target_field] = transformed_value
            else:
                result[target_field] = source_value
        
        logger.info(
            "Map transform completed",
            input_fields=list(inputs.keys()),
            output_fields=list(result.keys())
        )
        
        return {
            "status": "success",
            "transformed_data": result,
            "input_count": len(inputs),
            "output_count": len(result)
        }
    
    async def _execute_filter_transform(self, config: TransformConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute filter transform"""
        if not config.filter_conditions:
            raise ValueError("Filter transform requires filter_conditions")
        
        # Handle both single objects and arrays
        if isinstance(inputs.get("data"), list):
            # Filter array
            data = inputs.get("data", [])
            filtered_data = []
            
            for item in data:
                if self._evaluate_filter_conditions(item, config.filter_conditions):
                    filtered_data.append(item)
            
            result_data = filtered_data
        else:
            # Filter single object
            if self._evaluate_filter_conditions(inputs, config.filter_conditions):
                result_data = inputs
            else:
                result_data = {}
        
        logger.info(
            "Filter transform completed",
            input_count=len(inputs.get("data", [])) if isinstance(inputs.get("data"), list) else 1,
            output_count=len(result_data) if isinstance(result_data, list) else (1 if result_data else 0)
        )
        
        return {
            "status": "success",
            "filtered_data": result_data,
            "filter_conditions": config.filter_conditions
        }
    
    async def _execute_aggregate_transform(self, config: TransformConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute aggregate transform"""
        if not config.aggregation_rules:
            raise ValueError("Aggregate transform requires aggregation_rules")
        
        data = inputs.get("data", [])
        if not isinstance(data, list):
            raise ValueError("Aggregate transform requires array data")
        
        result = {}
        
        for field, operation in config.aggregation_rules.items():
            values = [self._get_nested_value(item, field) for item in data]
            values = [v for v in values if v is not None]
            
            if operation in self.TRANSFORM_FUNCTIONS:
                result[field] = self.TRANSFORM_FUNCTIONS[operation](values)
            else:
                logger.warning(f"Unknown aggregation operation: {operation}")
                result[field] = values
        
        logger.info(
            "Aggregate transform completed",
            input_count=len(data),
            aggregations=list(config.aggregation_rules.keys())
        )
        
        return {
            "status": "success",
            "aggregated_data": result,
            "aggregation_rules": config.aggregation_rules
        }
    
    async def _execute_format_transform(self, config: TransformConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute format transform (string templating)"""
        if not config.format_template:
            raise ValueError("Format transform requires format_template")
        
        # Replace placeholders in template
        formatted_string = config.format_template
        
        for key, value in inputs.items():
            placeholder = f"{{{{{key}}}}}"
            formatted_string = formatted_string.replace(placeholder, str(value))
        
        logger.info("Format transform completed", template=config.format_template)
        
        return {
            "status": "success",
            "formatted_string": formatted_string,
            "template": config.format_template
        }
    
    async def _execute_split_transform(self, config: TransformConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute split transform"""
        if not config.split_delimiter:
            raise ValueError("Split transform requires split_delimiter")
        
        data = inputs.get("data", "")
        if not isinstance(data, str):
            data = str(data)
        
        split_result = data.split(config.split_delimiter)
        
        logger.info(
            "Split transform completed",
            delimiter=config.split_delimiter,
            parts_count=len(split_result)
        )
        
        return {
            "status": "success",
            "split_data": split_result,
            "delimiter": config.split_delimiter,
            "parts_count": len(split_result)
        }
    
    async def _execute_join_transform(self, config: TransformConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute join transform"""
        data = inputs.get("data", [])
        if not isinstance(data, list):
            raise ValueError("Join transform requires array data")
        
        joined_string = config.join_delimiter.join(str(item) for item in data)
        
        logger.info(
            "Join transform completed",
            delimiter=config.join_delimiter,
            items_count=len(data)
        )
        
        return {
            "status": "success",
            "joined_string": joined_string,
            "delimiter": config.join_delimiter,
            "items_count": len(data)
        }
    
    async def _execute_custom_transform(self, config: TransformConfig, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute custom transform"""
        if not config.custom_function:
            raise ValueError("Custom transform requires custom_function")
        
        # For now, we'll use a simple eval-based approach
        # In production, this should use a sandboxed execution environment
        try:
            # Create a safe execution context
            safe_globals = {
                "inputs": inputs,
                "json": json,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "len": len,
                "sum": sum,
                "min": min,
                "max": max,
                "sorted": sorted,
                "reversed": reversed,
            }
            
            result = eval(config.custom_function, safe_globals)
            
            logger.info("Custom transform completed", function=config.custom_function)
            
            return {
                "status": "success",
                "custom_result": result,
                "function": config.custom_function
            }
            
        except Exception as e:
            logger.error("Custom transform failed", function=config.custom_function, error=str(e))
            raise Exception(f"Custom transform failed: {str(e)}")
    
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
    
    def _evaluate_filter_conditions(self, item: Any, conditions: List[Dict[str, Any]]) -> bool:
        """Evaluate filter conditions against an item"""
        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator", "equals")
            value = condition.get("value")
            
            item_value = self._get_nested_value(item, field)
            
            # Simple condition evaluation
            if operator == "equals":
                if item_value != value:
                    return False
            elif operator == "not_equals":
                if item_value == value:
                    return False
            elif operator == "contains":
                if value not in str(item_value):
                    return False
            elif operator == "not_contains":
                if value in str(item_value):
                    return False
            elif operator == "greater_than":
                if not (isinstance(item_value, (int, float)) and item_value > value):
                    return False
            elif operator == "less_than":
                if not (isinstance(item_value, (int, float)) and item_value < value):
                    return False
            elif operator == "is_empty":
                if item_value and str(item_value).strip():
                    return False
            elif operator == "is_not_empty":
                if not item_value or not str(item_value).strip():
                    return False
        
        return True
    
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
