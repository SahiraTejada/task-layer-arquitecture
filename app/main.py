from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
#from app.api.v1.router import api_router
from app.models import user, task, tag
from app.config.database import engine, Base


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API para gestión de tareas con prioridades, tags y tiempo"
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar según necesidades
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
#app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Task Manager API", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}