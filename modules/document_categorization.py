import streamlit as st
import logging
import json
import requests
import re
from typing import Dict, Any, List, Optional, Tuple

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
        if st.button("Go to File Browser", key="go_to_file_browser_button_cat"):
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
    
    # AI Model selection
    ai_models = [
        "azure__openai__gpt_4o_mini",
        "azure__openai__gpt_4o_2024_05_13",
        "google__gemini_2_0_flash_001",
        "google__gemini_2_0_flash_lite_preview",
        "google__gemini_1_5_flash_001",
        "google__gemini_1_5_pro_001",
        "aws__claude_3_haiku",
        "aws__claude_3_sonnet",
        "aws__claude_3_5_sonnet",
        "aws__claude_3_7_sonnet",
        "aws__titan_text_lite"
    ]
    
    selected_model = st.selectbox(
        "Select AI Model for Categorization",
        options=ai_models,
        index=0,
        key="ai_model_select_cat",
        help="Choose the AI model to use for document categorization"
    )
    
    # Categorization controls
    col1, col2 = st.columns(2)
    
    with col1:
        start_button = st.button("Start Categorization", key="start_categorization_button_cat", use_container_width=True)
    
    with col2:
        cancel_button = st.button("Cancel Categorization", key="cancel_categorization_button_cat", use_container_width=True)
    
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
                    result = categorize_document(file_id, selected_model)
                    
                    # Store result
                    st.session_state.document_categorization["results"][file_id] = {
                        "file_id": file_id,
                        "file_name": file_name,
                        "document_type": result["document_type"],
                        "confidence": result["confidence"],
                        "reasoning": result["reasoning"]
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
        results_data = []
        for file_id, result in st.session_state.document_categorization["results"].items():
            results_data.append({
                "File Name": result["file_name"],
                "Document Type": result["document_type"],
                "Confidence": f"{result['confidence']:.2f}"
            })
        
        if results_data:
            st.table(results_data)
        
        # Display errors if any
        if st.session_state.document_categorization["errors"]:
            st.write("### Errors")
            
            for file_id, error in st.session_state.document_categorization["errors"].items():
                st.error(f"{error['file_name']}: {error['error']}")
        
        # Continue button
        st.write("---")
        if st.button("Continue to Metadata Configuration", key="continue_to_metadata_button_cat", use_container_width=True):
            st.session_state.current_page = "Metadata Configuration"
            st.rerun()

def categorize_document(file_id: str, model: str = "azure__openai__gpt_4o_mini") -> Dict[str, Any]:
    """
    Categorize a document using Box AI
    
    Args:
        file_id: Box file ID
        model: AI model to use for categorization
        
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
    
    # Create prompt for document categorization with confidence score request
    prompt = (
        f"Analyze this document and determine which category it belongs to from the following options: "
        f"{', '.join(document_types)}. "
        f"Provide your answer in the following format:\n"
        f"Category: [selected category]\n"
        f"Confidence: [confidence score between 0 and 1, where 1 is highest confidence]\n"
        f"Reasoning: [brief explanation of your categorization]"
    )
    
    # Construct API URL for Box AI Ask
    api_url = "https://api.box.com/2.0/ai/ask"
    
    # Construct request body according to the API documentation
    request_body = {
        "mode": "single_item_qa",  # Required parameter - single_item_qa or multiple_item_qa
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
                "model": model,
                "mode": "default"  # Required parameter for basic_text
            }
        }
    }
    
    try:
        # Make API call
        logger.info(f"Making Box AI API call with request: {json.dumps(request_body)}")
        response = requests.post(api_url, headers=headers, json=request_body)
        
        # Log response for debugging
        logger.info(f"Box AI API response status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Box AI API error response: {response.text}")
            raise Exception(f"Error in Box AI API call: {response.status_code} Client Error: Bad Request for url: {api_url}")
        
        # Parse response
        response_data = response.json()
        logger.info(f"Box AI API response data: {json.dumps(response_data)}")
        
        # Extract answer from response
        if "answer" in response_data:
            answer_text = response_data["answer"]
            
            # Parse the structured response to extract category, confidence, and reasoning
            document_type, confidence, reasoning = parse_categorization_response(answer_text, document_types)
            
            return {
                "document_type": document_type,
                "confidence": confidence,
                "reasoning": reasoning
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

def parse_categorization_response(response_text: str, document_types: List[str]) -> Tuple[str, float, str]:
    """
    Parse the AI response to extract document type, confidence score, and reasoning
    
    Args:
        response_text: The AI response text
        document_types: List of valid document types
        
    Returns:
        tuple: (document_type, confidence, reasoning)
    """
    # Default values
    document_type = "Other"
    confidence = 0.5
    reasoning = response_text
    
    try:
        # Try to extract category using regex
        category_match = re.search(r"Category:\s*([^\n]+)", response_text, re.IGNORECASE)
        if category_match:
            category_text = category_match.group(1).strip()
            # Find the closest matching document type
            for dt in document_types:
                if dt.lower() in category_text.lower():
                    document_type = dt
                    break
        
        # Try to extract confidence using regex
        confidence_match = re.search(r"Confidence:\s*(0\.\d+|1\.0|1)", response_text, re.IGNORECASE)
        if confidence_match:
            confidence = float(confidence_match.group(1))
        else:
            # If no explicit confidence, try to find confidence-related words
            confidence_words = {
                "very high": 0.9,
                "high": 0.8,
                "good": 0.7,
                "moderate": 0.6,
                "medium": 0.5,
                "low": 0.4,
                "very low": 0.3,
                "uncertain": 0.2
            }
            
            for word, value in confidence_words.items():
                if word in response_text.lower():
                    confidence = value
                    break
        
        # Try to extract reasoning
        reasoning_match = re.search(r"Reasoning:\s*([^\n]+(?:\n[^\n]+)*)", response_text, re.IGNORECASE)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
        
        # If no document type was found in the structured response, try to find it in the full text
        if document_type == "Other":
            for dt in document_types:
                if dt.lower() in response_text.lower():
                    document_type = dt
                    break
        
        return document_type, confidence, reasoning
    
    except Exception as e:
        logger.error(f"Error parsing categorization response: {str(e)}")
        return document_type, confidence, reasoning
