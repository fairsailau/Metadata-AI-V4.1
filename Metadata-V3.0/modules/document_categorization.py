import streamlit as st
import time
import logging
import json
import pandas as pd
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def document_categorization():
    """
    Categorize documents using Box AI before metadata extraction
    """
    st.title("Document Categorization")
    
    # Check authentication and file selection
    if not st.session_state.authenticated or not st.session_state.client:
        st.error("Please authenticate with Box first")
        return
    
    if not st.session_state.selected_files:
        st.warning("No files selected. Please select files in the File Browser first.")
        if st.button("Go to File Browser"):
            st.session_state.current_page = "File Browser"
            st.rerun()
        return
    
    # Initialize document categorization state if needed
    initialize_categorization_state()
    
    # Display categorization information
    st.write(f"Ready to categorize {len(st.session_state.selected_files)} files using Box AI.")
    
    # Process files button
    col1, col2 = st.columns(2)
    
    with col1:
        start_button = st.button(
            "Start Categorization",
            disabled=st.session_state.document_categorization["processing_state"]["is_processing"],
            use_container_width=True
        )
    
    with col2:
        cancel_button = st.button(
            "Cancel Categorization",
            disabled=not st.session_state.document_categorization["processing_state"]["is_processing"],
            use_container_width=True
        )
    
    # Progress tracking
    progress_container = st.container()
    
    # Start categorization process
    if start_button:
        st.session_state.document_categorization["processing_state"]["is_processing"] = True
        st.session_state.document_categorization["total_files"] = len(st.session_state.selected_files)
        st.session_state.document_categorization["categorized_files"] = 0
        st.session_state.document_categorization["results"] = {}
        st.session_state.document_categorization["errors"] = {}
        st.session_state.document_categorization["processing_state"]["current_file_index"] = -1
        st.rerun()
    
    # Cancel categorization process
    if cancel_button:
        st.session_state.document_categorization["processing_state"]["is_processing"] = False
        st.rerun()
    
    # Process files if categorization is in progress
    if st.session_state.document_categorization["processing_state"]["is_processing"]:
        # Get next file to process
        next_file_index = st.session_state.document_categorization["processing_state"]["current_file_index"] + 1
        
        if next_file_index < len(st.session_state.selected_files):
            # Get file information
            file = st.session_state.selected_files[next_file_index]
            file_id = file["id"]
            file_name = file["name"]
            
            # Update processing state
            st.session_state.document_categorization["processing_state"]["current_file_index"] = next_file_index
            st.session_state.document_categorization["processing_state"]["current_file"] = file_name
            
            # Categorize document
            try:
                # Call Box AI to categorize document
                categorization_result = categorize_document(file_id, st.session_state.client)
                
                # Store result
                st.session_state.document_categorization["results"][file_id] = {
                    "file_name": file_name,
                    "document_type": categorization_result.get("document_type", "Other"),
                    "confidence": categorization_result.get("confidence", 0.0),
                    "reasoning": categorization_result.get("reasoning", "")
                }
                
                # Update categorized files count
                st.session_state.document_categorization["categorized_files"] += 1
                
            except Exception as e:
                # Store error
                st.session_state.document_categorization["errors"][file_id] = {
                    "file_name": file_name,
                    "error": str(e)
                }
            
            # Rerun to process next file
            time.sleep(0.1)  # Small delay to prevent UI freezing
            st.rerun()
        else:
            # All files processed
            st.session_state.document_categorization["processing_state"]["is_processing"] = False
            st.session_state.document_categorization["is_categorized"] = True
    
    # Display progress
    with progress_container:
        if st.session_state.document_categorization["processing_state"]["is_processing"]:
            # Display progress bar
            progress = st.progress(st.session_state.document_categorization["categorized_files"] / 
                                  st.session_state.document_categorization["total_files"])
            
            # Display current file
            st.write(f"Categorizing file {st.session_state.document_categorization['processing_state']['current_file_index'] + 1} " +
                    f"of {st.session_state.document_categorization['total_files']}: " +
                    f"{st.session_state.document_categorization['processing_state']['current_file']}")
        elif st.session_state.document_categorization["categorized_files"] > 0:
            # Categorization complete
            st.success(f"Categorization complete! Processed {st.session_state.document_categorization['categorized_files']} files.")
            
            # Display results
            st.subheader("Categorization Results")
            
            # Create a DataFrame for display
            results_data = []
            
            for file_id, result in st.session_state.document_categorization["results"].items():
                results_data.append({
                    "File Name": result["file_name"],
                    "Document Type": result["document_type"],
                    "Confidence": f"{result['confidence']:.2f}",
                    "Reasoning": result["reasoning"]
                })
            
            if results_data:
                results_df = pd.DataFrame(results_data)
                st.dataframe(results_df)
            
            # Display errors if any
            if st.session_state.document_categorization["errors"]:
                st.subheader("Errors")
                
                for file_id, error_data in st.session_state.document_categorization["errors"].items():
                    st.error(f"{error_data['file_name']}: {error_data['error']}")
            
            # Continue button
            if st.button("Continue to Metadata Configuration", use_container_width=True):
                st.session_state.current_page = "Metadata Configuration"
                st.rerun()

