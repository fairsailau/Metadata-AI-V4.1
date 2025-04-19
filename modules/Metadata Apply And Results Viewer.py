### modules/direct_metadata_application_enhanced_fixed.py
```python
import streamlit as st
import logging
import json
from boxsdk import Client
from .enhanced_logging import log_full_exception, log_metadata_operation

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_metadata_direct():
    """Direct approach to apply metadata to Box files with simplified iteration over AI results"""
    st.title("Apply Metadata")

    # Debug sidebar
    debug_mode = st.sidebar.checkbox("Debug Session State", key="debug_checkbox")
    if debug_mode:
        st.sidebar.write("### RAW processing_state")
        st.sidebar.json(st.session_state.get("processing_state", {}))

    # Ensure client exists
    if 'client' not in st.session_state:
        st.error("Box client not found. Please authenticate first.")
        if st.button("Go to Authentication", key="go_to_auth_btn"):
            st.session_state.current_page = "Home"
            st.rerun()
        return

    client = st.session_state.client
    try:
        user = client.user().get()
        logger.info(f"Verified client authentication as {user.name}")
        st.success(f"Authenticated as {user.name}")
    except Exception as e:
        logger.error(f"Error verifying client: {e}")
        st.error(f"Authentication error: {e}. Please re-authenticate.")
        if st.button("Go to Authentication", key="go_to_auth_error_btn"):
            st.session_state.current_page = "Home"
            st.rerun()
        return

    # Ensure processing results exist
    if not st.session_state.get("processing_state"):
        st.warning("No processing results available. Please process files first.")
        if st.button("Go to Process Files", key="go_to_process_files_btn"):
            st.session_state.current_page = "Process Files"
            st.rerun()
        return

    processing_state = st.session_state.processing_state
    logger.info(f"Processing state keys: {list(processing_state.keys())}")

    # Collect selected file info
    available_file_ids = []
    file_id_to_file_name = {}
    for file_info in st.session_state.get('selected_files', []):
        fid = str(file_info.get('id'))
        available_file_ids.append(fid)
        file_id_to_file_name[fid] = file_info.get('name', fid)
        logger.info(f"Added file ID {fid} from selected_files")

    # --- NEW: iterate only the AI results map ---
    results_map = processing_state.get("results", {})
    logger.info(f"Results map keys: {list(results_map.keys())}")

    file_id_to_metadata = {}
    for raw_id, payload in results_map.items():
        file_id = str(raw_id)
        available_file_ids.append(file_id)
        file_id_to_file_name.setdefault(file_id, payload.get('file_name', file_id))

        # Most extractions under payload['results']
        if isinstance(payload, dict) and payload.get('results'):
            metadata = payload['results']
        else:
            metadata = payload if isinstance(payload, dict) else {}

        file_id_to_metadata[file_id] = metadata
        logger.info(f"Extracted metadata for {file_id}: {json.dumps(metadata, default=str)}")
    # Dedupe IDs
    available_file_ids = list(dict.fromkeys(available_file_ids))
    logger.info(f"Final Available file IDs: {available_file_ids}")
    logger.info(f"File ID -> metadata keys: {list(file_id_to_metadata.keys())}")
    # ------------------------------------------

    # UI: list files, options, apply button
    st.subheader("Selected Files")
    for fid in available_file_ids:
        st.write(f"- {file_id_to_file_name.get(fid)} ({fid})")

    st.subheader("Application Options")
    normalize_keys = st.checkbox("Normalize keys", value=True)
    filter_placeholders = st.checkbox("Filter placeholder values", value=True)

    apply_button = st.button("Apply Metadata", key="apply_metadata_btn")

    if apply_button:
        results, errors = [], []
        progress_bar = st.progress(0)
        status_text = st.empty()
        for i, fid in enumerate(available_file_ids):
            status_text.text(f"Applying to {file_id_to_file_name.get(fid)}...")
            metadata_values = file_id_to_metadata.get(fid, {})
            logger.info(f"Metadata before apply for {fid}: {metadata_values}")
            # Call helper decorated function
            result = apply_metadata_to_file(client, fid, metadata_values, normalize_keys, filter_placeholders)
            if result['success']:
                results.append(result)
            else:
                errors.append(result)
            progress_bar.progress((i+1)/len(available_file_ids))
        progress_bar.empty()
        status_text.empty()
        st.subheader("Results")
        st.write(f"Success: {len(results)}, Errors: {len(errors)}")
        if errors:
            with st.expander("View Errors"):
                for e in errors:
                    st.write(f"{e['file_name']}: {e['error']}")


# Decorated helper now simplified to create/update using Box SDK
@log_full_exception
@log_metadata_operation("apply_metadata_to_file")
def apply_metadata_to_file(client, file_id, metadata_values, normalize, filter_placeholders):
    file_obj = client.file(file_id=file_id)
    # [ ... same logic as before for placeholders/normalize ... ]
    try:
        meta = file_obj.metadata('global', 'properties').create(metadata_values)
        return {'file_id': file_id, 'file_name': file_id, 'success': True}
    except Exception as e:
        if 'already exists' in str(e).lower():
            ops = [{'op': 'replace', 'path': f"/{k}", 'value': v} for k, v in metadata_values.items()]
            meta = file_obj.metadata('global', 'properties').update(ops)
            return {'file_id': file_id, 'file_name': file_id, 'success': True}
        return {'file_id': file_id, 'file_name': file_id, 'success': False, 'error': str(e)}
```


### modules/results_viewer.py
```python
import streamlit as st

# ... other imports ...

def view_results():
    st.title("View Results")

    processing_state = st.session_state.processing_state
    results_map = processing_state.get("results", {})

    for fid, payload in results_map.items():
        file_name = payload.get('file_name', fid)
        data = payload.get('results', {})

        with st.expander(f"File: {file_name} ({fid})"):
            show_details = st.checkbox("Show detailed results", key=f"detail_{fid}")
            if show_details:
                st.json(data)
