from typing import Dict, Any, List
import json


class MappingTool:
    """Tool for suggesting data field mappings and transformations"""
    
    def __init__(self):
        # Common field mapping patterns
        self.mapping_patterns = {
            "name_fields": {
                "source_patterns": ["name", "full_name", "fullname", "display_name"],
                "target_patterns": ["firstname", "lastname", "name", "display_name"],
                "transformations": ["split_name", "extract_initials", "title_case"]
            },
            "email_fields": {
                "source_patterns": ["email", "email_address", "e_mail"],
                "target_patterns": ["email", "email_address", "primary_email"],
                "transformations": ["lowercase", "validate_email", "extract_domain"]
            },
            "phone_fields": {
                "source_patterns": ["phone", "phone_number", "telephone", "mobile"],
                "target_patterns": ["phone", "phone_number", "mobile", "work_phone"],
                "transformations": ["format_phone", "validate_phone", "extract_country_code"]
            },
            "date_fields": {
                "source_patterns": ["created_at", "created_date", "date_created", "timestamp"],
                "target_patterns": ["createdate", "created_at", "date_created", "created"],
                "transformations": ["format_date", "convert_timezone", "extract_year"]
            },
            "company_fields": {
                "source_patterns": ["company", "organization", "org", "business_name"],
                "target_patterns": ["company", "organization", "account_name", "business_name"],
                "transformations": ["title_case", "remove_inc", "extract_industry"]
            }
        }
        
        # Common transformation functions
        self.transformations = {
            "split_name": {
                "description": "Split full name into first and last name",
                "config": {
                    "delimiter": " ",
                    "max_parts": 2,
                    "fallback": "first_name"
                }
            },
            "format_phone": {
                "description": "Format phone number to international standard",
                "config": {
                    "format": "E164",
                    "default_country": "US"
                }
            },
            "validate_email": {
                "description": "Validate email format and domain",
                "config": {
                    "check_mx": True,
                    "allow_disposable": False
                }
            },
            "format_date": {
                "description": "Convert date to ISO format",
                "config": {
                    "input_formats": ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"],
                    "output_format": "%Y-%m-%dT%H:%M:%SZ"
                }
            }
        }
    
    def suggest_mappings(self, source_schema: Dict[str, Any], target_schema: Dict[str, Any]) -> str:
        """
        Suggest field mappings between source and target schemas
        
        Args:
            source_schema: Source system data schema
            target_schema: Target system data schema
            
        Returns:
            JSON string with suggested mappings and transformations
        """
        suggestions = []
        
        # Extract field names from schemas
        source_fields = self._extract_fields(source_schema)
        target_fields = self._extract_fields(target_schema)
        
        for source_field in source_fields:
            for target_field in target_fields:
                mapping = self._find_mapping(source_field, target_field)
                if mapping:
                    suggestions.append(mapping)
        
        return json.dumps({
            "source_schema": source_schema,
            "target_schema": target_schema,
            "suggestions": suggestions,
            "confidence_scores": self._calculate_confidence(suggestions)
        }, indent=2)
    
    def _extract_fields(self, schema: Dict[str, Any]) -> List[str]:
        """Extract field names from a nested schema"""
        fields = []
        
        def extract_recursive(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, (dict, list)):
                        extract_recursive(value, current_path)
                    else:
                        fields.append(current_path)
            elif isinstance(obj, list) and obj:
                extract_recursive(obj[0], prefix)
        
        extract_recursive(schema)
        return fields
    
    def _find_mapping(self, source_field: str, target_field: str) -> Dict[str, Any]:
        """Find potential mapping between source and target fields"""
        source_lower = source_field.lower()
        target_lower = target_field.lower()
        
        for pattern_name, pattern_data in self.mapping_patterns.items():
            source_match = any(pattern in source_lower for pattern in pattern_data["source_patterns"])
            target_match = any(pattern in target_lower for pattern in pattern_data["target_patterns"])
            
            if source_match and target_match:
                return {
                    "source_field": source_field,
                    "target_field": target_field,
                    "pattern": pattern_name,
                    "confidence": 0.9,
                    "suggested_transformations": pattern_data["transformations"]
                }
        
        # Check for exact or partial matches
        if source_lower == target_lower:
            return {
                "source_field": source_field,
                "target_field": target_field,
                "pattern": "exact_match",
                "confidence": 1.0,
                "suggested_transformations": []
            }
        elif source_lower in target_lower or target_lower in source_lower:
            return {
                "source_field": source_field,
                "target_field": target_field,
                "pattern": "partial_match",
                "confidence": 0.7,
                "suggested_transformations": []
            }
        
        return None
    
    def _calculate_confidence(self, suggestions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate confidence scores for mapping suggestions"""
        if not suggestions:
            return {"overall": 0.0}
        
        total_confidence = sum(s.get("confidence", 0) for s in suggestions)
        avg_confidence = total_confidence / len(suggestions)
        
        return {
            "overall": avg_confidence,
            "high_confidence_mappings": len([s for s in suggestions if s.get("confidence", 0) >= 0.8]),
            "total_mappings": len(suggestions)
        }
    
    def get_transformation_details(self, transformation_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific transformation"""
        return self.transformations.get(transformation_name, {})
    
    def suggest_transformations(self, field_name: str, field_type: str) -> List[str]:
        """Suggest transformations for a specific field"""
        suggestions = []
        
        field_lower = field_name.lower()
        
        if any(pattern in field_lower for pattern in ["name", "full_name"]):
            suggestions.extend(["split_name", "title_case", "extract_initials"])
        elif any(pattern in field_lower for pattern in ["email", "e_mail"]):
            suggestions.extend(["lowercase", "validate_email", "extract_domain"])
        elif any(pattern in field_lower for pattern in ["phone", "telephone"]):
            suggestions.extend(["format_phone", "validate_phone"])
        elif any(pattern in field_lower for pattern in ["date", "created", "updated"]):
            suggestions.extend(["format_date", "convert_timezone"])
        
        return suggestions
