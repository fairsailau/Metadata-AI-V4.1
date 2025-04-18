import streamlit as st
import os
import json
import requests
from boxsdk import BoxAPIException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Export these functions directly at the module level for easier importing
def extract_metadata_structured(file_id, use_template=True, template_id=None, template_scope="enterprise", custom_fields=None, ai_model="azure__openai__gpt_4o_mini"):
    """
    Extract structured metadata from a file using Box AI API
    
    Args:
        file_id (str): Box file ID
        use_template (bool): Whether to use a metadata template
        template_id (str): Metadata template ID
        template_scope (str): Metadata template scope (enterprise or global)
        custom_fields (list): List of custom fields for extraction
        ai_model (str): AI model to use for extraction
        
    Returns:
        dict: Extracted metadata
    """
    try:
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
        
        # Get client from session state
        client = st.session_state.client
        
        # Prepare request based on whether we're using template or custom fields
        if use_template and template_id:
            # Create metadata template reference
            metadata_template = {
                "templateKey": template_id,
                "scope": template_scope
            }
            
            try:
                # Try to make API call with metadata template
                result = make_direct_api_call(
                    client=client,
                    endpoint="ai/extract_structured",
                    data={
                        "items": items,
                        "metadata_template": metadata_template,
                        "ai_agent": ai_agent
                    }
                )
            except Exception as e:
                logger.error(f"Error making API call with template: {str(e)}")
                return {"error": str(e)}
        
        elif custom_fields:
            # Convert custom fields to Box API format
            api_fields = []
            for field in custom_fields:
                api_field = {
                    "key": field["key"],
                    "display_name": field["display_name"],
                    "type": field["type"]
                }
                
                # Add description and prompt if available
                if "description" in field:
                    api_field["description"] = field["description"]
                if "prompt" in field:
                    api_field["prompt"] = field["prompt"]
                
                # Add options for enum fields
                if field["type"] == "enum" and "options" in field:
                    api_field["options"] = field["options"]
                
                api_fields.append(api_field)
            
            try:
                # Make API call with fields
                result = make_direct_api_call(
                    client=client,
                    endpoint="ai/extract_structured",
                    data={
                        "items": items,
                        "fields": api_fields,
                        "ai_agent": ai_agent
                    }
                )
            except Exception as e:
                logger.error(f"Error making API call with fields: {str(e)}")
                return {"error": str(e)}
        
        else:
            raise ValueError("Either template_id or custom_fields must be provided")
        
        # Process and return results
        return result
    
    except BoxAPIException as e:
        logger.error(f"Box API Error: {str(e)}")
        return {"error": str(e)}
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"error": str(e)}

def extract_metadata_freeform(file_id, prompt, ai_model="azure__openai__gpt_4o_mini"):
    """
    Extract freeform metadata from a file using Box AI API
    
    Args:
        file_id (str): Box file ID
        prompt (str): Extraction prompt
        ai_model (str): AI model to use for extraction
        
    Returns:
        dict: Extracted metadata
    """
    try:
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
        
        # Get client from session state
        client = st.session_state.client
        
        try:
            # Make direct API call
            result = make_direct_api_call(
                client=client,
                endpoint="ai/extract",
                data={
                    "items": items,
                    "prompt": prompt,
                    "ai_agent": ai_agent
                }
            )
        except Exception as e:
            logger.error(f"Error making API call: {str(e)}")
            return {"error": str(e)}
        
        # Process and return results
        return result
    
    except BoxAPIException as e:
        logger.error(f"Box API Error: {str(e)}")
        return {"error": str(e)}
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"error": str(e)}

