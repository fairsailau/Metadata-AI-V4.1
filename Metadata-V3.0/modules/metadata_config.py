import streamlit as st
import logging
from typing import Dict, List, Any, Optional
import json
import pandas as pd

# Import metadata template retrieval functions
from modules.metadata_template_retrieval import get_metadata_templates, match_template_to_document_type, get_template_for_structured_extraction

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def metadata_config():
    """
    Configure metadata extraction parameters
    """
    st.title("Metadata Configuration")
    
    if not st.session_state.authenticated or not st.session_state.client:
        st.error("Please authenticate with Box first")
        return
    
    if not st.session_state.selected_files:
        st.warning("No files selected. Please select files in the File Browser first.")
        if st.button("Go to File Browser"):
            st.session_state.current_page = "File Browser"
            st.rerun()
        return
    
    st.write("Configure how metadata should be extracted from your selected files.")
    
    # Initialize session state for metadata configuration
    if "metadata_config" not in st.session_state:
        st.session_state.metadata_config = {
            "extraction_method": "structured",
            "use_template": False,
            "template_id": "",
            "custom_fields": []
        }
    
    # Check if documents have been categorized
    has_categorization = (
        "document_categorization" in st.session_state and 
        st.session_state.document_categorization.get("is_categorized", False) and
        st.session_state.document_categorization.get("results", {})
    )
    
    if not has_categorization:
        st.warning("Documents have not been categorized. It's recommended to categorize documents first for better template matching.")
        if st.button("Go to Document Categorization"):
            st.session_state.current_page = "Document Categorization"
            st.rerun()
    else:
        st.success("Documents have been categorized. Suggested templates will be based on document types.")
        
        # Display document categorization results
        with st.expander("Document Categorization Results", expanded=True):
            # Create a DataFrame for display
            results_data = []
            
            for file_id, result in st.session_state.document_categorization["results"].items():
                results_data.append({
                    "File Name": result["file_name"],
                    "Document Type": result["document_type"],
                    "Confidence": f"{result['confidence']:.2f}"
                })
            
            if results_data:
                results_df = pd.DataFrame(results_data)
                st.dataframe(results_df)
    
    # Get metadata templates
    templates = st.session_state.metadata_templates
    
    # Create mapping of document types to templates if documents have been categorized
    document_type_to_template = {}
    file_to_template = {}
    
    if has_categorization and templates:
        # Get unique document types
        document_types = set()
        for file_id, result in st.session_state.document_categorization["results"].items():
            document_types.add(result.get("document_type", "Other"))
        
        # Match templates to document types
        for document_type in document_types:
            matched_template = match_template_to_document_type(document_type, templates)
            document_type_to_template[document_type] = matched_template
        
        # Map files to templates
        for file_id, result in st.session_state.document_categorization["results"].items():
            document_type = result.get("document_type", "Other")
            file_to_template[file_id] = document_type_to_template.get(document_type)
        
        # Store mappings in session state
        st.session_state.document_type_to_template = document_type_to_template
        st.session_state.file_to_template = file_to_template
        
        # Display document type to template mapping
        with st.expander("Document Type to Template Mapping", expanded=True):
            mapping_data = []
            
            for document_type, template in document_type_to_template.items():
                template_name = "None (Freeform)"
                template_id = ""
                
                if template is not None:
                    template_name = template.get("displayName", "Unknown")
                    template_id = template.get("id", "")
                
                mapping_data.append({
                    "Document Type": document_type,
                    "Suggested Template": template_name,
                    "Template ID": template_id
                })
            
            if mapping_data:
                mapping_df = pd.DataFrame(mapping_data)
                st.dataframe(mapping_df)
    
    # Extraction method selection
    st.subheader("Extraction Method")
    
    # If we have categorization results, show a more advanced UI
    if has_categorization:
        st.write("Based on document categorization, you can choose to:")
        extraction_approach = st.radio(
            "Select extraction approach:",
            options=["Use suggested templates for each document type", "Use a single method for all files"],
            index=0,
            help="Choose whether to use different templates based on document type or a single method for all files."
        )
        
        if extraction_approach == "Use suggested templates for each document type":
            st.session_state.metadata_config["use_document_type_templates"] = True
            
            # Allow users to override template suggestions
            st.subheader("Override Template Suggestions")
            st.write("You can override the suggested templates for each document type:")
            
            # Create columns for the form
            col1, col2 = st.columns(2)
            
            # For each document type, allow overriding the template
            for document_type in document_type_to_template.keys():
                with col1:
                    st.write(f"**{document_type}**")
                
                with col2:
                    # Get all template names
                    template_options = ["None (Freeform)"] + [t.get("displayName", f"Template {i}") for i, t in enumerate(templates)]
                    
                    # Get current template index
                    current_template = document_type_to_template.get(document_type)
                    current_index = 0  # Default to None (Freeform)
                    
                    if current_template:
                        # Find the index of the current template
                        for i, t in enumerate(templates):
                            if t.get("id") == current_template.get("id"):
                                current_index = i + 1  # +1 because "None (Freeform)" is at index 0
                                break
                    
                    # Create selectbox for template selection
                    selected_template_name = st.selectbox(
                        f"Template for {document_type}",
                        options=template_options,
                        index=current_index,
                        key=f"template_override_{document_type}"
                    )
                    
                    # Update the template mapping based on selection
                    if selected_template_name == "None (Freeform)":
                        document_type_to_template[document_type] = None
                    else:
                        # Find the template by name
                        for t in templates:
                            if t.get("displayName") == selected_template_name:
                                document_type_to_template[document_type] = t
                                break
            
            # Update file to template mapping based on new document type to template mapping
            for file_id, result in st.session_state.document_categorization["results"].items():
                document_type = result.get("document_type", "Other")
                file_to_template[file_id] = document_type_to_template.get(document_type)
            
            # Store updated mappings in session state
            st.session_state.document_type_to_template = document_type_to_template
            st.session_state.file_to_template = file_to_template
            
            # Allow customizing freeform prompts for document types without templates
            st.subheader("Customize Freeform Prompts")
            st.write("For document types without templates, you can customize the freeform extraction prompt:")
            
            # Initialize freeform prompts if not exists
            if "document_type_to_freeform_prompt" not in st.session_state:
                st.session_state.document_type_to_freeform_prompt = {}
            
            # For each document type without a template, allow customizing the prompt
            for document_type, template in document_type_to_template.items():
                if not template:
                    # Get current prompt or use default
                    current_prompt = st.session_state.document_type_to_freeform_prompt.get(
                        document_type, 
                        f"Extract key metadata from this {document_type.lower()} document including dates, names, amounts, and other important information."
                    )
                    
                    # Create text area for prompt customization
                    custom_prompt = st.text_area(
                        f"Prompt for {document_type}",
                        value=current_prompt,
                        height=100,
                        key=f"freeform_prompt_{document_type}"
                    )
                    
                    # Update the prompt mapping
                    st.session_state.document_type_to_freeform_prompt[document_type] = custom_prompt
        else:
            # Use a single method for all files
            st.session_state.metadata_config["use_document_type_templates"] = False
            
            # Standard extraction method selection
            extraction_method = st.radio(
                "Select extraction method:",
                options=["Structured", "Freeform"],
                index=0 if st.session_state.metadata_config["extraction_method"] == "structured" else 1,
                help="Structured extraction uses predefined fields. Freeform extraction uses a prompt to extract metadata."
            )
            
            st.session_state.metadata_config["extraction_method"] = extraction_method.lower()
            
            # Configure based on selected method
            if extraction_method.lower() == "structured":
                configure_structured_extraction()
            else:
                configure_freeform_extraction()
    else:
        # Standard extraction method selection for when no categorization is available
        extraction_method = st.radio(
            "Select extraction method:",
            options=["Structured", "Freeform"],
            index=0 if st.session_state.metadata_config["extraction_method"] == "structured" else 1,
            help="Structured extraction uses predefined fields. Freeform extraction uses a prompt to extract metadata."
        )
        
        st.session_state.metadata_config["extraction_method"] = extraction_method.lower()
        
        # Configure based on selected method
        if extraction_method.lower() == "structured":
            configure_structured_extraction()
        else:
            configure_freeform_extraction()
    
    # AI model configuration
    st.subheader("AI Model Configuration")
    
    if "ai_model" not in st.session_state.metadata_config:
        st.session_state.metadata_config["ai_model"] = "azure__openai__gpt_4o_mini"
    
    st.session_state.metadata_config["ai_model"] = st.selectbox(
        "Select AI Model",
        options=["azure__openai__gpt_4o_mini", "azure__openai__gpt_4o", "anthropic__claude_3_haiku"],
        index=["azure__openai__gpt_4o_mini", "azure__openai__gpt_4o", "anthropic__claude_3_haiku"].index(st.session_state.metadata_config["ai_model"])
    )
    
    # Batch processing configuration
    st.subheader("Batch Processing Configuration")
    
    if "batch_size" not in st.session_state.metadata_config:
        st.session_state.metadata_config["batch_size"] = 5
    
    st.session_state.metadata_config["batch_size"] = st.slider(
        "Batch Size",
        min_value=1,
        max_value=25,
        value=st.session_state.metadata_config["batch_size"],
        help="Number of files to process in parallel. Maximum is 25."
    )
    
    # Continue button
    st.write("---")
    if st.button("Continue to Processing", use_container_width=True):
        # Validate configuration
        if st.session_state.metadata_config.get("use_document_type_templates", False):
            # When using document type templates, no additional validation needed
            st.session_state.current_page = "Process Files"
            st.rerun()
        elif st.session_state.metadata_config["extraction_method"] == "structured" and not st.session_state.metadata_config["use_template"] and not st.session_state.metadata_config["custom_fields"]:
            st.error("Please define at least one field for structured extraction.")
        elif st.session_state.metadata_config["extraction_method"] == "freeform" and not st.session_state.metadata_config["freeform_prompt"]:
            st.error("Please provide a prompt for freeform extraction.")
        else:
            st.session_state.current_page = "Process Files"
            st.rerun()
    
    # Debug information (can be removed in production)
    with st.expander("Debug: Current Configuration"):
        st.json(st.session_state.metadata_config)

