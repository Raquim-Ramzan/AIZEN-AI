import pytest
from app.core.model_router import ModelRouter, TaskType, ModelProvider

def test_model_router_initialization():
    """Verify router loads the correct table"""
    router = ModelRouter()
    assert router.routing_table is not None
    assert TaskType.CODING in router.routing_table

def test_model_router_selection():
    """Verify router selects the preferred model from config"""
    router = ModelRouter()
    provider, model = router.select_model(TaskType.CODING)
    
    # In testing, it should use the defaults from .env or config
    assert provider == ModelProvider.GEMINI
    assert "gemini-3.1-pro" in model

def test_model_router_fallback(monkeypatch):
    """Verify router falls back to Ollama if Gemini key is missing"""
    router = ModelRouter()
    
    # Simulate missing Gemini key
    monkeypatch.setattr(router.settings, "gemini_api_key", "")
    
    # We need to mock _is_provider_available for Gemini to return False
    provider, model = router.select_model(TaskType.CODING)
    
    # If Gemini is unavailable, it should check fallbacks
    # In our current router, the fallback for coding is Groq then Ollama
    # If Groq is also unavailable (empty key in test), it goes to Ollama
    assert provider == ModelProvider.OLLAMA

def test_health_check(test_client):
    """Verify basic API health endpoint"""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_auth_bypass(test_client):
    """Verify auth bypass works in non-production environment"""
    # The hook in app/api/auth.py should allow access with "dev-user"
    response = test_client.get("/api/conversations")
    # Even if empty, it shouldn't be a 401
    assert response.status_code != 401
