import streamlit as st
import logging
import time
import json
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_metadata_templates(client, force_refresh=False):
    """
    Retrieve metadata templates from Box
    
    Args:
        client: Box client
        force_refresh: Force refresh of templates
        
    Returns:
        dict: Metadata templates
    """
    # Check if templates are already cached
    if not force_refresh and hasattr(st.session_state, "metadata_templates") and st.session_state.metadata_templates:
        logger.info(f"Using cached metadata templates: {len(st.session_state.metadata_templates)} templates")
        return st.session_state.metadata_templates
    
    try:
        # Get enterprise ID
        enterprise_id = None
        user = client.user().get()
        enterprise = user.enterprise
        if enterprise:
            enterprise_id = enterprise.id
        
        if not enterprise_id:
            logger.warning("Could not determine enterprise ID")
            st.session_state.metadata_templates = {}
            return {}
        
        # Get metadata templates
        templates = {}
        template_list = client.metadata_template().get_enterprise_templates()
        
        for template in template_list:
            template_key = template.templateKey
            template_id = f"enterprise_{enterprise_id}_{template_key}"
            
            # Get template schema
            template_schema = client.metadata_template(template_id).get()
            
            # Store template
            templates[template_id] = {
                "id": template_id,
                "key": template_key,
                "displayName": template_schema.displayName,
                "fields": template_schema.fields,
                "hidden": template_schema.hidden
            }
        
        # Cache templates
        st.session_state.metadata_templates = templates
        st.session_state.template_cache_timestamp = time.time()
        
        logger.info(f"Retrieved {len(templates)} metadata templates")
        return templates
    
    except Exception as e:
        logger.error(f"Error retrieving metadata templates: {str(e)}")
        st.session_state.metadata_templates = {}
        return {}

def initialize_template_state():
    """
    Initialize template-related session state variables
    """
    # Template cache
    if not hasattr(st.session_state, "metadata_templates"):
        st.session_state.metadata_templates = {}
        logger.info("Initialized metadata_templates in session state")
    
    # Template cache timestamp
    if not hasattr(st.session_state, "template_cache_timestamp"):
        st.session_state.template_cache_timestamp = None
        logger.info("Initialized template_cache_timestamp in session state")
    
    # Document type to template mapping
    if not hasattr(st.session_state, "document_type_to_template"):
        st.session_state.document_type_to_template = {
            "Sales Contract": None,
            "Invoices": None,
            "Tax": None,
            "Financial Report": None,
            "Employment Contract": None,
            "PII": None,
            "Other": None
        }
        logger.info("Initialized document_type_to_template in session state")

def get_template_by_id(template_id):
    """
    Get template by ID
    
    Args:
        template_id: Template ID
        
    Returns:
        dict: Template or None if not found
    """
    if not template_id:
        return None
    
    if not hasattr(st.session_state, "metadata_templates") or not st.session_state.metadata_templates:
        return None
    
    return st.session_state.metadata_templates.get(template_id)

def get_template_by_document_type(document_type):
    """
    Get template by document type
    
    Args:
        document_type: Document type
        
    Returns:
        dict: Template or None if not found
    """
    if not document_type:
        return None
    
    if not hasattr(st.session_state, "document_type_to_template"):
        return None
    
    template_id = st.session_state.document_type_to_template.get(document_type)
    if not template_id:
        return None
    
    return get_template_by_id(template_id)

def map_document_type_to_template(document_type, template_id):
    """
    Map document type to template
    
    Args:
        document_type: Document type
        template_id: Template ID
    """
    if not hasattr(st.session_state, "document_type_to_template"):
        st.session_state.document_type_to_template = {}
    
    st.session_state.document_type_to_template[document_type] = template_id
    logger.info(f"Mapped document type '{document_type}' to template '{template_id}'")
