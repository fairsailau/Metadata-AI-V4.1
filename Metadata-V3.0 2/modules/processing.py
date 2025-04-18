import streamlit as st
import time
import uuid
import logging
from typing import Dict, Any, List, Optional, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from .metadata_extraction import extract_metadata_structured, extract_metadata_freeform

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Debug mode flag
DEBUG_MODE = True

def debug_log(message, data=None):
    """Log debug messages if debug mode is enabled"""
    if DEBUG_MODE:
        if data:
            logger.info(f"{message}: {data}")
        else:
            logger.info(message)

def get_extraction_functions():
    """
    Get the appropriate metadata extraction functions based on the configured extraction type
    """
    # Check if using document type templates
    if st.session_state.metadata_config.get("use_document_type_templates", False):
        debug_log("Using document type templates for extraction")
        return {
            "structured": extract_metadata_structured,
            "freeform": extract_metadata_freeform
        }
    
    # Default extraction functions
    extraction_type = st.session_state.metadata_config.get("extraction_type", "structured")
    debug_log(f"Using extraction type: {extraction_type}")
    
    if extraction_type == "structured":
        return {
            "structured": extract_metadata_structured
        }
    elif extraction_type == "freeform":
        return {
            "freeform": extract_metadata_freeform
        }
    else:
        return {
            "structured": extract_metadata_structured,
            "freeform": extract_metadata_freeform
        }

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
        if st.button("Go to File Browser", key="go_to_file_browser"):
            st.session_state.current_page = "File Browser"
            st.rerun()
        return
    
    # Initialize processing state if not exists
    if "processing_state" not in st.session_state:
        st.session_state.processing_state = {
            "is_processing": False,
            "is_cancelled": False,
            "processed_files": 0,
            "total_files": 0,
            "results": {},
            "errors": {}
        }
    
    st.write(f"Ready to process {len(st.session_state.selected_files)} files using the configured metadata extraction parameters.")
    
    # Batch processing controls
    with st.expander("Batch Processing Controls", expanded=True):
        batch_size = st.number_input("Batch Size", min_value=1, max_value=20, value=5, key="batch_size_input")
        
        col1, col2 = st.columns(2)
        with col1:
            retry_delay = st.number_input("Retry Delay (seconds)", min_value=1, max_value=60, value=2, key="retry_delay_input")
        
        with col2:
            max_retries = st.number_input("Max Retries", min_value=0, max_value=10, value=3, key="max_retries_input")
        
        processing_mode = st.selectbox(
            "Processing Mode",
            options=["Sequential", "Parallel"],
            index=0,
            key="processing_mode_input"
        )
    
    # Template management
    with st.expander("Metadata Template Management", expanded=True):
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
            # Ensure template_options is a dictionary or None, not a list
            template_options = st.session_state.metadata_templates
            if template_options and isinstance(template_options, dict):
                selected_template = st.selectbox(
                    "Select Template",
                    options=list(template_options.keys()),
                    key="load_template_select"
                )
                
                if st.button("Load Template", key="load_template_button"):
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
                st.error(f"Error processing files: {str(e)}")
                debug_log(f"Error in process_files_with_progress: {str(e)}")
                st.session_state.processing_state["is_processing"] = False
    
    # Display results after processing
    if not st.session_state.processing_state["is_processing"] and st.session_state.processing_state["processed_files"] > 0:
        # Display success message
        num_processed = st.session_state.processing_state["processed_files"]
        num_errors = len(st.session_state.processing_state["errors"])
        num_total = st.session_state.processing_state["total_files"]
        
        if num_errors == 0:
            st.success(f"Processing complete! Successfully processed {num_processed} files.")
        else:
            st.warning(f"Processing complete! Successfully processed {num_processed - num_errors} files with {num_errors} errors.")
        
        # Display errors if any
        if num_errors > 0:
            st.error("The following errors occurred during processing:")
            for file_id, error_info in st.session_state.processing_state["errors"].items():
                st.error(f"{error_info['file_name']}: {error_info['error']}")
        
        # Continue button
        if st.button("View Results", key="view_results_button"):
            st.session_state.current_page = "View Results"
            st.rerun()

