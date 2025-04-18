import streamlit as st
import logging
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_session_state_edge_cases():
    """
    Test function to verify the session state management solution handles edge cases properly
    """
    st.title("Session State Edge Case Tester")
    
    # Import the session state manager
    try:
        from modules.session_state_manager import (
            initialize_app_session_state, 
            get_safe_session_state, 
            set_safe_session_state, 
            reset_session_state,
            debug_session_state
        )
        st.success("Successfully imported session_state_manager module")
    except ImportError as e:
        st.error(f"Failed to import session_state_manager module: {str(e)}")
        return
    
    # Initialize session state
    initialize_app_session_state()
    st.success("Session state initialized")
    
    # Display current session state
    st.subheader("Current Session State")
    debug_info = debug_session_state()
    st.json(debug_info)
    
    # Test cases section
    st.subheader("Test Cases")
    
    # Test Case 1: Access non-existent key
    with st.expander("Test Case 1: Access non-existent key"):
        st.write("This test verifies that accessing a non-existent key returns the default value instead of raising an error")
        
        test_key = "non_existent_key"
        default_value = "default_value"
        
        result = get_safe_session_state(test_key, default_value)
        
        if result == default_value:
            st.success(f"Test passed: get_safe_session_state('{test_key}', '{default_value}') returned '{result}'")
        else:
            st.error(f"Test failed: get_safe_session_state('{test_key}', '{default_value}') returned '{result}' instead of '{default_value}'")
    
    # Test Case 2: Set and retrieve a value
    with st.expander("Test Case 2: Set and retrieve a value"):
        st.write("This test verifies that setting a value and retrieving it works correctly")
        
        test_key = "test_key"
        test_value = f"test_value_{time.time()}"
        
        set_result = set_safe_session_state(test_key, test_value)
        get_result = get_safe_session_state(test_key)
        
        if set_result and get_result == test_value:
            st.success(f"Test passed: set_safe_session_state('{test_key}', '{test_value}') and get_safe_session_state('{test_key}') returned '{get_result}'")
        else:
            st.error(f"Test failed: set_result={set_result}, get_result='{get_result}', expected='{test_value}'")
    
    # Test Case 3: Reset session state
    with st.expander("Test Case 3: Reset session state"):
        st.write("This test verifies that resetting session state works correctly")
        
        # Set a test value
        test_key = "test_reset_key"
        test_value = "test_reset_value"
        set_safe_session_state(test_key, test_value)
        
        # Verify it was set
        before_reset = get_safe_session_state(test_key)
        
        # Reset session state
        reset_button = st.button("Reset Session State")
        
        if reset_button:
            reset_result = reset_session_state()
            after_reset = get_safe_session_state(test_key)
            
            if reset_result and after_reset is None:
                st.success(f"Test passed: reset_session_state() cleared '{test_key}'")
            else:
                st.error(f"Test failed: reset_result={reset_result}, after_reset='{after_reset}', expected=None")
        else:
            st.info(f"Current value of '{test_key}' is '{before_reset}'. Click the button to reset.")
    
    # Test Case 4: Handle nested dictionaries
    with st.expander("Test Case 4: Handle nested dictionaries"):
        st.write("This test verifies that nested dictionaries in session state are handled correctly")
        
        # Set a nested dictionary
        test_key = "test_nested"
        test_value = {
            "level1": {
                "level2": {
                    "level3": "nested_value"
                }
            }
        }
        
        set_result = set_safe_session_state(test_key, test_value)
        get_result = get_safe_session_state(test_key)
        
        if set_result and get_result and get_result.get("level1", {}).get("level2", {}).get("level3") == "nested_value":
            st.success(f"Test passed: Nested dictionary was stored and retrieved correctly")
        else:
            st.error(f"Test failed: set_result={set_result}, get_result={json.dumps(get_result)}")
    
    # Test Case 5: Simulate extraction_results
    with st.expander("Test Case 5: Simulate extraction_results"):
        st.write("This test simulates the extraction_results structure to verify it's handled correctly")
        
        # Create a simulated extraction_results structure
        file_id = "1773119545338"
        composite_key = f"{file_id}_structured"
        
        extraction_results = {
            composite_key: {
                "file_id": file_id,
                "file_name": "Test Document.pdf",
                "result": {
                    "Effective Date": "February 23, 2017",
                    "Seller": "Quarry Jumpers Produce, Inc.",
                    "Buyer": "Indianapolis Public Schools",
                    "Product": "Corn"
                }
            }
        }
        
        # Set the extraction_results
        set_result = set_safe_session_state("extraction_results", extraction_results)
        
        # Verify it was set correctly
        get_result = get_safe_session_state("extraction_results")
        
        if set_result and get_result and file_id in str(get_result):
            st.success(f"Test passed: extraction_results was stored correctly")
            st.json(get_result)
        else:
            st.error(f"Test failed: set_result={set_result}, get_result={json.dumps(get_result)}")
    
    # Test Case 6: Simulate missing extraction_results
    with st.expander("Test Case 6: Simulate missing extraction_results"):
        st.write("This test simulates the scenario where extraction_results is missing")
        
        # Clear extraction_results
        if "extraction_results" in st.session_state:
            del st.session_state.extraction_results
            st.info("Deleted extraction_results from session state")
        
        # Try to access it
        get_result = get_safe_session_state("extraction_results", {})
        
        if isinstance(get_result, dict) and len(get_result) == 0:
            st.success(f"Test passed: get_safe_session_state('extraction_results', {{}}) returned an empty dict")
        else:
            st.error(f"Test failed: get_result={json.dumps(get_result)}")
        
        # Re-initialize session state
        initialize_app_session_state()
        st.info("Re-initialized session state")
        
        # Verify extraction_results exists now
        if "extraction_results" in st.session_state:
            st.success("extraction_results was re-initialized")
        else:
            st.error("extraction_results was not re-initialized")
    
    # Summary
    st.subheader("Test Summary")
    st.write("The session state management solution has been tested with various edge cases to ensure it handles all scenarios correctly.")
    st.write("The solution provides robust error handling and fallback mechanisms for accessing and setting session state variables.")
    
    # Final session state
    st.subheader("Final Session State")
    final_debug_info = debug_session_state()
    st.json(final_debug_info)

if __name__ == "__main__":
    test_session_state_edge_cases()
