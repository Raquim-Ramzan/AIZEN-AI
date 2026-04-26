import os
from unittest.mock import MagicMock, patch

import pytest

# Set dummy environment variables for testing
os.environ["ENV"] = "testing"
os.environ["GEMINI_API_KEY"] = "test_gemini_key"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test_supabase_key"
os.environ["MODEL_EMBEDDING"] = "BAAI/bge-small-en-v1.5"


@pytest.fixture(autouse=True)
def mock_google_genai():
    """Mock Google Generative AI SDK globally"""
    with (
        patch("google.generativeai.configure"),
        patch("google.generativeai.GenerativeModel") as mock_model,
    ):
        # Setup mock response for generate_content
        instance = mock_model.return_value
        mock_response = MagicMock()
        mock_response.text = "Mocked AI response"
        instance.generate_content.return_value = mock_response

        yield mock_model


@pytest.fixture(autouse=True)
def mock_supabase():
    """Mock Supabase Client globally"""
    with patch("app.core.supabase.create_client") as mock_client:
        client_instance = MagicMock()
        mock_client.return_value = client_instance

        # Mock common table operations
        table_mock = MagicMock()
        client_instance.table.return_value = table_mock
        table_mock.select.return_value = table_mock
        table_mock.insert.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=[], error=None)

        yield client_instance


@pytest.fixture
def test_client():
    """FastAPI TestClient fixture"""
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


@pytest.fixture
def mock_fastembed():
    """Mock FastEmbed for offline testing"""
    with patch("fastembed.TextEmbedding") as mock_embed:
        instance = mock_embed.return_value
        instance.embed.return_value = iter([[0.1] * 384])
        yield mock_embed
