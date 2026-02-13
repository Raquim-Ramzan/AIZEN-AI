# AI Assistant Backend - Bolt.new Implementation Guide

## Project Overview
Building the Python FastAPI backend for the AI assistant with Perplexity API integration, ChromaDB RAG system, and multi-model support.

**Budget:** $20/month (Perplexity Pro subscription only)  
**Frontend:** Already complete (React + TypeScript + Vite)  
**Backend Tool:** Bolt.new (uses Claude Sonnet 4.5)

---

## What Changed From Original Plan

### ❌ OLD PLAN:
- Groq API (free tier) + Ollama
- No RAG in Phase 1
- Limited model options

### ✅ NEW PLAN:
- **Perplexity API** (access to GPT-4o, Claude Sonnet 4.5, Gemini 2.5 Pro, Grok-4)
- **Perplexity Sonar** (built-in web search RAG)
- **ChromaDB RAG** from Phase 1
- **Hybrid RAG System** (Sonar for web + ChromaDB for personal data)
- Still have Ollama as local fallback

---

## Tech Stack (UPDATED)

### Backend Framework
```
FastAPI 0.104.1
- REST API endpoints
- WebSocket for real-time streaming
- CORS enabled for React frontend
- Pydantic for data validation

Python 3.11+
- Async/await support
- Type hints
- Modern syntax

Uvicorn (ASGI Server)
- Production-ready
- WebSocket support
- Hot reload in development
```

### AI Models (via Perplexity API)

```
Perplexity API Models:
├── GPT-5o (OpenAI)              → Best for complex reasoning
├── Claude Sonnet 4.5 (Anthropic) → Best for coding
├── Gemini 2.5 Pro (Google)      → Best for creative tasks
├── Grok-4 (xAI)                 → Best for math/analysis
├── Sonar Pro (Perplexity)       → Built-in web search RAG
└── Llama 3.1 70B (Meta)         → Fast, cost-effective

Local Fallback:
└── Ollama (Llama 3.1 8B, Qwen 2.5) → Offline, private, instant
```

### RAG System Architecture

```
Hybrid RAG Approach:

1. Perplexity Sonar (Web RAG)
   - Real-time web search
   - Citations included
   - Up-to-date information
   - No setup needed

2. ChromaDB (Personal RAG)
   - User profile storage
   - Conversation history
   - Learned facts
   - User documents (PDFs, notes)
   - Web search cache
   - Task history
```

### Storage & Memory

```
Vector Storage (ChromaDB):
├── user_profile/       # Name, preferences, settings
├── conversations/      # Vectorized chat history
├── learned_facts/      # Important facts user taught
├── documents/          # User uploaded PDFs, DOCX, TXT
├── web_cache/          # Cached Sonar search results
└── task_history/       # Completed tasks log

Structured Storage (SQLite):
├── conversations table # Full message history
├── messages table      # Individual messages
└── metadata table      # Session info, timestamps

Quick Access (JSON):
└── core_memory.json    # User profile, preferences
```

### Dependencies

```python
# API Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pydantic==2.5.0

# AI & Embeddings
httpx==0.25.0                    # Perplexity API client
sentence-transformers==2.2.2     # Local embeddings
ollama==0.1.0                    # Local fallback

# RAG & Vector DB
chromadb==0.4.18
langchain==0.1.0

# Storage
aiosqlite==0.19.0

# Document Processing
PyPDF2==3.0.1
pdfplumber==0.10.3
python-docx==1.1.0
markdown==3.5.1

# Tools
duckduckgo-search==4.0.0
wikipedia==1.4.0

# Utilities
python-multipart==0.0.6          # File uploads
```

---

## Project Structure

```
ai-assistant-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI entry point
│   ├── config.py                    # Environment config
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── brain.py                 # AI orchestration
│   │   ├── model_router.py          # Smart model selection
│   │   ├── memory_manager.py        # Memory coordination
│   │   ├── rag_orchestrator.py      # RAG coordination
│   │   └── tools_executor.py        # Tool execution
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── perplexity_client.py     # Perplexity API wrapper
│   │   ├── ollama_client.py         # Ollama API wrapper
│   │   └── schemas.py               # Pydantic models
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── chroma_manager.py        # ChromaDB operations
│   │   ├── embeddings.py            # Embedding generation
│   │   ├── document_processor.py    # PDF/DOCX chunking
│   │   ├── retriever.py             # Context retrieval
│   │   └── web_cache.py             # Sonar results caching
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── conversation_db.py       # SQLite chat storage
│   │   ├── core_memory.py           # JSON memory handler
│   │   └── fact_extractor.py        # Extract learned facts
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py                  # Base tool class
│   │   ├── web_search.py            # DuckDuckGo backup
│   │   ├── file_ops.py              # File operations
│   │   └── wikipedia.py             # Wikipedia lookup
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py              # Chat endpoints
│   │   │   ├── conversations.py     # Conversation management
│   │   │   ├── memory.py            # Memory endpoints
│   │   │   ├── documents.py         # Document upload
│   │   │   └── models.py            # Model selection
│   │   ├── websocket.py             # WebSocket handler
│   │   └── middleware.py            # CORS, auth, logging
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                # Logging setup
│       └── helpers.py               # Utility functions
│
├── data/
│   ├── chroma_db/                   # ChromaDB persistence
│   ├── conversations.db             # SQLite database
│   ├── core_memory.json             # Core memory file
│   └── uploads/                     # User uploaded files
│
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_rag.py
│   └── test_models.py
│
├── .env.example                     # Environment template
├── .gitignore
├── requirements.txt
├── README.md
└── run.py                           # Development server
```

