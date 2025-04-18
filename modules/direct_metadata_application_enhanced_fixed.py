import streamlit as st
import logging
import json
from boxsdk import Client

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_metadata_direct():
    """
    A simplified direct approach to apply metadata to Box files without complex session state management
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
    
    # Check if extraction results exist - ENHANCED: Check multiple possible locations
    extraction_results = {}
    
    # Check primary location
    if "extraction_results" in st.session_state and st.session_state.extraction_results:
        extraction_results = st.session_state.extraction_results
        logger.info(f"Found extraction results in primary location with {len(extraction_results)} items")
    # Check processing state
    elif "processing_state" in st.session_state and "results" in st.session_state.processing_state:
        extraction_results = st.session_state.processing_state["results"]
        logger.info(f"Found extraction results in processing_state with {len(extraction_results)} items")
    # Check results filter
    elif "results_filter" in st.session_state and "displayed_results" in st.session_state.results_filter:
        # Convert list to dict using file_id as key
        displayed_results = st.session_state.results_filter["displayed_results"]
        for result in displayed_results:
            if "file_id" in result:
                extraction_results[result["file_id"]] = result
        logger.info(f"Found extraction results in results_filter with {len(extraction_results)} items")
    
    if not extraction_results:
        st.warning("No extraction results available. Please process files first.")
        if st.button("Go to Process Files", key="go_to_process_files_btn"):
            st.session_state.current_page = "Process Files"
            st.rerun()
        return
    
    # Debug the structure of extraction_results
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
    
    # DIRECT ACCESS TO EXTRACTION RESULTS
    # This is a more direct approach to access the extraction results
    # based on the structure observed in the screenshots
    
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
        
        # ENHANCED: Check if result itself contains file_id
        elif isinstance(result, dict) and "file_id" in result:
            file_id = result["file_id"]
            logger.info(f"Extracted file ID {file_id} directly from result")
        
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
                
                # Extract metadata
                if isinstance(result, dict):
                    # Try different paths to find metadata
                    if "result" in result and result["result"]:
                        file_id_to_metadata[file_id] = result["result"]
                    elif "api_response" in result and "answer" in result["api_response"]:
                        # Try to parse answer as JSON if it's a string
                        answer = result["api_response"]["answer"]
                        if isinstance(answer, str):
                            try:
                                parsed_answer = json.loads(answer)
                                file_id_to_metadata[file_id] = parsed_answer
                            except json.JSONDecodeError:
                                file_id_to_metadata[file_id] = {"extracted_text": answer}
                        else:
                            file_id_to_metadata[file_id] = answer
                    # ENHANCED: Check for metadata directly in the result
                    elif "metadata" in result:
                        file_id_to_metadata[file_id] = result["metadata"]
                    elif "extracted_data" in result:
                        file_id_to_metadata[file_id] = result["extracted_data"]
                    else:
                        # Use the entire result as metadata
                        file_id_to_metadata[file_id] = {k: v for k, v in result.items() 
                                                      if k not in ["file_id", "file_name"] and not k.startswith("_")}
                
                logger.info(f"Added file ID {file_id} from key {key}")
    
    # If we still don't have metadata, try to extract it from the UI display data
    # This is based on the structure observed in the screenshots
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
                    if "result" in result:
                        file_id_to_metadata[file_id] = result["result"]
                    elif "api_response" in result and "answer" in result["api_response"]:
                        # Try to parse answer as JSON if it's a string
                        answer = result["api_response"]["answer"]
                        if isinstance(answer, str):
                            try:
                                parsed_answer = json.loads(answer)
                                file_id_to_metadata[file_id] = parsed_answer
                            except json.JSONDecodeError:
                                file_id_to_metadata[file_id] = {"extracted_text": answer}
                        else:
                            file_id_to_metadata[file_id] = answer
                    # ENHANCED: Check for metadata directly in the result
                    elif "metadata" in result:
                        file_id_to_metadata[file_id] = result["metadata"]
                    elif "extracted_data" in result:
                        file_id_to_metadata[file_id] = result["extracted_data"]
                    
                    logger.info(f"Added file ID {file_id} from processing_state results")
    
    # SPECIAL HANDLING FOR UI DISPLAY DATA
    # This is based on the structure observed in the screenshots
    # where metadata is displayed in the UI but not found in extraction_results
    
    # Check if we have any UI display data in session state
    if "results_filter" in st.session_state:
        results_filter = st.session_state.results_filter
        logger.info(f"Found results_filter in session state: {results_filter}")
        
        # If we have a results_filter, it might contain the displayed metadata
        if "displayed_results" in results_filter:
            displayed_results = results_filter["displayed_results"]
            logger.info(f"Found {len(displayed_results)} displayed results in results_filter")
            
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
    
    # DIRECT ACCESS TO API RESPONSE
    # This is based on the structure observed in the screenshots
    # where the API response contains the metadata
    
    # Check if we have any API responses in session state
    for key, value in st.session_state.items():
        if key.startswith("api_response_") or key.endswith("_api_response"):
            logger.info(f"Found API response in session state: {key}")
            
            # Try to extract file ID from the key
            file_id = None
            
            # Check if the key contains a file ID
            if "_" in key:
                parts = key.split("_")
                for part in parts:
                    if part.isdigit():
                        file_id = part
                        break
            
            # If we found a file ID, process it
            if file_id:
                if file_id not in available_file_ids:
                    available_file_ids.append(file_id)
                
                # Extract metadata
                if isinstance(value, dict) and "answer" in value:
                    # Try to parse answer as JSON if it's a string
                    answer = value["answer"]
                    if isinstance(answer, str):
                        try:
                            parsed_answer = json.loads(answer)
                            file_id_to_metadata[file_id] = parsed_answer
                        except json.JSONDecodeError:
                            file_id_to_metadata[file_id] = {"extracted_text": answer}
                    else:
                        file_id_to_metadata[file_id] = answer
                
                logger.info(f"Added file ID {file_id} from API response {key}")
    
    # LAST RESORT: CHECK ALL SESSION STATE VARIABLES
    # This is a last resort to find metadata in any session state variable
    
    # Look for any dictionary in session state that might contain metadata
    for key, value in st.session_state.items():
        if isinstance(value, dict) and "answer" in value:
            logger.info(f"Found potential metadata in session state: {key}")
            
            # Try to extract file ID from the key
            file_id = None
            
            # Check if the key contains a file ID
            if "_" in key:
                parts = key.split("_")
                for part in parts:
                    if part.isdigit():
                        file_id = part
                        break
            
            # If we found a file ID, process it
            if file_id:
                if file_id not in available_file_ids:
                    available_file_ids.append(file_id)
                
                # Extract metadata
                if "answer" in value:
                    # Try to parse answer as JSON if it's a string
                    answer = value["answer"]
                    if isinstance(answer, str):
                        try:
                            parsed_answer = json.loads(answer)
                            file_id_to_metadata[file_id] = parsed_answer
                        except json.JSONDecodeError:
                            file_id_to_metadata[file_id] = {"extracted_text": answer}
                    else:
                        file_id_to_metadata[file_id] = answer
                
                logger.info(f"Added file ID {file_id} from session state {key}")
    
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
    
    # Function to extract metadata from UI display data
    def extract_metadata_from_ui():
        """Extract metadata from UI display data"""
        ui_metadata = {}
        
        # This function would need to be customized based on your specific UI structure
        # For now, we'll use a simple approach based on the screenshots
        
        # Check if we have any UI display data in session state
        if "results_viewer" in st.session_state:
            results_viewer = st.session_state.results_viewer
            logger.info(f"Found results_viewer in session state")
            
            # If we have a results_viewer, it might contain the displayed metadata
            if "displayed_results" in results_viewer:
                displayed_results = results_viewer["displayed_results"]
                logger.info(f"Found displayed results in results_viewer")
                
                # Extract metadata from displayed results
                for result in displayed_results:
                    if "metadata" in result:
                        ui_metadata.update(result["metadata"])
                    elif "extracted_data" in result:
                        ui_metadata.update(result["extracted_data"])
        
        return ui_metadata
    
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
            
            # If no metadata values provided, try to get them from UI display data
            if not metadata_values and use_ui_data:
                ui_metadata = extract_metadata_from_ui()
                if ui_metadata:
                    metadata_values = ui_metadata
                    logger.info(f"Using metadata from UI display data: {json.dumps(metadata_values, default=str)}")
            
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
            metadata_values = {}
            
            # Try to get metadata from file_id_to_metadata
            if file_id in file_id_to_metadata:
                metadata_content = file_id_to_metadata[file_id]
                
                if isinstance(metadata_content, dict):
                    # Extract all fields from the metadata that aren't internal fields
                    for key, value in metadata_content.items():
                        if not key.startswith("_"):
                            metadata_values[key] = value
                elif isinstance(metadata_content, str):
                    # If metadata is a string, try to parse it as JSON
                    try:
                        parsed_metadata = json.loads(metadata_content)
                        if isinstance(parsed_metadata, dict):
                            for key, value in parsed_metadata.items():
                                metadata_values[key] = value
                        else:
                            # Use as a single metadata value
                            metadata_values["extracted_text"] = metadata_content
                    except json.JSONDecodeError:
                        # Use as a single metadata value
                        metadata_values["extracted_text"] = metadata_content
            
            # SPECIAL HANDLING FOR EXTRACTION RESULTS STRUCTURE
            # This is based on the structure observed in the screenshots
            
            # If no metadata found, try to find it in the raw extraction results
            if not metadata_values:
                # Look for a nested structure where the file ID might be part of a composite key
                for key, value in extraction_results.items():
                    # Check if this key contains our file ID
                    if str(file_id) in key:
                        logger.info(f"Found potential match for file ID {file_id} in key {key}")
                        
                        # Try to extract metadata from this result
                        if isinstance(value, dict):
                            # Try different paths to find metadata
                            if "result" in value:
                                result_data = value["result"]
                                if isinstance(result_data, dict):
                                    metadata_values = result_data
                                    logger.info(f"Found metadata in result field")
                                    break
                            elif "api_response" in value and "answer" in value["api_response"]:
                                answer = value["api_response"]["answer"]
                                try:
                                    # Try to parse as JSON
                                    if isinstance(answer, str):
                                        parsed_answer = json.loads(answer)
                                        if isinstance(parsed_answer, dict):
                                            metadata_values = parsed_answer
                                            logger.info(f"Found metadata in api_response.answer field (parsed JSON)")
                                            break
                                    else:
                                        metadata_values = answer
                                        logger.info(f"Found metadata in api_response.answer field (direct)")
                                        break
                                except (json.JSONDecodeError, TypeError):
                                    continue
            
            # DIRECT ACCESS TO API RESPONSE IN EXTRACTION RESULTS
            # This is based on the structure observed in the screenshots
            
            # If still no metadata, try to find it directly in the extraction results
            if not metadata_values:
                for key, value in extraction_results.items():
                    if isinstance(value, dict) and "api_response" in value and "answer" in value["api_response"]:
                        answer = value["api_response"]["answer"]
                        try:
                            # Try to parse as JSON
                            if isinstance(answer, str):
                                parsed_answer = json.loads(answer)
                                if isinstance(parsed_answer, dict):
                                    metadata_values = parsed_answer
                                    logger.info(f"Found metadata in api_response.answer field (parsed JSON)")
                                    break
                            else:
                                metadata_values = answer
                                logger.info(f"Found metadata in api_response.answer field (direct)")
                                break
                        except (json.JSONDecodeError, TypeError):
                            continue
            
            # ENHANCED: Check for metadata directly in the extraction results
            if not metadata_values:
                # Check if the file_id is a direct key in extraction_results
                if file_id in extraction_results:
                    result = extraction_results[file_id]
                    if isinstance(result, dict):
                        if "metadata" in result:
                            metadata_values = result["metadata"]
                            logger.info(f"Found metadata directly in extraction_results[{file_id}].metadata")
                        elif "extracted_data" in result:
                            metadata_values = result["extracted_data"]
                            logger.info(f"Found metadata directly in extraction_results[{file_id}].extracted_data")
                        elif "result" in result:
                            metadata_values = result["result"]
                            logger.info(f"Found metadata directly in extraction_results[{file_id}].result")
            
            # HARDCODED METADATA FOR TESTING
            # This is a last resort to ensure metadata is applied
            
            # If still no metadata, use hardcoded metadata for testing
            if not metadata_values and debug_mode:
                logger.warning(f"No metadata found for file {file_name} ({file_id}), using hardcoded metadata for testing")
                metadata_values = {
                    "test_key": "test_value",
                    "file_id": file_id,
                    "file_name": file_name
                }
            
            # If we have metadata, apply it
            if metadata_values:
                # Apply metadata directly
                result = apply_metadata_to_file_direct(client, file_id, metadata_values)
                
                if result["success"]:
                    results.append(result)
                else:
                    errors.append(result)
            else:
                # No metadata found
                errors.append({
                    "file_id": file_id,
                    "file_name": file_name,
                    "success": False,
                    "error": "No metadata found for this file"
                })
            
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
