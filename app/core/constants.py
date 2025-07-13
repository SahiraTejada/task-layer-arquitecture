from enum import Enum
from dataclasses import dataclass


class HTTPStatus(Enum):
   # Success
   OK = 200
   CREATED = 201
   NO_CONTENT = 204
   
   # Client Error
   BAD_REQUEST = 400
   UNAUTHORIZED = 401
   FORBIDDEN = 403
   NOT_FOUND = 404
   CONFLICT = 409
   UNPROCESSABLE_ENTITY = 422
   TOO_MANY_REQUESTS = 429
   
   # Server Error
   INTERNAL_SERVER_ERROR = 500
   BAD_GATEWAY = 502
   SERVICE_UNAVAILABLE = 503
   GATEWAY_TIMEOUT = 504


class ErrorSeverity(Enum):
   """Severity levels for errors with usage guidelines"""
   LOW = "low"           # No immediate attention required - normal user errors
   MEDIUM = "medium"     # Potentially problematic - requires monitoring
   HIGH = "high"         # Should be monitored - affects important functionality
   CRITICAL = "critical" # Needs urgent attention - system failure


@dataclass(frozen=True)
class ErrorCodeData:
   """Immutable dataclass for error code data"""
   code: str
   status: HTTPStatus
   message: str
   severity: ErrorSeverity
   
   @property
   def status_code(self) -> int:
       return self.status.value
   
   @property
   def is_client_error(self) -> bool:
       return 400 <= self.status_code < 500
   
   @property
   def is_server_error(self) -> bool:
       return 500 <= self.status_code < 600