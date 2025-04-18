import streamlit as st
import logging
import json
import requests
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def document_categorization():
    """
    Categorize documents using Box AI
    """
    st.title("Document Categorization")
    
    if not st.session_state.authenticated or not st.session_state.client:
        st.error("Please authenticate with Box first")
        return
    
    if not st.session_state.selected_files:
        st.warning("No files selected. Please select files in the File Browser first.")
        if st.button("Go to File Browser"):
            st.session_state.current_page = "File Browser"
            st.rerun()
        return
    
    # Initialize document categorization state if not exists
    if "document_categorization" not in st.session_state:
        st.session_state.document_categorization = {
            "is_categorized": False,
            "results": {},
            "errors": {}
        }
    
    # Display selected files
    num_files = len(st.session_state.selected_files)
    st.write(f"Ready to categorize {num_files} files using Box AI.")
    
    # Categorization controls
    col1, col2 = st.columns(2)
    
    with col1:
        start_button = st.button("Start Categorization", use_container_width=True)
    
    with col2:
        cancel_button = st.button("Cancel Categorization", use_container_width=True)
    
    # Process categorization
    if start_button:
        with st.spinner("Categorizing documents..."):
            # Reset categorization results
            st.session_state.document_categorization = {
                "is_categorized": False,
                "results": {},
                "errors": {}
            }
            
            # Process each file
            for file in st.session_state.selected_files:
                file_id = file["id"]
                file_name = file["name"]
                
                try:
                    # Categorize document
                    result = categorize_document(file_id)
                    
                    # Store result
                    st.session_state.document_categorization["results"][file_id] = {
                        "file_id": file_id,
                        "file_name": file_name,
                        "document_type": result["document_type"],
                        "confidence": result["confidence"]
                    }
                except Exception as e:
                    logger.error(f"Error categorizing document {file_name}: {str(e)}")
                    st.session_state.document_categorization["errors"][file_id] = {
                        "file_id": file_id,
                        "file_name": file_name,
                        "error": str(e)
                    }
            
            # Mark as categorized
            st.session_state.document_categorization["is_categorized"] = True
            
            # Show success message
            num_processed = len(st.session_state.document_categorization["results"])
            num_errors = len(st.session_state.document_categorization["errors"])
            
            if num_errors == 0:
                st.success(f"Categorization complete! Processed {num_processed} files.")
            else:
                st.warning(f"Categorization complete! Processed {num_processed} files with {num_errors} errors.")
    
    # Display categorization results
    if st.session_state.document_categorization["is_categorized"]:
        st.write("### Categorization Results")
        
        # Create a table of results
        results_table = []
        
        for file_id, result in st.session_state.document_categorization["results"].items():
            results_table.append({
                "File Name": result["file_name"],
                "Document Type": result["document_type"],
                "Confidence": f"{result['confidence']:.2f}"
            })
        
        if results_table:
            st.table(results_table)
        
        # Display errors if any
        if st.session_state.document_categorization["errors"]:
            st.write("### Errors")
            
            for file_id, error in st.session_state.document_categorization["errors"].items():
                st.error(f"{error['file_name']}: {error['error']}")
        
        # Continue button
        st.write("---")
        if st.button("Continue to Metadata Configuration", use_container_width=True):
            st.session_state.current_page = "Metadata Configuration"
            st.rerun()

def categorize_document(file_id: str) -> Dict[str, Any]:
    """
    Categorize a document using Box AI
    
    Args:
        file_id: Box file ID
        
    Returns:
        dict: Document categorization result
    """
    # Get access token from client
    access_token = None
    if hasattr(st.session_state.client, '_oauth'):
        access_token = st.session_state.client._oauth.access_token
    elif hasattr(st.session_state.client, 'auth') and hasattr(st.session_state.client.auth, 'access_token'):
        access_token = st.session_state.client.auth.access_token
    
    if not access_token:
        raise ValueError("Could not retrieve access token from client")
    
    # Set headers
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Define document types to categorize
    document_types = [
        "Sales Contract",
        "Invoices",
        "Tax",
        "Financial Report",
        "Employment Contract",
        "PII",
        "Other"
    ]
    
    # Create prompt for document categorization
    prompt = f"""Analyze this document and determine which of the following document types it belongs to:
{', '.join(document_types)}

Respond with a JSON object containing:
1. document_type: The document type from the list above
2. confidence: A number between 0 and 1 indicating your confidence in the classification
3. reasoning: A brief explanation of why you classified it this way

Example response:
{{
  "document_type": "Invoices",
  "confidence": 0.95,
  "reasoning": "The document contains invoice number, line items, prices, and payment terms."
}}"""
    
    # Construct API URL for Box AI Ask
    api_url = "https://api.box.com/2.0/ai/ask"
    
    # Construct request body
    request_body = {
        "item": {
            "type": "file",
            "id": file_id
        },
        "prompt": prompt,
        "model": "azure__openai__gpt_4o_mini"  # Use a default model
    }
    
    try:
        # Make API call
        response = requests.post(api_url, headers=headers, json=request_body)
        
        # Check for errors
        response.raise_for_status()
        
        # Parse response
        response_data = response.json()
        
        # Extract answer from response
        if "answer" in response_data:
            answer_text = response_data["answer"]
            
            # Try to parse JSON from answer
            try:
                answer_json = json.loads(answer_text)
                
                # Validate required fields
                if "document_type" not in answer_json or "confidence" not in answer_json:
                    # If missing fields, try to extract from text
                    document_type = next((dt for dt in document_types if dt.lower() in answer_text.lower()), "Other")
                    confidence = 0.5  # Default confidence
                    
                    return {
                        "document_type": document_type,
                        "confidence": confidence,
                        "reasoning": "Extracted from text response"
                    }
                
                return answer_json
            except json.JSONDecodeError:
                # If not valid JSON, try to extract from text
                document_type = next((dt for dt in document_types if dt.lower() in answer_text.lower()), "Other")
                confidence = 0.5  # Default confidence
                
                return {
                    "document_type": document_type,
                    "confidence": confidence,
                    "reasoning": "Extracted from text response"
                }
        
        # If no answer in response, return default
        return {
            "document_type": "Other",
            "confidence": 0.0,
            "reasoning": "Could not determine document type"
        }
    
    except Exception as e:
        logger.error(f"Error in Box AI API call: {str(e)}")
        raise Exception(f"Error categorizing document: {str(e)}")
