# AI Assistant Backend

A powerful personal AI assistant backend built with FastAPI, featuring Perplexity API integration, Ollama local models, ChromaDB vector store, LangGraph orchestration, and speech capabilities.

## Features

### Core AI Brain
- **Perplexity API**: Access to GPT-5o, Claude Sonnet 4.5, Gemini 2.5 Pro, Grok-4
- **Ollama Local**: Privacy-focused local inference with Llama 3.1, Qwen 2.5, Deepseek Coder
- **Intelligent Routing**: Automatic selection between cloud and local models based on task complexity

### Memory System (Two-Tier)
- **Core Memory**: Persistent knowledge shared across all conversations (JSON + ChromaDB)
- **Conversation Threads**: Isolated conversation history (MongoDB)
- **Vector Search**: Semantic search with ChromaDB for relevant context retrieval

### Tool System
- **Web Search**: DuckDuckGo and Wikipedia integration
- **File Operations**: Safe sandboxed file management
- **Code Execution**: Python code execution with timeout protection
- **Calendar**: Task and reminder management
- **System Monitoring**: Resource usage and process information

### Speech Features
- **Faster-Whisper STT**: Local speech-to-text transcription
- **Piper TTS**: High-quality local text-to-speech synthesis

### API Architecture
- **REST API**: Full CRUD operations for conversations, messages, memory, and tools
- **WebSocket**: Real-time streaming responses with token-by-token updates
- **LangGraph Orchestration**: Multi-step task planning and execution

## Project Structure

```
backend/
├── app/
│   ├── core/           # AI brain, memory, planner, executor
│   ├── tools/          # Tool implementations
│   ├── memory/         # Vector store, conversations, core memory
│   ├── api/            # REST routes, WebSocket, models
│   ├── speech/         # STT and TTS
│   ├── main.py         # FastAPI entry point
│   └── config.py       # Configuration management
├── data/               # Persistent storage
│   ├── core_memory.json
│   ├── conversations.db
│   ├── vector_store/
│   └── user_files/
└── requirements.txt
```

## Installation

### Prerequisites
- Python 3.11+
- MongoDB running on localhost:27017
- Ollama (optional, for local models)
- Piper TTS (optional, for speech synthesis)

### Setup

1. **Install Dependencies**
```bash
cd /app/backend
pip install -r requirements.txt
```

2. **Configure Environment**
Edit `.env` file with your API keys:
```bash
PERPLEXITY_API_KEY="your_perplexity_api_key"
OLLAMA_HOST="http://localhost:11434"
MONGO_URL="mongodb://localhost:27017"
DB_NAME="ai_assistant"
```

3. **Install Ollama (Optional)**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b
ollama serve
```

4. **Run Backend**

Recommended (best practice): run the package with Python's -m flag so imports resolve correctly:

```powershell
Set-Location -Path 'C:\Projects\APP\backend'
python -m app.main
```

This mirrors running the package as intended and avoids import/path issues.

Script fallback (convenience): you can still run the file directly. The repository contains a small, explicit
sys.path insertion in `app/main.py` to make `python app/main.py` work for local development, but the module
approach above is preferred.

Direct script run (PowerShell):

```powershell
# From the backend directory
python app/main.py

# Or set PYTHONPATH so Python can find the `app` package:
$env:PYTHONPATH = "${PWD}"; python app/main.py
```

## API Endpoints

### Conversations
- `GET /api/conversations` - List all conversations
- `POST /api/conversations` - Create new conversation
- `GET /api/conversations/{id}` - Get specific conversation
- `DELETE /api/conversations/{id}` - Delete conversation
- `GET /api/conversations/{id}/messages` - Get conversation messages

### Chat
- `POST /api/chat` - Non-streaming chat completion
- `WS /api/ws/{client_id}` - WebSocket for real-time streaming

### Memory
- `GET /api/memory/core` - Get core memory
- `POST /api/memory/preference` - Update user preference
- `POST /api/memory/fact` - Store new fact
- `GET /api/memory/search?query=` - Search memory

### Tools
- `GET /api/tools` - List available tools
- `POST /api/tools/execute` - Execute a tool

### Speech
- `POST /api/speech/transcribe` - Transcribe audio to text
- `POST /api/speech/synthesize` - Synthesize text to speech

### System
- `GET /` - Health check
- `GET /health` - Detailed status
- `GET /api/settings` - Application settings

## Usage Examples

### Non-Streaming Chat
```python
import requests

response = requests.post("http://localhost:8001/api/chat", json={
    "message": "What is Python?",
    "temperature": 0.7,
    "use_ollama": False
})

print(response.json())
```

### WebSocket Streaming
```javascript
const ws = new WebSocket("ws://localhost:8001/api/ws/user123");

