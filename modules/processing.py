import streamlit as st
import logging
import time
import concurrent.futures
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Debug mode flag
DEBUG_MODE = True

def process_files():
    """
    Process files with metadata extraction
    """
    st.title("Process Files")
    
    if not st.session_state.authenticated or not st.session_state.client:
        st.error("Please authenticate with Box first")
        return
    
    if not st.session_state.selected_files:
        st.warning("No files selected. Please select files in the File Browser first.")
        if st.button("Go to File Browser", key="go_to_file_browser_button_process"):
            st.session_state.current_page = "File Browser"
            st.rerun()
        return
    
    # Display processing parameters
    st.write(f"Ready to process {len(st.session_state.selected_files)} files using the configured metadata extraction parameters.")
    
    # Batch processing controls
    with st.expander("Batch Processing Controls", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            batch_size = st.number_input(
                "Batch Size",
                min_value=1,
                max_value=10,
                value=st.session_state.metadata_config["batch_size"],
                step=1,
                key="batch_size_input_process"
            )
            
            # Update batch size in session state
            st.session_state.metadata_config["batch_size"] = batch_size
        
        with col2:
            retry_delay = st.number_input(
                "Retry Delay (seconds)",
                min_value=1,
                max_value=30,
                value=st.session_state.processing_state.get("retry_delay", 2),
                step=1,
                key="retry_delay_input"
            )
            
            # Update retry delay in session state
            st.session_state.processing_state["retry_delay"] = retry_delay
        
        max_retries = st.number_input(
            "Max Retries",
            min_value=0,
            max_value=5,
            value=st.session_state.processing_state.get("max_retries", 3),
            step=1,
            key="max_retries_input"
        )
        
        # Update max retries in session state
        st.session_state.processing_state["max_retries"] = max_retries
        
        # Processing mode
        processing_mode = st.selectbox(
            "Processing Mode",
            options=["Sequential", "Parallel"],
            index=0,
            key="processing_mode_input"
        )
        
        # Update processing mode in session state
        st.session_state.processing_state["processing_mode"] = processing_mode
    
    # Metadata template management
    with st.expander("Metadata Template Management", expanded=True):
        st.subheader("Save Current Configuration as Template")
        
        template_name = st.text_input(
            "Template Name",
            key="template_name_input"
        )
        
        if st.button("Save Template", key="save_template_button"):
            if template_name:
                # Save template
                if "saved_templates" not in st.session_state:
                    st.session_state.saved_templates = {}
                
                st.session_state.saved_templates[template_name] = {
                    "extraction_method": st.session_state.metadata_config["extraction_method"],
                    "freeform_prompt": st.session_state.metadata_config["freeform_prompt"],
                    "use_template": st.session_state.metadata_config["use_template"],
                    "template_id": st.session_state.metadata_config["template_id"],
                    "custom_fields": st.session_state.metadata_config["custom_fields"],
                    "ai_model": st.session_state.metadata_config["ai_model"],
                    "batch_size": st.session_state.metadata_config["batch_size"],
                    "document_type_prompts": st.session_state.metadata_config.get("document_type_prompts", {}),
                    "document_type_to_template": st.session_state.document_type_to_template if hasattr(st.session_state, "document_type_to_template") else {}
                }
                
                st.success(f"Template '{template_name}' saved successfully")
            else:
                st.error("Please enter a template name")
        
        st.subheader("Load Template")
        
        if "saved_templates" in st.session_state and st.session_state.saved_templates:
            template_options = list(st.session_state.saved_templates.keys())
            selected_template = st.selectbox(
                "Select a template",
                options=template_options,
                key="load_template_selectbox"
            )
            
            if st.button("Load Template", key="load_template_button"):
                # Load template
                template = st.session_state.saved_templates[selected_template]
                
                # Update metadata config
                st.session_state.metadata_config["extraction_method"] = template["extraction_method"]
                st.session_state.metadata_config["freeform_prompt"] = template["freeform_prompt"]
                st.session_state.metadata_config["use_template"] = template["use_template"]
                st.session_state.metadata_config["template_id"] = template["template_id"]
                st.session_state.metadata_config["custom_fields"] = template["custom_fields"]
                st.session_state.metadata_config["ai_model"] = template["ai_model"]
                st.session_state.metadata_config["batch_size"] = template["batch_size"]
                
                if "document_type_prompts" in template:
                    st.session_state.metadata_config["document_type_prompts"] = template["document_type_prompts"]
                
                if "document_type_to_template" in template:
                    st.session_state.document_type_to_template = template["document_type_to_template"]
                
                st.success(f"Template '{selected_template}' loaded successfully")
                st.rerun()
        else:
            st.info("No saved templates yet")
    
    # Process files button
    col1, col2 = st.columns(2)
    
    with col1:
        start_button = st.button("Start Processing", key="start_processing_button", use_container_width=True)
    
    with col2:
        cancel_button = st.button("Cancel Processing", key="cancel_processing_button", use_container_width=True)
    
    # Process files
    if start_button:
        # Reset processing state
        st.session_state.processing_state = {
            "is_processing": True,
            "processed_files": 0,
            "total_files": len(st.session_state.selected_files),
            "current_file_index": -1,
            "current_file": "",
            "results": {},
            "errors": {},
            "retries": {},
            "max_retries": max_retries,
            "retry_delay": retry_delay,
            "processing_mode": processing_mode,
            "visualization_data": {}
        }
        
        # Reset extraction results
        st.session_state.extraction_results = {}
        
        # Process files
        process_files_with_progress(
            st.session_state.selected_files,
            get_extraction_functions(),
            batch_size=batch_size,
            processing_mode=processing_mode
        )
    
    # Cancel processing
    if cancel_button and st.session_state.processing_state.get("is_processing", False):
        st.session_state.processing_state["is_processing"] = False
        st.warning("Processing cancelled")
    
    # Display processing progress
    if st.session_state.processing_state.get("is_processing", False):
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Update progress
        processed_files = st.session_state.processing_state["processed_files"]
        total_files = st.session_state.processing_state["total_files"]
        current_file = st.session_state.processing_state["current_file"]
        
        # Calculate progress
        progress = processed_files / total_files if total_files > 0 else 0
        
        # Update progress bar
        progress_bar.progress(progress)
        
        # Update status text
        if current_file:
            status_text.text(f"Processing {current_file}... ({processed_files}/{total_files})")
        else:
            status_text.text(f"Processed {processed_files}/{total_files} files")
    
    # Display processing results
    if "results" in st.session_state.processing_state and st.session_state.processing_state["results"]:
        st.write("### Processing Results")
        
        # Display success message
        processed_files = len(st.session_state.processing_state["results"])
        error_files = len(st.session_state.processing_state["errors"]) if "errors" in st.session_state.processing_state else 0
        
        if error_files == 0:
            st.success(f"Processing complete! Successfully processed {processed_files} files.")
        else:
            st.warning(f"Processing complete! Successfully processed {processed_files} files with {error_files} errors.")
        
        # Display errors if any
        if "errors" in st.session_state.processing_state and st.session_state.processing_state["errors"]:
            st.write("### Errors")
            
            for file_id, error in st.session_state.processing_state["errors"].items():
                # Find file name
                file_name = ""
                for file in st.session_state.selected_files:
                    if file["id"] == file_id:
                        file_name = file["name"]
                        break
                
                st.error(f"{file_name}: {error}")
        
        # Continue button
        st.write("---")
        if st.button("Continue to View Results", key="continue_to_results_button", use_container_width=True):
            st.session_state.current_page = "View Results"
            st.rerun()

def process_files_with_progress(files, extraction_functions, batch_size=5, processing_mode="Sequential"):
    """
    Process files with progress tracking
    
    Args:
        files: List of files to process
        extraction_functions: Dictionary of extraction functions
        batch_size: Number of files to process in parallel
        processing_mode: Processing mode (Sequential or Parallel)
    """
    # Check if already processing
    if not st.session_state.processing_state.get("is_processing", False):
        return
    
    # Get total files
    total_files = len(files)
    st.session_state.processing_state["total_files"] = total_files
    
    # Process files
    if processing_mode == "Parallel":
        # Process files in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Submit tasks
            future_to_file = {}
            for file in files:
                future = executor.submit(process_single_file, file, extraction_functions)
                future_to_file[future] = file
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                
                try:
                    result = future.result()
                    
                    # Update processing state
                    st.session_state.processing_state["processed_files"] += 1
                    st.session_state.processing_state["current_file"] = ""
                    
                    # Store result
                    if result["success"]:
                        st.session_state.processing_state["results"][file["id"]] = result["data"]
                        st.session_state.extraction_results[file["id"]] = result["data"]
                    else:
                        st.session_state.processing_state["errors"][file["id"]] = result["error"]
                
                except Exception as e:
                    # Update processing state
                    st.session_state.processing_state["processed_files"] += 1
                    st.session_state.processing_state["current_file"] = ""
                    
                    # Store error
                    st.session_state.processing_state["errors"][file["id"]] = str(e)
    else:
        # Process files sequentially
        for i, file in enumerate(files):
            # Check if processing was cancelled
            if not st.session_state.processing_state.get("is_processing", False):
                break
            
            # Update processing state
            st.session_state.processing_state["current_file_index"] = i
            st.session_state.processing_state["current_file"] = file["name"]
            
            try:
                # Process file
                result = process_single_file(file, extraction_functions)
                
                # Update processing state
                st.session_state.processing_state["processed_files"] += 1
                
                # Store result
                if result["success"]:
                    st.session_state.processing_state["results"][file["id"]] = result["data"]
                    st.session_state.extraction_results[file["id"]] = result["data"]
                else:
                    st.session_state.processing_state["errors"][file["id"]] = result["error"]
            
            except Exception as e:
                # Update processing state
                st.session_state.processing_state["processed_files"] += 1
                
                # Store error
                st.session_state.processing_state["errors"][file["id"]] = str(e)
    
    # Mark processing as complete
    st.session_state.processing_state["is_processing"] = False
    st.session_state.processing_state["current_file"] = ""
    
    # Rerun to update UI
    st.rerun()

def process_single_file(file, extraction_functions):
    """
    Process a single file
    
    Args:
        file: File to process
        extraction_functions: Dictionary of extraction functions
        
    Returns:
        dict: Processing result
    """
    try:
        # Get file ID and name
        file_id = file["id"]
        file_name = file["name"]
        
        # Log processing start
        if DEBUG_MODE:
            logger.info(f"Processing file: {file_name} ({file_id})")
        
        # Get document type if available
        document_type = None
        if (hasattr(st.session_state, "document_categorization") and 
            "results" in st.session_state.document_categorization and 
            file_id in st.session_state.document_categorization["results"]):
            document_type = st.session_state.document_categorization["results"][file_id]["document_type"]
        
        # Get extraction method
        extraction_method = st.session_state.metadata_config["extraction_method"]
        
        # Get extraction function
        if extraction_method == "freeform":
            extraction_func = extraction_functions["freeform"]
        else:
            extraction_func = extraction_functions["structured"]
        
        # Check if using document type templates
        use_document_type_template = (
            document_type is not None and 
            hasattr(st.session_state, "document_type_to_template") and 
            document_type in st.session_state.document_type_to_template and 
            st.session_state.document_type_to_template[document_type] is not None and 
            st.session_state.document_type_to_template[document_type] != ""
        )
        
        # Get template ID
        template_id = None
        if use_document_type_template:
            template_id = st.session_state.document_type_to_template[document_type]
        elif st.session_state.metadata_config["use_template"]:
            template_id = st.session_state.metadata_config["template_id"]
        
        # Get AI model
        ai_model = st.session_state.metadata_config["ai_model"]
        
        # Get prompt for freeform extraction
        prompt = None
        if extraction_method == "freeform":
            # Check if using document type specific prompt
            if (document_type is not None and 
                "document_type_prompts" in st.session_state.metadata_config and 
                document_type in st.session_state.metadata_config["document_type_prompts"]):
                prompt = st.session_state.metadata_config["document_type_prompts"][document_type]
            else:
                prompt = st.session_state.metadata_config["freeform_prompt"]
        
        # Get custom fields for structured extraction
        custom_fields = None
        if extraction_method == "structured" and not template_id:
            custom_fields = st.session_state.metadata_config["custom_fields"]
        
        # Extract metadata
        if extraction_method == "freeform":
            result = extraction_func(
                st.session_state.client,
                file_id,
                prompt=prompt,
                ai_model=ai_model
            )
        else:
            result = extraction_func(
                st.session_state.client,
                file_id,
                template_id=template_id,
                custom_fields=custom_fields,
                ai_model=ai_model
            )
        
        # Log processing result
        if DEBUG_MODE:
            logger.info(f"Processed file: {file_name} ({file_id}) - Success")
        
        # Return result
        return {
            "success": True,
            "data": result
        }
    
    except Exception as e:
        # Log error
        logger.error(f"Error processing file {file['name']} ({file['id']}): {str(e)}")
        
        # Return error
        return {
            "success": False,
            "error": str(e)
        }

def get_extraction_functions():
    """
    Get extraction functions based on configuration
    
    Returns:
        dict: Dictionary of extraction functions
    """
    try:
        # Import extraction functions
        from modules.metadata_extraction import extract_metadata_freeform, extract_metadata_structured
        
        # Return functions
        return {
            "freeform": extract_metadata_freeform,
            "structured": extract_metadata_structured
        }
    except ImportError as e:
        logger.error(f"Error importing extraction functions: {str(e)}")
        st.error(f"Error importing extraction functions: {str(e)}")
        return {
            "freeform": lambda client, file_id, **kwargs: {"error": "Extraction function not available"},
            "structured": lambda client, file_id, **kwargs: {"error": "Extraction function not available"}
        }
