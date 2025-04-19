import logging
import traceback
import json
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

def log_full_exception(func):
    """
    Decorator to log full exception stack traces for metadata operations
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log the full exception stack trace
            logger.error(f"Exception in {func.__name__}: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Re-raise the exception
            raise
    
    return wrapper

def log_metadata_operation(operation_name):
    """
    Decorator to log metadata operations with detailed information
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Log the operation start
            logger.info(f"Starting metadata operation: {operation_name}")
            
            # Try to extract file information
            file_info = None
            if len(args) > 1 and hasattr(args[1], 'id'):
                file_info = f"File ID: {args[1].id}"
            
            # Log metadata values if available
            metadata_values = kwargs.get('metadata_values', None)
            if metadata_values:
                logger.info(f"Metadata values: {json.dumps(metadata_values, default=str)}")
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Log the operation success
                logger.info(f"Metadata operation {operation_name} completed successfully")
                if file_info:
                    logger.info(f"Operation details: {file_info}")
                
                return result
            except Exception as e:
                # Log the operation failure with full stack trace
                logger.error(f"Metadata operation {operation_name} failed: {str(e)}")
                if file_info:
                    logger.error(f"Operation details: {file_info}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
                
                # Re-raise the exception
                raise
        
        return wrapper
    
    return decorator