def categorize_document(file_id, client):
    """
    Use Box AI to categorize a document into predefined types
    
    Args:
        file_id (str): Box file ID
        client: Box client object
        
    Returns:
        dict: Categorization result with document type and confidence score
    """
    # Define document types
    document_types = [
        "Sales Contract", 
        "Invoices", 
        "Tax", 
        "Financial Report", 
        "Employment Contract", 
        "PII"
    ]
    
    # Create prompt for Box AI
    prompt = f"""
    Analyze this document and categorize it into exactly ONE of the following types:
    {', '.join(document_types)}, or "Other" if it doesn't match any of these types.
    
    Provide your answer in JSON format with the following structure:
    {{
        "document_type": "The determined document type",
        "confidence": "A number between 0 and 1 indicating your confidence",
        "reasoning": "Brief explanation of why you categorized it this way"
    }}
    """
    
    # Create AI agent configuration
    ai_agent = {
        "type": "ai_agent_extract",
        "long_text": {
            "model": "azure__openai__gpt_4o"  # Using a more capable model for categorization
        },
        "basic_text": {
            "model": "azure__openai__gpt_4o"
        }
    }
    
    # Create items array with file ID
    items = [{"id": file_id, "type": "file"}]
    
    try:
        # Make API call using client.ai
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
        
        # Process and return results
        if "answer" in result:
            try:
                # Try to parse the answer as JSON
                categorization = json.loads(result["answer"])
                return categorization
            except json.JSONDecodeError:
                # If parsing fails, extract document type using string matching
                answer = result["answer"]
                for doc_type in document_types + ["Other"]:
                    if doc_type in answer:
                        return {
                            "document_type": doc_type,
                            "confidence": 0.7,  # Default confidence when parsing fails
                            "reasoning": "Extracted from text response"
                        }
                
                # Default to "Other" if no match found
                return {
                    "document_type": "Other",
                    "confidence": 0.5,
                    "reasoning": "Could not determine document type from response"
                }
        else:
            return {
                "document_type": "Other",
                "confidence": 0.0,
                "reasoning": "No answer received from AI"
            }
    
    except Exception as e:
        logger.error(f"Error categorizing document: {str(e)}")
        return {
            "document_type": "Other",
            "confidence": 0.0,
            "reasoning": f"Error: {str(e)}"
        }

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
        import requests
        response = requests.post(api_url, headers=headers, json=data)
        
        # Check for errors
        response.raise_for_status()
        
        # Return response as JSON
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API Request Error: {str(e)}")
        return {"error": str(e)}

def initialize_categorization_state():
    """
    Initialize session state variables for document categorization
    """
    if not hasattr(st.session_state, "document_categorization"):
        st.session_state.document_categorization = {
            "is_categorized": False,
            "categorized_files": 0,
            "total_files": 0,
            "results": {},  # file_id -> categorization result
            "errors": {},   # file_id -> error message
            "processing_state": {
                "is_processing": False,
                "current_file_index": -1,
                "current_file": ""
            }
        }
        logger.info("Initialized document_categorization in session state")
