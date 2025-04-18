import streamlit as st
import logging
import json
from boxsdk import Client

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_metadata_from_results(extraction_results, file_id):
    """
    Extract metadata from extraction results using multiple approaches
    
    Args:
        extraction_results: Dictionary of extraction results
        file_id: File ID to extract metadata for
        
    Returns:
        dict: Extracted metadata values
    """
    metadata_values = {}
    
    # Try to find direct match in extraction_results
    if file_id in extraction_results and isinstance(extraction_results[file_id], dict):
        result = extraction_results[file_id]
        
        # Try different paths to find metadata
        if "result" in result and result["result"]:
            metadata_values = result["result"]
        elif "api_response" in result and "answer" in result["api_response"]:
            # Try to parse answer as JSON if it's a string
            answer = result["api_response"]["answer"]
            if isinstance(answer, str):
                try:
                    parsed_answer = json.loads(answer)
                    metadata_values = parsed_answer
                except json.JSONDecodeError:
                    metadata_values = {"extracted_text": answer}
            else:
                metadata_values = answer
        else:
            # Use the entire result as metadata
            metadata_values = {k: v for k, v in result.items() 
                              if k not in ["file_id", "file_name"] and not k.startswith("_")}
    
    # If no direct match, look for composite keys
    if not metadata_values:
        for key, result in extraction_results.items():
            # Check if this key contains our file ID
            if isinstance(key, str) and str(file_id) in key:
                # Try to extract metadata from this result
                if isinstance(result, dict):
                    # Try different paths to find metadata
                    if "result" in result:
                        result_data = result["result"]
                        if isinstance(result_data, dict):
                            metadata_values = result_data
                            break
                    elif "api_response" in result and "answer" in result["api_response"]:
                        answer = result["api_response"]["answer"]
                        try:
                            # Try to parse as JSON
                            if isinstance(answer, str):
                                parsed_answer = json.loads(answer)
                                if isinstance(parsed_answer, dict):
                                    metadata_values = parsed_answer
                                    break
                            else:
                                metadata_values = answer
                                break
                        except (json.JSONDecodeError, TypeError):
                            continue
    
    return metadata_values

