# app/utils/response_docs.py
"""
Reusable response documentation templates for OpenAPI/Swagger.
"""

from app.schemas.common import ErrorResponseSchema


class ResponseDocs:
    """Standard response documentation templates."""

    @staticmethod
    def success_200(model, description: str = "Operation successful"):
        """Standard 200 success response."""
        return {
            "description": description,
            "model": model,
            
        }

    @staticmethod
    def created_201(model, description: str = "Resource created successfully"):
        """Standard 201 created response."""
        return {
            "description": description,
            "model": model,
          
        }

    @staticmethod
    def validation_error_400():
        """Standard 400 validation error response."""
        return {
            "description": "Validation error",
            "model": ErrorResponseSchema,
            "content": {
                "application/json": {
                    "examples": {
                        "field_validation": {
                            "summary": "Field validation failed",
                            "value": {
                                "error": "Validation Error",
                                "code": 400,
                                "detail": "Field validation failed",
                                "error_type": "AppValidationError",
                                "field": "field_name"
                            }
                        },
                        "business_rule": {
                            "summary": "Business rule violation",
                            "value": {
                                "error": "Validation Error",
                                "code": 400,
                                "detail": "Business rule validation failed",
                                "error_type": "AppValidationError"
                            }
                        }
                    }
                }
            }
        }

    @staticmethod
    def unauthorized_401():
        """Standard 401 unauthorized response."""
        return {
            "description": "Authentication failed",
            "model": ErrorResponseSchema,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_credentials": {
                            "summary": "Invalid credentials",
                            "value": {
                                "error": "Authentication Failed",
                                "code": 401,
                                "detail": "Invalid credentials provided",
                                "error_type": "InvalidCredentialsError"
                            }
                        },
                        "token_expired": {
                            "summary": "Token expired",
                            "value": {
                                "error": "Authentication Failed",
                                "code": 401,
                                "detail": "Access token has expired",
                                "error_type": "TokenExpiredError"
                            }
                        }
                    }
                }
            }
        }

    @staticmethod
    def forbidden_403():
        """Standard 403 forbidden response."""
        return {
            "description": "Access forbidden",
            "model": ErrorResponseSchema,
            "content": {
                "application/json": {
                    "examples": {
                        "insufficient_permissions": {
                            "summary": "Insufficient permissions",
                            "value": {
                                "error": "Access Forbidden",
                                "code": 403,
                                "detail": "Insufficient permissions to access this resource",
                                "error_type": "AuthorizationError"
                            }
                        },
                        "account_inactive": {
                            "summary": "Account inactive",
                            "value": {
                                "error": "Access Forbidden",
                                "code": 403,
                                "detail": "User account is inactive",
                                "error_type": "UserInactiveError"
                            }
                        }
                    }
                }
            }
        }

    @staticmethod
    def not_found_404(resource_name: str = "Resource"):
        """Standard 404 not found response."""
        return {
            "description": f"{resource_name} not found",
            "model": ErrorResponseSchema,
            "content": {
                "application/json": {
                    "examples": {
                        "resource_not_found": {
                            "summary": f"{resource_name} does not exist",
                            "value": {
                                "error": "Not Found",
                                "code": 404,
                                "detail": f"{resource_name} not found",
                                "error_type": "NotFoundError"
                            }
                        },
                        "resource_deleted": {
                            "summary": f"{resource_name} was deleted",
                            "value": {
                                "error": "Not Found",
                                "code": 404,
                                "detail": f"{resource_name} not found",
                                "error_type": "NotFoundError"
                            }
                        }
                    }
                }
            }
        }

    @staticmethod
    def conflict_409(resource_name: str = "Resource"):
        """Standard 409 conflict response."""
        return {
            "description": f"{resource_name} already exists",
            "model": ErrorResponseSchema,
            "content": {
                "application/json": {
                    "examples": {
                        "resource_exists": {
                            "summary": f"{resource_name} already exists",
                            "value": {
                                "error": f"{resource_name} Already Exists",
                                "code": 409,
                                "detail": f"{resource_name} with this identifier already exists",
                                "error_type": f"{resource_name}AlreadyExistsError"
                            }
                        }
                    }
                }
            }
        }

    @staticmethod
    def unprocessable_entity_422():
        """Standard 422 validation error response."""
        return {
            "description": "Request validation error",
            "model": ErrorResponseSchema,
            "content": {
                "application/json": {
                    "examples": {
                        "pydantic_validation": {
                            "summary": "Pydantic validation failed",
                            "value": {
                                "error": "Validation Error",
                                "code": 422,
                                "detail": "Invalid input data",
                                "error_type": "ValidationError",
                                "field": "field_name"
                            }
                        },
                        "type_error": {
                            "summary": "Type conversion error",
                            "value": {
                                "error": "Validation Error",
                                "code": 422,
                                "detail": "Invalid data type",
                                "error_type": "ValidationError",
                                "field": "field_name"
                            }
                        }
                    }
                }
            }
        }

    @staticmethod
    def internal_server_error_500():
        """Standard 500 internal server error response."""
        return {
            "description": "Internal server error",
            "model": ErrorResponseSchema,
            "content": {
                "application/json": {
                    "examples": {
                        "database_error": {
                            "summary": "Database error",
                            "value": {
                                "error": "Database Error",
                                "code": 500,
                                "detail": "A database error occurred",
                                "error_type": "DatabaseError"
                            }
                        },
                        "service_error": {
                            "summary": "Service error",
                            "value": {
                                "error": "Service Error",
                                "code": 500,
                                "detail": "An internal service error occurred",
                                "error_type": "ServiceError"
                            }
                        },
                        "unexpected_error": {
                            "summary": "Unexpected error",
                            "value": {
                                "error": "Internal Server Error",
                                "code": 500,
                                "detail": "An unexpected error occurred",
                                "error_type": "InternalServerError"
                            }
                        }
                    }
                }
            }
        }

    @classmethod
    def standard_responses(cls, include_auth: bool = True, resource_name: str = "Resource"):
        """Get standard response documentation set."""
        responses = {
            400: cls.validation_error_400(),
            404: cls.not_found_404(resource_name),
            422: cls.unprocessable_entity_422(),
            500: cls.internal_server_error_500(),
        }
        
        if include_auth:
            responses.update({
                401: cls.unauthorized_401(),
                403: cls.forbidden_403(),
            })
        
        return responses