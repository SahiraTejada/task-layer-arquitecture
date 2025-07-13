# app/middlewares/error_middleware.py - COMPLETE ERROR HANDLING

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
import uuid
import logging
from app.core.error_processor import EnterpriseErrorHandler

logger = logging.getLogger(__name__)


class ErrorMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive error middleware that captures ALL exceptions.
    
    This middleware:
    1. Generates tracking IDs for all requests
    2. Catches ALL exceptions (including validation errors)
    3. Uses the EnterpriseErrorHandler to process them
    4. Returns properly formatted JSON responses
    """
    
    def __init__(self, app, debug: bool = False, enable_cors: bool = True):
        super().__init__(app)
        self.error_handler = EnterpriseErrorHandler(debug=debug, enable_cors=enable_cors)
        self.debug = debug
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique tracking IDs
        request_id = str(uuid.uuid4())
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        
        # Store in request state for access in route handlers
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        
        try:
            # Process request normally
            response = await call_next(request)
            
            # Add tracking headers to successful responses
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as exc:
            # Log the exception for debugging
            logger.error(
                f"Exception caught in middleware: {type(exc).__name__}: {str(exc)}",
                extra={
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "path": request.url.path,
                    "method": request.method
                },
                exc_info=self.debug  # Include full traceback in debug mode
            )
            
            # Use our enterprise error handler to process the exception
            return await self.error_handler.handle_error(
                request, exc, request_id, correlation_id
            )