---

## Environment Configuration

### `.env` File Structure

```bash
# Perplexity API
PERPLEXITY_API_KEY=your_api_key_here
PERPLEXITY_BASE_URL=https://api.perplexity.ai

# Ollama (Local)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# ChromaDB
CHROMA_PERSIST_DIR=./data/chroma_db
CHROMA_COLLECTION_PREFIX=ai_assistant

# SQLite
SQLITE_DB_PATH=./data/conversations.db

# Core Memory
CORE_MEMORY_PATH=./data/core_memory.json

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# CORS (React Frontend)
CORS_ORIGINS=http://localhost:8080,http://localhost:5173

# File Uploads
MAX_UPLOAD_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=pdf,docx,txt,md

# RAG Settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=5

# Model Selection Defaults
DEFAULT_MODEL=claude-sonnet-4.5
DEFAULT_WEB_MODEL=sonar-pro
```

---

## API Endpoints Design

### Health & Info

```
GET /api/health
Response: {"status": "ok", "timestamp": "..."}

GET /api/models
Response: {
  "available_models": [
    "gpt-4o",
    "claude-sonnet-4.5",
    "gemini-2.5-pro",
    "grok-4",
    "sonar-pro",
    "llama-3.1-70b",
    "ollama-llama3.1"
  ],
  "default": "claude-sonnet-4.5"
}
```

### Chat & Conversations

```
POST /api/chat
Body: {
  "message": "user message",
  "conversation_id": "conv_123" (optional),
  "model": "claude-sonnet-4.5" (optional),
  "use_rag": true (optional)
}
Response: {
  "response": "assistant message",
  "conversation_id": "conv_123",
  "model_used": "claude-sonnet-4.5",
  "sources": [...] (if RAG used),
  "tokens_used": 150
}

WebSocket /ws/chat
Send: {
  "type": "message",
  "content": "user message",
  "conversation_id": "conv_123",
  "model": "claude-sonnet-4.5"
}
Receive (streaming): {
  "type": "token",
  "content": "word",
  "conversation_id": "conv_123"
}
Receive (complete): {
  "type": "complete",
  "message_id": "msg_456",
  "tokens_used": 150
}

GET /api/conversations
Response: {
  "conversations": [
    {
      "id": "conv_123",
      "title": "Building AI Assistant",
      "created_at": "2024-11-08T10:00:00Z",
      "updated_at": "2024-11-08T12:30:00Z",
      "message_count": 15
    }
  ]
}

GET /api/conversations/{conversation_id}
Response: {
  "id": "conv_123",
  "title": "Building AI Assistant",
  "messages": [
    {
      "id": "msg_1",
      "role": "user",
      "content": "Hello",
      "timestamp": "2024-11-08T10:00:00Z"
    },
    {
      "id": "msg_2",
      "role": "assistant",
      "content": "Hi! How can I help?",
      "model": "claude-sonnet-4.5",
      "timestamp": "2024-11-08T10:00:05Z"
    }
  ]
}

DELETE /api/conversations/{conversation_id}
Response: {"success": true}

POST /api/conversations/{conversation_id}/title
Body: {"title": "New Title"}
Response: {"success": true, "title": "New Title"}
```

### Memory Management

```
GET /api/memory/profile
Response: {
  "name": "John Doe",
  "preferences": {
    "response_style": "concise",
    "preferred_model": "claude-sonnet-4.5"
  },
  "learned_facts": [
    "User is building an AI assistant",
    "Prefers Python over JavaScript"
  ]
}

POST /api/memory/profile
Body: {
  "name": "John Doe",
  "preferences": {...}
}
Response: {"success": true}

POST /api/memory/fact
Body: {
  "fact": "My server password is XYZ",
  "category": "credentials",
  "importance": "high"
}
Response: {"success": true, "fact_id": "fact_123"}

GET /api/memory/facts
Response: {
  "facts": [
    {
      "id": "fact_123",
      "content": "User prefers Python",
      "category": "preference",
      "timestamp": "2024-11-08T10:00:00Z"
    }
  ]
}

DELETE /api/memory/facts/{fact_id}
Response: {"success": true}

POST /api/memory/search
Body: {
  "query": "what do I like?",
  "limit": 5
}
Response: {
  "results": [
    {
      "content": "User prefers Python over JavaScript",
      "relevance_score": 0.95,
      "source": "conversation_5"
    }
  ]
}
```

### Document Management

```
POST /api/documents/upload
Body: multipart/form-data with file
Response: {
  "success": true,
  "document_id": "doc_123",
  "filename": "notes.pdf",
  "pages": 10,
  "status": "processing"
}

GET /api/documents
Response: {
  "documents": [
    {
      "id": "doc_123",
      "filename": "notes.pdf",
      "size": 1024000,
      "pages": 10,
      "uploaded_at": "2024-11-08T10:00:00Z",
      "status": "ready"
    }
  ]
}

DELETE /api/documents/{document_id}
Response: {"success": true}

POST /api/documents/query
Body: {
  "query": "summarize my notes",
  "document_ids": ["doc_123", "doc_456"]
}
Response: {
  "answer": "Your notes discuss...",
  "sources": [
    {
      "document": "notes.pdf",
      "page": 3,
      "snippet": "..."
    }
  ]
}
```

