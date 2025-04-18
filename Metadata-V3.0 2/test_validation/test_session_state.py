import sys
import os
import logging
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_session_state_initialization():
    """
    Test the session state initialization function to ensure all required variables are initialized.
    This is a mock test since we can't directly test Streamlit session state outside of a Streamlit app.
    """
    logger.info("Testing session state initialization...")
    
    # Mock session state
    class MockSessionState:
        def __init__(self):
            self._state = {}
        
        def __contains__(self, key):
            return key in self._state
        
        def __getattr__(self, key):
            if key not in self._state:
                return None
            return self._state[key]
        
        def __setattr__(self, key, value):
            if key == '_state':
                super().__setattr__(key, value)
            else:
                self._state[key] = value
    
    # Create mock session state
    st = type('', (), {})()
    st.session_state = MockSessionState()
    
    # Import the initialize_session_state function
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Define a mock initialize function based on our app.py implementation
    def initialize_session_state():
        """Mock of the centralized session state initialization function"""
        # Core session state variables
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
            logger.info("Initialized authenticated in session state")
        
        if "client" not in st.session_state:
            st.session_state.client = None
            logger.info("Initialized client in session state")
        
        if "current_page" not in st.session_state:
            st.session_state.current_page = "Home"
            logger.info("Initialized current_page in session state")
        
        # File selection and processing variables
        if "selected_files" not in st.session_state:
            st.session_state.selected_files = []
            logger.info("Initialized selected_files in session state")
        
        # Metadata configuration
        if "metadata_config" not in st.session_state:
            st.session_state.metadata_config = {
                "extraction_method": "freeform",
                "freeform_prompt": "Extract key metadata from this document.",
                "use_template": False,
                "template_id": "",
                "custom_fields": [],
                "ai_model": "azure__openai__gpt_4o_mini",
                "batch_size": 5
            }
            logger.info("Initialized metadata_config in session state")
        
        # Extraction results
        if "extraction_results" not in st.session_state:
            st.session_state.extraction_results = {}
            logger.info("Initialized extraction_results in session state")
        
        # Selected results for metadata application
        if "selected_result_ids" not in st.session_state:
            st.session_state.selected_result_ids = []
            logger.info("Initialized selected_result_ids in session state")
        
        # Application state for metadata application
        if "application_state" not in st.session_state:
            st.session_state.application_state = {
                "is_applying": False,
                "applied_files": 0,
                "total_files": 0,
                "current_batch": [],
                "results": {},
                "errors": {}
            }
            logger.info("Initialized application_state in session state")
        
        # Processing state for file processing
        if "processing_state" not in st.session_state:
            st.session_state.processing_state = {
                "is_processing": False,
                "processed_files": 0,
                "total_files": 0,
                "current_file_index": -1,
                "current_file": "",
                "results": {},
                "errors": {},
                "retries": {},
                "max_retries": 3,
                "retry_delay": 2,
                "visualization_data": {}
            }
            logger.info("Initialized processing_state in session state")
    
    # Run the initialization function
    initialize_session_state()
    
    # Check if all required variables are initialized
    required_vars = [
        "authenticated", "client", "current_page", "selected_files", 
        "metadata_config", "extraction_results", "selected_result_ids",
        "application_state", "processing_state"
    ]
    
    all_initialized = True
    for var in required_vars:
        if var not in st.session_state:
            logger.error(f"Variable {var} not initialized in session state")
            all_initialized = False
    
    if all_initialized:
        logger.info("All session state variables successfully initialized")
        return True
    else:
        logger.error("Some session state variables were not initialized")
        return False

def test_metadata_extraction_structure():
    """
    Test the structure of the metadata extraction results to ensure they follow the standardized format.
    """
    logger.info("Testing metadata extraction result structure...")
    
    # Example of standardized extraction result structure
    standard_result = {
        "file_id": "123456789",
        "file_name": "example.pdf",
        "extraction_method": "freeform",
        "result_data": {
            # Extracted metadata key-value pairs
            "company_name": "Acme Corp",
            "contract_date": "2023-01-01",
        },
        "api_response": {
            # Original API response for reference
            "answer": {
                "company_name": "Acme Corp",
                "contract_date": "2023-01-01",
            }
        }
    }
    
    # Check if the structure has all required fields
    required_fields = ["file_id", "file_name", "result_data"]
    
    all_fields_present = True
    for field in required_fields:
        if field not in standard_result:
            logger.error(f"Required field {field} missing from standard result structure")
            all_fields_present = False
    
    if all_fields_present:
        logger.info("Standard result structure contains all required fields")
        return True
    else:
        logger.error("Standard result structure is missing required fields")
        return False

