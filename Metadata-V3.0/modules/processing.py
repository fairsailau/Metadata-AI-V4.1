import streamlit as st
import logging
from typing import Dict, List, Any, Optional
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_files():
    """
    Process files using the configured metadata extraction parameters
    """
    st.title("Process Files")
    
    if not st.session_state.authenticated or not st.session_state.client:
        st.error("Please authenticate with Box first")
        return
    
    if not st.session_state.selected_files:
        st.warning("No files selected. Please select files in the File Browser first.")
        if st.button("Go to File Browser"):
            st.session_state.current_page = "File Browser"
            st.rerun()
        return
    
    # Check if metadata configuration is complete
    if "metadata_config" not in st.session_state:
        st.warning("Metadata configuration is not complete. Please configure metadata extraction first.")
        if st.button("Go to Metadata Configuration"):
            st.session_state.current_page = "Metadata Configuration"
            st.rerun()
        return
    
    # Initialize processing state if not exists
    if "processing_state" not in st.session_state:
        st.session_state.processing_state = {
            "is_processing": False,
            "current_file_index": -1,
            "current_file": "",
            "processed_files": 0,
            "total_files": 0,
            "results": {},
            "errors": {},
            "retries": {},
            "max_retries": 3,
            "retry_delay": 2,
            "processing_mode": "Sequential"
        }
    
    # Display processing information
    num_files = len(st.session_state.selected_files)
    st.write(f"Ready to process {num_files} files using the configured metadata extraction parameters.")
    
    # Batch processing controls
    with st.expander("Batch Processing Controls", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Batch size control
            batch_size = st.number_input(
                "Batch Size",
                min_value=1,
                max_value=25,
                value=st.session_state.metadata_config.get("batch_size", 5),
                key="batch_size_input"
            )
            st.session_state.metadata_config["batch_size"] = batch_size
            
            # Max retries control
            max_retries = st.number_input(
                "Max Retries",
                min_value=0,
                max_value=10,
                value=st.session_state.processing_state.get("max_retries", 3),
                key="max_retries_input"
            )
            st.session_state.processing_state["max_retries"] = max_retries
        
        with col2:
            # Retry delay control
            retry_delay = st.number_input(
                "Retry Delay (seconds)",
                min_value=1,
                max_value=30,
                value=st.session_state.processing_state.get("retry_delay", 2),
                key="retry_delay_input"
            )
            st.session_state.processing_state["retry_delay"] = retry_delay
            
            # Processing mode
            processing_mode = st.selectbox(
                "Processing Mode",
                options=["Sequential", "Parallel"],
                index=0,
                key="processing_mode_input"
            )
            st.session_state.processing_state["processing_mode"] = processing_mode
    
    # Template management
    with st.expander("Metadata Template Management"):
        st.write("#### Save Current Configuration as Template")
        template_name = st.text_input("Template Name", key="template_name_input")
        
        if st.button("Save Template", key="save_template_button"):
            if template_name:
                # Initialize template dictionary if not exists
                if "metadata_templates" not in st.session_state:
                    st.session_state.metadata_templates = {}
                
                st.session_state.metadata_templates[template_name] = st.session_state.metadata_config.copy()
                st.success(f"Template '{template_name}' saved successfully!")
            else:
                st.warning("Please enter a template name")
        
        st.write("#### Load Template")
        if "metadata_templates" in st.session_state and st.session_state.metadata_templates:
            template_options = list(st.session_state.metadata_templates.keys())
            selected_template = st.selectbox(
                "Select Template",
                options=template_options,
                key="load_template_select"
            )
            
            if st.button("Load Template", key="load_template_button"):
                st.session_state.metadata_config = st.session_state.metadata_templates[selected_template].copy()
                st.success(f"Template '{selected_template}' loaded successfully!")
        else:
            st.info("No saved templates yet")
    
    # Display configuration summary
    with st.expander("Configuration Summary"):
        # Check if using document type templates
        if st.session_state.metadata_config.get("use_document_type_templates", False):
            st.write("#### Using Document Type Templates")
            st.write("Each file will be processed using its document type's template or freeform prompt.")
            
            # Display document type to template mapping
            if "document_type_to_template" in st.session_state:
                st.write("Document Type to Template Mapping:")
                for doc_type, template in st.session_state.document_type_to_template.items():
                    if template:
                        st.write(f"- {doc_type}: {template.get('displayName', 'Unknown')}")
                    else:
                        st.write(f"- {doc_type}: Freeform extraction")
            
            # Display document type to freeform prompt mapping
            if "document_type_to_freeform_prompt" in st.session_state:
                st.write("Document Type to Freeform Prompt Mapping:")
                for doc_type, prompt in st.session_state.document_type_to_freeform_prompt.items():
                    if prompt:
                        st.write(f"- {doc_type}: {prompt[:50]}...")
        else:
            st.write("#### Extraction Method")
            st.write(f"Method: {st.session_state.metadata_config['extraction_method'].capitalize()}")
            
            if st.session_state.metadata_config["extraction_method"] == "structured":
                if st.session_state.metadata_config["use_template"]:
                    st.write(f"Using template: Template ID {st.session_state.metadata_config['template_id']}")
                else:
                    st.write(f"Using {len(st.session_state.metadata_config['custom_fields'])} custom fields")
                    for i, field in enumerate(st.session_state.metadata_config["custom_fields"]):
                        st.write(f"- {field['display_name']} ({field['type']})")
            else:
                st.write("Freeform prompt:")
                st.write(f"> {st.session_state.metadata_config['freeform_prompt']}")
        
        st.write(f"AI Model: {st.session_state.metadata_config['ai_model']}")
        st.write(f"Batch Size: {st.session_state.metadata_config['batch_size']}")
    
    # Display selected files
    with st.expander("Selected Files"):
        for file in st.session_state.selected_files:
            st.write(f"- {file['name']} (Type: {file['type']})")
    
    # Process files button
    col1, col2 = st.columns(2)
    
    with col1:
        start_button = st.button(
            "Start Processing",
            disabled=st.session_state.processing_state["is_processing"],
            use_container_width=True,
            key="start_processing_button"
        )
    
    with col2:
        cancel_button = st.button(
            "Cancel Processing",
            disabled=not st.session_state.processing_state["is_processing"],
            use_container_width=True,
            key="cancel_processing_button"
        )
    
    # Progress tracking
    progress_container = st.container()
    
    # Get metadata extraction functions
    from modules.metadata_extraction import metadata_extraction
    extraction_functions = metadata_extraction()
    
    # Import template retrieval functions
    from modules.metadata_template_retrieval import get_template_for_structured_extraction
    
    # Helper function to extract structured data from API response
    def extract_structured_data_from_response(response):
        """
        Extract structured data from various possible response structures
        
        Args:
            response (dict): API response
            
        Returns:
            dict: Extracted structured data (key-value pairs)
        """
        structured_data = {}
        extracted_text = ""
        
        # Log the response structure for debugging
        logger.info(f"Response structure: {json.dumps(response, indent=2) if isinstance(response, dict) else str(response)}")
        
        if isinstance(response, dict):
            # Check for answer field (contains structured data in JSON format)
            if "answer" in response and isinstance(response["answer"], dict):
                structured_data = response["answer"]
                logger.info(f"Found structured data in 'answer' field: {structured_data}")
                return structured_data
            
            # Check for answer field as string (JSON string)
            if "answer" in response and isinstance(response["answer"], str):
                try:
                    answer_data = json.loads(response["answer"])
                    if isinstance(answer_data, dict):
                        structured_data = answer_data
                        logger.info(f"Found structured data in 'answer' field (JSON string): {structured_data}")
                        return structured_data
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse 'answer' field as JSON: {response['answer']}")
            
            # Check for key-value pairs directly in response
            for key, value in response.items():
                if key not in ["error", "items", "response", "item_collection", "entries", "type", "id", "sequence_id"]:
                    structured_data[key] = value
            
            # Check in response field
            if "response" in response and isinstance(response["response"], dict):
                response_obj = response["response"]
                if "answer" in response_obj and isinstance(response_obj["answer"], dict):
                    structured_data = response_obj["answer"]
                    logger.info(f"Found structured data in 'response.answer' field: {structured_data}")
                    return structured_data
            
            # Check in items array
            if "items" in response and isinstance(response["items"], list) and len(response["items"]) > 0:
                item = response["items"][0]
                if isinstance(item, dict):
                    if "answer" in item and isinstance(item["answer"], dict):
                        structured_data = item["answer"]
                        logger.info(f"Found structured data in 'items[0].answer' field: {structured_data}")
                        return structured_data
        
        # If we couldn't find structured data, return empty dict
        if not structured_data:
            logger.warning("Could not find structured data in response")
        
        return structured_data
    
    # Process a single file
    def process_file(file):
        try:
            file_id = file["id"]
            file_name = file["name"]
            
            logger.info(f"Processing file: {file_name} (ID: {file_id})")
            st.session_state.debug_info.append(f"Processing file: {file_name} (ID: {file_id})")
            
            # Check if we have feedback data for this file
            feedback_key = f"{file_id}_{st.session_state.metadata_config['extraction_method']}"
            has_feedback = feedback_key in st.session_state.feedback_data
            
            if has_feedback:
                logger.info(f"Using feedback data for file: {file_name}")
                st.session_state.debug_info.append(f"Using feedback data for file: {file_name}")
                
                # Check if using document type templates
                if st.session_state.metadata_config.get("use_document_type_templates", False):
                    # Get document type for this file
                    document_type = "Other"
                    if "document_categorization" in st.session_state and file_id in st.session_state.document_categorization["results"]:
                        document_type = st.session_state.document_categorization["results"][file_id].get("document_type", "Other")
                    
                    # Get template for this document type
                    template = None
                    if "file_to_template" in st.session_state and file_id in st.session_state.file_to_template:
                        template = st.session_state.file_to_template[file_id]
                    
                    if template:
                        # Use structured extraction with template
                        logger.info(f"Using template-based extraction for document type: {document_type}")
                        st.session_state.debug_info.append(f"Using template-based extraction for document type: {document_type}")
                        
                        # Convert template to format required for structured extraction
                        metadata_template = get_template_for_structured_extraction(template)
                        
                        # Use real API call
                        api_result = extraction_functions["extract_structured_metadata"](
                            file_id=file_id,
                            metadata_template=metadata_template,
                            ai_model=st.session_state.metadata_config["ai_model"]
                        )
                        
                        # Create a clean result object with the extracted data
                        result = {}
                        
                        # Copy fields from API result to our result object
                        if isinstance(api_result, dict):
                            for key, value in api_result.items():
                                if key not in ["error", "items", "response"]:
                                    result[key] = value
                        
                        # Apply feedback if available
                        if has_feedback:
                            feedback = st.session_state.feedback_data[feedback_key]
                            # Merge feedback with result, prioritizing feedback
                            for key, value in feedback.items():
                                result[key] = value
                    else:
                        # Use freeform extraction with custom prompt for document type
                        logger.info(f"Using freeform extraction for document type: {document_type}")
                        st.session_state.debug_info.append(f"Using freeform extraction for document type: {document_type}")
                        
                        # Get custom prompt for this document type
                        prompt = st.session_state.metadata_config["freeform_prompt"]  # Default prompt
                        if "document_type_to_freeform_prompt" in st.session_state and document_type in st.session_state.document_type_to_freeform_prompt:
                            prompt = st.session_state.document_type_to_freeform_prompt[document_type]
                        
                        # Use real API call
                        api_result = extraction_functions["extract_freeform_metadata"](
                            file_id=file_id,
                            prompt=prompt,
                            ai_model=st.session_state.metadata_config["ai_model"]
                        )
                        
                        # Create a clean result object with the extracted data
                        result = {}
                        
                        # Extract structured data from API response
                        structured_data = extract_structured_data_from_response(api_result)
                        
                        # Copy structured data to result
                        for key, value in structured_data.items():
                            result[key] = value
                        
                        # Apply feedback if available
                        if has_feedback:
                            feedback = st.session_state.feedback_data[feedback_key]
                            # Merge feedback with result, prioritizing feedback
                            for key, value in feedback.items():
                                result[key] = value
                else:
                    # Determine extraction method from metadata config
                    if st.session_state.metadata_config["extraction_method"] == "structured":
                        # Structured extraction
                        if st.session_state.metadata_config["use_template"]:
                            # Template-based extraction
                            template_id = st.session_state.metadata_config["template_id"]
                            metadata_template = {
                                "template_key": template_id,
                                "scope": "enterprise",  # Default to enterprise scope
                                "type": "metadata_template"
                            }
                            
                            logger.info(f"Using template-based extraction with template ID: {template_id}")
                            st.session_state.debug_info.append(f"Using template-based extraction with template ID: {template_id}")
                            
                            # Use real API call
                            api_result = extraction_functions["extract_structured_metadata"](
                                file_id=file_id,
                                metadata_template=metadata_template,
                                ai_model=st.session_state.metadata_config["ai_model"]
                            )
                            
                            # Create a clean result object with the extracted data
                            result = {}
                            
                            # Copy fields from API result to our result object
                            if isinstance(api_result, dict):
                                for key, value in api_result.items():
                                    if key not in ["error", "items", "response"]:
                                        result[key] = value
                            
                            # Apply feedback if available
                            if has_feedback:
                                feedback = st.session_state.feedback_data[feedback_key]
                                # Merge feedback with result, prioritizing feedback
                                for key, value in feedback.items():
                                    result[key] = value
                        else:
                            # Custom fields extraction
                            custom_fields = st.session_state.metadata_config["custom_fields"]
                            
                            logger.info(f"Using custom fields extraction with {len(custom_fields)} fields")
                            st.session_state.debug_info.append(f"Using custom fields extraction with {len(custom_fields)} fields")
                            
                            # Use real API call
                            api_result = extraction_functions["extract_structured_metadata"](
                                file_id=file_id,
                                custom_fields=custom_fields,
                                ai_model=st.session_state.metadata_config["ai_model"]
                            )
                            
                            # Create a clean result object with the extracted data
                            result = {}
                            
                            # Copy fields from API result to our result object
                            if isinstance(api_result, dict):
                                for key, value in api_result.items():
                                    if key not in ["error", "items", "response"]:
                                        result[key] = value
                            
                            # Apply feedback if available
                            if has_feedback:
                                feedback = st.session_state.feedback_data[feedback_key]
                                # Merge feedback with result, prioritizing feedback
                                for key, value in feedback.items():
                                    result[key] = value
                    else:
                        # Freeform extraction
                        prompt = st.session_state.metadata_config["freeform_prompt"]
                        
                        logger.info(f"Using freeform extraction with prompt: {prompt[:50]}...")
                        st.session_state.debug_info.append(f"Using freeform extraction with prompt: {prompt[:50]}...")
                        
                        # Use real API call
                        api_result = extraction_functions["extract_freeform_metadata"](
                            file_id=file_id,
                            prompt=prompt,
                            ai_model=st.session_state.metadata_config["ai_model"]
                        )
                        
                        # Create a clean result object with the extracted data
                        result = {}
                        
                        # Extract structured data from API response
                        structured_data = extract_structured_data_from_response(api_result)
                        
                        # Copy structured data to result
                        for key, value in structured_data.items():
                            result[key] = value
                        
                        # Apply feedback if available
                        if has_feedback:
                            feedback = st.session_state.feedback_data[feedback_key]
                            # Merge feedback with result, prioritizing feedback
                            for key, value in feedback.items():
                                result[key] = value
            else:
                # No feedback data, process normally
                
                # Check if using document type templates
                if st.session_state.metadata_config.get("use_document_type_templates", False):
                    # Get document type for this file
                    document_type = "Other"
                    if "document_categorization" in st.session_state and file_id in st.session_state.document_categorization["results"]:
                        document_type = st.session_state.document_categorization["results"][file_id].get("document_type", "Other")
                    
                    # Get template for this document type
                    template = None
                    if "file_to_template" in st.session_state and file_id in st.session_state.file_to_template:
                        template = st.session_state.file_to_template[file_id]
                    
                    if template:
                        # Use structured extraction with template
                        logger.info(f"Using template-based extraction for document type: {document_type}")
                        st.session_state.debug_info.append(f"Using template-based extraction for document type: {document_type}")
                        
                        # Convert template to format required for structured extraction
                        metadata_template = get_template_for_structured_extraction(template)
                        
                        # Use real API call
                        api_result = extraction_functions["extract_structured_metadata"](
                            file_id=file_id,
                            metadata_template=metadata_template,
                            ai_model=st.session_state.metadata_config["ai_model"]
                        )
                        
                        # Create a clean result object with the extracted data
                        result = {}
                        
                        # Copy fields from API result to our result object
                        if isinstance(api_result, dict):
                            for key, value in api_result.items():
                                if key not in ["error", "items", "response"]:
                                    result[key] = value
                    else:
                        # Use freeform extraction with custom prompt for document type
                        logger.info(f"Using freeform extraction for document type: {document_type}")
                        st.session_state.debug_info.append(f"Using freeform extraction for document type: {document_type}")
                        
                        # Get custom prompt for this document type
                        prompt = st.session_state.metadata_config.get("freeform_prompt", "Extract key metadata from this document.")  # Default prompt
                        if "document_type_to_freeform_prompt" in st.session_state and document_type in st.session_state.document_type_to_freeform_prompt:
                            prompt = st.session_state.document_type_to_freeform_prompt[document_type]
                        
                        # Use real API call
                        api_result = extraction_functions["extract_freeform_metadata"](
                            file_id=file_id,
                            prompt=prompt,
                            ai_model=st.session_state.metadata_config["ai_model"]
                        )
                        
                        # Create a clean result object with the extracted data
                        result = {}
                        
                        # Extract structured data from API response
                        structured_data = extract_structured_data_from_response(api_result)
                        
                        # Copy structured data to result
                        for key, value in structured_data.items():
                            result[key] = value
                else:
                    # Determine extraction method from metadata config
                    if st.session_state.metadata_config["extraction_method"] == "structured":
                        # Structured extraction
                        if st.session_state.metadata_config["use_template"]:
                            # Template-based extraction
                            template_id = st.session_state.metadata_config["template_id"]
                            metadata_template = {
                                "template_key": template_id,
                                "scope": "enterprise",  # Default to enterprise scope
                                "type": "metadata_template"
                            }
                            
                            logger.info(f"Using template-based extraction with template ID: {template_id}")
                            st.session_state.debug_info.append(f"Using template-based extraction with template ID: {template_id}")
                            
                            # Use real API call
                            api_result = extraction_functions["extract_structured_metadata"](
                                file_id=file_id,
                                metadata_template=metadata_template,
                                ai_model=st.session_state.metadata_config["ai_model"]
                            )
                            
                            # Create a clean result object with the extracted data
                            result = {}
                            
                            # Copy fields from API result to our result object
                            if isinstance(api_result, dict):
                                for key, value in api_result.items():
                                    if key not in ["error", "items", "response"]:
                                        result[key] = value
                        else:
                            # Custom fields extraction
                            custom_fields = st.session_state.metadata_config.get("custom_fields", [])
                            
                            logger.info(f"Using custom fields extraction with {len(custom_fields)} fields")
                            st.session_state.debug_info.append(f"Using custom fields extraction with {len(custom_fields)} fields")
                            
                            # Use real API call
                            api_result = extraction_functions["extract_structured_metadata"](
                                file_id=file_id,
                                custom_fields=custom_fields,
                                ai_model=st.session_state.metadata_config["ai_model"]
                            )
                            
                            # Create a clean result object with the extracted data
                            result = {}
                            
                            # Copy fields from API result to our result object
                            if isinstance(api_result, dict):
                                for key, value in api_result.items():
                                    if key not in ["error", "items", "response"]:
                                        result[key] = value
                    else:
                        # Freeform extraction
                        prompt = st.session_state.metadata_config.get("freeform_prompt", "Extract key metadata from this document.")
                        
                        logger.info(f"Using freeform extraction with prompt: {prompt[:50]}...")
                        st.session_state.debug_info.append(f"Using freeform extraction with prompt: {prompt[:50]}...")
                        
                        # Use real API call
                        api_result = extraction_functions["extract_freeform_metadata"](
                            file_id=file_id,
                            prompt=prompt,
                            ai_model=st.session_state.metadata_config["ai_model"]
                        )
                        
                        # Create a clean result object with the extracted data
                        result = {}
                        
                        # Extract structured data from API response
                        structured_data = extract_structured_data_from_response(api_result)
                        
                        # Copy structured data to result
                        for key, value in structured_data.items():
                            result[key] = value
            
            # Store result in processing state
            st.session_state.processing_state["results"][file_id] = {
                "file_id": file_id,
                "file_name": file_name,
                "result": result
            }
            
            logger.info(f"Successfully processed file: {file_name}")
            st.session_state.debug_info.append(f"Successfully processed file: {file_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error processing file {file['name']}: {str(e)}")
            st.session_state.debug_info.append(f"Error processing file {file['name']}: {str(e)}")
            
            # Store error in processing state
            st.session_state.processing_state["errors"][file_id] = {
                "file_id": file_id,
                "file_name": file_name,
                "error": str(e)
            }
            
            return False
    
    # Start processing
    if start_button:
        # Initialize processing state
        st.session_state.processing_state["is_processing"] = True
        st.session_state.processing_state["processed_files"] = 0
        st.session_state.processing_state["total_files"] = len(st.session_state.selected_files)
        st.session_state.processing_state["current_file_index"] = -1
        st.session_state.processing_state["results"] = {}
        st.session_state.processing_state["errors"] = {}
        st.session_state.processing_state["retries"] = {}
        st.rerun()
    
    # Cancel processing
    if cancel_button:
        st.session_state.processing_state["is_processing"] = False
        st.rerun()
    
    # Process files if processing is in progress
    if st.session_state.processing_state["is_processing"]:
        # Get next file to process
        next_file_index = st.session_state.processing_state["current_file_index"] + 1
        
        if next_file_index < len(st.session_state.selected_files):
            # Get file information
            file = st.session_state.selected_files[next_file_index]
            file_id = file["id"]
            file_name = file["name"]
            
            # Update processing state
            st.session_state.processing_state["current_file_index"] = next_file_index
            st.session_state.processing_state["current_file"] = file_name
            
            # Check if file has already been processed
            if file_id in st.session_state.processing_state["results"]:
                # Skip file
                logger.info(f"Skipping already processed file: {file_name}")
                st.session_state.debug_info.append(f"Skipping already processed file: {file_name}")
                st.session_state.processing_state["processed_files"] += 1
                st.rerun()
            
            # Check if file has errors and retries
            elif file_id in st.session_state.processing_state["errors"]:
                # Get retry count
                retry_count = st.session_state.processing_state["retries"].get(file_id, 0)
                
                if retry_count < st.session_state.processing_state["max_retries"]:
                    # Increment retry count
                    st.session_state.processing_state["retries"][file_id] = retry_count + 1
                    
                    # Log retry
                    logger.info(f"Retrying file {file_name} (retry {retry_count + 1} of {st.session_state.processing_state['max_retries']})")
                    st.session_state.debug_info.append(f"Retrying file {file_name} (retry {retry_count + 1} of {st.session_state.processing_state['max_retries']})")
                    
                    # Process file
                    success = process_file(file)
                    
                    if success:
                        # Remove error
                        del st.session_state.processing_state["errors"][file_id]
                        
                        # Increment processed files count
                        st.session_state.processing_state["processed_files"] += 1
                    
                    # Wait for retry delay
                    time.sleep(st.session_state.processing_state["retry_delay"])
                else:
                    # Max retries reached, skip file
                    logger.info(f"Max retries reached for file: {file_name}")
                    st.session_state.debug_info.append(f"Max retries reached for file: {file_name}")
                    st.session_state.processing_state["processed_files"] += 1
            
            else:
                # Process file
                success = process_file(file)
                
                if success:
                    # Increment processed files count
                    st.session_state.processing_state["processed_files"] += 1
            
            # Increment current file index
            st.session_state.processing_state["current_file_index"] += 1
            
            # Check if we're done
            if st.session_state.processing_state["current_file_index"] >= len(st.session_state.selected_files):
                st.session_state.processing_state["is_processing"] = False
                logger.info("Processing complete")
                st.session_state.debug_info.append("Processing complete")
            
            # Update extraction results in session state
            st.session_state.extraction_results = st.session_state.processing_state["results"]
            
            # Rerun to process next file or show results
            st.rerun()
        else:
            # All files processed
            st.session_state.processing_state["is_processing"] = False
    
    # Display progress
    with progress_container:
        if st.session_state.processing_state["is_processing"]:
            # Display progress bar
            progress = st.progress(st.session_state.processing_state["processed_files"] / st.session_state.processing_state["total_files"])
            
            # Display current file
            st.write(f"Processing file: {st.session_state.processing_state['current_file']}")
            
            # Display processed files count
            st.write(f"Processed {st.session_state.processing_state['processed_files']} of {st.session_state.processing_state['total_files']} files")
        elif st.session_state.processing_state["processed_files"] > 0:
            # Display completion message
            st.success(f"Processing complete! Processed {st.session_state.processing_state['processed_files']} of {st.session_state.processing_state['total_files']} files")
            
            # Display errors if any
            if st.session_state.processing_state["errors"]:
                st.warning(f"Encountered {len(st.session_state.processing_state['errors'])} errors during processing")
                
                with st.expander("View Errors"):
                    for file_id, error in st.session_state.processing_state["errors"].items():
                        st.error(f"{error['file_name']}: {error['error']}")
            
            # Continue button
            if st.button("Continue to View Results", use_container_width=True):
                st.session_state.current_page = "View Results"
                st.rerun()
    
    # Debug information
    with st.expander("Debug Information"):
        if "debug_info" in st.session_state:
            for info in st.session_state.debug_info:
                st.write(info)
