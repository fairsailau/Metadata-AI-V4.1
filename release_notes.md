# Release Notes - Box Metadata AI V4.1 Fixed V2

## Overview
This release fixes critical issues with structured metadata extraction and session management in the Box Metadata AI application, while preserving all the enhanced features from the previous version.

## Fixed Issues

### Structured Metadata Extraction
- Fixed API request format for structured metadata extraction
- Added required "type" field to metadata template reference
- Corrected AI agent configuration to match Box API requirements
- Improved error handling for template-based extraction

### Session Management
- Enhanced session timeout handling with configurable timeout duration
- Added activity tracking to prevent premature session expiration
- Implemented session timeout warnings and automatic logout
- Added session time remaining indicator in the sidebar

### Visual Enhancements
- Restored all visual enhancements from the previous version
- Ensured user journey guide displays correctly
- Maintained workflow visualization on the home page
- Preserved UI settings functionality

## Existing Features

### Batch Processing for Document Categorization
- Support for processing multiple files simultaneously
- Configurable batch size (1-100 files)
- Real-time progress tracking with detailed status updates
- Error handling and retry mechanisms for improved reliability

### Policies Document Type
- "Policies" document type option
- Enhanced categorization to identify policy documents
- Updated parsing logic to handle the new document type

### Folder Selection
- Ability to select entire folders for processing
- Support for recursive file retrieval from subfolders
- Enhanced UI for managing folder selections

## Installation
Simply extract the zip file and run the application using Streamlit:
```
streamlit run app.py
```

## Requirements
- Python 3.7+
- Streamlit 1.10+
- Box SDK 3.0+
- Internet connection for Box API access

## Known Issues
- Processing very large batches (100+ files) may encounter API rate limits
- Some document types may require additional training for optimal categorization
