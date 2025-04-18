# Deployment Instructions

## Prerequisites
Before deploying the metadata extraction app, ensure you have the following dependencies installed:

```bash
pip install -r requirements.txt
```

## Required Dependencies
The app requires the following Python packages:
- streamlit>=1.22.0
- boxsdk>=3.0.0
- pandas>=1.5.0
- matplotlib>=3.5.0
- seaborn>=0.11.0

## Common Deployment Issues

### Missing boxsdk Module
If you encounter the error `ModuleNotFoundError: No module named 'boxsdk'`, it means the Box SDK Python package is not installed in your deployment environment. To fix this:

1. Make sure you're installing dependencies in the correct Python environment
2. Run the following command:
   ```bash
   pip install boxsdk>=3.0.0
   ```
3. If you're using a virtual environment, ensure it's activated before installing dependencies

### Deployment Environment Setup
For Streamlit Cloud deployments:
1. Create a `requirements.txt` file in your repository root
2. Ensure it includes all the dependencies listed above
3. Streamlit Cloud will automatically install these dependencies during deployment

For other deployment platforms:
1. Install dependencies manually before starting the app
2. Some platforms may require a `Procfile` or similar configuration file
3. Ensure your deployment environment has access to install Python packages

## Verifying Installation
To verify that all dependencies are correctly installed:

```bash
python -c "import streamlit, boxsdk, pandas, matplotlib, seaborn; print('All dependencies successfully imported')"
```

If this command runs without errors, all required dependencies are properly installed.
