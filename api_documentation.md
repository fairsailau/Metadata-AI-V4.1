# Box AI Metadata Extraction API Documentation

## Structured Metadata Extraction

### API Endpoint
```
POST https://api.box.com/2.0/ai/extract_structured
```

### Request Format
```json
{
  "items": [
    {
      "id": "file_id",
      "type": "file"
    }
  ],
  "ai_agent": {
    "type": "extract",
    "basic_text": {
      "model": "google__gemini_2_0_flash_001"
    }
  },
  "metadata_template": {
    "template_key": "template_key",
    "scope": "enterprise",
    "type": "metadata_template"
  }
}
```

### Key Parameters

#### AI Agent Configuration
- `ai_agent.type`: Must be set to `"extract"` (not `"ai_agent_extract"`)
- `ai_agent.basic_text.model`: Specify the AI model to use (e.g., `"google__gemini_2_0_flash_001"`)

#### Metadata Template
When using a template:
- `metadata_template.template_key`: The template key (not `templateKey`)
- `metadata_template.scope`: Usually `"enterprise"` or `"global"`
- `metadata_template.type`: Must be set to `"metadata_template"`

#### Custom Fields
When using custom fields instead of a template:
```json
{
  "fields": [
    {
      "key": "field_key",
      "displayName": "Field Display Name",
      "type": "string",
      "description": "Field description"
    }
  ]
}
```

- Each field must have a non-empty `displayName`
- Supported field types: `"string"`, `"enum"`, `"date"`, `"number"`, etc.

## Freeform Metadata Extraction

### API Endpoint
```
POST https://api.box.com/2.0/ai/extract
```

### Request Format
```json
{
  "items": [
    {
      "id": "file_id",
      "type": "file"
    }
  ],
  "prompt": "Extract key metadata from this document",
  "ai_agent": {
    "type": "extract",
    "basic_text": {
      "model": "google__gemini_2_0_flash_001"
    }
  }
}
```

### Key Parameters
- `prompt`: The extraction prompt for the AI model
- `ai_agent.type`: Must be set to `"extract"`

## Common Errors and Solutions

### 400 Bad Request - Invalid AI Agent Type
```json
{
  "type": "error",
  "code": "bad_request",
  "status": 400,
  "message": "Bad request",
  "context_info": {
    "errors": [
      {
        "name": "type",
        "message": "should be equal to one of the allowed values",
        "reason": "invalid_parameter"
      }
    ]
  }
}
```

**Solution**: Ensure `ai_agent.type` is set to `"extract"`, not `"ai_agent_extract"` or other values.

### Accessibility Warning - Empty Label
```
`label` got an empty value. This is discouraged for accessibility reasons
```

**Solution**: Ensure all fields have a non-empty `displayName` value.

## Best Practices

1. Always use the correct `ai_agent.type` value (`"extract"`)
2. Provide non-empty display names for all fields
3. Include the required `type` field in metadata templates
4. Use the correct property names (`template_key` not `templateKey`)
5. Handle API errors gracefully with appropriate user feedback
6. Test with both template-based and custom field-based extraction
