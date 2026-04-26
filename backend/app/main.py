from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
import sys
# If this file is executed as a script (python app/main.py), ensure the
# backend directory is on sys.path so package-style imports like
# `from app.config import ...` work. This mirrors running as a package
# (python -m app.main) but keeps convenience for direct script runs.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.api import routes, websocket as ws_handler, system_routes
from app.core.brain import AIBrain
from app.core.connection_pool import get_connection_pool, close_connection_pool
from app.core.audit_logger import get_audit_logger, EventType
from app.core.metrics import get_metrics, Metrics
from app.memory.vector_store import VectorStore
from app.memory.core_memory import CoreMemory
from app.memory.conversation import ConversationManager
from app.memory.rag_manager import initialize_rag_manager
from app.memory.reranker import get_reranker
from app.memory.smart_memory import get_smart_memory_manager
from app.memory.history_manager import get_history_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Determine base data directory (cross-platform)
BASE_DIR = Path(__file__).resolve().parents[1]  # backend/
DATA_DIR = BASE_DIR / "data"

# Global instances
ai_brain = None
vector_store = None
core_memory = None
conv_manager = None
rag_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ai_brain, vector_store, core_memory, conv_manager, rag_manager
    
    logger.info("Starting AI Assistant Backend")
    logger.info(f"Environment: {get_settings().environment}")
    
    # Create data directories (cross-platform)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    Path(get_settings().chroma_persist_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize connection pool first
    conn_pool = await get_connection_pool()
    logger.info("Connection pool initialized")
    
    # Initialize audit logger
    audit_logger = await get_audit_logger()
    await audit_logger.log(EventType.SYSTEM_STARTUP, "AIZEN Backend starting")
    
    # Initialize metrics
    metrics = get_metrics()
    metrics.increment(Metrics.REQUESTS_TOTAL, labels={"type": "startup"})
    
    # Initialize components
    vector_store = VectorStore()
    await vector_store.initialize()
    
    core_memory = CoreMemory(vector_store=vector_store)
    await core_memory.initialize()
    
    ai_brain = AIBrain()
    await ai_brain.initialize()
    
    conv_manager = ConversationManager()
    await conv_manager.initialize()
    
    # Initialize RAG Manager (central orchestration)
    rag_manager = initialize_rag_manager(
        vector_store=vector_store,
        core_memory=core_memory,
        conversation_manager=conv_manager
    )
    
    # Initialize reranker
    reranker = get_reranker()
    logger.info("Reranker initialized")
    
    # Initialize smart memory manager
    smart_memory = get_smart_memory_manager(vector_store, core_memory)
    logger.info("Smart Memory Manager initialized")
    
    # Initialize history manager
    history_manager = get_history_manager()
    logger.info("History Manager initialized")
    
    # Make available to app state
    app.state.ai_brain = ai_brain
    app.state.vector_store = vector_store
    app.state.core_memory = core_memory
    app.state.conv_manager = conv_manager
    app.state.rag_manager = rag_manager
    app.state.reranker = reranker
    app.state.smart_memory = smart_memory
    app.state.history_manager = history_manager
    app.state.audit_logger = audit_logger
    app.state.metrics = metrics
    app.state.conn_pool = conn_pool
    
    logger.info("AI Assistant Backend initialized successfully")
    logger.info("="*60)
    logger.info(f"AIZEN Backend server started successfully!")
    
    # Display localhost if binding to 0.0.0.0, otherwise use the actual host
    _s = get_settings()
    display_host = "localhost" if _s.host == "0.0.0.0" else _s.host

    logger.info(f"API running at: http://{display_host}:{_s.port}")
    logger.info(f"API Documentation: http://{display_host}:{_s.port}/docs")
    logger.info(f"Health Check: http://{display_host}:{_s.port}/health")
    logger.info(f"Metrics: http://{display_host}:{_s.port}/metrics")
    logger.info(f"WebSocket: ws://{display_host}:{_s.port}/api/ws/{{client_id}}")
    logger.info("="*60)
    
    yield
    
    # Cleanup
    logger.info("Shutting down AI Assistant Backend")
    await audit_logger.log(EventType.SYSTEM_SHUTDOWN, "AIZEN Backend shutting down")
    await close_connection_pool()

app = FastAPI(
    title="AI Assistant Backend",
    description="Personal AI Assistant with Perplexity API, Ollama, LangGraph, ChromaDB, and Speech",
    version="1.0.0",
    lifespan=lifespan
)

_cors_origins = [o.strip() for o in get_settings().cors_origins.split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
from app.core.rate_limiter import RateLimitMiddleware, get_rate_limiter
app.add_middleware(RateLimitMiddleware, rate_limiter=get_rate_limiter())

app.include_router(routes.router, prefix="/api")
app.include_router(ws_handler.router, prefix="/api")
app.include_router(system_routes.router)  # System operations


@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "AI Assistant Backend",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Public health check — returns only operational status.
    Detailed diagnostics are intentionally omitted to prevent
    leaking API-key configuration to unauthenticated callers.
    """
    return {"status": "ok"}

@app.get("/metrics")
async def get_metrics_endpoint():
    """Prometheus-compatible metrics endpoint"""
    from app.core.metrics import get_metrics
    from app.core.cache import get_all_cache_stats
    from fastapi.responses import PlainTextResponse
    
    metrics = get_metrics()
    
    # Return in Prometheus format
    return PlainTextResponse(
        content=metrics.to_prometheus_format(),
        media_type="text/plain"
    )

@app.get("/metrics/json")
async def get_metrics_json():
    """Get metrics in JSON format"""
    from app.core.metrics import get_metrics
    from app.core.cache import get_all_cache_stats
    
    metrics = get_metrics()
    cache_stats = get_all_cache_stats()
    
    return {
        "metrics": metrics.get_all_metrics(),
        "cache": cache_stats
    }

if __name__ == "__main__":
    import uvicorn
    _settings = get_settings()

    print("="*60)
    print("Starting AI Assistant Backend...")
    print("="*60)

    uvicorn.run(
        "app.main:app",
        host=_settings.host,
        port=_settings.port,
        reload=_settings.debug,
        log_level="info"
    )
