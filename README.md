# Enhanced Box AI Metadata Extraction App

## Overview
This repository contains an enhanced version of the Box AI Metadata Extraction application with new features for document categorization and template selection. The application connects to Box.com and uses Box AI API to extract metadata from files and apply it at scale.

## New Features

### Document Categorization
- Preprocessing step that uses Box AI to categorize documents into predefined types
- Supports document types: Sales Contract, Invoices, Tax, Financial Report, Employment Contract, PII, and Other
- Displays categorization results with confidence scores and reasoning

### Metadata Template Retrieval
- Retrieves existing metadata templates from Box at application startup
- Caches templates to avoid unnecessary API calls
- Provides template refresh functionality
- Matches templates to document types based on categorization results

### Template Selection
- Displays document type to template mapping
- Allows overriding suggested templates for each document type
- Provides customizable freeform prompts for document types without templates

### Processing Integration
- Uses document type-specific templates for structured extraction
- Uses customized freeform prompts for document types without templates
- Provides enhanced error handling and retry mechanisms

## Installation

1. Clone the repository:
```
git clone https://github.com/fairsailau/Metadata-V3.0.git
cd Metadata-V3.0
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Run the application:
```
streamlit run app.py
```

## User Workflow

1. **Authentication**: Authenticate with Box
2. **File Selection**: Select files in the File Browser
3. **Document Categorization**: Categorize documents using Box AI
4. **Template Selection**: Review and optionally override suggested templates
5. **Processing**: Process files with the appropriate templates or freeform prompts
6. **Results Review**: Review extraction results
7. **Metadata Application**: Apply extracted metadata to Box files

## Documentation

- [Implementation Guide](implementation_guide_enhanced.md): Detailed documentation of the implementation
- [Test Plan](test_plan.md): Comprehensive test plan for the enhanced application

## Project Structure

- `app.py`: Main application file
- `modules/`: Application modules
  - `authentication.py`: Box authentication
  - `document_categorization.py`: Document categorization using Box AI
  - `file_browser.py`: File browser for selecting Box files
  - `metadata_config.py`: Metadata configuration with template selection
  - `metadata_extraction.py`: Metadata extraction functions
  - `metadata_template_retrieval.py`: Metadata template retrieval from Box
  - `processing.py`: File processing with document type-specific templates
  - `results_viewer.py`: Results viewer
  - `direct_metadata_application_enhanced.py`: Metadata application to Box files

## Requirements

- Python 3.7+
- Streamlit
- Box SDK
- Pandas
- Matplotlib
- Seaborn

## License

This project is licensed under the MIT License - see the LICENSE file for details.