def process_files_with_progress(
    extraction_functions: Dict[str, Callable],
    progress_bar,
    status_text,
    batch_size: int = 5,
    retry_delay: int = 2,
    max_retries: int = 3,
    processing_mode: str = "Sequential"
):
    """
    Process files with progress tracking
    
    Args:
        extraction_functions: Dictionary of extraction functions
        progress_bar: Streamlit progress bar
        status_text: Streamlit text element for status updates
        batch_size: Number of files to process in each batch
        retry_delay: Delay between retries in seconds
        max_retries: Maximum number of retries for failed operations
        processing_mode: Processing mode (Sequential or Parallel)
    """
    debug_log("Starting process_files_with_progress")
    
    # Get selected files
    files = st.session_state.selected_files
    total_files = len(files)
    
    # Update processing state
    st.session_state.processing_state["total_files"] = total_files
    
    # Process files in batches
    processed_count = 0
    
    # Create batches
    batches = [files[i:i + batch_size] for i in range(0, len(files), batch_size)]
    
    # Process each batch
    for batch_index, batch in enumerate(batches):
        # Check if processing is cancelled
        if st.session_state.processing_state["is_cancelled"]:
            debug_log("Processing cancelled by user")
            status_text.info("Processing cancelled by user.")
            break
        
        # Update status
        batch_num = batch_index + 1
        total_batches = len(batches)
        status_text.info(f"Processing batch {batch_num}/{total_batches}...")
        
        # Process batch
        if processing_mode == "Parallel":
            debug_log(f"Processing batch {batch_num} in parallel mode")
            process_batch_parallel(batch, extraction_functions, max_retries, retry_delay)
        else:
            debug_log(f"Processing batch {batch_num} in sequential mode")
            process_batch_sequential(batch, extraction_functions, max_retries, retry_delay, status_text)
        
        # Update processed count
        processed_count += len(batch)
        st.session_state.processing_state["processed_files"] = processed_count
        
        # Update progress
        progress = min(processed_count / total_files, 1.0)
        progress_bar.progress(progress)
    
    # Complete processing
    debug_log("File processing completed")
    progress_bar.progress(1.0)
    status_text.info("Processing complete!")
    
    # Update processing state
    st.session_state.processing_state["is_processing"] = False

def process_batch_sequential(
    batch: List[Dict[str, Any]],
    extraction_functions: Dict[str, Callable],
    max_retries: int,
    retry_delay: int,
    status_text
):
    """
    Process a batch of files sequentially
    
    Args:
        batch: List of files to process
        extraction_functions: Dictionary of extraction functions
        max_retries: Maximum number of retries for failed operations
        retry_delay: Delay between retries in seconds
        status_text: Streamlit text element for status updates
    """
    for file in batch:
        # Check if processing is cancelled
        if st.session_state.processing_state["is_cancelled"]:
            break
        
        file_id = file["id"]
        file_name = file["name"]
        
        # Update status
        status_text.info(f"Retrying {file_name} in {retry_delay} seconds...")
        
        # Process file with retries
        for retry in range(max_retries + 1):
            try:
                # Process file
                debug_log(f"Processing file {file_name} (attempt {retry + 1})")
                result = process_single_file(file, extraction_functions)
                
                # Store result
                st.session_state.processing_state["results"][file_id] = result
                
                # Success, break retry loop
                break
            except Exception as e:
                debug_log(f"Error processing file {file_name} (attempt {retry + 1}): {str(e)}")
                
                # Check if this was the last retry
                if retry == max_retries:
                    # Store error
                    st.session_state.processing_state["errors"][file_id] = {
                        "file_id": file_id,
                        "file_name": file_name,
                        "error": str(e)
                    }
                else:
                    # Wait before retrying
                    time.sleep(retry_delay)

