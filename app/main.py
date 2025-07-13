from datetime import datetime, timezone
import uuid
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config.settings import settings
from app.api.v1.router import api_router
from app.core.exceptions import BaseError
from app.middlewares.error_middleware import ErrorMiddleware
from app.middlewares.logging_middleware import LoggingMiddleware
from app.models import __all__
from app.config.database import engine, Base


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.PROJECT_DESCRIPTION
)


@app.exception_handler(BaseError)
async def handle_custom_errors(request: Request, exc: BaseError):
    """Maneja TODAS tus excepciones personalizadas (DuplicateResourceError, ValidationError, etc.)"""
    
    # Generar IDs si no existen
    request_id = str(uuid.uuid4())
    
    # Crear respuesta JSON usando el método que ya tienes
    response_data = exc.to_schema().model_dump(exclude_none=True)
    
    return JSONResponse(
        status_code=exc.error_code.status_code,
        content=response_data,
        headers={
            "X-Request-ID": request_id,
            "Content-Type": "application/json"
        }
    )

@app.exception_handler(RequestValidationError)
async def handle_validation_errors(request: Request, exc: RequestValidationError):
    """Maneja errores de validación de Pydantic"""
    
    request_id = str(uuid.uuid4())
    
    # Crear respuesta simple para errores de validación
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if str(loc) not in ["body"])
        errors.append({
            "field": field or "root",
            "message": error["msg"],
            "invalid_value": error.get("input")
        })
    
    response_data = {
        "error": "VAL001",
        "message": "Validation errors found",
        "status_code": 422,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "validation_errors": errors
    }
    
    return JSONResponse(
        status_code=422,
        content=response_data,
        headers={"X-Request-ID": request_id}
    )
    
app.add_middleware(LoggingMiddleware, log_requests=True, log_responses=True)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers

app = FastAPI()

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Task Manager API", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}