### Task History

```
GET /api/tasks
Response: {
  "tasks": [
    {
      "id": "task_123",
      "type": "code_generation",
      "description": "Generated Python script",
      "completed_at": "2024-11-08T10:00:00Z",
      "model_used": "claude-sonnet-4.5"
    }
  ]
}

POST /api/tasks
Body: {
  "type": "web_search",
  "description": "Researched AI trends",
  "result": "..."
}
Response: {"success": true, "task_id": "task_456"}
```

---

## Model Router Logic

### Smart Model Selection Algorithm

```
Query Analysis
    ↓
Determine Query Type
    ↓
┌─────────────────────────────────────────┐
│                                         │
│ Current Events / Web Search?            │
│ → Sonar Pro (built-in web RAG)         │
│                                         │
│ Complex Reasoning / Analysis?           │
│ → GPT-4o                                │
│                                         │
│ Code Generation / Technical?            │
│ → Claude Sonnet 4.5                     │
│                                         │
│ Creative Writing / Brainstorming?       │
│ → Gemini 2.5 Pro                        │
│                                         │
│ Math / Scientific Analysis?             │
│ → Grok-4                                │
│                                         │
│ Quick Chat / Privacy Needed?            │
│ → Ollama (Local)                        │
│                                         │
│ Personal Memory Query?                  │
│ → ChromaDB → Claude Sonnet 4.5          │
│                                         │
└─────────────────────────────────────────┘
```

### Query Type Detection

```
Keywords/Patterns for Auto-Routing:

Web Search Triggers:
- "latest", "current", "today", "news"
- "what's happening", "recent", "update on"
- "search for", "find information about"
→ Route to: Sonar Pro

Code Triggers:
- "write code", "generate function", "debug"
- "implement", "create script", "fix this code"
- Language names: Python, JavaScript, etc.
→ Route to: Claude Sonnet 4.5

Analysis Triggers:
- "analyze", "compare", "evaluate"
- "pros and cons", "should I", "what if"
- "explain", "break down", "understand"
→ Route to: GPT-4o

Creative Triggers:
- "write a story", "brainstorm", "imagine"
- "creative", "ideas for", "design"
→ Route to: Gemini 2.5 Pro

Math Triggers:
- "calculate", "solve", "equation"
- Numbers, formulas, mathematical symbols
→ Route to: Grok-4

Personal Memory Triggers:
- "remember when", "what did I", "my"
- "last time", "yesterday", "our conversation"
→ Route to: ChromaDB + Claude Sonnet 4.5
```

---

## RAG Implementation Strategy

### Hybrid RAG Architecture

```
User Query
    ↓
Query Analyzer
    ↓
┌──────────────────┬──────────────────┐
│                  │                  │
│ Web/Current?     │ Personal Data?   │
│                  │                  │
│ Perplexity       │ ChromaDB         │
│ Sonar Pro        │ Search           │
│                  │                  │
│ Returns:         │ Returns:         │
│ - Answer         │ - User docs      │
│ - Citations      │ - Conversations  │
│ - Sources        │ - Learned facts  │
│                  │                  │
└──────────────────┴──────────────────┘
            ↓
    Combine Contexts
            ↓
    Send to Selected Model
            ↓
    Generate Answer
```

### ChromaDB Collections Setup

```
Collection: user_profile
- Purpose: Name, preferences, settings
- Metadata: last_updated, category
- Example: "User prefers concise responses"

Collection: conversations
- Purpose: Vectorized chat history
- Metadata: timestamp, conversation_id, model_used
- Example: Past Q&A pairs

Collection: learned_facts
- Purpose: Important user-taught information
- Metadata: importance, category, source
- Example: "My server IP is 192.168.1.1"

Collection: documents
- Purpose: User uploaded files (chunked)
- Metadata: filename, page, chunk_id
- Example: PDF content chunks

Collection: web_cache
- Purpose: Cached Sonar search results
- Metadata: query, timestamp, expiry
- Example: Saved search results for faster retrieval

Collection: task_history
- Purpose: Completed tasks log
- Metadata: task_type, model_used, timestamp
- Example: "Generated Python script for data analysis"
```

### Document Processing Pipeline

```
User Uploads PDF/DOCX
    ↓
1. Validate File
   - Check size (<10MB)
   - Check type (PDF, DOCX, TXT, MD)
    ↓
2. Extract Text
   - PDF: pdfplumber
   - DOCX: python-docx
   - TXT/MD: direct read
    ↓
3. Chunk Text
   - Size: 1000 characters
   - Overlap: 200 characters
   - Preserve context at boundaries
    ↓
4. Generate Embeddings
   - Model: all-MiniLM-L6-v2
   - Dimension: 384
    ↓
5. Store in ChromaDB
   - Collection: documents
   - Metadata: filename, page, chunk_id
    ↓
6. Ready for Querying
```

### Context Retrieval Process