def apply_metadata_direct():
    """
    Direct approach to apply metadata to Box files with enhanced extraction from multiple sources
    """
    st.title("Apply Metadata")
    
    # Debug checkbox
    debug_mode = st.sidebar.checkbox("Debug Session State", key="debug_checkbox")
    if debug_mode:
        st.sidebar.write("### Session State Debug")
        st.sidebar.write("**Session State Keys:**")
        st.sidebar.write(list(st.session_state.keys()))
        
        if "client" in st.session_state:
            st.sidebar.write("**Client:** Available")
            try:
                user = st.session_state.client.user().get()
                st.sidebar.write(f"**Authenticated as:** {user.name}")
            except Exception as e:
                st.sidebar.write(f"**Client Error:** {str(e)}")
        else:
            st.sidebar.write("**Client:** Not available")
            
        if "extraction_results" in st.session_state:
            st.sidebar.write("**Extraction Results Keys:**")
            st.sidebar.write(list(st.session_state.extraction_results.keys()))
            
            # Dump the first extraction result for debugging
            if st.session_state.extraction_results:
                first_key = next(iter(st.session_state.extraction_results))
                st.sidebar.write(f"**First Extraction Result ({first_key}):**")
                st.sidebar.json(st.session_state.extraction_results[first_key])
    
    # Check if client exists directly
    if 'client' not in st.session_state:
        st.error("Box client not found. Please authenticate first.")
        if st.button("Go to Authentication", key="go_to_auth_btn"):
            st.session_state.current_page = "Home"  # Assuming Home page has authentication
            st.rerun()
        return
    
    # Get client directly
    client = st.session_state.client
    
    # Verify client is working
    try:
        user = client.user().get()
        logger.info(f"Verified client authentication as {user.name}")
        st.success(f"Authenticated as {user.name}")
    except Exception as e:
        logger.error(f"Error verifying client: {str(e)}")
        st.error(f"Authentication error: {str(e)}. Please re-authenticate.")
        if st.button("Go to Authentication", key="go_to_auth_error_btn"):
            st.session_state.current_page = "Home"
            st.rerun()
        return
    
    # Check if extraction results exist
    if "extraction_results" not in st.session_state or not st.session_state.extraction_results:
        st.warning("No extraction results available. Please process files first.")
        if st.button("Go to Process Files", key="go_to_process_files_btn"):
            st.session_state.current_page = "Process Files"
            st.rerun()
        return
    
    # Debug the structure of extraction_results
    extraction_results = st.session_state.extraction_results
    logger.info(f"Extraction results keys: {list(extraction_results.keys())}")
    
    # Extract file IDs and metadata from extraction_results
    available_file_ids = []
    file_id_to_file_name = {}
    file_id_to_metadata = {}
    
    # Check if we have any selected files in session state
    if "selected_files" in st.session_state and st.session_state.selected_files:
        selected_files = st.session_state.selected_files
        logger.info(f"Found {len(selected_files)} selected files in session state")
        for file_info in selected_files:
            if isinstance(file_info, dict) and "id" in file_info and file_info["id"]:
                file_id = file_info["id"]
                file_name = file_info.get("name", "Unknown")
                available_file_ids.append(file_id)
                file_id_to_file_name[file_id] = file_name
                logger.info(f"Added file ID {file_id} from selected_files")
    
    # ENHANCED EXTRACTION FROM EXTRACTION RESULTS
    # This is the key part that has been fixed
    
    # First, try to access extraction_results directly
    for key, result in extraction_results.items():
        logger.info(f"Checking extraction result key: {key}")
        
        # Try to extract file ID from the key
        file_id = None
        
        # Check if the key itself is a file ID (direct match)
        if isinstance(key, str) and key.isdigit():
            file_id = key
        
        # Check if the key contains a file ID in parentheses
        elif isinstance(key, str) and "(" in key and ")" in key:
            # Extract content between parentheses
            start_idx = key.find("(") + 1
            end_idx = key.find(")")
            if start_idx > 0 and end_idx > start_idx:
                potential_id = key[start_idx:end_idx]
                if potential_id.isdigit():
                    file_id = potential_id
                    logger.info(f"Extracted file ID {file_id} from key {key}")
        
        # If we found a file ID, process it
        if file_id:
            if file_id not in available_file_ids:
                available_file_ids.append(file_id)
                
                # Extract file name if available
                if isinstance(result, dict) and "file_name" in result:
                    file_id_to_file_name[file_id] = result["file_name"]
                elif isinstance(key, str) and "(" in key and ")" in key:
                    # Extract file name from the key (everything before the parentheses)
                    file_name = key.split("(")[0].strip()
                    file_id_to_file_name[file_id] = file_name
                
                # Extract metadata using the enhanced function
                metadata_values = extract_metadata_from_results(extraction_results, file_id)
                if metadata_values:
                    file_id_to_metadata[file_id] = metadata_values
                    logger.info(f"Extracted metadata for file ID {file_id}")
                else:
                    # Fallback to using the entire result as metadata
                    file_id_to_metadata[file_id] = result
                    logger.info(f"Using entire result as metadata for file ID {file_id}")
                
                logger.info(f"Added file ID {file_id} from key {key}")
    
    # If we still don't have metadata, try to extract it from the processing state
    if "processing_state" in st.session_state:
        processing_state = st.session_state.processing_state
        
        # Check if we have results in processing_state
        if "results" in processing_state:
            processing_results = processing_state["results"]
            logger.info(f"Found {len(processing_results)} results in processing_state")
            
            for file_id, result in processing_results.items():
                if file_id not in available_file_ids:
                    available_file_ids.append(file_id)
                    
                    # Extract file name if available
                    if "file_name" in result:
                        file_id_to_file_name[file_id] = result["file_name"]
                    
                    # Extract metadata
                    metadata_values = extract_metadata_from_results({"processing_result": result}, file_id)
                    if metadata_values:
                        file_id_to_metadata[file_id] = metadata_values
                        logger.info(f"Extracted metadata from processing_state for file ID {file_id}")
                    else:
                        # Fallback to using the entire result as metadata
                        file_id_to_metadata[file_id] = result
                        logger.info(f"Using entire processing_state result as metadata for file ID {file_id}")
                    
                    logger.info(f"Added file ID {file_id} from processing_state results")
    
    # SPECIAL HANDLING FOR UI DISPLAY DATA
    # This is based on the structure observed in the screenshots
    
    # Check if we have any UI display data in session state
    if "results_filter" in st.session_state:
        results_filter = st.session_state.results_filter
        logger.info(f"Found results_filter in session state")
        
        # If we have a results_filter, it might contain the displayed metadata
        if "displayed_results" in results_filter:
            displayed_results = results_filter["displayed_results"]
            logger.info(f"Found displayed results in results_filter")
            
            for result in displayed_results:
                if "file_id" in result and result["file_id"]:
                    file_id = result["file_id"]
                    
                    if file_id not in available_file_ids:
                        available_file_ids.append(file_id)
                    
                    # Extract file name if available
                    if "file_name" in result:
                        file_id_to_file_name[file_id] = result["file_name"]
                    
                    # Extract metadata
                    if "metadata" in result:
                        file_id_to_metadata[file_id] = result["metadata"]
                    elif "extracted_data" in result:
                        file_id_to_metadata[file_id] = result["extracted_data"]
                    
                    logger.info(f"Added file ID {file_id} from displayed results")
    
    # Remove duplicates while preserving order
    available_file_ids = list(dict.fromkeys(available_file_ids))
    
    # Debug logging
    logger.info(f"Available file IDs: {available_file_ids}")
    logger.info(f"File ID to file name mapping: {file_id_to_file_name}")
    logger.info(f"File ID to metadata mapping: {list(file_id_to_metadata.keys())}")
    
    st.write("Apply extracted metadata to your Box files.")
    
    # Display selected files
    st.subheader("Selected Files")
    
    if not available_file_ids:
        st.error("No file IDs available for metadata application. Please process files first.")
        if st.button("Go to Process Files", key="go_to_process_files_error_btn"):
            st.session_state.current_page = "Process Files"
            st.rerun()
        return
    
    st.write(f"You have selected {len(available_file_ids)} files for metadata application.")
    
    with st.expander("View Selected Files"):
        for file_id in available_file_ids:
            file_name = file_id_to_file_name.get(file_id, "Unknown")
            st.write(f"- {file_name} ({file_id})")
    
    # Metadata application options
    st.subheader("Application Options")
    
    # For freeform extraction
    st.write("Freeform extraction results will be applied as properties metadata.")
    
    # Option to normalize keys
    normalize_keys = st.checkbox(
        "Normalize keys",
        value=True,
        help="If checked, keys will be normalized (lowercase, spaces replaced with underscores).",
        key="normalize_keys_checkbox"
    )
    
    # Option to filter placeholder values
    filter_placeholders = st.checkbox(
        "Filter placeholder values",
        value=True,
        help="If checked, placeholder values like 'insert date' will be filtered out.",
        key="filter_placeholders_checkbox"
    )
    
    # Option to use UI display data
    use_ui_data = st.checkbox(
        "Use UI display data",
        value=True,
        help="If checked, metadata displayed in the UI will be used even if not found in extraction results.",
        key="use_ui_data_checkbox"
    )
    
    # Batch size (simplified to just 1)
    st.subheader("Batch Processing Options")
    st.write("Using single file processing for reliability.")
    
    # Operation timeout
    timeout_seconds = st.slider(
        "Operation Timeout (seconds)",
        min_value=10,
        max_value=300,
        value=60,
        help="Maximum time to wait for each operation to complete.",
        key="timeout_slider"
    )
    
    # Apply metadata button
    col1, col2 = st.columns(2)
    
    with col1:
        apply_button = st.button(
            "Apply Metadata",
            use_container_width=True,
            key="apply_metadata_btn"
        )
    
    with col2:
        cancel_button = st.button(
            "Cancel",
            use_container_width=True,
            key="cancel_btn"
        )
    
    # Progress tracking
    progress_container = st.container()
    
    # Function to check if a value is a placeholder
    def is_placeholder(value):
        """Check if a value appears to be a placeholder"""
        if not isinstance(value, str):
            return False
            
        placeholder_indicators = [
            "insert", "placeholder", "<", ">", "[", "]", 
            "enter", "fill in", "your", "example"
        ]
        
        value_lower = value.lower()
        return any(indicator in value_lower for indicator in placeholder_indicators)
    
    # Direct function to apply metadata to a single file
    def apply_metadata_to_file_direct(client, file_id, metadata_values):
        """
        Apply metadata to a single file with direct client reference
        
        Args:
            client: Box client object
            file_id: File ID to apply metadata to
            metadata_values: Dictionary of metadata values to apply
            
        Returns:
            dict: Result of metadata application
        """
        try:
            file_name = file_id_to_file_name.get(file_id, "Unknown")
            
            # If no metadata values provided, return error
            if not metadata_values:
                logger.warning(f"No metadata found for file {file_name} ({file_id})")
                return {
                    "file_id": file_id,
                    "file_name": file_name,
                    "success": False,
                    "error": "No metadata found for this file"
                }
            
            # Filter out placeholder values if requested
            if filter_placeholders:
                filtered_metadata = {}
                for key, value in metadata_values.items():
                    if not is_placeholder(value):
                        filtered_metadata[key] = value
                
                # If all values were placeholders, keep at least one for debugging
                if not filtered_metadata and metadata_values:
                    # Get the first key-value pair
                    first_key = next(iter(metadata_values))
                    filtered_metadata[first_key] = metadata_values[first_key]
                    filtered_metadata["_note"] = "All other values were placeholders"
                
                metadata_values = filtered_metadata
            
            # If no metadata values after filtering, return error
            if not metadata_values:
                logger.warning(f"No valid metadata found for file {file_name} ({file_id}) after filtering")
                return {
                    "file_id": file_id,
                    "file_name": file_name,
                    "success": False,
                    "error": "No valid metadata found after filtering placeholders"
                }
            
            # Normalize keys if requested
            if normalize_keys:
                normalized_metadata = {}
                for key, value in metadata_values.items():
                    # Convert to lowercase and replace spaces with underscores
                    normalized_key = key.lower().replace(" ", "_").replace("-", "_")
                    normalized_metadata[normalized_key] = value
                metadata_values = normalized_metadata
            
            # Convert all values to strings for Box metadata
            for key, value in metadata_values.items():
                if not isinstance(value, (str, int, float, bool)):
                    metadata_values[key] = str(value)
            
            # Debug logging
            logger.info(f"Applying metadata for file: {file_name} ({file_id})")
            logger.info(f"Metadata values: {json.dumps(metadata_values, default=str)}")
            
            # Get file object
            file_obj = client.file(file_id=file_id)
            
            # Apply as global properties
            try:
                metadata = file_obj.metadata("global", "properties").create(metadata_values)
                logger.info(f"Successfully applied metadata to file {file_name} ({file_id})")
                return {
                    "file_id": file_id,
                    "file_name": file_name,
                    "success": True,
                    "metadata": metadata
                }
            except Exception as e:
                if "already exists" in str(e).lower():
                    # If metadata already exists, update it
                    try:
                        # Create update operations
                        operations = []
                        for key, value in metadata_values.items():
                            operations.append({
                                "op": "replace",
                                "path": f"/{key}",
                                "value": value
                            })
                        
                        # Update metadata
                        logger.info(f"Metadata already exists, updating with operations")
                        metadata = file_obj.metadata("global", "properties").update(operations)
                        
                        logger.info(f"Successfully updated metadata for file {file_name} ({file_id})")
                        return {
                            "file_id": file_id,
                            "file_name": file_name,
                            "success": True,
                            "metadata": metadata
                        }
                    except Exception as update_error:
                        logger.error(f"Error updating metadata for file {file_name} ({file_id}): {str(update_error)}")
                        return {
                            "file_id": file_id,
                            "file_name": file_name,
                            "success": False,
                            "error": f"Error updating metadata: {str(update_error)}"
                        }
                else:
                    logger.error(f"Error creating metadata for file {file_name} ({file_id}): {str(e)}")
                    return {
                        "file_id": file_id,
                        "file_name": file_name,
                        "success": False,
                        "error": f"Error creating metadata: {str(e)}"
                    }
        
        except Exception as e:
            logger.exception(f"Unexpected error applying metadata to file {file_id}: {str(e)}")
            return {
                "file_id": file_id,
                "file_name": file_id_to_file_name.get(file_id, "Unknown"),
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    # Handle apply button click - DIRECT APPROACH WITHOUT THREADING
    if apply_button:
        # Check if client exists directly again
        if 'client' not in st.session_state:
            st.error("Box client not found. Please authenticate first.")
            return
        
        # Get client directly
        client = st.session_state.client
        
        # Process files one by one
        results = []
        errors = []
        
        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Process each file
        for i, file_id in enumerate(available_file_ids):
            file_name = file_id_to_file_name.get(file_id, "Unknown")
            status_text.text(f"Processing {file_name}...")
            
            # Get metadata for this file
            metadata_values = file_id_to_metadata.get(file_id, {})
            
            # Apply metadata directly
            result = apply_metadata_to_file_direct(client, file_id, metadata_values)
            
            if result["success"]:
                results.append(result)
            else:
                errors.append(result)
            
            # Update progress
            progress = (i + 1) / len(available_file_ids)
            progress_bar.progress(progress)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Show results
        st.subheader("Metadata Application Results")
        st.write(f"Successfully applied metadata to {len(results)} of {len(available_file_ids)} files.")
        
        if errors:
            with st.expander("View Errors"):
                for error in errors:
                    st.write(f"**{error['file_name']}:** {error['error']}")
        
        if results:
            with st.expander("View Successful Applications"):
                for result in results:
                    st.write(f"**{result['file_name']}:** Metadata applied successfully")
    
    # Handle cancel button click
    if cancel_button:
        st.warning("Operation cancelled.")
        st.rerun()