ws.onopen = () => {
    ws.send(JSON.stringify({
        type: "message",
        conversation_id: null,
        content: "Tell me about artificial intelligence",
        metadata: {
            temperature: 0.7
        }
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === "token") {
        console.log(data.content); // Stream chunks
    } else if (data.type === "complete") {
        console.log("Done:", data.full_response);
    }
};
```

### Execute Tool
```python
import requests

response = requests.post("http://localhost:8001/api/tools/execute", json={
    "tool_name": "web_search",
    "parameters": {
        "query": "latest AI news",
        "source": "duckduckgo",
        "max_results": 5
    }
})

print(response.json())
```

### Store Fact in Memory
```python
import requests

response = requests.post("http://localhost:8001/api/memory/fact", json={
    "content": "User prefers Python over JavaScript for backend development",
    "metadata": {
        "category": "preference",
        "confidence": 0.95
    }
})

print(response.json())
```

## Memory Architecture

### Core Memory
Shared across all conversations, stored in JSON and vector database:
- User profile and preferences
- Learned knowledge with confidence scores
- Conversation summaries
- Unlocked skills/capabilities

### Conversation Memory
Isolated per conversation, stored in SQLite:
- Message history
- Tool call results
- Metadata and timestamps

### Vector Store
ChromaDB for semantic search:
- Fact embeddings
- Context retrieval
- Similarity search

## Task Planning with LangGraph

The planner analyzes user intent and creates execution plans:

1. **Intent Analysis**: Classify task type (simple query, web search, code execution, etc.)
2. **Plan Creation**: Generate step-by-step execution flow
3. **Model Selection**: Route to Perplexity API or Ollama based on complexity
4. **Tool Execution**: Execute required tools in sequence or parallel
5. **Response Generation**: Synthesize final response with context

## Tool Development

Create custom tools by extending `BaseTool`:

```python
from app.tools.base import BaseTool

class MyTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "my_tool"
        self.description = "My custom tool"
        self.parameters = {
            "type": "object",
            "properties": {
                "param": {
                    "type": "string",
                    "description": "Parameter description"
                }
            },
            "required": ["param"]
        }
    
    async def execute(self, param: str):
        # Tool logic here
        return {"result": f"Executed with {param}"}
```

Register the tool in `app/api/routes.py`:
```python
tool_executor.register_tool(MyTool())
```

## Configuration

All settings are managed via environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `PERPLEXITY_API_KEY` | Perplexity API key | - |
| `OLLAMA_HOST` | Ollama server URL | http://localhost:11434 |
| `OLLAMA_MODEL` | Default Ollama model | llama3.1:8b |
| `MONGO_URL` | MongoDB connection string | mongodb://localhost:27017 |
| `DB_NAME` | Database name | ai_assistant |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path | /app/backend/data/vector_store |
| `SQLITE_DB` | SQLite database path | /app/backend/data/conversations.db |
| `CORE_MEMORY_FILE` | Core memory JSON path | /app/backend/data/core_memory.json |
| `WHISPER_MODEL` | Faster-Whisper model | base |
| `PIPER_MODEL` | Piper TTS model | en_US-lessac-medium |

## Error Handling

The system includes automatic fallback mechanisms:
- Perplexity API failure → Ollama local model
- Tool execution errors → Graceful error messages
- WebSocket disconnection → Automatic reconnection support
- Timeout protection → All operations have timeout limits

## Performance Optimization

- **Caching**: Core memory and settings cached with `@lru_cache`
- **Async Operations**: Full async/await throughout
- **Parallel Tool Execution**: Multiple tools run concurrently
- **Streaming Responses**: Token-by-token streaming reduces perceived latency
- **Connection Pooling**: Persistent connections for MongoDB and vector store

## Security

- **Sandboxed Execution**: Code execution limited to safe operations
- **Path Validation**: File operations restricted to safe directories
- **Timeout Protection**: All long-running operations have timeouts
- **Input Validation**: Pydantic models validate all inputs
- **CORS Configuration**: Configurable allowed origins

## Logging

Comprehensive logging at all levels:
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

Check logs for:
- API requests and responses
- Tool executions
- Memory operations
- AI model interactions
- Errors and warnings

## Testing

Test the API using the interactive docs:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

Or use curl:
```bash
# Health check
curl http://localhost:8001/health

# List conversations
curl http://localhost:8001/api/conversations

# Create conversation
curl -X POST http://localhost:8001/api/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "My First Chat"}'
```

## Troubleshooting

### Ollama Not Available
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull model if missing
ollama pull llama3.1:8b
```

### ChromaDB Issues
```bash
# Clear and reinitialize
rm -rf /app/backend/data/vector_store
# Restart backend - will recreate automatically
```

### MongoDB Connection
```bash
# Check MongoDB status
sudo systemctl status mongod

# Start MongoDB
sudo systemctl start mongod
```

## Deployment

For production deployment:

1. Use environment-specific `.env` files
2. Set `DEBUG=false` and `ENVIRONMENT=production`
3. Use supervisor or systemd for process management
4. Configure proper CORS origins
5. Set up monitoring and logging
6. Use reverse proxy (nginx) for WebSocket support
7. Implement rate limiting and authentication

## Future Enhancements

- [ ] Voice activity detection for speech
- [ ] Multi-user support with authentication
- [ ] Advanced LangGraph workflows
- [ ] Tool marketplace and plugin system
- [ ] Performance metrics dashboard
- [ ] Automated testing suite
- [ ] Docker containerization
- [ ] Kubernetes deployment manifests

## License

This project is part of the AI Assistant system built on the Emergent platform.

## Support

For issues and questions, check the logs or contact the development team.