```
User Query: "What's in my project notes?"
    ↓
1. Generate Query Embedding
   - Same model as documents (all-MiniLM-L6-v2)
    ↓
2. Search ChromaDB Collections
   - Search: documents, conversations, learned_facts
   - Get top 5 results per collection
   - Use cosine similarity
    ↓
3. Rank by Relevance
   - Score based on similarity
   - Prioritize recent items
   - Consider metadata (importance, recency)
    ↓
4. Build Context Window
   - Top 3-5 most relevant chunks
   - Total: ~2000 tokens max
   - Maintain coherence
    ↓
5. Format for Model
   Context: [retrieved chunks]
   
   User: [original query]
   
   Instructions: Answer based on context
    ↓
6. Send to Selected Model
```

---

## WebSocket Implementation

### Connection Flow

```
Client connects to: ws://localhost:8000/ws/chat
    ↓
Server accepts connection
    ↓
Client sends authentication (optional)
    ↓
Server validates & creates session
    ↓
Client sends message:
{
  "type": "message",
  "content": "Hello",
  "conversation_id": "conv_123",
  "model": "claude-sonnet-4.5",
  "use_rag": true
}
    ↓
Server processes:
1. Check if RAG needed
2. Retrieve context (if RAG)
3. Route to selected model
4. Stream response token by token
    ↓
Server sends tokens:
{"type": "token", "content": "Hi"}
{"type": "token", "content": " there"}
{"type": "token", "content": "!"}
    ↓
Server sends complete:
{
  "type": "complete",
  "message_id": "msg_456",
  "tokens_used": 25,
  "model_used": "claude-sonnet-4.5"
}
```

### WebSocket Message Types

```json
// Client → Server

{
  "type": "message",
  "content": "user message",
  "conversation_id": "conv_123",
  "model": "claude-sonnet-4.5",
  "use_rag": true,
  "temperature": 0.7
}

{
  "type": "ping",
  "timestamp": 1699440000
}

{
  "type": "stop",
  "message_id": "msg_456"
}

// Server → Client

{
  "type": "token",
  "content": "word",
  "conversation_id": "conv_123"
}

{
  "type": "tool_call",
  "tool": "web_search",
  "parameters": {"query": "..."}
}

{
  "type": "tool_result",
  "tool": "web_search",
  "result": {...}
}

{
  "type": "sources",
  "sources": [
    {"title": "...", "url": "...", "snippet": "..."}
  ]
}

{
  "type": "complete",
  "message_id": "msg_456",
  "conversation_id": "conv_123",
  "tokens_used": 150,
  "model_used": "claude-sonnet-4.5"
}

{
  "type": "error",
  "error": "Model temporarily unavailable",
  "code": "MODEL_ERROR"
}

{
  "type": "pong",
  "timestamp": 1699440000
}
```

---

## Perplexity API Integration

### API Client Setup

```
Base URL: https://api.perplexity.ai
Authentication: Bearer token in headers

Available Models:
- openai/gpt-4o
- anthropic/claude-sonnet-4.5
- google/gemini-2.5-pro
- xai/grok-4
- meta-llama/llama-3.1-70b
- sonar-pro (Perplexity's web-RAG model)
```

### Request Format

```json
POST /chat/completions
Headers:
{
  "Authorization": "Bearer YOUR_API_KEY",
  "Content-Type": "application/json"
}

Body:
{
  "model": "anthropic/claude-sonnet-4.5",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful AI assistant."
    },
    {
      "role": "user",
      "content": "What is Python?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": true
}
```

### Sonar Model (Web Search)

```json
// Sonar Pro automatically searches web and includes citations

POST /chat/completions
{
  "model": "sonar-pro",
  "messages": [
    {
      "role": "user",
      "content": "What's the latest news about AI?"
    }
  ]
}

Response:
{
  "id": "...",
  "model": "sonar-pro",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "Based on recent sources, AI developments include..."
    },
    "finish_reason": "stop"
  }],
  "citations": [
    {
      "url": "https://example.com/article",
      "title": "Latest AI News",
      "snippet": "..."
    }
  ]
}
```

### Streaming Response Handling

```
Stream Format: Server-Sent Events (SSE)

data: {"id":"...","choices":[{"delta":{"content":"Hello"}}]}

data: {"id":"...","choices":[{"delta":{"content":" there"}}]}

data: {"id":"...","choices":[{"delta":{"content":"!"}}]}

data: [DONE]
```

---

## Error Handling Strategy

### Error Types & Recovery

```
1. API Errors (Perplexity/Ollama)
   - Rate limit exceeded
   - Model unavailable
   - Invalid API key
   Recovery:
   → Retry with exponential backoff
   → Fall back to different model
   → Fall back to Ollama (local)

2. RAG Errors (ChromaDB)
   - Collection not found
   - Embedding generation failed
   - Query timeout
   Recovery:
   → Create collection if missing
   → Use backup embedding model
   → Skip RAG, use direct model

3. Storage Errors (SQLite/File)
   - Database locked
   - Disk full
   - Permission denied
   Recovery:
   → Retry operation
   → Graceful degradation
   → Log error, continue without persistence

4. WebSocket Errors
   - Connection dropped
   - Message too large
   - Invalid format
   Recovery:
   → Auto-reconnect client-side
   → Chunk large messages
   → Validate before processing

5. Tool Errors
   - Web search failed
   - File not found
   - Operation timeout
   Recovery:
   → Return error to user
   → Try alternative tool
   → Continue conversation
```

