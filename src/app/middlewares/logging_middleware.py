"""
Middleware for logs in http request
"""

import time
import logging

from fastapi import Request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def logging_middleware(request: Request, call_next):
    """Middleware to log request and response information"""
    
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(f"Response: {response.status_code}")
    logger.info(f"Processing time: {process_time:.4f} seconds")
    
    # Add processing time to response headers
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
