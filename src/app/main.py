"""main module"""

from fastapi import FastAPI, HTTPException
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
    general_exception_handler,
    custom_http_exception_handler
)
from src.app.schemas.error import CustomHTTPException

app = FastAPI(
    title="APIChatBot",
    description="API ChatBot with FastAPI",
    version="1.0.0"
)

# Register custom error handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(CustomHTTPException, custom_http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

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


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