### Fallback Hierarchy

```
Primary: Perplexity (Selected Model)
    ↓ (if fails)
Secondary: Different Perplexity Model
    ↓ (if fails)
Tertiary: Ollama (Local)
    ↓ (if fails)
Final: Graceful error message to user
```

---

## Security & Privacy

### Data Protection

```
Sensitive Data Handling:
1. Passwords/Keys
   - Never store in plain text
   - Use Fernet encryption
   - Store encrypted in ChromaDB

2. Personal Information
   - Local storage only
   - No cloud sync without user consent
   - User can delete anytime

3. Conversations
   - Encrypted at rest (optional)
   - User owns data
   - Export/delete options

4. API Keys
   - Environment variables only
   - Never in code
   - Never in logs
```

### Input Validation

```
All Endpoints:
- Validate request structure
- Sanitize user input
- Check file types/sizes
- Rate limiting per user/IP

File Uploads:
- Max size: 10MB
- Allowed types: PDF, DOCX, TXT, MD only
- Virus scan (optional)
- Sandboxed processing
```

---

## Testing Strategy

### Test Categories

```
1. Unit Tests
   - Model router logic
   - RAG retrieval accuracy
   - Memory operations
   - Tool functions

2. Integration Tests
   - API endpoints
   - WebSocket flow
   - Database operations
   - Perplexity API calls

3. End-to-End Tests
   - Complete chat flow
   - Document upload → query
   - Multi-turn conversation
   - Model switching

4. Performance Tests
   - Response time < 2s
   - WebSocket latency < 100ms
   - Concurrent users (10+)
   - Memory usage stability
```

---

## Phase 1 Implementation Plan

### Week 1: Core Backend (Bolt.new)

**Day 1-2: Project Setup**
- [ ] FastAPI project structure
- [ ] Environment configuration
- [ ] CORS setup for React frontend
- [ ] Health check endpoint
- [ ] Basic logging

**Day 3-4: Perplexity Integration**
- [ ] API client wrapper
- [ ] Model selection endpoint
- [ ] Basic chat endpoint (non-streaming)
- [ ] Error handling & retries
- [ ] Test with all models (GPT-4o, Claude, Gemini, Grok)

**Day 5-6: WebSocket Streaming**
- [ ] WebSocket endpoint
- [ ] Token streaming implementation
- [ ] Connection management
- [ ] Test with React frontend

**Day 7: ChromaDB RAG Basics**
- [ ] ChromaDB setup
- [ ] Create collections (user_profile, conversations)
- [ ] Basic embedding generation
- [ ] Simple context retrieval
- [ ] Test RAG flow

### Success Criteria (Week 1)
✅ Can send messages via REST API  
✅ Can stream responses via WebSocket  
✅ Can switch between models (GPT-4o, Claude, Gemini, Grok)  
✅ Sonar model works for web search  
✅ Basic RAG stores & retrieves conversations  
✅ Frontend can connect and chat  

---

## Bolt.new Prompts

### Prompt 1: Project Setup

```
Create a FastAPI backend project with the following structure:

Project Name: ai-assistant-backend
Python Version: 3.11+

Requirements:
- FastAPI 0.104.1 with WebSocket support
- CORS middleware for React frontend (http://localhost:8080)
- Pydantic models for request/response validation
- Environment variable configuration using python-dotenv
- Logging setup with rotating file handler
- Health check endpoint at GET /api/health

File Structure:
app/
├── __init__.py
├── main.py (FastAPI app with CORS)
├── config.py (environment variables)
└── api/
    └── routes.py (health endpoint)

Also create:
- requirements.txt with all dependencies
- .env.example with configuration template
- .gitignore for Python projects
- README.md with setup instructions

Make it production-ready with error handling and proper async/await patterns.
```

### Prompt 2: Perplexity API Client

```
Create a Perplexity API client module for FastAPI backend.

Location: app/models/perplexity_client.py

Features needed:
- Async HTTP client using httpx
- Support for all Perplexity models:
  * openai/gpt-4o
  * anthropic/claude-sonnet-4.5
  * google/gemini-2.5-pro
  * xai/grok-4
  * meta-llama/llama-3.1-70b
  * sonar-pro (web search model)

Methods:
- chat_completion(model, messages, temperature, max_tokens, stream)
- Stream handling for real-time responses
- Error handling with retry logic (3 attempts, exponential backoff)
- Rate limit detection and handling
- Response parsing (including Sonar citations)

Configuration from environment:
- PERPLEXITY_API_KEY
- PERPLEXITY_BASE_URL (default: https://api.perplexity.ai)

Include proper type hints, error classes, and async context manager support.
```

### Prompt 3: Model Router

```
Create an intelligent model router that selects the best AI model based on query type.

Location: app/core/model_router.py

Router Logic:
1. Analyze user query for keywords/patterns
2. Determine query type:
   - Web search (latest, current, news) → sonar-pro
   - Code generation (code, function, implement) → claude-sonnet-4.5
   - Complex reasoning (analyze, compare) → gpt-4o
   - Creative writing (story, imagine, brainstorm) → gemini-2.5-pro
   - Math/science (calculate, solve, equation) → grok-4
   - Personal memory (remember, my, what did I) → chromadb + claude-sonnet-4.5
   - Quick chat → llama-3.1-70b

Features:
- Query analysis function with keyword matching
- Model selection with fallback options
- User override (can manually select model)
- Logging of routing decisions
- Configuration for default models

Return format: (selected_model, reasoning, confidence_score)
```