def process_batch_parallel(
    batch: List[Dict[str, Any]],
    extraction_functions: Dict[str, Callable],
    max_retries: int,
    retry_delay: int
):
    """
    Process a batch of files in parallel
    
    Args:
        batch: List of files to process
        extraction_functions: Dictionary of extraction functions
        max_retries: Maximum number of retries for failed operations
        retry_delay: Delay between retries in seconds
    """
    with ThreadPoolExecutor() as executor:
        # Submit all files for processing
        future_to_file = {
            executor.submit(
                process_single_file_with_retry,
                file,
                extraction_functions,
                max_retries,
                retry_delay
            ): file for file in batch
        }
        
        # Process results as they complete
        for future in as_completed(future_to_file):
            file = future_to_file[future]
            file_id = file["id"]
            file_name = file["name"]
            
            try:
                # Get result
                result = future.result()
                
                # Store result
                st.session_state.processing_state["results"][file_id] = result
            except Exception as e:
                debug_log(f"Error processing file {file_name}: {str(e)}")
                
                # Store error
                st.session_state.processing_state["errors"][file_id] = {
                    "file_id": file_id,
                    "file_name": file_name,
                    "error": str(e)
                }

def process_single_file_with_retry(
    file: Dict[str, Any],
    extraction_functions: Dict[str, Callable],
    max_retries: int,
    retry_delay: int
) -> Dict[str, Any]:
    """
    Process a single file with retry logic
    
    Args:
        file: File to process
        extraction_functions: Dictionary of extraction functions
        max_retries: Maximum number of retries for failed operations
        retry_delay: Delay between retries in seconds
        
    Returns:
        dict: Processing result
    """
    file_id = file["id"]
    file_name = file["name"]
    
    # Process file with retries
    for retry in range(max_retries + 1):
        try:
            # Process file
            debug_log(f"Processing file {file_name} (attempt {retry + 1})")
            result = process_single_file(file, extraction_functions)
            
            # Success, return result
            return result
        except Exception as e:
            debug_log(f"Error processing file {file_name} (attempt {retry + 1}): {str(e)}")
            
            # Check if this was the last retry
            if retry == max_retries:
                # Raise exception to be caught by caller
                raise
            else:
                # Wait before retrying
                time.sleep(retry_delay)

def process_single_file(
    file: Dict[str, Any],
    extraction_functions: Dict[str, Callable]
) -> Dict[str, Any]:
    """
    Process a single file
    
    Args:
        file: File to process
        extraction_functions: Dictionary of extraction functions
        
    Returns:
        dict: Processing result
    """
    file_id = file["id"]
    file_name = file["name"]
    
    debug_log(f"Processing file {file_name}")
    
    # Get document type if available
    document_type = None
    if "document_categorization" in st.session_state and st.session_state.document_categorization["is_categorized"]:
        if file_id in st.session_state.document_categorization["results"]:
            document_type = st.session_state.document_categorization["results"][file_id]["document_type"]
    
    # Get extraction parameters
    extraction_params = {}
    
    # Check if using document type templates
    if st.session_state.metadata_config.get("use_document_type_templates", False) and document_type:
        # Get template for document type
        if "document_type_templates" in st.session_state.metadata_config:
            templates = st.session_state.metadata_config["document_type_templates"]
            if document_type in templates:
                extraction_params = templates[document_type]
    
    # Use default parameters if no document type template
    if not extraction_params:
        extraction_params = {
            "extraction_type": st.session_state.metadata_config.get("extraction_type", "structured"),
            "fields": st.session_state.metadata_config.get("fields", []),
            "prompt": st.session_state.metadata_config.get("prompt", "")
        }
    
    # Extract metadata
    extraction_type = extraction_params.get("extraction_type", "structured")
    
    result = {
        "file_id": file_id,
        "file_name": file_name,
        "document_type": document_type,
        "extraction_type": extraction_type,
        "metadata": {}
    }
    
    # Call appropriate extraction function
    if extraction_type == "structured" and "structured" in extraction_functions:
        fields = extraction_params.get("fields", [])
        result["metadata"] = extraction_functions["structured"](
            st.session_state.client,
            file_id,
            fields
        )
    elif extraction_type == "freeform" and "freeform" in extraction_functions:
        prompt = extraction_params.get("prompt", "")
        result["metadata"] = extraction_functions["freeform"](
            st.session_state.client,
            file_id,
            prompt
        )
    else:
        raise ValueError(f"Unsupported extraction type: {extraction_type}")
    
    return result
