import streamlit as st
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def metadata_config():
    """
    Metadata configuration page
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
    
    # Initialize metadata config if not exists
    if "metadata_config" not in st.session_state:
        st.session_state.metadata_config = {
            "extraction_method": "structured",
            "use_template": True,
            "template_id": None,
            "template_scope": "enterprise",
            "custom_fields": [],
            "freeform_prompt": "Extract all relevant metadata from this document.",
            "ai_model": "azure__openai__gpt_4o_mini",
            "batch_size": 5,
            "use_document_type_templates": False
        }
    
    # Check if document categorization is available
    has_categorization = (
        "document_categorization" in st.session_state and 
        st.session_state.document_categorization.get("is_categorized", False)
    )
    
    # Document type templates option
    use_document_type_templates = st.checkbox(
        "Use document type-specific templates",
        value=st.session_state.metadata_config.get("use_document_type_templates", False),
        disabled=not has_categorization,
        help="Use different templates or freeform prompts based on document types from categorization"
    )
    
    st.session_state.metadata_config["use_document_type_templates"] = use_document_type_templates
    
    if use_document_type_templates:
        if has_categorization:
            configure_document_type_templates()
        else:
            st.warning("Document categorization is required for this option. Please categorize documents first.")
            if st.button("Go to Document Categorization"):
                st.session_state.current_page = "Document Categorization"
                st.rerun()
    else:
        # Standard metadata configuration
        configure_standard_metadata()
    
    # Continue button
    if st.button("Continue to Process Files", use_container_width=True):
        st.session_state.current_page = "Process Files"
        st.rerun()

def configure_document_type_templates():
    """
    Configure document type-specific templates
    """
    st.write("### Document Type Templates")
    st.write("Configure templates or freeform prompts for each document type.")
    
    # Get document types from categorization results
    document_types = set()
    for file_id, result in st.session_state.document_categorization["results"].items():
        document_types.add(result["document_type"])
    
    # Initialize document type to template mapping if not exists
    if "document_type_to_template" not in st.session_state:
        st.session_state.document_type_to_template = {doc_type: None for doc_type in document_types}
    
    # Initialize document type to freeform prompt mapping if not exists
    if "document_type_to_freeform_prompt" not in st.session_state:
        st.session_state.document_type_to_freeform_prompt = {doc_type: None for doc_type in document_types}
    
    # Add any new document types
    for doc_type in document_types:
        if doc_type not in st.session_state.document_type_to_template:
            st.session_state.document_type_to_template[doc_type] = None
        if doc_type not in st.session_state.document_type_to_freeform_prompt:
            st.session_state.document_type_to_freeform_prompt[doc_type] = None
    
    # Get available templates
    templates = []
    if "template_cache" in st.session_state:
        templates = st.session_state.template_cache
    
    # Configure each document type
    for doc_type in sorted(document_types):
        with st.expander(f"Configure {doc_type}", expanded=True):
            # Count files of this type
            file_count = sum(1 for file_id, result in st.session_state.document_categorization["results"].items() 
                           if result["document_type"] == doc_type)
            
            st.write(f"Files of this type: {file_count}")
            
            # Choose extraction method
            extraction_method = st.radio(
                "Extraction Method",
                options=["Structured", "Freeform"],
                index=0 if st.session_state.document_type_to_template.get(doc_type) is not None else 1,
                key=f"extraction_method_{doc_type}"
            )
            
            if extraction_method == "Structured":
                # Template selection
                if templates:
                    template_options = [(t["templateKey"], t["displayName"], t.get("scope", "enterprise")) for t in templates]
                    template_names = [f"{t[1]} ({t[2]})" for t in template_options]
                    
                    # Get current template index
                    current_template = st.session_state.document_type_to_template.get(doc_type)
                    current_index = 0
                    if current_template:
                        for i, t in enumerate(template_options):
                            if t[0] == current_template.get("templateKey"):
                                current_index = i
                                break
                    
                    selected_index = st.selectbox(
                        "Select Template",
                        options=range(len(template_names)),
                        format_func=lambda i: template_names[i],
                        index=current_index,
                        key=f"template_select_{doc_type}"
                    )
                    
                    # Update template
                    selected_key, selected_name, selected_scope = template_options[selected_index]
                    st.session_state.document_type_to_template[doc_type] = {
                        "templateKey": selected_key,
                        "displayName": selected_name,
                        "scope": selected_scope
                    }
                    
                    # Clear freeform prompt
                    st.session_state.document_type_to_freeform_prompt[doc_type] = None
                else:
                    st.warning("No templates available. Please refresh templates.")
                    st.session_state.document_type_to_template[doc_type] = None
            else:
                # Freeform prompt
                default_prompt = st.session_state.document_type_to_freeform_prompt.get(doc_type)
                if not default_prompt:
                    default_prompt = f"Extract all relevant metadata from this {doc_type.lower()} document."
                
                freeform_prompt = st.text_area(
                    "Freeform Prompt",
                    value=default_prompt,
                    height=100,
                    key=f"freeform_prompt_{doc_type}"
                )
                
                # Update freeform prompt
                st.session_state.document_type_to_freeform_prompt[doc_type] = freeform_prompt
                
                # Clear template
                st.session_state.document_type_to_template[doc_type] = None
    
    # AI model selection
    st.write("### AI Model")
    ai_models = [
        "azure__openai__gpt_4o_mini",
        "azure__openai__gpt_4o_2024_05_13",
        "google__gemini_2_0_flash_001",
        "google__gemini_2_0_flash_lite_preview",
        "google__gemini_1_5_flash_001",
        "google__gemini_1_5_pro_001",
        "aws__claude_3_haiku",
        "aws__claude_3_sonnet",
        "aws__claude_3_5_sonnet",
        "aws__claude_3_7_sonnet",
        "aws__titan_text_lite"
    ]
    
    ai_model = st.selectbox(
        "Select AI Model",
        options=ai_models,
        index=ai_models.index(st.session_state.metadata_config.get("ai_model", "azure__openai__gpt_4o_mini")) if st.session_state.metadata_config.get("ai_model") in ai_models else 0,
        help="Choose the AI model to use for metadata extraction"
    )
    
    st.session_state.metadata_config["ai_model"] = ai_model
    
    # Batch size
    st.write("### Batch Size")
    batch_size = st.number_input(
        "Number of files to process in each batch",
        min_value=1,
        max_value=10,
        value=st.session_state.metadata_config.get("batch_size", 5)
    )
    
    st.session_state.metadata_config["batch_size"] = batch_size

def configure_standard_metadata():
    """
    Configure standard metadata extraction
    """
    # Extraction method
    st.write("### Extraction Method")
    extraction_method = st.radio(
        "Select extraction method",
        options=["Structured", "Freeform"],
        index=0 if st.session_state.metadata_config["extraction_method"] == "structured" else 1,
        help="Structured extraction uses templates or custom fields, freeform extraction uses a prompt"
    )
    
    st.session_state.metadata_config["extraction_method"] = extraction_method.lower()
    
    if extraction_method == "Structured":
        configure_structured_extraction()
    else:
        configure_freeform_extraction()
    
    # AI model selection
    st.write("### AI Model")
    ai_models = [
        "azure__openai__gpt_4o_mini",
        "azure__openai__gpt_4o_2024_05_13",
        "google__gemini_2_0_flash_001",
        "google__gemini_2_0_flash_lite_preview",
        "google__gemini_1_5_flash_001",
        "google__gemini_1_5_pro_001",
        "aws__claude_3_haiku",
        "aws__claude_3_sonnet",
        "aws__claude_3_5_sonnet",
        "aws__claude_3_7_sonnet",
        "aws__titan_text_lite"
    ]
    
    ai_model = st.selectbox(
        "Select AI Model",
        options=ai_models,
        index=ai_models.index(st.session_state.metadata_config.get("ai_model", "azure__openai__gpt_4o_mini")) if st.session_state.metadata_config.get("ai_model") in ai_models else 0,
        help="Choose the AI model to use for metadata extraction"
    )
    
    st.session_state.metadata_config["ai_model"] = ai_model
    
    # Batch size
    st.write("### Batch Size")
    batch_size = st.number_input(
        "Number of files to process in each batch",
        min_value=1,
        max_value=10,
        value=st.session_state.metadata_config.get("batch_size", 5)
    )
    
    st.session_state.metadata_config["batch_size"] = batch_size

def configure_structured_extraction():
    """
    Configure structured metadata extraction
    """
    st.write("### Structured Extraction Configuration")
    
    # Template or custom fields
    use_template = st.checkbox(
        "Use metadata template",
        value=st.session_state.metadata_config["use_template"],
        help="Use an existing metadata template or define custom fields"
    )
    
    st.session_state.metadata_config["use_template"] = use_template
    
    if use_template:
        # Template selection
        templates = []
        if "template_cache" in st.session_state:
            templates = st.session_state.template_cache
        
        if templates:
            template_options = [(t["templateKey"], t["displayName"], t.get("scope", "enterprise")) for t in templates]
            template_names = [f"{t[1]} ({t[2]})" for t in template_options]
            
            # Get current template index
            current_template_id = st.session_state.metadata_config.get("template_id")
            current_index = 0
            if current_template_id:
                for i, t in enumerate(template_options):
                    if t[0] == current_template_id:
                        current_index = i
                        break
            
            selected_index = st.selectbox(
                "Select Template",
                options=range(len(template_names)),
                format_func=lambda i: template_names[i],
                index=current_index
            )
            
            # Update template
            selected_key, selected_name, selected_scope = template_options[selected_index]
            st.session_state.metadata_config["template_id"] = selected_key
            st.session_state.metadata_config["template_scope"] = selected_scope
        else:
            st.warning("No templates available. Please refresh templates.")
            st.session_state.metadata_config["template_id"] = None
    else:
        # Custom fields
        st.write("### Custom Fields")
        st.write("Define custom fields for structured extraction.")
        
        # Initialize custom fields if not exists
        if "custom_fields" not in st.session_state.metadata_config or not st.session_state.metadata_config["custom_fields"]:
            st.session_state.metadata_config["custom_fields"] = []
        
        # Add new field
        with st.expander("Add New Field"):
            col1, col2 = st.columns(2)
            
            with col1:
                field_name = st.text_input("Field Name", key="new_field_name")
            
            with col2:
                field_type = st.selectbox(
                    "Field Type",
                    options=["string", "float", "date", "enum"],
                    key="new_field_type"
                )
            
            if st.button("Add Field"):
                if field_name:
                    st.session_state.metadata_config["custom_fields"].append({
                        "type": field_type,
                        "display_name": field_name,
                        "key": field_name.lower().replace(" ", "_")
                    })
                    st.success(f"Field '{field_name}' added successfully!")
                    st.rerun()
                else:
                    st.warning("Please enter a field name")
        
        # Display and edit existing fields
        if st.session_state.metadata_config["custom_fields"]:
            st.write("### Existing Fields")
            
            for i, field in enumerate(st.session_state.metadata_config["custom_fields"]):
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{field['display_name']}**")
                
                with col2:
                    st.write(f"Type: {field['type']}")
                
                with col3:
                    if st.button("Remove", key=f"remove_field_{i}"):
                        st.session_state.metadata_config["custom_fields"].pop(i)
                        st.rerun()
        else:
            st.info("No custom fields defined yet")

def configure_freeform_extraction():
    """
    Configure freeform metadata extraction
    """
    st.write("### Freeform Extraction Configuration")
    
    # Freeform prompt
    st.write("Enter a prompt for freeform metadata extraction:")
    freeform_prompt = st.text_area(
        "",
        value=st.session_state.metadata_config.get("freeform_prompt", "Extract all relevant metadata from this document."),
        height=150
    )
    
    st.session_state.metadata_config["freeform_prompt"] = freeform_prompt
    
    # Prompt suggestions
    with st.expander("Prompt Suggestions"):
        suggestions = [
            "Extract all relevant metadata from this document.",
            "Extract the following information: document title, date, author, recipient, and key topics.",
            "Extract metadata in JSON format including document type, date, parties involved, and key terms.",
            "Identify and extract all dates, names, organizations, and monetary values from this document.",
            "Extract document metadata and organize it into categories: basic information, parties, financial details, and dates."
        ]
        
        for i, suggestion in enumerate(suggestions):
            if st.button(f"Use Suggestion {i+1}", key=f"suggestion_{i}"):
                st.session_state.metadata_config["freeform_prompt"] = suggestion
                st.rerun()