### Prompt 4: ChromaDB RAG Setup

```
Create ChromaDB RAG system for personal memory storage.

Location: app/rag/chroma_manager.py

Collections to create:
1. user_profile (name, preferences, settings)
2. conversations (chat history vectors)
3. learned_facts (important user-taught info)
4. documents (uploaded file chunks)
5. web_cache (cached Sonar results)
6. task_history (completed tasks)

Features:
- Initialize ChromaDB with persistence
- Create/get collections with metadata
- Add documents with embeddings
- Search with semantic similarity (top_k results)
- Update/delete documents
- Clear collection option

Embedding:
- Use sentence-transformers: all-MiniLM-L6-v2
- Async embedding generation
- Batch processing for multiple docs

Configuration:
- CHROMA_PERSIST_DIR from environment
- Collection naming with prefix

Include proper error handling and connection management.
```

### Prompt 5: Chat API Endpoints

```
Create REST API endpoints for chat functionality.

Location: app/api/routes/chat.py

Endpoints needed:

POST /api/chat
- Send message and get response
- Support model selection
- Optional RAG context retrieval
- Return: response, model_used, tokens, sources (if RAG)

GET /api/models
- List all available models
- Include descriptions and use cases
- Return default model

Request/Response Pydantic models:
- ChatRequest: message, conversation_id?, model?, use_rag?, temperature?
- ChatResponse: response, conversation_id, model_used, tokens_used, sources?
- ModelInfo: name, description, provider, use_case

Features:
- Input validation
- Error responses with proper HTTP codes
- Logging all requests
- Rate limiting (optional)

Integrate with:
- model_router.py for smart routing
- perplexity_client.py for API calls
- chroma_manager.py for RAG context
```

### Prompt 6: WebSocket Streaming

```
Create WebSocket endpoint for real-time chat streaming.

Location: app/api/websocket.py

WebSocket Endpoint: /ws/chat

Features:
- Accept connection with optional auth
- Receive message: {type: "message", content, conversation_id, model}
- Stream response token by token
- Send progress updates (tool_call, tool_result, sources)
- Handle connection errors gracefully
- Support stop/cancel mid-stream
- Heartbeat/ping-pong for connection health

Message Types (Server → Client):
- token: streamed word
- tool_call: when using tools
- tool_result: tool execution result
- sources: RAG citations
- complete: generation finished
- error: something went wrong
- pong: heartbeat response

Integration:
- Use Perplexity streaming API
- Add RAG context before streaming
- Log all WebSocket events
- Handle disconnections and reconnects

Include connection manager for multiple clients.
```

### Prompt 7: Conversation Storage

```
Create conversation management with SQLite.

Location: app/memory/conversation_db.py

Database Schema:
Table: conversations
- id (PRIMARY KEY)
- title (auto-generated from first message)
- created_at
- updated_at
- metadata (JSON)

Table: messages
- id (PRIMARY KEY)
- conversation_id (FOREIGN KEY)
- role (user/assistant/system)
- content
- model_used
- tokens_used
- timestamp
- metadata (JSON)

Functions needed:
- create_conversation() → conversation_id
- add_message(conversation_id, role, content, model, tokens)
- get_conversation(conversation_id) → all messages
- list_conversations() → all conversations with summary
- delete_conversation(conversation_id)
- update_title(conversation_id, title)
- search_messages(query) → matching messages

Features:
- Async database operations using aiosqlite
- Auto-generate conversation title from first exchange
- Pagination for large conversations
- Full-text search on message content

Configuration: SQLITE_DB_PATH from environment
```

### Prompt 8: Document Upload & Processing

```
Create document upload and processing system.

Location: app/api/routes/documents.py

Endpoints:
POST /api/documents/upload
- Accept: PDF, DOCX, TXT, MD files
- Max size: 10MB
- Process and store in ChromaDB

GET /api/documents
- List all uploaded documents
- Include metadata: filename, size, pages, upload date

DELETE /api/documents/{document_id}
- Remove document from storage and ChromaDB

POST /api/documents/query
- Query specific documents
- Return answer with source citations

Document Processing Pipeline:
1. Validate file (type, size)
2. Extract text (PyPDF2 for PDF, python-docx for DOCX)
3. Chunk text (1000 chars, 200 overlap)
4. Generate embeddings
5. Store in ChromaDB documents collection
6. Save file metadata

Location: app/rag/document_processor.py
- chunk_text(text, chunk_size, overlap)
- extract_pdf(file)
- extract_docx(file)
- process_document(file) → document_id

Include progress tracking for large files.
```

### Prompt 9: Memory Management API

