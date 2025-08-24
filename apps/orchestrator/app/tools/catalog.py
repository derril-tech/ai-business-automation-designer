from crewai import Tool
from typing import Dict, Any, List
import json


class CatalogTool:
    """Tool for searching and retrieving connector catalog information"""
    
    def __init__(self):
        self.tool = Tool(
            name="Catalog",
            func=self.search_catalog,
            description="Search the connector catalog for available integrations, their capabilities, pricing, and configuration options"
        )
        
        # Mock catalog data - in production this would come from a database or API
        self.catalog_data = {
            "calendly": {
                "name": "Calendly",
                "type": "scheduling",
                "capabilities": ["webhooks", "api_access", "event_management"],
                "pricing": {"free": 0, "pro": 8, "teams": 12},
                "rate_limits": {"requests_per_minute": 100},
                "authentication": ["api_key", "oauth2"],
                "webhook_events": ["invitee.created", "invitee.canceled", "event_type.updated"]
            },
            "hubspot": {
                "name": "HubSpot",
                "type": "crm",
                "capabilities": ["contact_management", "deal_tracking", "email_marketing"],
                "pricing": {"starter": 45, "professional": 450, "enterprise": 1200},
                "rate_limits": {"requests_per_minute": 100},
                "authentication": ["api_key", "oauth2"],
                "api_endpoints": ["contacts", "deals", "companies", "tickets"]
            },
            "salesforce": {
                "name": "Salesforce",
                "type": "crm",
                "capabilities": ["lead_management", "opportunity_tracking", "account_management"],
                "pricing": {"essentials": 25, "professional": 75, "enterprise": 150},
                "rate_limits": {"requests_per_minute": 200},
                "authentication": ["oauth2", "jwt"],
                "api_endpoints": ["sobjects", "query", "composite"]
            },
            "slack": {
                "name": "Slack",
                "type": "communication",
                "capabilities": ["messaging", "notifications", "channel_management"],
                "pricing": {"free": 0, "pro": 7.25, "business": 12.50},
                "rate_limits": {"requests_per_minute": 50},
                "authentication": ["bot_token", "user_token"],
                "api_endpoints": ["chat.postMessage", "users.list", "channels.list"]
            },
            "clearbit": {
                "name": "Clearbit",
                "type": "data_enrichment",
                "capabilities": ["company_data", "contact_enrichment", "intent_data"],
                "pricing": {"enrichment": 0.10, "reveal": 0.25},
                "rate_limits": {"requests_per_minute": 60},
                "authentication": ["api_key"],
                "api_endpoints": ["enrichment", "discovery", "reveal"]
            }
        }
    
    def search_catalog(self, query: str) -> str:
        """
        Search the connector catalog for relevant integrations
        
        Args:
            query: Search query describing the integration need
            
        Returns:
            JSON string with matching connectors and their details
        """
        query_lower = query.lower()
        results = []
        
        for connector_id, connector_data in self.catalog_data.items():
            # Simple keyword matching - in production this would use semantic search
            if any(keyword in query_lower for keyword in [
                connector_id, 
                connector_data["name"].lower(),
                connector_data["type"]
            ]):
                results.append({
                    "connector_id": connector_id,
                    **connector_data
                })
        
        # If no specific matches, return popular connectors
        if not results:
            results = [
                {
                    "connector_id": "calendly",
                    **self.catalog_data["calendly"]
                },
                {
                    "connector_id": "hubspot", 
                    **self.catalog_data["hubspot"]
                },
                {
                    "connector_id": "salesforce",
                    **self.catalog_data["salesforce"]
                }
            ]
        
        return json.dumps({
            "query": query,
            "results": results,
            "total_count": len(results)
        }, indent=2)
    
    def get_connector_details(self, connector_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific connector"""
        return self.catalog_data.get(connector_id, {})
    
    def get_connectors_by_type(self, connector_type: str) -> List[Dict[str, Any]]:
        """Get all connectors of a specific type"""
        return [
            {"connector_id": cid, **data}
            for cid, data in self.catalog_data.items()
            if data["type"] == connector_type
        ]
