import unittest
from unittest.mock import MagicMock, patch
import json
import streamlit as st
from boxsdk import Client, BoxAPIException

# Import the module to test
# Note: This will be imported when running the test
# from .direct_metadata_application_enhanced_fixed import apply_metadata_to_file_direct

class TestMetadataApplication(unittest.TestCase):
    """
    Unit tests for metadata application functionality
    """
    
    def setUp(self):
        """Set up test environment"""
        # Mock session state
        if not hasattr(st, 'session_state'):
            setattr(st, 'session_state', {})
        
        # Create mock client
        self.mock_client = MagicMock(spec=Client)
        
        # Create mock file object
        self.mock_file = MagicMock()
        self.mock_client.file.return_value = self.mock_file
        
        # Create mock metadata object
        self.mock_metadata = MagicMock()
        self.mock_file.metadata.return_value = self.mock_metadata
        
        # Test data
        self.file_id = "12345"
        self.file_name = "test_file.pdf"
        self.metadata_values = {
            "title": "Test Document",
            "author": "Test Author",
            "date": "2025-04-19"
        }
        
        # Add file name mapping to session state for testing
        st.session_state.file_id_to_file_name = {
            self.file_id: self.file_name
        }
    
    def test_metadata_create_success(self):
        """Test successful metadata creation"""
        # Import here to avoid circular imports during testing
        from direct_metadata_application_enhanced_fixed import apply_metadata_to_file_direct
        
        # Configure mock
        self.mock_metadata.create.return_value = self.metadata_values
        
        # Call function
        result = apply_metadata_to_file_direct(self.mock_client, self.file_id, self.metadata_values)
        
        # Verify result
        self.assertTrue(result["success"])
        self.assertEqual(result["file_id"], self.file_id)
        self.assertEqual(result["file_name"], self.file_name)
        self.assertEqual(result["metadata"], self.metadata_values)
        
        # Verify mock calls
        self.mock_client.file.assert_called_once_with(file_id=self.file_id)
        self.mock_file.metadata.assert_called_once_with("global", "properties")
        self.mock_metadata.create.assert_called_once_with(self.metadata_values)
    
    def test_metadata_already_exists(self):
        """Test handling of 'already exists' error"""
        # Import here to avoid circular imports during testing
        from direct_metadata_application_enhanced_fixed import apply_metadata_to_file_direct
        
        # Configure mock to raise exception on create but succeed on update
        self.mock_metadata.create.side_effect = BoxAPIException(
            status=409, 
            code="metadata_already_exists", 
            message="Metadata already exists"
        )
        self.mock_metadata.update.return_value = self.metadata_values
        
        # Call function
        result = apply_metadata_to_file_direct(self.mock_client, self.file_id, self.metadata_values)
        
        # Verify result
        self.assertTrue(result["success"])
        self.assertEqual(result["file_id"], self.file_id)
        self.assertEqual(result["metadata"], self.metadata_values)
        
        # Verify update was called with correct operations
        self.mock_metadata.update.assert_called_once()
        # Check that operations were created correctly
        call_args = self.mock_metadata.update.call_args[0][0]
        self.assertEqual(len(call_args), len(self.metadata_values))
        for op in call_args:
            self.assertEqual(op["op"], "replace")
            self.assertTrue(op["path"].startswith("/"))
            key = op["path"][1:]  # Remove leading slash
            self.assertEqual(op["value"], self.metadata_values[key])
    
    def test_metadata_create_error(self):
        """Test handling of creation error"""
        # Import here to avoid circular imports during testing
        from direct_metadata_application_enhanced_fixed import apply_metadata_to_file_direct
        
        # Configure mock to raise exception
        error_message = "API error"
        self.mock_metadata.create.side_effect = BoxAPIException(
            status=400, 
            code="error", 
            message=error_message
        )
        
        # Call function
        result = apply_metadata_to_file_direct(self.mock_client, self.file_id, self.metadata_values)
        
        # Verify result
        self.assertFalse(result["success"])
        self.assertEqual(result["file_id"], self.file_id)
        self.assertIn(error_message, result["error"])
        
        # Verify update was not called
        self.mock_metadata.update.assert_not_called()
    
    def test_empty_metadata_values(self):
        """Test handling of empty metadata values"""
        # Import here to avoid circular imports during testing
        from direct_metadata_application_enhanced_fixed import apply_metadata_to_file_direct
        
        # Call function with empty metadata
        result = apply_metadata_to_file_direct(self.mock_client, self.file_id, {})
        
        # Verify result
        self.assertFalse(result["success"])
        self.assertEqual(result["file_id"], self.file_id)
        self.assertIn("No metadata", result["error"])
        
        # Verify create was not called
        self.mock_metadata.create.assert_not_called()

if __name__ == '__main__':
    unittest.main()
