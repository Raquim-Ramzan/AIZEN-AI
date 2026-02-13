# AI Assistant Backend Entry Point
# This file imports and runs the main FastAPI application from app.main

from app.main import app

# The app is now imported from app.main which includes all routes, middleware, and lifecycle management
# Run with: uvicorn server:app --host 0.0.0.0 --port 8001

if __name__ == "__main__":
    import uvicorn
    from app.config import get_settings
    
    settings = get_settings()
    uvicorn.run(
        "server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )