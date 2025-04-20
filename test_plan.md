# Test Plan for Structured Metadata Extraction

## Test Case 1: Structured Metadata with Template (No AI Agent Override)
```json
{
  "items": [{"id": "file_id", "type": "file"}],
  "metadata_template": {
    "template_key": "template_key",
    "scope": "enterprise",
    "type": "metadata_template"
  }
}
```

## Test Case 2: Structured Metadata with Custom Fields (No AI Agent Override)
```json
{
  "items": [{"id": "file_id", "type": "file"}],
  "fields": [
    {
      "key": "vendor",
      "displayName": "Vendor",
      "type": "string",
      "description": "Vendor name"
    }
  ]
}
```

## Test Case 3: Freeform Metadata Extraction (Minimal Request)
```json
{
  "items": [{"id": "file_id", "type": "file"}],
  "prompt": "Extract key metadata from this document"
}
```

## Test Execution Steps

1. **Prepare Test Environment**
   - Set up Box API credentials
   - Create test files in Box with known content
   - Ensure metadata templates are available

2. **Execute Test Cases**
   - For each test case, make the API call with the specified format
   - Log the full request and response
   - Verify HTTP status code is 200
   - Verify response contains expected metadata fields

3. **Verify UI Label Fixes**
   - Navigate through all app pages
   - Confirm no "label got an empty value" warnings in console
   - Verify all UI elements display correctly

4. **Regression Testing**
   - Verify document categorization still works
   - Verify metadata application still works
   - Verify folder selection functionality still works

## Expected Results

1. **Structured Metadata with Template**
   - API call succeeds with 200 status code
   - Response contains metadata fields from template
   - No errors or warnings in logs

2. **Structured Metadata with Custom Fields**
   - API call succeeds with 200 status code
   - Response contains values for custom fields
   - No errors or warnings in logs

3. **Freeform Metadata Extraction**
   - API call succeeds with 200 status code
   - Response contains extracted text based on prompt
   - No errors or warnings in logs

4. **UI Elements**
   - No "label got an empty value" warnings
   - All buttons, checkboxes, and inputs display correctly
   - Navigation between pages works smoothly

## Test Results Documentation

For each test case, document:
- Request payload (with sensitive data redacted)
- Response status code
- Response payload (with sensitive data redacted)
- Any errors or warnings
- Screenshots of UI elements (if applicable)

This comprehensive testing approach ensures both the API format issues and UI label warnings are properly addressed.