```
Create memory management endpoints.

Location: app/api/routes/memory.py

Endpoints:

GET /api/memory/profile
- Get user profile from core_memory.json
- Return: name, preferences, learned_facts

POST /api/memory/profile
- Update user profile
- Auto-extract facts from conversations

POST /api/memory/fact
- Add learned fact to ChromaDB
- Categories: preference, credential, information
- Importance: high, medium, low

GET /api/memory/facts
- List all learned facts
- Filter by category, importance
- Pagination support

DELETE /api/memory/facts/{fact_id}
- Remove specific fact

POST /api/memory/search
- Semantic search across all memory
- Return relevant memories with scores

POST /api/memory/clear
- Clear specific collection or all memory
- Require confirmation

Integration:
- Use ChromaDB for semantic storage
- Use core_memory.json for quick-access data
- Auto-extract facts during conversations

Include fact extraction logic using LLM.
```

### Prompt 10: Complete Integration

```
Integrate all components into main FastAPI application.

Location: app/main.py

Integration tasks:
1. Import all routers (chat, conversations, documents, memory)
2. Register all endpoints with /api prefix
3. Add WebSocket endpoint
4. Setup CORS for React frontend
5. Initialize ChromaDB on startup
6. Create SQLite tables if not exist
7. Load core_memory.json on startup
8. Setup logging and error handlers
9. Add startup/shutdown events
10. Add global exception handlers

Middleware:
- CORS with credentials support
- Request logging
- Error handling (catch all exceptions)
- Request ID generation
- Performance timing

Startup checks:
- Verify PERPLEXITY_API_KEY exists
- Test database connection
- Initialize ChromaDB collections
- Check Ollama availability (optional)

Include comprehensive error messages and health status endpoint.
```

---

## Prompt Usage Strategy for Bolt.new

### How to Use These Prompts

**Step-by-Step Process:**

1. **Start with Prompt 1** (Project Setup)
   - Copy Prompt 1 into Bolt.new
   - Review generated code
   - Download and test locally
   - Verify structure is correct

2. **Continue with Prompt 2** (Perplexity Client)
   - Build on existing project
   - Test API connection
   - Verify all models work

3. **Follow Sequence 3-10**
   - Each prompt builds on previous
   - Test after each component
   - Fix any issues before moving forward

4. **After All Prompts**
   - Run complete integration
   - Test with React frontend
   - Deploy if everything works

### Tips for Bolt.new

- **Be specific**: Bolt works best with detailed requirements
- **One component at a time**: Don't try to build everything in one prompt
- **Test incrementally**: Verify each piece works before continuing
- **Iterate**: If something doesn't work, refine the prompt
- **Copy locally**: Always test downloaded code locally

---

## Testing Checklist

### After Building with Bolt.new

**Basic Functionality:**
- [ ] Server starts without errors
- [ ] Health endpoint returns 200
- [ ] CORS allows React frontend
- [ ] Environment variables load correctly

**API Endpoints:**
- [ ] POST /api/chat returns response
- [ ] GET /api/models lists all models
- [ ] WebSocket /ws/chat connects and streams
- [ ] All CRUD endpoints work (conversations, documents, memory)

**AI Integration:**
- [ ] Can call GPT-4o via Perplexity
- [ ] Can call Claude Sonnet 4.5
- [ ] Can call Gemini 2.5 Pro
- [ ] Can call Grok-4
- [ ] Sonar Pro returns web search results with citations
- [ ] Ollama works as fallback (if installed)

**RAG System:**
- [ ] ChromaDB initializes all collections
- [ ] Can store and retrieve embeddings
- [ ] Context retrieval returns relevant results
- [ ] Document upload and chunking works
- [ ] Memory search finds relevant facts

**WebSocket:**
- [ ] Connection establishes successfully
- [ ] Tokens stream in real-time
- [ ] Can handle multiple concurrent connections
- [ ] Gracefully handles disconnections

**Model Router:**
- [ ] Correctly identifies web search queries → Sonar
- [ ] Routes code questions → Claude
- [ ] Routes reasoning → GPT-4o
- [ ] User can override auto-selection

**Storage:**
- [ ] SQLite stores conversations
- [ ] Messages persist across restarts
- [ ] Can delete conversations
- [ ] ChromaDB persists data

**Error Handling:**
- [ ] API errors return proper messages
- [ ] Fallback to Ollama when Perplexity fails
- [ ] WebSocket errors don't crash server
- [ ] Invalid requests return 400/422

---

## Deployment Strategy

### Development (Local)

```bash
# Backend
cd ai-assistant-backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your PERPLEXITY_API_KEY
python run.py

# Frontend (separate terminal)
cd ../frontend
npm install
npm run dev

# Access at: http://localhost:8080
```

### Production Options

**Option 1: Railway.app (Free Tier)**
- Deploy FastAPI backend
- PostgreSQL available if needed
- Auto HTTPS
- Free 500 hours/month

**Option 2: Render.com (Free Tier)**
- Web service for FastAPI
- Auto deploy from GitHub
- Free tier sleeps after 15min inactivity

**Option 3: Fly.io (Free Tier)**
- Better for long-running services
- 3 free VMs
- Persistent storage available

**Frontend Options:**
- Vercel (recommended for React)
- Netlify
- Cloudflare Pages
All have generous free tiers

### Environment Variables (Production)

