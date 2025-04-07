# backend/app/error_handlers.py
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException

logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handles FastAPI's built-in HTTPExceptions."""
    logger.warning(f"HTTP Exception caught: Status={exc.status_code}, Detail={exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles Pydantic validation errors."""
    # Log the detailed validation errors
    logger.warning(f"Request Validation Error: {exc.errors()}") 
    # Provide a user-friendly summary
    error_summary = []
    for error in exc.errors():
         field = " -> ".join(map(str, error.get('loc', ['unknown'])) ) # e.g., body -> field_name
         message = error.get('msg', 'Invalid input')
         error_summary.append(f"Field '{field}': {message}")
         
    detail = f"Validation failed for request: {'; '.join(error_summary)}"
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": detail, "errors": exc.errors()}, # Include detailed errors optionally
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """Handles any other unexpected exceptions."""
    # Log the full traceback for unexpected errors
    logger.exception(f"Unhandled exception caught: {exc}") 
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
    )

# Function to register handlers with the FastAPI app
def register_error_handlers(app):
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler) # Catch-all for other errors
    logger.info("Custom error handlers registered.")