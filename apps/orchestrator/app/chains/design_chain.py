from crewai import Crew
from typing import Dict, Any, List
from app.agents.process_architect import ProcessArchitect
from app.agents.integrator import Integrator
from app.agents.data_mapper import DataMapper
from app.tasks.draft_flow_task import DraftFlowTask
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)


class DesignChain:
    """Main chain for orchestrating the workflow design process"""
    
    def __init__(self):
        self.process_architect = ProcessArchitect()
        self.integrator = Integrator()
        self.data_mapper = DataMapper()
        self.draft_task = DraftFlowTask()
    
    def create_design_crew(self) -> Crew:
        """
        Create a crew for the workflow design process
        
        Returns:
            CrewAI Crew with all necessary agents and tasks
        """
        
        # Create tasks
        draft_task = self.draft_task.create_draft_flow_task(
            goal="[PLACEHOLDER] - Will be set dynamically",
            context={},
            constraints=[]
        )
        
        integration_task = self.draft_task.create_integration_task(
            workflow_nodes=[],
            business_context={}
        )
        
        mapping_task = self.draft_task.create_mapping_task(
            source_schema={},
            target_schema={},
            business_rules=[]
        )
        
        # Create crew
        crew = Crew(
            agents=[
                self.process_architect.agent,
                self.integrator.agent,
                self.data_mapper.agent
            ],
            tasks=[
                draft_task,
                integration_task,
                mapping_task
            ],
            verbose=settings.CREWAI_VERBOSE,
            max_iter=settings.CREWAI_MAX_ITERATIONS
        )
        
        return crew
    
    def design_workflow(self, goal: str, context: Dict[str, Any] = None, constraints: List[str] = None) -> Dict[str, Any]:
        """
        Design a complete workflow from a natural language goal
        
        Args:
            goal: Natural language description of the workflow goal
            context: Business context and constraints
            constraints: Technical or business constraints
            
        Returns:
            Complete workflow design with all components
        """
        
        try:
            logger.info("Starting workflow design process", goal=goal)
            
            # Execute the design process using the task-based approach
            result = self.draft_task.execute_draft_flow(goal, context, constraints)
            
            logger.info("Workflow design completed successfully", 
                       workflow_id=result["workflow"]["workflow_id"],
                       confidence_score=result["summary"]["confidence_score"])
            
            return result
            
        except Exception as e:
            logger.error("Workflow design failed", error=str(e), goal=goal)
            raise
    
    def design_workflow_with_crew(self, goal: str, context: Dict[str, Any] = None, constraints: List[str] = None) -> Dict[str, Any]:
        """
        Design a workflow using the CrewAI crew approach (alternative method)
        
        Args:
            goal: Natural language description of the workflow goal
            context: Business context and constraints
            constraints: Technical or business constraints
            
        Returns:
            Complete workflow design with all components
        """
        
        try:
            logger.info("Starting workflow design with crew", goal=goal)
            
            # Create crew with dynamic task configuration
            crew = self.create_design_crew()
            
            # Update task descriptions with actual goal
            for task in crew.tasks:
                if "PLACEHOLDER" in task.description:
                    task.description = task.description.replace("[PLACEHOLDER]", goal)
            
            # Execute the crew
            result = crew.kickoff()
            
            logger.info("Crew-based workflow design completed", result=result)
            
            # Parse and structure the result
            return self._parse_crew_result(result, goal, context, constraints)
            
        except Exception as e:
            logger.error("Crew-based workflow design failed", error=str(e), goal=goal)
            raise
    
    def _parse_crew_result(self, crew_result: str, goal: str, context: Dict[str, Any], constraints: List[str]) -> Dict[str, Any]:
        """
        Parse the result from the crew execution into a structured format
        
        Args:
            crew_result: Raw result from crew execution
            goal: Original goal
            context: Original context
            constraints: Original constraints
            
        Returns:
            Structured workflow design result
        """
        
        # TODO: Implement parsing logic for crew results
        # This would extract structured data from the crew's output
        
        return {
            "workflow": {
                "workflow_id": "wf_crew_generated",
                "version": "1.0.0",
                "bpmn_data": {
                    "nodes": [],
                    "edges": []
                },
                "nodes": [],
                "edges": [],
                "estimated_steps": 0,
                "confidence_score": 0.8
            },
            "connectors": {
                "connector_mappings": [],
                "connection_configs": [],
                "estimated_cost": 0.0,
                "reliability_score": 0.8
            },
            "mappings": {},
            "summary": {
                "total_cost": 0.0,
                "reliability_score": 0.8,
                "confidence_score": 0.8,
                "estimated_steps": 0
            },
            "crew_result": crew_result
        }
    
    def validate_design(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a workflow design for completeness and correctness
        
        Args:
            design: Workflow design to validate
            
        Returns:
            Validation results with any issues found
        """
        
        validation_result = {
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Validate workflow structure
        if not design.get("workflow", {}).get("nodes"):
            validation_result["is_valid"] = False
            validation_result["issues"].append("No workflow nodes defined")
        
        if not design.get("workflow", {}).get("edges"):
            validation_result["warnings"].append("No workflow edges defined")
        
        # Validate connectors
        if not design.get("connectors", {}).get("connector_mappings"):
            validation_result["warnings"].append("No connector mappings defined")
        
        # Validate confidence scores
        confidence_score = design.get("summary", {}).get("confidence_score", 0)
        if confidence_score < 0.7:
            validation_result["warnings"].append(f"Low confidence score: {confidence_score}")
        
        # Validate cost estimates
        total_cost = design.get("summary", {}).get("total_cost", 0)
        if total_cost > 1000:
            validation_result["recommendations"].append(f"High estimated cost: ${total_cost}")
        
        return validation_result