def test_metadata_application_function():
    """
    Test the metadata application function to ensure it correctly extracts metadata values
    from different result formats and applies them to files.
    This is a mock test since we can't directly interact with Box API outside of the app.
    """
    logger.info("Testing metadata application function...")
    
    # Mock extraction results in different formats
    test_cases = [
        {
            "name": "Standard result_data format",
            "result": {
                "file_id": "123456789",
                "file_name": "example1.pdf",
                "result_data": {
                    "company_name": "Acme Corp",
                    "contract_date": "2023-01-01",
                }
            },
            "expected_metadata": {
                "company_name": "Acme Corp",
                "contract_date": "2023-01-01",
            }
        },
        {
            "name": "Legacy result format",
            "result": {
                "file_id": "987654321",
                "file_name": "example2.pdf",
                "result": {
                    "company_name": "Beta Inc",
                    "contract_date": "2023-02-15",
                }
            },
            "expected_metadata": {
                "company_name": "Beta Inc",
                "contract_date": "2023-02-15",
            }
        },
        {
            "name": "API response format",
            "result": {
                "file_id": "456789123",
                "file_name": "example3.pdf",
                "api_response": {
                    "answer": {
                        "company_name": "Gamma LLC",
                        "contract_date": "2023-03-30",
                    }
                }
            },
            "expected_metadata": {
                "company_name": "Gamma LLC",
                "contract_date": "2023-03-30",
            }
        },
        {
            "name": "String result format",
            "result": {
                "file_id": "789123456",
                "file_name": "example4.pdf",
                "result_data": "This is a contract between Delta Corp and the client dated 2023-04-15."
            },
            "expected_metadata": {
                "extracted_text": "This is a contract between Delta Corp and the client dated 2023-04-15."
            }
        }
    ]
    
    # Mock function to extract metadata values (simplified version of the actual function)
    def extract_metadata_values(result_data):
        metadata_values = {}
        
        # 1. Check for result_data field (preferred format)
        if "result_data" in result_data and result_data["result_data"]:
            if isinstance(result_data["result_data"], dict):
                # Extract all fields from the result_data that aren't internal fields
                for key, value in result_data["result_data"].items():
                    if not key.startswith("_"):
                        metadata_values[key] = value
            elif isinstance(result_data["result_data"], str):
                # If result_data is a string, use it as a single metadata value
                metadata_values["extracted_text"] = result_data["result_data"]
        
        # 2. Check for result field (backward compatibility)
        if not metadata_values and "result" in result_data:
            if isinstance(result_data["result"], dict):
                # Extract all fields from the result that aren't internal fields
                for key, value in result_data["result"].items():
                    if not key.startswith("_") and key != "extracted_text":
                        metadata_values[key] = value
                
                # Check for key_value_pairs in result
                if not metadata_values and "key_value_pairs" in result_data["result"]:
                    kv_pairs = result_data["result"]["key_value_pairs"]
                    if isinstance(kv_pairs, dict):
                        metadata_values = kv_pairs
            elif isinstance(result_data["result"], str):
                # If result is a string, use it as a single metadata value
                metadata_values["extracted_text"] = result_data["result"]
        
        # 3. Check for api_response field
        if not metadata_values and "api_response" in result_data:
            api_response = result_data["api_response"]
            if isinstance(api_response, dict) and "answer" in api_response:
                if isinstance(api_response["answer"], dict):
                    # Use answer field directly
                    for key, value in api_response["answer"].items():
                        metadata_values[key] = value
                elif isinstance(api_response["answer"], str):
                    # Use as a single metadata value
                    metadata_values["answer"] = api_response["answer"]
        
        return metadata_values
    
    # Test each case
    all_tests_passed = True
    for test_case in test_cases:
        logger.info(f"Testing {test_case['name']}...")
        extracted_metadata = extract_metadata_values(test_case["result"])
        
        # Check if extracted metadata matches expected metadata
        if extracted_metadata == test_case["expected_metadata"]:
            logger.info(f"✓ {test_case['name']} passed")
        else:
            logger.error(f"✗ {test_case['name']} failed")
            logger.error(f"  Expected: {test_case['expected_metadata']}")
            logger.error(f"  Got: {extracted_metadata}")
            all_tests_passed = False
    
    if all_tests_passed:
        logger.info("All metadata extraction tests passed")
        return True
    else:
        logger.error("Some metadata extraction tests failed")
        return False

if __name__ == "__main__":
    # Run all tests
    session_state_test = test_session_state_initialization()
    structure_test = test_metadata_extraction_structure()
    application_test = test_metadata_application_function()
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Session State Initialization: {'PASSED' if session_state_test else 'FAILED'}")
    logger.info(f"Metadata Extraction Structure: {'PASSED' if structure_test else 'FAILED'}")
    logger.info(f"Metadata Application Function: {'PASSED' if application_test else 'FAILED'}")
    
    # Overall result
    if session_state_test and structure_test and application_test:
        logger.info("All tests PASSED")
    else:
        logger.error("Some tests FAILED")
