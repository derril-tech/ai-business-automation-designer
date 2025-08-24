from crewai import Task
from typing import Dict, Any
from app.agents.process_architect import ProcessArchitect, ProcessArchitectInput, ProcessArchitectOutput
from app.agents.integrator import Integrator, IntegratorInput, IntegratorOutput
from app.agents.data_mapper import DataMapper, DataMapperInput, DataMapperOutput


class DraftFlowTask:
    """Main task for orchestrating the workflow drafting process"""
    
    def __init__(self):
        self.process_architect = ProcessArchitect()
        self.integrator = Integrator()
        self.data_mapper = DataMapper()
    
    def create_draft_flow_task(self, goal: str, context: Dict[str, Any] = None, constraints: list = None) -> Task:
        """
        Create the main task for drafting a workflow from a natural language goal
        
        Args:
            goal: Natural language description of the workflow goal
            context: Business context and constraints
            constraints: Technical or business constraints
            
        Returns:
            CrewAI Task for orchestrating the workflow drafting process
        """
        
        return Task(
            description=f"""
            Draft a complete workflow from the following goal: "{goal}"
            
            Context: {context or 'No specific context provided'}
            Constraints: {constraints or 'No specific constraints'}
            
            Your task is to:
            1. Analyze the goal and break it down into actionable workflow steps
            2. Design a BPMN-lite workflow with appropriate nodes and edges
            3. Identify required connectors and integrations
            4. Suggest data mappings between systems
            5. Provide cost and reliability estimates
            
            The workflow should be:
            - Executable and well-structured
            - Optimized for reliability and performance
            - Cost-effective and scalable
            - Compliant with any specified constraints
            
            Return a comprehensive workflow design with all necessary components.
            """,
            agent=self.process_architect.agent,
            expected_output="""
            A complete workflow design including:
            - Workflow ID and version
            - BPMN-lite structure with nodes and edges
            - Connector recommendations
            - Data mapping suggestions
            - Cost and reliability estimates
            - Confidence scores
            """,
            context={
                "goal": goal,
                "context": context or {},
                "constraints": constraints or []
            }
        )
    
    def create_integration_task(self, workflow_nodes: list, business_context: Dict[str, Any] = None) -> Task:
        """
        Create a task for selecting and configuring connectors
        
        Args:
            workflow_nodes: List of workflow nodes requiring connectors
            business_context: Business context for connector selection
            
        Returns:
            CrewAI Task for connector selection and configuration
        """
        
        return Task(
            description=f"""
            Select optimal connectors for the following workflow nodes:
            {workflow_nodes}
            
            Business Context: {business_context or 'No specific context provided'}
            
            Your task is to:
            1. Analyze each workflow node and identify integration requirements
            2. Search the connector catalog for suitable options
            3. Evaluate connectors based on cost, reliability, and capabilities
            4. Recommend the best connector for each node
            5. Provide configuration details for each connector
            6. Estimate total costs and reliability scores
            
            Consider:
            - API capabilities and rate limits
            - Authentication methods
            - Pricing and scalability
            - Reliability and uptime
            - Existing system connections
            
            Return detailed connector recommendations with configurations.
            """,
            agent=self.integrator.agent,
            expected_output="""
            Connector recommendations including:
            - Mapping of nodes to recommended connectors
            - Configuration details for each connector
            - Cost estimates
            - Reliability scores
            - Reasoning for each selection
            """,
            context={
                "workflow_nodes": workflow_nodes,
                "business_context": business_context or {}
            }
        )
    
    def create_mapping_task(self, source_schema: Dict[str, Any], target_schema: Dict[str, Any], business_rules: list = None) -> Task:
        """
        Create a task for data field mapping and transformation
        
        Args:
            source_schema: Source system data schema
            target_schema: Target system data schema
            business_rules: Business rules for data transformation
            
        Returns:
            CrewAI Task for data mapping and transformation
        """
        
        return Task(
            description=f"""
            Create data mappings between the following schemas:
            
            Source Schema: {source_schema}
            Target Schema: {target_schema}
            Business Rules: {business_rules or 'No specific rules provided'}
            
            Your task is to:
            1. Analyze both schemas and identify field relationships
            2. Suggest optimal field-to-field mappings
            3. Recommend data transformations where needed
            4. Define validation rules for data quality
            5. Identify idempotency keys for deduplication
            6. Ensure compliance with business rules
            
            Consider:
            - Data type compatibility
            - Field naming conventions
            - Required vs optional fields
            - Data quality requirements
            - Performance implications
            
            Return comprehensive field mappings with transformations and validations.
            """,
            agent=self.data_mapper.agent,
            expected_output="""
            Data mapping design including:
            - Field-to-field mappings
            - Data transformation rules
            - Validation rules
            - Idempotency keys
            - Confidence scores
            """,
            context={
                "source_schema": source_schema,
                "target_schema": target_schema,
                "business_rules": business_rules or []
            }
        )
    
    def execute_draft_flow(self, goal: str, context: Dict[str, Any] = None, constraints: list = None) -> Dict[str, Any]:
        """
        Execute the complete workflow drafting process
        
        Args:
            goal: Natural language description of the workflow goal
            context: Business context and constraints
            constraints: Technical or business constraints
            
        Returns:
            Complete workflow design with all components
        """
        
        # Step 1: Draft the workflow structure
        process_input = ProcessArchitectInput(
            goal=goal,
            context=context or {},
            constraints=constraints or []
        )
        workflow_design = self.process_architect.draft_workflow(process_input)
        
        # Step 2: Select connectors for the workflow nodes
        integrator_input = IntegratorInput(
            workflow_nodes=workflow_design.nodes,
            business_context=context or {},
            existing_connections=[]
        )
        connector_design = self.integrator.select_connectors(integrator_input)
        
        # Step 3: Create data mappings (if schemas are provided)
        # This would be implemented when source/target schemas are available
        
        # Combine all results
        return {
            "workflow": workflow_design.dict(),
            "connectors": connector_design.dict(),
            "mappings": {},  # Would be populated when schemas are available
            "summary": {
                "total_cost": connector_design.estimated_cost,
                "reliability_score": connector_design.reliability_score,
                "confidence_score": workflow_design.confidence_score,
                "estimated_steps": workflow_design.estimated_steps
            }
        }