def apply_metadata_structured(file_id, metadata, use_template=True, template_id=None, template_scope="enterprise"):
    """
    Apply structured metadata to a file
    
    Args:
        file_id (str): Box file ID
        metadata (dict): Metadata to apply
        use_template (bool): Whether to use a metadata template
        template_id (str): Metadata template ID
        template_scope (str): Metadata template scope (enterprise or global)
        
    Returns:
        dict: Result of metadata application
    """
    try:
        # Get client from session state
        client = st.session_state.client
        
        # Get file object
        file_obj = client.file(file_id)
        
        if use_template and template_id:
            # Apply metadata using template
            metadata_obj = file_obj.metadata(template_scope, template_id)
            
            try:
                # Check if metadata already exists
                try:
                    existing_metadata = metadata_obj.get()
                    # Update existing metadata
                    result = metadata_obj.update(metadata)
                except BoxAPIException as e:
                    if e.status == 404:
                        # Create new metadata
                        result = metadata_obj.create(metadata)
                    else:
                        raise e
                
                return {
                    "success": True,
                    "metadata": result
                }
            
            except BoxAPIException as e:
                logger.error(f"Box API Error: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
        
        else:
            # Apply custom properties
            metadata_obj = file_obj.metadata("properties")
            
            try:
                # Check if metadata already exists
                try:
                    existing_metadata = metadata_obj.get()
                    # Update existing metadata
                    result = metadata_obj.update(metadata)
                except BoxAPIException as e:
                    if e.status == 404:
                        # Create new metadata
                        result = metadata_obj.create(metadata)
                    else:
                        raise e
                
                return {
                    "success": True,
                    "metadata": result
                }
            
            except BoxAPIException as e:
                logger.error(f"Box API Error: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def apply_metadata_freeform(file_id, metadata):
    """
    Apply freeform metadata to a file
    
    Args:
        file_id (str): Box file ID
        metadata (dict): Metadata to apply
        
    Returns:
        dict: Result of metadata application
    """
    try:
        # Get client from session state
        client = st.session_state.client
        
        # Get file object
        file_obj = client.file(file_id)
        
        # Apply metadata as custom properties
        metadata_obj = file_obj.metadata("properties")
        
        try:
            # Check if metadata already exists
            try:
                existing_metadata = metadata_obj.get()
                # Update existing metadata
                result = metadata_obj.update(metadata)
            except BoxAPIException as e:
                if e.status == 404:
                    # Create new metadata
                    result = metadata_obj.create(metadata)
                else:
                    raise e
            
            return {
                "success": True,
                "metadata": result
            }
        
        except BoxAPIException as e:
            logger.error(f"Box API Error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# Helper function to make direct API calls to Box API
def make_direct_api_call(client, endpoint, data):
    """
    Make a direct API call to Box API
    
    Args:
        client: Box client object
        endpoint (str): API endpoint (without base URL)
        data (dict): Request data
        
    Returns:
        dict: API response
    """
    try:
        # Get access token from client
        access_token = None
        if hasattr(client, '_oauth'):
            access_token = client._oauth.access_token
        elif hasattr(client, 'auth') and hasattr(client.auth, 'access_token'):
            access_token = client.auth.access_token
        
        if not access_token:
            raise ValueError("Could not retrieve access token from client")
        
        # Construct API URL
        api_url = f"https://api.box.com/2.0/{endpoint}"
        
        # Set headers
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Make API call
        response = requests.post(api_url, headers=headers, json=data)
        
        # Check for errors
        response.raise_for_status()
        
        # Return response as JSON
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API Request Error: {str(e)}")
        raise Exception(f"API Request Error: {str(e)}")

# Legacy function for backward compatibility
def metadata_extraction():
    """
    Legacy function for backward compatibility
    """
    st.title("Box AI Metadata Extraction")
    
    if not st.session_state.authenticated or not st.session_state.client:
        st.error("Please authenticate with Box first")
        return
    
    st.write("""
    This module implements the actual Box AI API calls for metadata extraction.
    It will be used by the processing module to extract metadata from files.
    """)
    
    # Return the extraction functions for use in other modules
    return {
        "extract_metadata_structured": extract_metadata_structured,
        "extract_metadata_freeform": extract_metadata_freeform,
        "apply_metadata_structured": apply_metadata_structured,
        "apply_metadata_freeform": apply_metadata_freeform
    }
