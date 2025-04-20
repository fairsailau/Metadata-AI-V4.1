# Box AI Metadata Extraction API Documentation

## Structured Metadata Extraction

### API Endpoint
```
POST https://api.box.com/2.0/ai/extract_structured
```

### Request Format - SIMPLIFIED APPROACH
```json
{
  "items": [
    {
      "id": "file_id",
      "type": "file"
    }
  ],
  "metadata_template": {
    "template_key": "template_key",
    "scope": "enterprise",
    "type": "metadata_template"
  }
}
```

### Key Parameters

#### Items Array (Required)
- `items`: Array containing file references
  - `id`: Box file ID
  - `type`: Must be "file"

#### Metadata Template (Required for template-based extraction)
- `metadata_template.template_key`: The template key (not `templateKey`)
- `metadata_template.scope`: Usually `"enterprise"` or `"global"`
- `metadata_template.type`: Must be set to `"metadata_template"`

#### Custom Fields (Alternative to metadata_template)
```json
{
  "items": [
    {
      "id": "file_id",
      "type": "file"
    }
  ],
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

### Important Notes
- **DO NOT include the `ai_agent` field** - Box will use the default agent
- If you must override the AI agent, consult Box API documentation for exact format
- Always include the required `type: "metadata_template"` field in template references

## Freeform Metadata Extraction

### API Endpoint
```
POST https://api.box.com/2.0/ai/extract
```

### Request Format - SIMPLIFIED APPROACH
```json
{
  "items": [
    {
      "id": "file_id",
      "type": "file"
    }
  ],
  "prompt": "Extract key metadata from this document"
}
```

### Key Parameters
- `prompt`: The extraction prompt for the AI model
- **DO NOT include the `ai_agent` field** unless absolutely necessary

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

**Solution**: Remove the `ai_agent` field entirely from your request.

### Accessibility Warning - Empty Label
```
`label` got an empty value. This is discouraged for accessibility reasons
```

**Solution**: Ensure all UI elements have a non-empty label and use `label_visibility="collapsed"` if you want to hide it.

## Best Practices

1. **Use minimal request format** - Only include required fields
2. **Let Box choose the default AI agent** - Don't override unless necessary
3. **Always include required type fields** in metadata templates
4. **Use correct property names** (`template_key` not `templateKey`)
5. **Provide non-empty labels** for all UI elements
6. **Handle API errors gracefully** with appropriate user feedback
7. **Test with both template-based and custom field-based extraction**
