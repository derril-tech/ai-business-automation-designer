from crewai import Agent
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.core.config import settings
from app.tools.mapping import MappingTool


class DataMapperInput(BaseModel):
    source_schema: Dict[str, Any] = Field(..., description="Source system data schema")
    target_schema: Dict[str, Any] = Field(..., description="Target system data schema")
    business_rules: List[str] = Field(default_factory=list, description="Business rules for data transformation")
    data_quality_requirements: Dict[str, Any] = Field(default_factory=dict, description="Data quality and validation requirements")


class DataMapperOutput(BaseModel):
    field_mappings: List[Dict[str, Any]] = Field(..., description="Field-to-field mappings with transformations")
    data_transformations: List[Dict[str, Any]] = Field(..., description="Data transformation rules")
    validation_rules: List[Dict[str, Any]] = Field(..., description="Data validation rules")
    idempotency_keys: List[str] = Field(..., description="Fields to use for idempotency")
    confidence_score: float = Field(..., description="Confidence in the mapping quality (0-1)")


class DataMapper:
    """Agent responsible for mapping data fields between systems and defining transformations"""
    
    def __init__(self):
        self.agent = Agent(
            role="Data Integration Specialist",
            goal="Create accurate, efficient data mappings and transformations that ensure data quality and consistency across systems",
            backstory="""You are a senior data integration specialist with expertise in ETL processes, 
            data modeling, and schema mapping. You have deep knowledge of data types, transformation 
            patterns, validation rules, and best practices for ensuring data quality and consistency. 
            You excel at identifying potential data issues and creating robust mapping solutions.""",
            verbose=settings.CREWAI_VERBOSE,
            allow_delegation=False,
            tools=[MappingTool()],
            llm=settings.CREWAI_LLM_MODEL
        )
    
    def create_mappings(self, input_data: DataMapperInput) -> DataMapperOutput:
        """
        Create field mappings and data transformations between source and target schemas
        
        Example input:
        {
            "source_schema": {
                "calendly_invitee": {
                    "name": "string",
                    "email": "string",
                    "event_type": "string",
                    "created_at": "datetime",
                    "questions_and_answers": "array"
                }
            },
            "target_schema": {
                "hubspot_contact": {
                    "firstname": "string",
                    "lastname": "string",
                    "email": "string",
                    "lead_source": "string",
                    "createdate": "datetime",
                    "lifecyclestage": "string"
                }
            },
            "business_rules": [
                "Split full name into first and last name",
                "Set lead source to 'Calendly Demo'",
                "Set lifecycle stage to 'lead' for demo bookings"
            ],
            "data_quality_requirements": {
                "email_validation": "required",
                "name_validation": "required",
                "deduplication": "email_based"
            }
        }
        
        Example output:
        {
            "field_mappings": [
                {
                    "source_field": "calendly_invitee.name",
                    "target_field": "hubspot_contact.firstname",
                    "transformation": "split_name.first",
                    "validation": "required"
                },
                {
                    "source_field": "calendly_invitee.name",
                    "target_field": "hubspot_contact.lastname",
                    "transformation": "split_name.last",
                    "validation": "required"
                },
                {
                    "source_field": "calendly_invitee.email",
                    "target_field": "hubspot_contact.email",
                    "transformation": "none",
                    "validation": "email_format"
                }
            ],
            "data_transformations": [
                {
                    "name": "split_name",
                    "type": "string_split",
                    "config": {
                        "delimiter": " ",
                        "max_parts": 2
                    }
                }
            ],
            "validation_rules": [
                {
                    "field": "email",
                    "rule": "email_format",
                    "message": "Invalid email format"
                }
            ],
            "idempotency_keys": ["email"],
            "confidence_score": 0.88
        }
        """
        
        # TODO: Implement CrewAI task execution
        # This would involve creating a task that uses the agent to analyze schemas
        # and create optimal field mappings
        
        # For now, return a mock response
        return DataMapperOutput(
            field_mappings=[
                {
                    "source_field": "data.name",
                    "target_field": "result.firstname",
                    "transformation": "split_name.first",
                    "validation": "required"
                }
            ],
            data_transformations=[
                {
                    "name": "split_name",
                    "type": "string_split",
                    "config": {
                        "delimiter": " ",
                        "max_parts": 2
                    }
                }
            ],
            validation_rules=[
                {
                    "field": "email",
                    "rule": "email_format",
                    "message": "Invalid email format"
                }
            ],
            idempotency_keys=["email"],
            confidence_score=0.85
        )
