import streamlit as st
import os
import sys
from pathlib import Path

def create_deployment_guide():
    """
    Create a deployment guide for the Box AI Metadata Extraction App
    """
    st.title("Deployment Guide")
    
    st.write("""
    ## Box AI Metadata Extraction App Deployment
    
    This guide provides instructions for deploying the Box AI Metadata Extraction App to various platforms.
    """)
    
    # Streamlit Cloud deployment
    st.subheader("Streamlit Cloud Deployment")
    
    st.write("""
    ### Prerequisites
    
    1. A GitHub account
    2. A Streamlit Cloud account (sign up at [streamlit.io/cloud](https://streamlit.io/cloud))
    
    ### Steps
    
    1. Push your app code to a GitHub repository
    2. Log in to Streamlit Cloud
    3. Click "New app"
    4. Select your GitHub repository
    5. Set the main file path to `app/app.py`
    6. Configure environment variables for sensitive information (optional)
    7. Deploy the app
    
    ### Environment Variables
    
    For security, you should store sensitive information like API keys as environment variables:
    
    - `BOX_CLIENT_ID`: Your Box app client ID
    - `BOX_CLIENT_SECRET`: Your Box app client secret
    
    ### Requirements File
    
    Make sure your repository includes a `requirements.txt` file with the following dependencies:
    
    ```
    streamlit>=1.22.0
    boxsdk>=3.0.0
    pandas>=1.5.0
    ```
    """)
    
    # Docker deployment
    st.subheader("Docker Deployment")
    
    st.write("""
    ### Prerequisites
    
    1. Docker installed on your server
    2. Basic knowledge of Docker commands
    
    ### Dockerfile
    
    Create a `Dockerfile` in your project root:
    
    ```dockerfile
    FROM python:3.10-slim
    
    WORKDIR /app
    
    COPY requirements.txt .
    RUN pip install -r requirements.txt
    
    COPY . .
    
    EXPOSE 8501
    
    CMD ["streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
    ```
    
    ### Build and Run
    
    ```bash
    # Build the Docker image
    docker build -t box-ai-metadata-app .
    
    # Run the container
    docker run -p 8501:8501 -e BOX_CLIENT_ID=your_client_id -e BOX_CLIENT_SECRET=your_client_secret box-ai-metadata-app
    ```
    
    ### Docker Compose
    
    For easier deployment, you can use Docker Compose. Create a `docker-compose.yml` file:
    
    ```yaml
    version: '3'
    
    services:
      app:
        build: .
        ports:
          - "8501:8501"
        environment:
          - BOX_CLIENT_ID=${BOX_CLIENT_ID}
          - BOX_CLIENT_SECRET=${BOX_CLIENT_SECRET}
        restart: always
    ```
    
    Then run:
    
    ```bash
    docker-compose up -d
    ```
    """)
    
    # Heroku deployment
    st.subheader("Heroku Deployment")
    
    st.write("""
    ### Prerequisites
    
    1. A Heroku account
    2. Heroku CLI installed
    
    ### Steps
    
    1. Create a `Procfile` in your project root:
    
    ```
    web: streamlit run app/app.py --server.port=$PORT --server.address=0.0.0.0
    ```
    
    2. Create a `runtime.txt` file:
    
    ```
    python-3.10.x
    ```
    
    3. Deploy to Heroku:
    
    ```bash
    # Login to Heroku
    heroku login
    
    # Create a new Heroku app
    heroku create box-ai-metadata-app
    
    # Set environment variables
    heroku config:set BOX_CLIENT_ID=your_client_id
    heroku config:set BOX_CLIENT_SECRET=your_client_secret
    
    # Push to Heroku
    git push heroku main
    ```
    """)
    
    # Local deployment
    st.subheader("Local Deployment")
    
    st.write("""
    ### Prerequisites
    
    1. Python 3.8+ installed
    2. pip package manager
    
    ### Steps
    
    1. Install dependencies:
    
    ```bash
    pip install -r requirements.txt
    ```
    
    2. Run the app:
    
    ```bash
    streamlit run app/app.py
    ```
    
    The app will be available at http://localhost:8501
    """)
    
    # Security considerations
    st.subheader("Security Considerations")
    
    st.write("""
    ### Protecting Sensitive Information
    
    - Never commit sensitive information like API keys to your repository
    - Use environment variables for all sensitive information
    - For production deployments, consider using a secrets management service
    
    ### Authentication
    
    - The app uses Box's OAuth 2.0 or JWT authentication
    - Ensure your Box app has the minimum required permissions
    - For production use, implement proper token storage and refresh mechanisms
    
    ### Data Protection
    
    - The app processes files and metadata from Box
    - No data is stored locally except temporarily during processing
    - Ensure your deployment environment complies with your organization's data protection policies
    """)
    
    return "Deployment guide created"
