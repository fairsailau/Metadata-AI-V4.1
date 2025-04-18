import streamlit as st
import logging
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Debug mode flag
DEBUG_MODE = True

def debug_log(message, data=None):
    """
    Log debug information if debug mode is enabled
    """
    if DEBUG_MODE:
        if data:
            logger.info(f"DEBUG: {message} - {json.dumps(data, default=str)}")
        else:
            logger.info(f"DEBUG: {message}")

def generate_unique_key(base_key):
    """
    Generate a unique key for Streamlit elements to avoid duplicate IDs
    """
    return f"{base_key}_{uuid.uuid4().hex[:8]}"

def process_files():
    """
    Process files page
    """
    st.title("Process Files")
    
    if not st.session_state.authenticated or not st.session_state.client:
        st.error("Please authenticate with Box first")
        return
    
    if not st.session_state.selected_files:
        st.warning("No files selected. Please select files in the File Browser first.")
        if st.button("Go to File Browser", key=generate_unique_key("go_to_file_browser")):
            st.session_state.current_page = "File Browser"
            st.rerun()
        return
    
    # Display selected files
    num_files = len(st.session_state.selected_files)
    st.write(f"Ready to process {num_files} files using the configured metadata extraction parameters.")
    
    # Batch processing controls
    with st.expander("Batch Processing Controls", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Batch Size")
            batch_size = st.number_input(
                "",
                min_value=1,
                max_value=10,
                value=st.session_state.metadata_config.get("batch_size", 5),
                key=generate_unique_key("batch_size_input")
            )
            st.session_state.metadata_config["batch_size"] = batch_size
        
        with col2:
            st.write("Retry Delay (seconds)")
            retry_delay = st.number_input(
                "",
                min_value=1,
                max_value=60,
                value=2,
                key=generate_unique_key("retry_delay_input")
            )
        
        st.write("Max Retries")
        max_retries = st.number_input(
            "",
            min_value=1,
            max_value=10,
            value=3,
            key=generate_unique_key("max_retries_input")
        )
        
        st.write("Processing Mode")
        processing_mode = st.selectbox(
            "",
            options=["Sequential", "Parallel"],
            index=0,
            key=generate_unique_key("processing_mode_input")
        )
        st.session_state.processing_state["processing_mode"] = processing_mode
    
    # Metadata Template Management
    with st.expander("Metadata Template Management", expanded=True):
        st.write("#### Save Current Configuration as Template")
        template_name = st.text_input("Template Name", key=generate_unique_key("save_template_name_input"))
        
        if st.button("Save Template", key=generate_unique_key("save_template_button")):
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
            # Ensure template_options is a dictionary or None, not a list
            template_options = st.session_state.metadata_templates
            if template_options and isinstance(template_options, dict):
                selected_template = st.selectbox(
                    "Select Template",
                    options=list(template_options.keys()),
                    key=generate_unique_key("load_template_select")
                )
                
                if st.button("Load Template", key=generate_unique_key("load_template_button")):
                    st.session_state.metadata_config = st.session_state.metadata_templates[selected_template].copy()
                    st.success(f"Template '{selected_template}' loaded successfully!")
            else:
                st.info("No valid templates available")
        else:
            st.info("No saved templates yet")
    
    # Process files button
    col1, col2 = st.columns(2)
    
    with col1:
        start_button = st.button(
            "Start Processing",
            disabled=st.session_state.processing_state["is_processing"],
            use_container_width=True,
            key=generate_unique_key("start_processing_button")
        )
    
    with col2:
        cancel_button = st.button(
            "Cancel Processing",
            disabled=not st.session_state.processing_state["is_processing"],
            use_container_width=True,
            key=generate_unique_key("cancel_processing_button")
        )
    
    # Progress tracking
    progress_container = st.container()
    
    # Get metadata extraction functions
    extraction_functions = get_extraction_functions()
    
    # Process files
    if start_button:
        debug_log("Start button clicked, initializing processing")
        # Update processing state
        st.session_state.processing_state["is_processing"] = True
        st.session_state.processing_state["is_cancelled"] = False
        st.session_state.processing_state["processed_files"] = 0
        st.session_state.processing_state["total_files"] = len(st.session_state.selected_files)
        st.session_state.processing_state["results"] = {}
        st.session_state.processing_state["errors"] = {}
        
        # Rerun to update UI
        st.rerun()
    
    # Cancel processing
    if cancel_button:
        st.session_state.processing_state["is_cancelled"] = True
        st.info("Cancelling processing... Please wait for current operations to complete.")
    
    # Display progress
    if st.session_state.processing_state["is_processing"]:
        with progress_container:
            # Create progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Process files
            try:
                debug_log("Starting file processing with parameters", {
                    "batch_size": batch_size,
                    "retry_delay": retry_delay,
                    "max_retries": max_retries,
                    "processing_mode": processing_mode
                })
                process_files_with_progress(
                    extraction_functions,
                    progress_bar,
                    status_text,
                    batch_size,
                    retry_delay,
                    max_retries,
                    processing_mode
                )
            except Exception as e:
                logger.error(f"Error processing files: {str(e)}")
                st.error(f"Error processing files: {str(e)}")
                st.session_state.processing_state["is_processing"] = False
                st.session_state.processing_state["is_cancelled"] = False
            
            # Update UI after processing
            if not st.session_state.processing_state["is_cancelled"]:
                num_processed = len(st.session_state.processing_state["results"])
                num_errors = len(st.session_state.processing_state["errors"])
                
                if num_errors == 0:
                    st.success(f"Processing complete! Successfully processed {num_processed} files.")
                else:
                    st.warning(f"Processing complete! Successfully processed {num_processed} files with {num_errors} errors.")
                
                # Reset processing state
                st.session_state.processing_state["is_processing"] = False
                
                # Show continue button
                if st.button("View Results", use_container_width=True, key=generate_unique_key("view_results_button")):
                    st.session_state.current_page = "View Results"
                    st.rerun()
            else:
                st.warning("Processing cancelled.")
                st.session_state.processing_state["is_processing"] = False
                st.session_state.processing_state["is_cancelled"] = False
                st.rerun()

def get_extraction_functions():
    """
    Get the appropriate metadata extraction functions based on the configuration
    """
    debug_log("Getting extraction functions")
    try:
        from modules.metadata_extraction import extract_metadata_structured, extract_metadata_freeform
        
        # Check if using document type templates
        if st.session_state.metadata_config.get("use_document_type_templates", False):
            debug_log("Using document type templates")
            # Return a function that selects the appropriate extraction method based on document type
            return {
                "extract": extract_metadata_by_document_type,
                "apply": apply_metadata_by_document_type
            }
        else:
            # Use the configured extraction method
            if st.session_state.metadata_config["extraction_method"] == "structured":
                debug_log("Using structured extraction")
                return {
                    "extract": extract_metadata_structured,
                    "apply": apply_metadata_structured
                }
            else:
                debug_log("Using freeform extraction")
                return {
                    "extract": extract_metadata_freeform,
                    "apply": apply_metadata_freeform
                }
    except ImportError as e:
        logger.error(f"Import error in get_extraction_functions: {str(e)}")
        st.error(f"Failed to import required modules: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_extraction_functions: {str(e)}")
        st.error(f"Unexpected error: {str(e)}")
        return None

def extract_metadata_by_document_type(file_id: str) -> Dict[str, Any]:
    """
    Extract metadata based on document type
    """
    debug_log(f"Extracting metadata by document type for file {file_id}")
    from modules.metadata_extraction import extract_metadata_structured, extract_metadata_freeform
    
    # Get document type from categorization results
    document_type = "Other"  # Default
    if "document_categorization" in st.session_state and st.session_state.document_categorization["is_categorized"]:
        if file_id in st.session_state.document_categorization["results"]:
            document_type = st.session_state.document_categorization["results"][file_id]["document_type"]
    
    debug_log(f"Document type for file {file_id}: {document_type}")
    
    # Get template for document type
    template = None
    if "document_type_to_template" in st.session_state:
        template = st.session_state.document_type_to_template.get(document_type)
    
    # Get freeform prompt for document type
    freeform_prompt = None
    if "document_type_to_freeform_prompt" in st.session_state:
        freeform_prompt = st.session_state.document_type_to_freeform_prompt.get(document_type)
    
    # Extract metadata based on template or freeform prompt
    if template:
        debug_log(f"Using template for document type {document_type}", template)
        # Use structured extraction with template
        result = extract_metadata_structured(
            file_id,
            use_template=True,
            template_id=template["templateKey"],
            template_scope=template.get("scope", "enterprise"),
            custom_fields=None,
            ai_model=st.session_state.metadata_config["ai_model"]
        )
        result["document_type"] = document_type
        result["extraction_method"] = "structured"
        result["template_id"] = template["templateKey"]
        return result
    else:
        debug_log(f"Using freeform prompt for document type {document_type}")
        # Use freeform extraction with prompt
        prompt = freeform_prompt if freeform_prompt else st.session_state.metadata_config["freeform_prompt"]
        result = extract_metadata_freeform(
            file_id,
            prompt=prompt,
            ai_model=st.session_state.metadata_config["ai_model"]
        )
        result["document_type"] = document_type
        result["extraction_method"] = "freeform"
        return result

def apply_metadata_by_document_type(file_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply metadata based on document type
    """
    debug_log(f"Applying metadata by document type for file {file_id}")
    from modules.metadata_extraction import apply_metadata_structured, apply_metadata_freeform
    
    # Apply metadata based on extraction method
    if metadata.get("extraction_method") == "structured":
        debug_log("Using structured application method")
        return apply_metadata_structured(
            file_id,
            metadata,
            use_template=True,
            template_id=metadata.get("template_id"),
            template_scope=metadata.get("template_scope", "enterprise")
        )
    else:
        debug_log("Using freeform application method")
        return apply_metadata_freeform(file_id, metadata)

def extract_metadata_structured(file_id: str) -> Dict[str, Any]:
    """
    Extract metadata using structured extraction
    """
    debug_log(f"Extracting structured metadata for file {file_id}")
    from modules.metadata_extraction import extract_metadata_structured as extract_func
    
    return extract_func(
        file_id,
        use_template=st.session_state.metadata_config["use_template"],
        template_id=st.session_state.metadata_config.get("template_id"),
        template_scope=st.session_state.metadata_config.get("template_scope", "enterprise"),
        custom_fields=st.session_state.metadata_config.get("custom_fields"),
        ai_model=st.session_state.metadata_config["ai_model"]
    )

def apply_metadata_structured(file_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply metadata using structured extraction
    """
    debug_log(f"Applying structured metadata for file {file_id}")
    from modules.metadata_extraction import apply_metadata_structured as apply_func
    
    return apply_func(
        file_id,
        metadata,
        use_template=st.session_state.metadata_config["use_template"],
        template_id=st.session_state.metadata_config.get("template_id"),
        template_scope=st.session_state.metadata_config.get("template_scope", "enterprise")
    )

def extract_metadata_freeform(file_id: str) -> Dict[str, Any]:
    """
    Extract metadata using freeform extraction
    """
    debug_log(f"Extracting freeform metadata for file {file_id}")
    from modules.metadata_extraction import extract_metadata_freeform as extract_func
    
    return extract_func(
        file_id,
        prompt=st.session_state.metadata_config["freeform_prompt"],
        ai_model=st.session_state.metadata_config["ai_model"]
    )

def apply_metadata_freeform(file_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply metadata using freeform extraction
    """
    debug_log(f"Applying freeform metadata for file {file_id}")
    from modules.metadata_extraction import apply_metadata_freeform as apply_func
    
    return apply_func(file_id, metadata)

def process_files_with_progress(
    extraction_functions: Dict[str, Any],
    progress_bar,
    status_text,
    batch_size: int,
    retry_delay: int,
    max_retries: int,
    processing_mode: str
):
    """
    Process files with progress tracking
    """
    debug_log("Processing files with progress tracking")
    # Get files to process
    files = st.session_state.selected_files
    total_files = len(files)
    
    # Process files
    if processing_mode == "Sequential":
        debug_log("Using sequential processing mode")
        process_files_sequential(
            files,
            extraction_functions,
            progress_bar,
            status_text,
            batch_size,
            retry_delay,
            max_retries
        )
    else:
        debug_log("Using parallel processing mode")
        process_files_parallel(
            files,
            extraction_functions,
            progress_bar,
            status_text,
            batch_size,
            retry_delay,
            max_retries
        )

def process_files_sequential(
    files: List[Dict[str, Any]],
    extraction_functions: Dict[str, Any],
    progress_bar,
    status_text,
    batch_size: int,
    retry_delay: int,
    max_retries: int
):
    """
    Process files sequentially
    """
    debug_log("Processing files sequentially")
    total_files = len(files)
    processed_files = 0
    
    # Process files in batches
    for i in range(0, total_files, batch_size):
        # Check if processing is cancelled
        if st.session_state.processing_state["is_cancelled"]:
            debug_log("Processing cancelled")
            break
        
        # Get batch of files
        batch = files[i:i+batch_size]
        
        # Process each file in batch
        for file in batch:
            # Check if processing is cancelled
            if st.session_state.processing_state["is_cancelled"]:
                debug_log("Processing cancelled")
                break
            
            # Get file info
            file_id = file["id"]
            file_name = file["name"]
            
            # Update status
            status_text.text(f"Processing {file_name}...")
            debug_log(f"Processing file {file_name} (ID: {file_id})")
            
            # Process file with retries
            for retry in range(max_retries):
                try:
                    # Extract metadata
                    metadata = extraction_functions["extract"](file_id)
                    
                    # Store result
                    st.session_state.processing_state["results"][file_id] = {
                        "file_id": file_id,
                        "file_name": file_name,
                        "metadata": metadata,
                        "is_applied": False
                    }
                    
                    # Update processed files count
                    processed_files += 1
                    st.session_state.processing_state["processed_files"] = processed_files
                    
                    # Update progress
                    progress = processed_files / total_files
                    progress_bar.progress(progress)
                    
                    # Break retry loop
                    break
                except Exception as e:
                    logger.error(f"Error processing file {file_name} (attempt {retry+1}/{max_retries}): {str(e)}")
                    
                    # Return error on last retry
                    if retry == max_retries - 1:
                        # Store error
                        st.session_state.processing_state["errors"][file_id] = {
                            "file_id": file_id,
                            "file_name": file_name,
                            "error": str(e)
                        }
                        
                        # Update processed files count
                        processed_files += 1
                        st.session_state.processing_state["processed_files"] = processed_files
                        
                        # Update progress
                        progress = processed_files / total_files
                        progress_bar.progress(progress)
                    else:
                        # Wait before retrying
                        time.sleep(retry_delay)

def process_files_parallel(
    files: List[Dict[str, Any]],
    extraction_functions: Dict[str, Any],
    progress_bar,
    status_text,
    batch_size: int,
    retry_delay: int,
    max_retries: int
):
    """
    Process files in parallel
    """
    debug_log("Processing files in parallel")
    total_files = len(files)
    processed_files = 0
    
    # Process files in batches
    for i in range(0, total_files, batch_size):
        # Check if processing is cancelled
        if st.session_state.processing_state["is_cancelled"]:
            debug_log("Processing cancelled")
            break
        
        # Get batch of files
        batch = files[i:i+batch_size]
        
        # Update status
        status_text.text(f"Processing batch {i//batch_size + 1}/{(total_files + batch_size - 1)//batch_size}...")
        
        # Process batch in parallel
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Submit tasks
            future_to_file = {
                executor.submit(
                    process_file_with_retries, 
                    file, 
                    extraction_functions, 
                    retry_delay, 
                    max_retries
                ): file for file in batch
            }
            
            # Process results as they complete
            for future in as_completed(future_to_file):
                # Check if processing is cancelled
                if st.session_state.processing_state["is_cancelled"]:
                    executor.shutdown(wait=False)
                    debug_log("Processing cancelled")
                    break
                
                file = future_to_file[future]
                file_id = file["id"]
                file_name = file["name"]
                
                try:
                    # Get result
                    result = future.result()
                    
                    if "error" in result:
                        # Store error
                        st.session_state.processing_state["errors"][file_id] = {
                            "file_id": file_id,
                            "file_name": file_name,
                            "error": result["error"]
                        }
                    else:
                        # Store result
                        st.session_state.processing_state["results"][file_id] = {
                            "file_id": file_id,
                            "file_name": file_name,
                            "metadata": result["metadata"],
                            "is_applied": False
                        }
                    
                    # Update processed files count
                    processed_files += 1
                    st.session_state.processing_state["processed_files"] = processed_files
                    
                    # Update progress
                    progress = processed_files / total_files
                    progress_bar.progress(progress)
                except Exception as e:
                    logger.error(f"Unexpected error processing file {file_name}: {str(e)}")
                    
                    # Store error
                    st.session_state.processing_state["errors"][file_id] = {
                        "file_id": file_id,
                        "file_name": file_name,
                        "error": str(e)
                    }
                    
                    # Update processed files count
                    processed_files += 1
                    st.session_state.processing_state["processed_files"] = processed_files
                    
                    # Update progress
                    progress = processed_files / total_files
                    progress_bar.progress(progress)

def process_file_with_retries(
    file: Dict[str, Any],
    extraction_functions: Dict[str, Any],
    retry_delay: int,
    max_retries: int
) -> Dict[str, Any]:
    """
    Process a file with retries
    """
    file_id = file["id"]
    file_name = file["name"]
    debug_log(f"Processing file with retries: {file_name} (ID: {file_id})")
    
    # Process file with retries
    for retry in range(max_retries):
        try:
            # Extract metadata
            metadata = extraction_functions["extract"](file_id)
            
            # Return result
            debug_log(f"Successfully processed file: {file_name}")
            return {
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"Error processing file {file_name} (attempt {retry+1}/{max_retries}): {str(e)}")
            
            # Return error on last retry
            if retry == max_retries - 1:
                debug_log(f"Failed to process file after {max_retries} attempts: {file_name}")
                return {
                    "error": str(e)
                }
            else:
                # Wait before retrying
                time.sleep(retry_delay)
    
    # Should never reach here, but just in case
    return {
        "error": "Maximum retries exceeded"
    }
