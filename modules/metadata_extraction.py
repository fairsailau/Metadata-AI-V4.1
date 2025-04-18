import streamlit as st
import logging
import json
import requests
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_metadata_freeform(client, file_id, prompt=None, ai_model="azure__openai__gpt_4o_mini"):
    """
    Extract metadata from a file using Box AI freeform extraction
    
    Args:
        client: Box client
        file_id: Box file ID
        prompt: Prompt for freeform extraction
        ai_model: AI model to use for extraction
        
    Returns:
        dict: Extracted metadata
    """
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
    
    # Set default prompt if not provided
    if not prompt:
        prompt = "Extract key metadata from this document including dates, names, amounts, and other important information."
    
    # Construct API URL for Box AI Extract
    api_url = "https://api.box.com/2.0/ai/extract"
    
    # Construct request body
    request_body = {
        "items": [
            {
                "id": file_id,
                "type": "file"
            }
        ],
        "prompt": prompt,
        "ai_agent": {
            "type": "ai_agent_extract",
            "long_text": {
                "model": ai_model
            },
            "basic_text": {
                "model": ai_model
            }
        }
    }
    
    try:
        # Make API call
        logger.info(f"Making Box AI API call for freeform extraction with request: {json.dumps(request_body)}")
        response = requests.post(api_url, headers=headers, json=request_body)
        
        # Check response
        if response.status_code != 200:
            logger.error(f"Box AI API error response: {response.text}")
            raise Exception(f"Error in Box AI API call: {response.status_code} {response.reason}")
        
        # Parse response
        response_data = response.json()
        
        # Return the response data
        return response_data
    
    except Exception as e:
        logger.error(f"Error in Box AI API call: {str(e)}")
        raise Exception(f"Error extracting metadata: {str(e)}")

def extract_metadata_structured(client, file_id, template_id=None, custom_fields=None, ai_model="azure__openai__gpt_4o_mini"):
    """
    Extract metadata from a file using Box AI structured extraction
    
    Args:
        client: Box client
        file_id: Box file ID
        template_id: Metadata template ID
        custom_fields: Custom fields for extraction
        ai_model: AI model to use for extraction
        
    Returns:
        dict: Extracted metadata
    """
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
    
    # Construct API URL for Box AI Extract Structured
    api_url = "https://api.box.com/2.0/ai/extract_structured"
    
    # Create AI agent configuration
    ai_agent = {
        "type": "ai_agent_extract",
        "long_text": {
            "model": ai_model
        },
        "basic_text": {
            "model": ai_model
        }
    }
    
    # Create items array with file ID
    items = [{"id": file_id, "type": "file"}]
    
    # Construct request body
    request_body = {
        "items": items,
        "ai_agent": ai_agent
    }
    
    # Add template or custom fields
    if template_id:
        # Get template details
        template = get_template_by_id(template_id)
        if template:
            # Create metadata template reference
            request_body["metadata_template"] = {
                "templateKey": template["key"],
                "scope": template_id.split("_")[0]  # Extract scope from template_id
            }
        else:
            raise ValueError(f"Template with ID {template_id} not found")
    elif custom_fields:
        # Convert custom fields to Box API format
        api_fields = []
        for field in custom_fields:
            api_field = {
                "key": field["name"],
                "display_name": field["name"],
                "type": field["type"]
            }
            
            # Add options for enum fields
            if field["type"] == "enum" and "options" in field:
                api_field["options"] = field["options"]
            
            api_fields.append(api_field)
        
        request_body["fields"] = api_fields
    else:
        raise ValueError("Either template_id or custom_fields must be provided")
    
    try:
        # Make API call
        logger.info(f"Making Box AI API call for structured extraction with request: {json.dumps(request_body)}")
        response = requests.post(api_url, headers=headers, json=request_body)
        
        # Check response
        if response.status_code != 200:
            logger.error(f"Box AI API error response: {response.text}")
            raise Exception(f"Error in Box AI API call: {response.status_code} {response.reason}")
        
        # Parse response
        response_data = response.json()
        
        # Return the response data
        return response_data
    
    except Exception as e:
        logger.error(f"Error in Box AI API call: {str(e)}")
        raise Exception(f"Error extracting metadata: {str(e)}")

def get_template_by_id(template_id):
    """
    Get template by ID from session state
    
    Args:
        template_id: Template ID
        
    Returns:
        dict: Template or None if not found
    """
    if not template_id:
        return None
    
    if not hasattr(st.session_state, "metadata_templates") or not st.session_state.metadata_templates:
        return None
    
    return st.session_state.metadata_templates.get(template_id)
