from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
import json

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging detallado de requests"""
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = False):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def dispatch(self, request: Request, call_next):
        """Intercepta requests y responses para logging"""
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # Log del request
        if self.log_requests:
            await self._log_request(request, request_id)
        
        # Ejecutar request
        response = await call_next(request)
        
        # Log del response
        process_time = time.time() - start_time
        if self.log_responses:
            await self._log_response(response, process_time, request_id)
        
        # Agregar headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    async def _log_request(self, request: Request, request_id: str):
        """Log detallado del request"""
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "client_ip": request.client.host if request.client else None
            }
        )
    
    async def _log_response(self, response, process_time: float, request_id: str):
        """Log detallado del response"""
        logger.info(
            f"Response {request_id}: {response.status_code} ({process_time:.3f}s)",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": process_time,
                "response_headers": dict(response.headers)
            }
        )