```bash
# Required
PERPLEXITY_API_KEY=your_key

# Optional (if using local Ollama)
OLLAMA_HOST=http://ollama-server:11434

# Database (auto-created)
SQLITE_DB_PATH=/data/conversations.db
CHROMA_PERSIST_DIR=/data/chroma_db

# CORS (your frontend URL)
CORS_ORIGINS=https://your-frontend.vercel.app

# Production settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

---

## Cost Analysis

### Monthly Costs

**Perplexity Pro: $20/month**
- Access to all premium models
- ~$0.50-2.00 per 1M tokens (varies by model)
- Generous usage limits
- Sonar models included

**Hosting: $0**
- Railway/Render free tier: Backend
- Vercel free tier: Frontend
- Combined: Good for personal use or small MVP

**Total: $20/month** for production-ready AI assistant with top-tier models!

### Cost Comparison

**Without Perplexity (Direct APIs):**
- OpenAI API (GPT-4o): ~$10-50/month
- Anthropic API (Claude): ~$10-50/month  
- Google API (Gemini): ~$5-20/month
- xAI API (Grok): ~$10-30/month
- **Total: $35-150/month**

**Savings: $15-130/month** by using Perplexity! 🎉

---

## Success Metrics

### Phase 1 Complete When:

✅ **Backend fully operational**
- All API endpoints working
- WebSocket streaming functional
- All 5+ models accessible
- RAG system storing and retrieving

✅ **Frontend connected**
- Can send messages
- Receives streamed responses  
- Can switch models
- Shows conversation history

✅ **Core features working**
- Chat with AI
- Model selection
- Basic memory (conversations)
- Web search via Sonar

✅ **Performance targets**
- Response time < 2 seconds
- WebSocket latency < 100ms
- No memory leaks
- Stable under 5+ concurrent users

✅ **Documentation complete**
- API documentation
- Setup instructions
- Environment configuration
- Testing guide

---

## Next Steps After Phase 1

### Phase 2 Features (Week 2)

**Advanced RAG:**
- Document upload UI
- Learned facts extraction
- Task history tracking
- Memory management dashboard

**Tool System:**
- Web search tool (DuckDuckGo backup)
- File operations
- Code execution (sandboxed)
- Wikipedia integration

**Enhanced Memory:**
- Fact extraction from conversations
- Importance scoring
- Auto-categorization
- Memory search UI

**Ollama Integration:**
- Local model support
- Privacy mode (no API calls)
- Faster simple queries

### Phase 3 Features (Week 3)

**Advanced Features:**
- Multi-model consensus
- Proactive suggestions
- Voice integration (Whisper + TTS)
- Calendar/task management

**UI Enhancements:**
- Beautiful chat interface
- Model comparison view
- Memory visualization
- Settings panel

**Optimization:**
- Caching layer
- Response compression
- Connection pooling
- Performance monitoring

---

## Troubleshooting Guide

### Common Issues

**Issue: Perplexity API returns 401**
- Solution: Check PERPLEXITY_API_KEY in .env
- Verify API key is active at perplexity.ai

**Issue: ChromaDB errors on startup**
- Solution: Delete chroma_db folder and restart
- Check CHROMA_PERSIST_DIR path exists

**Issue: WebSocket disconnects frequently**
- Solution: Add heartbeat/ping-pong
- Check firewall/proxy settings
- Increase timeout values

**Issue: Slow response times**
- Solution: Reduce TOP_K_RESULTS for RAG
- Use faster models (Llama instead of GPT-4o)
- Enable response caching

**Issue: Out of memory**
- Solution: Limit ChromaDB collection size
- Clear old conversations
- Reduce embedding dimensions

**Issue: CORS errors**
- Solution: Check CORS_ORIGINS includes frontend URL
- Verify credentials enabled
- Check browser console for exact error

---

## Resources & References

### Documentation Links

**APIs:**
- Perplexity API: https://docs.perplexity.ai
- FastAPI: https://fastapi.tiangolo.com
- ChromaDB: https://docs.trychroma.com

**Libraries:**
- sentence-transformers: https://www.sbert.net
- Pydantic: https://docs.pydantic.dev
- aiosqlite: https://aiosqlite.omnilib.dev

**Tools:**
- Bolt.new: https://bolt.new
- Railway: https://railway.app
- Vercel: https://vercel.com

### Learning Resources

**FastAPI + WebSocket:**
- https://fastapi.tiangolo.com/advanced/websockets

**RAG Systems:**
- https://www.pinecone.io/learn/retrieval-augmented-generation

**ChromaDB Tutorial:**
- https://docs.trychroma.com/getting-started

---

## Final Notes

### Remember:

✅ **This is a PLAN** - Use Bolt.new to generate actual code

✅ **Test incrementally** - Don't build everything at once

✅ **Start simple** - Get basic chat working first, add features later

✅ **Use the prompts** - They're designed for Bolt.new's strengths

✅ **Iterate** - If something doesn't work, refine and retry

✅ **Have fun!** - You're building something amazing! 🚀

---

## Questions Before Starting?

Before you start with Bolt.new, consider:

1. **Do you have Perplexity API key ready?**
2. **Is your React frontend running locally?**
3. **Do you want to start with all features or minimal MVP?**
4. **Any specific Bolt.new questions?**

**Ready to build?** Copy Prompt 1 into Bolt.new and let's go! 🎯

---

*Last Updated: 2024-11-08*  
*Status: Ready for Implementation*  
*Tool: Bolt.new (Claude Sonnet 4.5)*  
*Budget: $20/month (Perplexity Pro)*