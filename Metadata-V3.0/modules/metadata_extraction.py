import streamlit as st
import os
import json
import requests
from boxsdk import BoxAPIException

def metadata_extraction():
    """
    Implement metadata extraction using Box AI API
    """
    st.title("Box AI Metadata Extraction")
    
    if not st.session_state.authenticated or not st.session_state.client:
        st.error("Please authenticate with Box first")
        return
    
    st.write("""
    This module implements the actual Box AI API calls for metadata extraction.
    It will be used by the processing module to extract metadata from files.
    """)
    
    # Structured metadata extraction
    def extract_structured_metadata(file_id, fields=None, metadata_template=None, ai_model="azure__openai__gpt_4o_mini"):
        """
        Extract structured metadata from a file using Box AI API
        
        Args:
            file_id (str): Box file ID
            fields (list): List of field definitions for extraction
            metadata_template (dict): Metadata template definition
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
            
            # Prepare request based on whether we're using fields or template
            if fields:
                # Convert fields to Box API format
                api_fields = []
                for field in fields:
                    api_field = {
                        "key": field["key"],
                        "display_name": field["display_name"],
                        "description": field["description"],
                        "prompt": field["prompt"],
                        "type": field["type"]
                    }
                    
                    # Add options for multiSelect fields
                    if field["type"] == "multiSelect" and field["options"]:
                        api_field["options"] = field["options"]
                    
                    api_fields.append(api_field)
                
                try:
                    # Try to make API call with fields using client.ai
                    if hasattr(client, 'ai') and hasattr(client.ai, 'create_ai_extract_structured'):
                        result = client.ai.create_ai_extract_structured(
                            items=items,
                            fields=api_fields,
                            ai_agent=ai_agent
                        )
                    else:
                        # Fallback to direct API call if client.ai is not available
                        result = make_direct_api_call(
                            client=client,
                            endpoint="ai/extract_structured",
                            data={
                                "items": items,
                                "fields": api_fields,
                                "ai_agent": ai_agent
                            }
                        )
                except AttributeError as e:
                    # Handle the specific attribute error for base_api_url
                    if "'Client' object has no attribute 'base_api_url'" in str(e):
                        result = make_direct_api_call(
                            client=client,
                            endpoint="ai/extract_structured",
                            data={
                                "items": items,
                                "fields": api_fields,
                                "ai_agent": ai_agent
                            }
                        )
                    else:
                        # Re-raise if it's a different attribute error
                        raise e
            
            elif metadata_template:
                try:
                    # Try to make API call with metadata template using client.ai
                    if hasattr(client, 'ai') and hasattr(client.ai, 'create_ai_extract_structured'):
                        result = client.ai.create_ai_extract_structured(
                            items=items,
                            metadata_template=metadata_template,
                            ai_agent=ai_agent
                        )
                    else:
                        # Fallback to direct API call if client.ai is not available
                        result = make_direct_api_call(
                            client=client,
                            endpoint="ai/extract_structured",
                            data={
                                "items": items,
                                "metadata_template": metadata_template,
                                "ai_agent": ai_agent
                            }
                        )
                except AttributeError as e:
                    # Handle the specific attribute error for base_api_url
                    if "'Client' object has no attribute 'base_api_url'" in str(e):
                        result = make_direct_api_call(
                            client=client,
                            endpoint="ai/extract_structured",
                            data={
                                "items": items,
                                "metadata_template": metadata_template,
                                "ai_agent": ai_agent
                            }
                        )
                    else:
                        # Re-raise if it's a different attribute error
                        raise e
            
            else:
                raise ValueError("Either fields or metadata_template must be provided")
            
            # Process and return results
            return result
        
        except BoxAPIException as e:
            st.error(f"Box API Error: {str(e)}")
            return {"error": str(e)}
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
            return {"error": str(e)}
    
    # Freeform metadata extraction
    def extract_freeform_metadata(file_id, prompt, ai_model="azure__openai__gpt_4o_mini"):
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
                # Try to make API call using client.ai
                if hasattr(client, 'ai') and hasattr(client.ai, 'create_ai_extract'):
                    result = client.ai.create_ai_extract(
                        items=items,
                        prompt=prompt,
                        ai_agent=ai_agent
                    )
                else:
                    # Fallback to direct API call if client.ai is not available
                    result = make_direct_api_call(
                        client=client,
                        endpoint="ai/extract",
                        data={
                            "items": items,
                            "prompt": prompt,
                            "ai_agent": ai_agent
                        }
                    )
            except AttributeError as e:
                # Handle the specific attribute error for base_api_url
                if "'Client' object has no attribute 'base_api_url'" in str(e):
                    result = make_direct_api_call(
                        client=client,
                        endpoint="ai/extract",
                        data={
                            "items": items,
                            "prompt": prompt,
                            "ai_agent": ai_agent
                        }
                    )
                else:
                    # Re-raise if it's a different attribute error
                    raise e
            
            # Process and return results
            return result
        
        except BoxAPIException as e:
            st.error(f"Box API Error: {str(e)}")
            return {"error": str(e)}
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
            return {"error": str(e)}
    
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
            st.error(f"API Request Error: {str(e)}")
            return {"error": str(e)}
    
    # Return the extraction functions for use in other modules
    return {
        "extract_structured_metadata": extract_structured_metadata,
        "extract_freeform_metadata": extract_freeform_metadata
    }
