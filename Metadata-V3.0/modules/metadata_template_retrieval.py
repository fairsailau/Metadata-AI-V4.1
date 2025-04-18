import streamlit as st
import logging
import requests
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def retrieve_metadata_templates(client):
    """
    Retrieve all metadata templates from Box
    
    Args:
        client: Box client object
        
    Returns:
        list: List of metadata templates
    """
    templates = []
    
    try:
        # Retrieve enterprise templates
        enterprise_templates = retrieve_templates_by_scope(client, "enterprise")
        if enterprise_templates:
            templates.extend(enterprise_templates)
            logger.info(f"Retrieved {len(enterprise_templates)} enterprise templates")
        
        # Retrieve global templates
        global_templates = retrieve_templates_by_scope(client, "global")
        if global_templates:
            templates.extend(global_templates)
            logger.info(f"Retrieved {len(global_templates)} global templates")
        
        return templates
    
    except Exception as e:
        logger.error(f"Error retrieving metadata templates: {str(e)}")
        return []

def retrieve_templates_by_scope(client, scope):
    """
    Retrieve metadata templates for a specific scope
    
    Args:
        client: Box client object
        scope: Template scope (enterprise or global)
        
    Returns:
        list: List of metadata templates for the specified scope
    """
    templates = []
    next_marker = None
    
    try:
        # Make API calls until all templates are retrieved
        while True:
            # Construct API URL
            api_url = f"https://api.box.com/2.0/metadata_templates/{scope}"
            if next_marker:
                api_url += f"?marker={next_marker}"
            
            # Get access token from client
            access_token = None
            if hasattr(client, '_oauth'):
                access_token = client._oauth.access_token
            elif hasattr(client, 'auth') and hasattr(client.auth, 'access_token'):
                access_token = client.auth.access_token
            
            if not access_token:
                raise ValueError("Could not retrieve access token from client")
            
            # Set headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Make API call
            response = requests.get(api_url, headers=headers)
            
            # Check for errors
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Add templates to list
            if 'entries' in data:
                templates.extend(data['entries'])
            
            # Check for next marker
            if 'next_marker' in data and data['next_marker']:
                next_marker = data['next_marker']
            else:
                break
        
        return templates
    
    except Exception as e:
        logger.error(f"Error retrieving {scope} templates: {str(e)}")
        return []

def get_metadata_templates(client, force_refresh=False):
    """
    Get metadata templates from cache or retrieve from Box
    
    Args:
        client: Box client object
        force_refresh: Whether to force a refresh of the cache
        
    Returns:
        list: List of metadata templates
    """
    # Check if templates are already in session state and not forcing refresh
    if not force_refresh and "template_cache" in st.session_state and st.session_state.template_cache:
        return st.session_state.template_cache
    
    # Retrieve templates from Box
    templates = retrieve_metadata_templates(client)
    
    # Store templates in session state
    st.session_state.template_cache = templates
    st.session_state.template_cache_timestamp = time.time()
    
    return templates

def get_template_by_id(template_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a metadata template by ID from the cached templates
    
    Args:
        template_id: Template ID
        
    Returns:
        dict: Metadata template or None if not found
    """
    if "template_cache" not in st.session_state or not st.session_state.template_cache:
        return None
    
    for template in st.session_state.template_cache:
        if template.get("id") == template_id:
            return template
    
    return None

def get_template_by_key(scope: str, template_key: str) -> Optional[Dict[str, Any]]:
    """
    Get a metadata template by scope and key from the cached templates
    
    Args:
        scope: Template scope (enterprise or global)
        template_key: Template key
        
    Returns:
        dict: Metadata template or None if not found
    """
    if "template_cache" not in st.session_state or not st.session_state.template_cache:
        return None
    
    for template in st.session_state.template_cache:
        if template.get("scope") == scope and template.get("templateKey") == template_key:
            return template
    
    return None

def validate_template_format(template: Dict[str, Any]) -> bool:
    """
    Validate that a template has the required fields for Box AI API
    
    Args:
        template: Metadata template
        
    Returns:
        bool: Whether the template is valid
    """
    required_fields = ["templateKey", "scope", "displayName"]
    
    for field in required_fields:
        if field not in template:
            return False
    
    return True

def match_template_to_document_type(document_type: str, templates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Match a document type to an appropriate metadata template
    
    Args:
        document_type: Document type from categorization
        templates: List of available metadata templates
        
    Returns:
        dict: Best matching template or None if no match found
    """
    # Define mapping of document types to keywords to look for in template names/descriptions
    type_to_keywords = {
        "Sales Contract": ["sales", "contract", "agreement", "deal"],
        "Invoices": ["invoice", "bill", "payment", "receipt"],
        "Tax": ["tax", "irs", "return", "1099", "w2", "w-2"],
        "Financial Report": ["financial", "report", "statement", "balance", "income"],
        "Employment Contract": ["employment", "hr", "human resources", "employee", "personnel"],
        "PII": ["personal", "pii", "identity", "confidential", "private"]
    }
    
    # If document type is "Other", return None (will use freeform)
    if document_type == "Other":
        return None
    
    # Get keywords for the document type
    keywords = type_to_keywords.get(document_type, [])
    
    # Score each template based on keyword matches
    template_scores = []
    for template in templates:
        score = 0
        template_name = template.get("displayName", "").lower()
        template_desc = template.get("description", "").lower()
        
        # Check for keywords in template name and description
        for keyword in keywords:
            if keyword.lower() in template_name:
                score += 2  # Higher weight for matches in name
            if keyword.lower() in template_desc:
                score += 1  # Lower weight for matches in description
        
        template_scores.append((template, score))
    
    # Sort templates by score (highest first)
    template_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Return the highest scoring template if score > 0, otherwise None
    if template_scores and template_scores[0][1] > 0:
        return template_scores[0][0]
    else:
        return None

def get_template_for_structured_extraction(template: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a metadata template to the format required for structured extraction
    
    Args:
        template: Metadata template
        
    Returns:
        dict: Template in the format required for structured extraction
    """
    return {
        "template_key": template.get("templateKey"),
        "scope": template.get("scope"),
        "type": "metadata_template"
    }

def initialize_template_state():
    """
    Initialize session state variables for metadata templates
    """
    if "template_cache" not in st.session_state:
        st.session_state.template_cache = []
        logger.info("Initialized template_cache in session state")
    
    if "template_cache_timestamp" not in st.session_state:
        st.session_state.template_cache_timestamp = None
        logger.info("Initialized template_cache_timestamp in session state")
    
    if "document_type_to_template" not in st.session_state:
        st.session_state.document_type_to_template = {}
        logger.info("Initialized document_type_to_template in session state")
