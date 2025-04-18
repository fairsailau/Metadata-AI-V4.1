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
    api_url = "https://api.box.com/2.0/ai/ask"
    
    # Construct request body
    request_body = {
        "mode": "single_item_qa",
        "prompt": prompt,
        "items": [
            {
                "type": "file",
                "id": file_id
            }
        ],
        "ai_agent": {
            "type": "ai_agent_ask",
            "basic_text": {
                "model": ai_model,
                "mode": "default"
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
        
        # Extract answer from response
        if "answer" in response_data:
            answer_text = response_data["answer"]
            
            # Try to parse answer as JSON
            try:
                # Check if answer is already in JSON format
                if answer_text.strip().startswith('{') and answer_text.strip().endswith('}'):
                    metadata = json.loads(answer_text)
                else:
                    # Return as text
                    metadata = {"extracted_text": answer_text}
                
                return metadata
            except json.JSONDecodeError:
                # Return as text
                return {"extracted_text": answer_text}
        
        # If no answer in response, return empty result
        return {"error": "No answer in response"}
    
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
    
    # Construct API URL for Box AI Extract
    api_url = "https://api.box.com/2.0/ai/extract/structured"
    
    # Construct request body
    request_body = {
        "file": {
            "type": "file",
            "id": file_id
        },
        "ai_model": ai_model
    }
    
    # Add template or custom fields
    if template_id:
        request_body["template"] = {
            "type": "metadata_template",
            "id": template_id
        }
    elif custom_fields:
        request_body["fields"] = []
        for field in custom_fields:
            request_body["fields"].append({
                "name": field["name"],
                "type": field["type"]
            })
    
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
        
        # Extract metadata from response
        if "metadata" in response_data:
            metadata = response_data["metadata"]
            return metadata
        
        # If no metadata in response, return empty result
        return {"error": "No metadata in response"}
    
    except Exception as e:
        logger.error(f"Error in Box AI API call: {str(e)}")
        raise Exception(f"Error extracting metadata: {str(e)}")
