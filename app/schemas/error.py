from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class ErrorResponseSchema(BaseModel):
    """Base schema for all error responses"""
    
    error: str = Field(..., description="Unique error code", example="AUTH001")
    message: str = Field(..., description="User-friendly message", example="Invalid credentials")
    status_code: int = Field(..., description="HTTP status code", example=401)
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: str = Field(..., description="Request ID", example="req_abc123")
    
    # Optional fields
    path: Optional[str] = Field(None, description="Error path", example="/api/v1/auth/login")
    method: Optional[str] = Field(None, description="HTTP method", example="POST")
    field: Optional[str] = Field(None, description="Specific field", example="email")
    resource_id: Optional[str] = Field(None, description="Resource ID", example="user_123")
    resource_type: Optional[str] = Field(None, description="Resource type", example="User")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    suggestions: Optional[List[str]] = Field(None, description="Suggestions to resolve")
    trace_id: Optional[str] = Field(None, description="Trace ID", example="trace_xyz789")
    correlation_id: Optional[str] = Field(None, description="Correlation ID", example="corr_def456")

    @field_validator('status_code')
    def validate_status_code(cls, v):
        if not (200 <= v <= 599):
            raise ValueError('Status code must be between 200 and 599')
        return v

    @field_validator('suggestions')
    def validate_suggestions(cls, v):
        if v is not None and len(v) > 10:
            raise ValueError('Maximum 10 suggestions allowed')
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "error": "AUTH001",
                    "message": "Invalid credentials",
                    "status_code": 401,
                    "timestamp": "2024-01-15T10:30:00Z",
                    "request_id": "req_abc123",
                    "path": "/api/v1/auth/login",
                    "method": "POST",
                    "field": "password",
                    "suggestions": ["Check your password", "Use 'Forgot Password' option"]
                },
                {
                    "error": "RES001", 
                    "message": "User not found",
                    "status_code": 404,
                    "timestamp": "2024-01-15T10:31:00Z",
                    "request_id": "req_def456",
                    "resource_type": "User",
                    "resource_id": "123",
                    "suggestions": ["Verify that the user ID is correct"]
                }
            ]
        }


class ValidationErrorDetail(BaseModel):
    """Specific validation error detail"""
    
    field: str = Field(..., description="Field that failed", example="email")
    message: str = Field(..., description="Error message", example="Invalid format")
    invalid_value: Optional[Any] = Field(None, description="Invalid value", example="bad-email")
    constraint: Optional[str] = Field(None, description="Violated constraint", example="email_format")
    expected_type: Optional[str] = Field(None, description="Expected type", example="email")
    allowed_values: Optional[List[str]] = Field(None, description="Allowed values", example=["red", "green", "blue"])

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "field": "email",
                    "message": "Invalid email format",
                    "invalid_value": "not-an-email",
                    "constraint": "email_format",
                    "expected_type": "email"
                },
                {
                    "field": "age",
                    "message": "Age must be between 18 and 100",
                    "invalid_value": 150,
                    "constraint": "range",
                    "expected_type": "integer"
                },
                {
                    "field": "status",
                    "message": "Status must be one of the allowed values",
                    "invalid_value": "invalid_status",
                    "constraint": "choice",
                    "allowed_values": ["active", "inactive", "pending"]
                }
            ]
        }


class ValidationErrorResponseSchema(ErrorResponseSchema):
    """Schema for validation errors with specific details"""
    
    validation_errors: List[ValidationErrorDetail] = Field(
        default_factory=list,
        description="Detailed list of validation errors",
        min_items=1
    )

    @field_validator('validation_errors')
    def validate_errors_not_empty(cls, v):
        if len(v) == 0:
            raise ValueError('validation_errors cannot be empty for validation errors')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "error": "VAL001",
                "message": "Validation errors found",
                "status_code": 422,
                "timestamp": "2024-01-15T10:30:00Z",
                "request_id": "req_abc123",
                "path": "/api/v1/users",
                "method": "POST",
                "validation_errors": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "invalid_value": "bad-email",
                        "constraint": "email_format"
                    },
                    {
                        "field": "password",
                        "message": "Password must contain at least 8 characters",
                        "constraint": "min_length_8"
                    },
                    {
                        "field": "age",
                        "message": "Age must be greater than 18",
                        "invalid_value": 16,
                        "constraint": "min_value_18"
                    }
                ],
                "suggestions": [
                    "Review the fields marked as invalid",
                    "Check the documentation for expected formats"
                ]
            }
        }


class BusinessErrorResponseSchema(ErrorResponseSchema):
    """Schema for business rule errors"""
    
    rule_name: Optional[str] = Field(None, description="Name of violated rule", example="max_login_attempts")
    rule_description: Optional[str] = Field(None, description="Description of the rule", example="Maximum 5 login attempts per hour")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Rule context data")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "BIZ001",
                "message": "Too many login attempts",
                "status_code": 429,
                "timestamp": "2024-01-15T10:30:00Z",
                "request_id": "req_abc123",
                "path": "/api/v1/auth/login",
                "method": "POST",
                "rule_name": "max_login_attempts",
                "rule_description": "Maximum 5 login attempts per hour per user",
                "context_data": {
                    "user_id": "user_123",
                    "attempts_count": 6,
                    "max_attempts": 5,
                    "window_minutes": 60,
                    "next_attempt_allowed_at": "2024-01-15T11:30:00Z"
                },
                "suggestions": [
                    "Wait 1 hour before the next attempt",
                    "Use the 'Forgot Password' option if you don't remember your credentials",
                    "Contact support if you think this is an error"
                ]
            }
        }