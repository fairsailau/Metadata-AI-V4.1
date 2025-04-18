import streamlit as st
import pandas as pd
from typing import Dict, List, Any
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def view_results():
    """
    View and manage extraction results
    """
    st.title("View Results")
    
    # Validate session state
    if not hasattr(st.session_state, "authenticated") or not hasattr(st.session_state, "client") or not st.session_state.authenticated or not st.session_state.client:
        st.error("Please authenticate with Box first")
        return
    
    # Ensure extraction_results is initialized - FIXED: Use hasattr check instead of 'in' operator
    if not hasattr(st.session_state, "extraction_results"):
        st.session_state.extraction_results = {}
        logger.info("Initialized extraction_results in view_results")
    
    # Ensure selected_result_ids is initialized - FIXED: Use hasattr check instead of 'in' operator
    if not hasattr(st.session_state, "selected_result_ids"):
        st.session_state.selected_result_ids = []
        logger.info("Initialized selected_result_ids in view_results")
    
    # Ensure metadata_config is initialized
    if not hasattr(st.session_state, "metadata_config"):
        st.session_state.metadata_config = {
            "extraction_method": "freeform",
            "freeform_prompt": "Extract key metadata from this document.",
            "use_template": False,
            "template_id": "",
            "custom_fields": [],
            "ai_model": "azure__openai__gpt_4o_mini",
            "batch_size": 5
        }
        logger.info("Initialized metadata_config in view_results")
    
    if not hasattr(st.session_state, "extraction_results") or not st.session_state.extraction_results:
        st.warning("No extraction results available. Please process files first.")
        if st.button("Go to Process Files", key="go_to_process_files_btn"):
            st.session_state.current_page = "Process Files"
            st.rerun()
        return
    
    st.write("Review and manage the metadata extraction results.")
    
    # Initialize session state for results viewer
    if not hasattr(st.session_state, "results_filter"):
        st.session_state.results_filter = ""
    
    # Filter options
    st.subheader("Filter Results")
    st.session_state.results_filter = st.text_input(
        "Filter by file name",
        value=st.session_state.results_filter,
        key="filter_input"
    )
    
    # Get filtered results
    filtered_results = {}
    
    # Convert extraction_results to use file_id as the key for compatibility
    for key, result in st.session_state.extraction_results.items():
        file_id = result.get("file_id")
        if file_id:
            filtered_results[file_id] = result
    
    # Apply filter if specified
    if st.session_state.results_filter:
        filtered_results = {
            file_id: result for file_id, result in filtered_results.items()
            if st.session_state.results_filter.lower() in result.get("file_name", "").lower()
        }
    
    # Display results count
    st.write(f"Showing {len(filtered_results)} of {len(st.session_state.extraction_results)} results")
    
    # Display results
    st.subheader("Extraction Results")
    
    # Determine if we're using structured or freeform extraction
    is_structured = st.session_state.metadata_config.get("extraction_method") == "structured"
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Table View", "Detailed View"])
    
    with tab1:
        # Table view
        table_data = []
        
        for file_id, result_data in filtered_results.items():
            # Basic file info
            row = {"File Name": result_data.get("file_name", "Unknown"), "File ID": file_id}
            
            # Extract and add metadata to the table
            extracted_text = ""
            
            # Check for result_data field
            if "result_data" in result_data and result_data["result_data"]:
                if isinstance(result_data["result_data"], dict):
                    # For structured data, add key fields to the table
                    for key, value in result_data["result_data"].items():
                        if not key.startswith("_"):  # Skip internal fields
                            row[key] = str(value) if not isinstance(value, list) else ", ".join(str(v) for v in value)
                            # Limit to first 5 fields to keep table manageable
                            if len(row) > 7:  # File Name, File ID + 5 fields
                                break
                    
                    # Create a summary for the Extracted Text column
                    extracted_text = ", ".join([f"{k}: {v}" for k, v in list(result_data["result_data"].items())[:3]])
                elif isinstance(result_data["result_data"], str):
                    # If result_data is a string, use it directly
                    extracted_text = result_data["result_data"]
            
            # Check for result field (backward compatibility)
            elif "result" in result_data and result_data["result"]:
                if isinstance(result_data["result"], dict):
                    # For structured data, add key fields to the table
                    for key, value in result_data["result"].items():
                        if not key.startswith("_") and key != "extracted_text":  # Skip internal fields
                            row[key] = str(value) if not isinstance(value, list) else ", ".join(str(v) for v in value)
                            # Limit to first 5 fields to keep table manageable
                            if len(row) > 7:  # File Name, File ID + 5 fields
                                break
                    
                    # Create a summary for the Extracted Text column
                    extracted_text = ", ".join([f"{k}: {v}" for k, v in list(result_data["result"].items())[:3]])
                elif isinstance(result_data["result"], str):
                    # If result is a string, use it directly
                    extracted_text = result_data["result"]
            
            # Check for api_response field
            elif "api_response" in result_data and result_data["api_response"]:
                api_response = result_data["api_response"]
                if isinstance(api_response, dict):
                    if "answer" in api_response:
                        if isinstance(api_response["answer"], dict):
                            # Extract fields from answer
                            for key, value in api_response["answer"].items():
                                if not key.startswith("_"):  # Skip internal fields
                                    row[key] = str(value) if not isinstance(value, list) else ", ".join(str(v) for v in value)
                                    # Limit to first 5 fields to keep table manageable
                                    if len(row) > 7:  # File Name, File ID + 5 fields
                                        break
                            
                            # Create a summary for the Extracted Text column
                            extracted_text = ", ".join([f"{k}: {v}" for k, v in list(api_response["answer"].items())[:3]])
                        elif isinstance(api_response["answer"], str):
                            # If answer is a string, use it directly
                            extracted_text = api_response["answer"]
            
            # Add extracted text to row if not already added
            if "Extracted Text" not in row and extracted_text:
                row["Extracted Text"] = (extracted_text[:100] + "...") if len(extracted_text) > 100 else extracted_text
            elif "Extracted Text" not in row:
                row["Extracted Text"] = "No text extracted"
            
            table_data.append(row)
        
        if table_data:
            # Create dataframe
            df = pd.DataFrame(table_data)
            
            # Display dataframe
            st.dataframe(df, use_container_width=True)
            
            # Export options
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Export as CSV", use_container_width=True, key="export_csv_btn"):
                    # In a real app, we would save to a file
                    st.download_button(
                        label="Download CSV",
                        data=df.to_csv(index=False).encode('utf-8'),
                        file_name="extraction_results.csv",
                        mime="text/csv",
                        key="download_csv_btn"
                    )
            
            with col2:
                if st.button("Export as Excel", use_container_width=True, key="export_excel_btn"):
                    # In a real app, we would save to a file
                    st.info("Excel export would be implemented in the full app")
        else:
            st.info("No results match the current filter")
    
    with tab2:
        # Detailed view
        for file_id, result_data in filtered_results.items():
            with st.expander(f"{result_data.get('file_name', 'Unknown')} ({file_id})", expanded=True):
                # Display file info
                st.write(f"**File:** {result_data.get('file_name', 'Unknown')}")
                st.write(f"**File ID:** {file_id}")
                
                # Display extraction results
                st.write("#### Extracted Metadata")
                
                # Display the raw JSON for debugging
                st.write("##### Raw Result Data (Debug View)")
                st.json(result_data)
                
                # Extract and display metadata
                extracted_data = {}
                
                # Check for result_data field
                if "result_data" in result_data and result_data["result_data"]:
                    if isinstance(result_data["result_data"], dict):
                        # Extract key-value pairs from the result
                        for key, value in result_data["result_data"].items():
                            if not key.startswith("_"):  # Skip internal fields
                                extracted_data[key] = value
                    elif isinstance(result_data["result_data"], str):
                        # If result_data is a string, display it as extracted text
                        st.write("##### Extracted Text")
                        st.write(result_data["result_data"])
                
                # Check for result field (backward compatibility)
                elif "result" in result_data and result_data["result"]:
                    if isinstance(result_data["result"], dict):
                        # Extract key-value pairs from the result
                        for key, value in result_data["result"].items():
                            if not key.startswith("_") and key != "extracted_text":  # Skip internal fields
                                extracted_data[key] = value
                        
                        # Check for extracted_text field
                        if "extracted_text" in result_data["result"]:
                            st.write("##### Extracted Text")
                            st.write(result_data["result"]["extracted_text"])
                    elif isinstance(result_data["result"], str):
                        # If result is a string, display it as extracted text
                        st.write("##### Extracted Text")
                        st.write(result_data["result"])
                
                # Check for api_response field
                elif "api_response" in result_data and result_data["api_response"]:
                    api_response = result_data["api_response"]
                    if isinstance(api_response, dict) and "answer" in api_response:
                        if isinstance(api_response["answer"], dict):
                            # Extract fields from answer
                            for key, value in api_response["answer"].items():
                                if not key.startswith("_"):  # Skip internal fields
                                    extracted_data[key] = value
                        elif isinstance(api_response["answer"], str):
                            # If answer is a string, display it as extracted text
                            st.write("##### Extracted Text")
                            st.write(api_response["answer"])
                
                # Display extracted data as editable fields
                if extracted_data:
                    st.write("##### Key-Value Pairs")
                    for key, value in extracted_data.items():
                        # Create editable fields
                        if isinstance(value, list):
                            # For multiSelect fields
                            new_value = st.multiselect(
                                key,
                                options=value + ["Option 1", "Option 2", "Option 3"],
                                default=value,
                                key=f"edit_{file_id}_{key}"
                            )
                        else:
                            # For other field types
                            new_value = st.text_input(key, value=str(value), key=f"edit_{file_id}_{key}")
                        
                        # Update value if changed
                        if new_value != value:
                            # Find the original key in extraction_results
                            for orig_key, orig_result in st.session_state.extraction_results.items():
                                if orig_result.get("file_id") == file_id:
                                    # Update in result_data if it exists
                                    if "result_data" in orig_result and isinstance(orig_result["result_data"], dict):
                                        st.session_state.extraction_results[orig_key]["result_data"][key] = new_value
                                    # Update in result if it exists (backward compatibility)
                                    elif "result" in orig_result and isinstance(orig_result["result"], dict):
                                        st.session_state.extraction_results[orig_key]["result"][key] = new_value
                                    break
                else:
                    st.write("No structured data extracted")
                
                # Check for key_value_pairs in result
                if "result" in result_data and isinstance(result_data["result"], dict) and "key_value_pairs" in result_data["result"]:
                    kv_pairs = result_data["result"]["key_value_pairs"]
                    if kv_pairs:
                        st.write("##### Key-Value Pairs (Legacy Format)")
                        for key, value in kv_pairs.items():
                            new_value = st.text_input(key, value=value, key=f"edit_kv_{file_id}_{key}")
                            
                            # Update value if changed
                            if new_value != value:
                                # Find the original key in extraction_results
                                for orig_key, orig_result in st.session_state.extraction_results.items():
                                    if orig_result.get("file_id") == file_id:
                                        st.session_state.extraction_results[orig_key]["result"]["key_value_pairs"][key] = new_value
                                        break
                    else:
                        st.write("No key-value pairs extracted")
                
                # Selection checkbox for batch operations
                is_selected = file_id in st.session_state.selected_result_ids
                if st.checkbox("Select for batch operations", value=is_selected, key=f"select_{file_id}"):
                    if file_id not in st.session_state.selected_result_ids:
                        st.session_state.selected_result_ids.append(file_id)
                else:
                    if file_id in st.session_state.selected_result_ids:
                        st.session_state.selected_result_ids.remove(file_id)
    
    # Batch operations
    st.subheader("Batch Operations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Select All", use_container_width=True, key="select_all_btn"):
            st.session_state.selected_result_ids = list(filtered_results.keys())
            st.rerun()
    
    with col2:
        if st.button("Deselect All", use_container_width=True, key="deselect_all_btn"):
            st.session_state.selected_result_ids = []
            st.rerun()
    
    # Display selection count
    st.write(f"Selected {len(st.session_state.selected_result_ids)} of {len(filtered_results)} results")
    
    # Apply Metadata button
    if st.button("Apply Metadata", use_container_width=True, key="apply_metadata_btn", disabled=not st.session_state.selected_result_ids):
        # Save selected_result_ids before navigation
        logger.info(f"Saving {len(st.session_state.selected_result_ids)} selected result IDs before navigation")
        st.session_state.current_page = "Apply Metadata"
        st.rerun()
