#!/usr/bin/env python3
"""
Development script for running the AI Business Automation Designer locally
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app.chains.design_chain import DesignChain
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)


def setup_environment():
    """Setup the development environment"""
    # Set default environment variables if not already set
    os.environ.setdefault("OPENAI_API_KEY", "your-openai-api-key")
    os.environ.setdefault("ANTHROPIC_API_KEY", "your-anthropic-api-key")
    os.environ.setdefault("CREWAI_LLM_MODEL", "gpt-4")
    os.environ.setdefault("CREWAI_VERBOSE", "true")
    os.environ.setdefault("CREWAI_MAX_ITERATIONS", "10")


def test_workflow_design():
    """Test the workflow design functionality"""
    
    # Sample workflow goals for testing
    test_goals = [
        {
            "goal": "When a high-intent lead books a demo in Calendly, qualify them in HubSpot, enrich via Clearbit, create an opp in Salesforce, notify AE in Slack, and schedule a follow-up sequence",
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
        },
        {
            "goal": "Automate customer onboarding: when a new customer signs up, create their account, send welcome email, assign customer success manager, and schedule onboarding call",
            "context": {
                "business_domain": "customer_onboarding",
                "priority": "medium",
                "expected_volume": "50-200 customers/month"
            },
            "constraints": [
                "Must be personalized based on customer type",
                "Include approval steps for enterprise customers",
                "Track onboarding progress"
            ]
        }
    ]
    
    # Initialize the design chain
    design_chain = DesignChain()
    
    for i, test_case in enumerate(test_goals, 1):
        print(f"\n{'='*60}")
        print(f"TEST CASE {i}: {test_case['goal'][:50]}...")
        print(f"{'='*60}")
        
        try:
            # Execute the workflow design
            result = design_chain.design_workflow(
                goal=test_case["goal"],
                context=test_case["context"],
                constraints=test_case["constraints"]
            )
            
            # Display results
            print(f"✅ Workflow Design Completed")
            print(f"   Workflow ID: {result['workflow']['workflow_id']}")
            print(f"   Version: {result['workflow']['version']}")
            print(f"   Estimated Steps: {result['workflow']['estimated_steps']}")
            print(f"   Confidence Score: {result['workflow']['confidence_score']:.2f}")
            print(f"   Estimated Cost: ${result['summary']['total_cost']:.2f}")
            print(f"   Reliability Score: {result['summary']['reliability_score']:.2f}")
            
            # Validate the design
            validation = design_chain.validate_design(result)
            if validation["is_valid"]:
                print(f"   ✅ Design Validation: PASSED")
            else:
                print(f"   ❌ Design Validation: FAILED")
                for issue in validation["issues"]:
                    print(f"      - {issue}")
            
            if validation["warnings"]:
                print(f"   ⚠️  Warnings:")
                for warning in validation["warnings"]:
                    print(f"      - {warning}")
            
            if validation["recommendations"]:
                print(f"   💡 Recommendations:")
                for rec in validation["recommendations"]:
                    print(f"      - {rec}")
            
        except Exception as e:
            print(f"❌ Test case {i} failed: {str(e)}")
            logger.error(f"Test case {i} failed", error=str(e))


def test_catalog_search():
    """Test the connector catalog search functionality"""
    print(f"\n{'='*60}")
    print("TESTING CONNECTOR CATALOG SEARCH")
    print(f"{'='*60}")
    
    from app.tools.catalog import CatalogTool
    
    catalog = CatalogTool()
    
    test_queries = [
        "scheduling tool for demo bookings",
        "CRM system for lead management",
        "communication platform for notifications",
        "data enrichment service"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching for: {query}")
        try:
            results = catalog.search_catalog(query)
            print(f"   Found {len(eval(results)['results'])} connectors")
        except Exception as e:
            print(f"   ❌ Search failed: {str(e)}")


def test_mapping_suggestions():
    """Test the data mapping suggestion functionality"""
    print(f"\n{'='*60}")
    print("TESTING DATA MAPPING SUGGESTIONS")
    print(f"{'='*60}")
    
    from app.tools.mapping import MappingTool
    
    mapper = MappingTool()
    
    # Sample schemas
    source_schema = {
        "calendly_invitee": {
            "name": "string",
            "email": "string",
            "event_type": "string",
            "created_at": "datetime",
            "questions_and_answers": "array"
        }
    }
    
    target_schema = {
        "hubspot_contact": {
            "firstname": "string",
            "lastname": "string",
            "email": "string",
            "lead_source": "string",
            "createdate": "datetime",
            "lifecyclestage": "string"
        }
    }
    
    try:
        suggestions = mapper.suggest_mappings(source_schema, target_schema)
        print(f"✅ Mapping suggestions generated")
        print(f"   Suggestions: {len(eval(suggestions)['suggestions'])}")
        print(f"   Overall confidence: {eval(suggestions)['confidence_scores']['overall']:.2f}")
    except Exception as e:
        print(f"❌ Mapping suggestions failed: {str(e)}")


def main():
    """Main function to run all tests"""
    print("🚀 AI Business Automation Designer - Development Test Suite")
    print("=" * 60)
    
    # Setup environment
    setup_environment()
    
    # Run tests
    test_catalog_search()
    test_mapping_suggestions()
    test_workflow_design()
    
    print(f"\n{'='*60}")
    print("✅ All tests completed!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
