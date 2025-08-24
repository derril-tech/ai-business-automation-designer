from crewai import Agent
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.core.config import settings
from app.tools.catalog import CatalogTool
from app.tools.mapping import MappingTool


class ProcessArchitectInput(BaseModel):
    goal: str = Field(..., description="Natural language goal for the workflow")
    context: Dict[str, Any] = Field(default_factory=dict, description="Business context and constraints")
    constraints: List[str] = Field(default_factory=list, description="Technical or business constraints")


class ProcessArchitectOutput(BaseModel):
    workflow_id: str = Field(..., description="Unique identifier for the workflow")
    version: str = Field(..., description="Version of the workflow")
    bpmn_data: Dict[str, Any] = Field(..., description="BPMN-lite workflow definition")
    nodes: List[Dict[str, Any]] = Field(..., description="List of workflow nodes")
    edges: List[Dict[str, Any]] = Field(..., description="List of workflow edges")
    estimated_steps: int = Field(..., description="Estimated number of execution steps")
    confidence_score: float = Field(..., description="Confidence in the workflow design (0-1)")


class ProcessArchitect:
    """Agent responsible for drafting BPMN-lite workflows from natural language goals"""
    
    def __init__(self):
        self.agent = Agent(
            role="Process Architect",
            goal="Design efficient, scalable BPMN-lite workflows that transform business goals into executable automation pipelines",
            backstory="""You are an expert business process architect with 15+ years of experience in 
            designing enterprise automation workflows. You specialize in translating complex business 
            requirements into clear, executable BPMN-lite diagrams that optimize for reliability, 
            maintainability, and performance. You have deep knowledge of integration patterns, 
            error handling strategies, and best practices for workflow design.""",
            verbose=settings.CREWAI_VERBOSE,
            allow_delegation=False,
            tools=[CatalogTool(), MappingTool()],
            llm=settings.CREWAI_LLM_MODEL
        )
    
    def draft_workflow(self, input_data: ProcessArchitectInput) -> ProcessArchitectOutput:
        """
        Draft a BPMN-lite workflow from a natural language goal
        
        Example input:
        {
            "goal": "When a high-intent lead books a demo in Calendly, qualify them in HubSpot, 
                     enrich via Clearbit, create an opp in Salesforce, notify AE in Slack, 
                     and schedule a follow-up sequence",
            "context": {
                "business_domain": "sales_automation",
                "priority": "high",
                "expected_volume": "100-500 leads/day"
            },
            "constraints": [
                "Must handle rate limits gracefully",
                "Require human approval for high-value leads",
                "Comply with GDPR data handling"
            ]
        }
        
        Example output:
        {
            "workflow_id": "wf_lead_qualification_v1",
            "version": "1.0.0",
            "bpmn_data": {
                "nodes": [
                    {"id": "start", "type": "trigger", "name": "Calendly Demo Booking"},
                    {"id": "qualify", "type": "action", "name": "HubSpot Qualification"},
                    {"id": "enrich", "type": "action", "name": "Clearbit Enrichment"},
                    {"id": "approval", "type": "approval", "name": "High-Value Lead Approval"},
                    {"id": "create_opp", "type": "action", "name": "Salesforce Opportunity"},
                    {"id": "notify", "type": "action", "name": "Slack AE Notification"},
                    {"id": "schedule", "type": "action", "name": "Follow-up Sequence"}
                ],
                "edges": [
                    {"from": "start", "to": "qualify"},
                    {"from": "qualify", "to": "enrich"},
                    {"from": "enrich", "to": "approval"},
                    {"from": "approval", "to": "create_opp", "condition": "approved"},
                    {"from": "create_opp", "to": "notify"},
                    {"from": "notify", "to": "schedule"}
                ]
            },
            "estimated_steps": 7,
            "confidence_score": 0.85
        }
        """
        
        # TODO: Implement CrewAI task execution
        # This would involve creating a task that uses the agent to process the input
        # and return the structured output
        
        # For now, return a mock response
        return ProcessArchitectOutput(
            workflow_id="wf_mock_v1",
            version="1.0.0",
            bpmn_data={
                "nodes": [
                    {"id": "start", "type": "trigger", "name": "Start Trigger"},
                    {"id": "action1", "type": "action", "name": "First Action"},
                    {"id": "end", "type": "end", "name": "End"}
                ],
                "edges": [
                    {"from": "start", "to": "action1"},
                    {"from": "action1", "to": "end"}
                ]
            },
            nodes=[
                {"id": "start", "type": "trigger", "name": "Start Trigger"},
                {"id": "action1", "type": "action", "name": "First Action"},
                {"id": "end", "type": "end", "name": "End"}
            ],
            edges=[
                {"from": "start", "to": "action1"},
                {"from": "action1", "to": "end"}
            ],
            estimated_steps=3,
            confidence_score=0.8
        )
