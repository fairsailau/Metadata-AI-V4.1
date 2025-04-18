# Test Plan for Enhanced Box AI Metadata Extraction App

## Overview
This document outlines the testing approach for the enhanced Box AI Metadata Extraction application with document categorization and template selection features.

## Test Environment Setup
1. Ensure Python environment has all required dependencies
2. Verify Box API credentials are properly configured
3. Prepare test files of different document types:
   - Sales Contract
   - Invoice
   - Tax document
   - Financial Report
   - Employment Contract
   - PII document
   - Other document type

## Test Cases

### 1. Authentication and Startup
- **TC1.1**: Verify application starts correctly
- **TC1.2**: Verify authentication with Box works
- **TC1.3**: Verify metadata templates are retrieved at startup
- **TC1.4**: Verify template refresh functionality works

### 2. Document Categorization
- **TC2.1**: Verify document categorization UI loads correctly
- **TC2.2**: Verify document categorization process starts and completes
- **TC2.3**: Verify documents are correctly categorized into specified types
- **TC2.4**: Verify categorization results are displayed correctly
- **TC2.5**: Verify error handling for categorization failures

### 3. Metadata Template Retrieval
- **TC3.1**: Verify all metadata templates are retrieved from Box
- **TC3.2**: Verify template caching works correctly
- **TC3.3**: Verify template refresh functionality updates the cache
- **TC3.4**: Verify template matching logic suggests appropriate templates

### 4. Template Selection UI
- **TC4.1**: Verify document type to template mapping is displayed correctly
- **TC4.2**: Verify template override functionality works
- **TC4.3**: Verify freeform prompt customization for document types without templates
- **TC4.4**: Verify changes to template selections are saved correctly

### 5. Processing Integration
- **TC5.1**: Verify processing with document type-specific templates works
- **TC5.2**: Verify processing with document type-specific freeform prompts works
- **TC5.3**: Verify fallback to default extraction method works
- **TC5.4**: Verify error handling during processing

### 6. End-to-End Workflow
- **TC6.1**: Complete end-to-end workflow from file selection to metadata application
- **TC6.2**: Verify results are correctly displayed and can be applied to Box files
- **TC6.3**: Verify feedback mechanism for extraction results works

## Test Execution

### Test Case: TC1.1 - Verify application starts correctly
1. Run `streamlit run app.py`
2. Verify application loads without errors
3. Verify all UI elements are displayed correctly

### Test Case: TC2.1 - Verify document categorization UI loads correctly
1. Authenticate with Box
2. Select files in File Browser
3. Navigate to Document Categorization page
4. Verify UI elements for document categorization are displayed correctly

### Test Case: TC2.2 - Verify document categorization process starts and completes
1. Navigate to Document Categorization page with selected files
2. Click "Start Categorization" button
3. Verify progress bar and status updates are displayed
4. Verify process completes and results are displayed

### Test Case: TC3.1 - Verify all metadata templates are retrieved from Box
1. Authenticate with Box
2. Check sidebar for template count
3. Verify templates are retrieved and count matches expected number

### Test Case: TC4.1 - Verify document type to template mapping is displayed correctly
1. Complete document categorization
2. Navigate to Metadata Configuration page
3. Verify document type to template mapping is displayed
4. Verify suggested templates match expected templates for each document type

### Test Case: TC5.1 - Verify processing with document type-specific templates works
1. Complete document categorization and template selection
2. Navigate to Process Files page
3. Start processing
4. Verify each file is processed with its corresponding template
5. Verify results contain expected metadata fields

### Test Case: TC6.1 - Complete end-to-end workflow
1. Authenticate with Box
2. Select files in File Browser
3. Categorize documents
4. Configure metadata extraction with document type-specific templates
5. Process files
6. View results
7. Apply metadata to Box files
8. Verify metadata is correctly applied in Box

## Test Data
Prepare test files of different document types with known metadata that can be used to verify extraction accuracy.

## Expected Results
- All documents should be correctly categorized into the specified types
- Templates should be matched to document types based on keywords
- Processing should use the correct template or freeform prompt for each document
- Extracted metadata should match expected values for each document type
- Metadata should be correctly applied to Box files

## Test Reporting
Document any issues encountered during testing, including:
- UI issues
- Functionality issues
- Performance issues
- Error handling issues

## Post-Testing Activities
- Fix any identified issues
- Update documentation as needed
- Prepare final deliverable