def configure_structured_extraction():
    """
    Configure structured extraction parameters
    """
    st.subheader("Structured Extraction Configuration")
    
    # Option to use existing template or custom fields
    use_template = st.checkbox(
        "Use existing metadata template",
        value=st.session_state.metadata_config["use_template"],
        help="Select an existing metadata template or define custom fields"
    )
    
    st.session_state.metadata_config["use_template"] = use_template
    
    if use_template:
        # Template selection
        st.write("#### Select Metadata Template")
        
        # Get templates from session state
        templates = st.session_state.metadata_templates
        
        if not templates:
            st.warning("No metadata templates available. Please refresh templates or define custom fields.")
        else:
            # Create template options
            template_options = [t.get("displayName", f"Template {i}") for i, t in enumerate(templates)]
            
            # Get current template index
            current_template_id = st.session_state.metadata_config["template_id"]
            selected_template_index = 0
            
            for i, template in enumerate(templates):
                if template.get("id") == current_template_id:
                    selected_template_index = i
                    break
            
            # Create selectbox for template selection
            selected_template_name = st.selectbox(
                "Select a template:",
                options=template_options,
                index=selected_template_index
            )
            
            # Update template ID in session state
            for template in templates:
                if template.get("displayName") == selected_template_name:
                    st.session_state.metadata_config["template_id"] = template.get("id")
                    
                    # Display template details
                    st.write(f"Template ID: {template.get('id')}")
                    st.write(f"Template Key: {template.get('templateKey')}")
                    st.write(f"Scope: {template.get('scope')}")
                    
                    # Display fields if available
                    if "fields" in template:
                        st.write("#### Template Fields")
                        for field in template["fields"]:
                            st.write(f"- {field.get('displayName')} ({field.get('type')})")
    else:
        # Custom fields definition
        st.write("#### Define Custom Fields")
        
        # Initialize custom fields if not exists
        if "custom_fields" not in st.session_state.metadata_config:
            st.session_state.metadata_config["custom_fields"] = []
        
        # Display existing fields
        if st.session_state.metadata_config["custom_fields"]:
            st.write("Current fields:")
            
            # Create a DataFrame for display
            fields_data = []
            
            for i, field in enumerate(st.session_state.metadata_config["custom_fields"]):
                fields_data.append({
                    "Field Name": field["display_name"],
                    "Field Type": field["type"],
                    "Field Key": field["key"]
                })
            
            fields_df = pd.DataFrame(fields_data)
            st.dataframe(fields_df)
            
            # Option to remove fields
            if st.button("Remove All Fields"):
                st.session_state.metadata_config["custom_fields"] = []
                st.rerun()
        
        # Add new field
        st.write("Add a new field:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            field_name = st.text_input("Field Name", key="new_field_name")
        
        with col2:
            field_type = st.selectbox(
                "Field Type",
                options=["string", "float", "date", "enum"],
                key="new_field_type"
            )
        
        # Add field button
        if st.button("Add Field"):
            if field_name:
                # Create field key from name (lowercase, replace spaces with underscores)
                field_key = field_name.lower().replace(" ", "_")
                
                # Add field to custom fields
                st.session_state.metadata_config["custom_fields"].append({
                    "display_name": field_name,
                    "key": field_key,
                    "type": field_type
                })
                
                st.success(f"Field '{field_name}' added successfully!")
                st.rerun()
            else:
                st.warning("Please enter a field name.")

def configure_freeform_extraction():
    """
    Configure freeform extraction parameters
    """
    st.subheader("Freeform Extraction Configuration")
    
    # Initialize freeform prompt if not exists
    if "freeform_prompt" not in st.session_state.metadata_config:
        st.session_state.metadata_config["freeform_prompt"] = "Extract key metadata from this document including dates, names, amounts, and other important information."
    
    # Freeform prompt input
    st.session_state.metadata_config["freeform_prompt"] = st.text_area(
        "Extraction Prompt",
        value=st.session_state.metadata_config["freeform_prompt"],
        height=150,
        help="Provide a prompt for the AI to extract metadata from the document."
    )
    
    # Prompt suggestions
    st.write("#### Prompt Suggestions")
    
    prompt_suggestions = {
        "General": "Extract key metadata from this document including dates, names, amounts, and other important information.",
        "Invoice": "Extract invoice metadata including invoice number, date, due date, total amount, tax amount, vendor name, and line items.",
        "Contract": "Extract contract metadata including parties involved, effective date, termination date, contract value, and key terms.",
        "Resume": "Extract resume metadata including name, contact information, education, work experience, skills, and certifications."
    }
    
    selected_suggestion = st.selectbox(
        "Select a suggestion:",
        options=list(prompt_suggestions.keys()),
        index=0
    )
    
    if st.button("Use Suggestion"):
        st.session_state.metadata_config["freeform_prompt"] = prompt_suggestions[selected_suggestion]
        st.rerun()
