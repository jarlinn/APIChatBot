from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from src.app.controllers.auth import router as auth_router
from src.app.controllers.question import router as question_router
from src.app.controllers.modality import router as modality_router
from src.app.controllers.submodality import router as submodality_router
from src.app.controllers.category import router as category_router
from src.app.controllers.profile import router as profile_router
from src.app.utils.error_handlers import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)
# from src.app.middlewares.auth_middleware import auth_middleware
# from src.app.middlewares.logging_middleware import logging_middleware

app = FastAPI(
    title="APIChatBot",
    description="API ChatBot with FastAPI",
    version="1.0.0"
)

# Registrar manejadores de errores personalizados
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Add middlewares
# app.middleware("http")(logging_middleware)
# app.middleware("http")(auth_middleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(question_router, prefix="/chat")
app.include_router(modality_router, prefix="/chat")
app.include_router(submodality_router, prefix="/chat")
app.include_router(category_router, prefix="/chat")
app.include_router(profile_router)
# Nota: El router de embeddings fue eliminado - ahora los embeddings se generan automáticamente al crear preguntas


@app.get("/")
async def root():
    return {"message": "Welcome to APIChatBot API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
