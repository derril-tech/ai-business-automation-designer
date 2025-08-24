from crewai import Agent
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.core.config import settings
from app.tools.catalog import CatalogTool


class IntegratorInput(BaseModel):
    workflow_nodes: List[Dict[str, Any]] = Field(..., description="List of workflow nodes requiring connectors")
    business_context: Dict[str, Any] = Field(default_factory=dict, description="Business context for connector selection")
    existing_connections: List[Dict[str, Any]] = Field(default_factory=list, description="Existing system connections")


class IntegratorOutput(BaseModel):
    connector_mappings: List[Dict[str, Any]] = Field(..., description="Mapping of nodes to recommended connectors")
    connection_configs: List[Dict[str, Any]] = Field(..., description="Configuration for each connector")
    estimated_cost: float = Field(..., description="Estimated monthly cost for all connectors")
    reliability_score: float = Field(..., description="Reliability score for the connector selection (0-1)")


class Integrator:
    """Agent responsible for selecting and configuring connectors for workflow nodes"""
    
    def __init__(self):
        self.agent = Agent(
            role="Integration Specialist",
            goal="Select optimal connectors and configure them for reliable, cost-effective workflow execution",
            backstory="""You are a senior integration specialist with expertise in connecting 
            enterprise systems and SaaS platforms. You have deep knowledge of API capabilities, 
            rate limits, authentication methods, and best practices for reliable integrations. 
            You excel at balancing cost, performance, and reliability when selecting connectors.""",
            verbose=settings.CREWAI_VERBOSE,
            allow_delegation=False,
            tools=[CatalogTool()],
            llm=settings.CREWAI_LLM_MODEL
        )
    
    def select_connectors(self, input_data: IntegratorInput) -> IntegratorOutput:
        """
        Select and configure connectors for workflow nodes
        
        Example input:
        {
            "workflow_nodes": [
                {"id": "calendly_trigger", "type": "trigger", "name": "Calendly Demo Booking"},
                {"id": "hubspot_action", "type": "action", "name": "HubSpot Lead Qualification"},
                {"id": "salesforce_action", "type": "action", "name": "Salesforce Opportunity Creation"}
            ],
            "business_context": {
                "company_size": "mid-market",
                "budget_constraint": "moderate",
                "reliability_requirement": "high"
            },
            "existing_connections": [
                {"name": "HubSpot", "type": "hubspot", "status": "active"}
            ]
        }
        
        Example output:
        {
            "connector_mappings": [
                {
                    "node_id": "calendly_trigger",
                    "connector": "calendly",
                    "reason": "Native webhook support, reliable delivery",
                    "priority": "high"
                },
                {
                    "node_id": "hubspot_action",
                    "connector": "hubspot",
                    "reason": "Existing connection, cost-effective",
                    "priority": "high"
                },
                {
                    "node_id": "salesforce_action",
                    "connector": "salesforce",
                    "reason": "Enterprise-grade reliability, comprehensive API",
                    "priority": "high"
                }
            ],
            "connection_configs": [
                {
                    "connector": "calendly",
                    "config": {
                        "webhook_url": "https://api.example.com/webhooks/calendly",
                        "events": ["invitee.created"],
                        "authentication": "api_key"
                    }
                }
            ],
            "estimated_cost": 150.0,
            "reliability_score": 0.92
        }
        """
        
        # TODO: Implement CrewAI task execution
        # This would involve creating a task that uses the agent to analyze the workflow
        # and recommend optimal connectors
        
        # For now, return a mock response
        return IntegratorOutput(
            connector_mappings=[
                {
                    "node_id": "start",
                    "connector": "http_webhook",
                    "reason": "Generic webhook for testing",
                    "priority": "medium"
                }
            ],
            connection_configs=[
                {
                    "connector": "http_webhook",
                    "config": {
                        "webhook_url": "https://api.example.com/webhooks/test",
                        "events": ["data.received"],
                        "authentication": "none"
                    }
                }
            ],
            estimated_cost=50.0,
            reliability_score=0.85
        )
