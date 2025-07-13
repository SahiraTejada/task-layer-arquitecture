from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.api.v1.routes import api_router
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

app.add_middleware(ErrorMiddleware, debug=True)
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