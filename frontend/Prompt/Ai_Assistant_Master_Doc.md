# AI Assistant Project - Complete Master Document

## Project Overview
Building a personal AI assistant from scratch with **$0 budget**, superior to existing implementations, using Python as the core language.

---

## Learning from Alexus (Previous Project)

### What Went Wrong:
- Used JavaScript instead of Python for the brain
- Had 5 variants but lacked proper foundation
- Token/context window limitations killed the project
- Poor architecture made it hard to maintain and extend

### Key Lessons:
- Need solid foundation before building features
- Python is better for AI/ML ecosystem
- Modular architecture is essential
- Token costs need to be managed

---

## Development Strategy

### The Smart Approach:
1. **Use Bolt.new + Lovable.dev** as AI-powered code generators (both use Claude Sonnet 4.5)
2. **Copy generated code** to local environment for full control
3. **Use Claude (me)** for:
   - Architecture design
   - System-level code (Ollama, Whisper, etc.)
   - Integration logic
   - Debugging complex issues
4. **Keep costs at $0** by leveraging free tools

### Why This Works:
- Unlimited generations from Bolt/Lovable
- Full local control and customization
- No context window nightmares
- Access to system-level features Bolt/Lovable can't provide

---

## Tech Stack (Zero Cost)

### Backend (Python - Local)
```
Core Framework:
- FastAPI (REST API + WebSocket for real-time)
- Python 3.11+

AI Brain (Dual System):
- Groq API (free tier: 14,400 requests/day)
  - Llama 3.1 70B, Mixtral
  - Extremely fast inference
  - For complex reasoning tasks
- Ollama (100% local)
  - Llama 3.1, Qwen 2.5, Deepseek Coder
  - For quick tasks and privacy
  - No internet required

Orchestration:
- LangGraph (state machines, complex workflows)
- Custom tool framework for extensibility

Memory:
- ChromaDB (local vector database)
- SQLite (conversations, structured data)
- JSON (config, core memory)

Speech:
- Faster-Whisper (local STT)
- Piper TTS (local TTS, high quality)

Tools:
- DuckDuckGo (web search)
- Wikipedia API
- File system operations
- Code execution (sandboxed)
- Calendar management
```

### Frontend (React - Local)
```
Framework:
- Vite + React
- TailwindCSS for styling
- Zustand for state management

Communication:
- WebSocket (real-time streaming)
- REST API (operations)

Features:
- Chat interface
- Conversation management
- Voice input/output UI
- Settings panel
- Tool usage visualization
```

---

## Architecture Overview

### High-Level Flow
```
User Input 
  ↓
React UI (Frontend)
  ↓
WebSocket/REST → FastAPI (Backend)
  ↓
AI Brain (Groq/Ollama)
  ↓
Tool Layer (search, files, code, etc.)
  ↓
Memory Layer (core + conversations)
  ↓
Response → Stream back to UI
```

### Key Principles
1. **Modular Design** - Each component is independent and testable
2. **Agent Architecture** - Not just a chatbot, but a task-planning agent
3. **Tool-Based** - Extensible system for adding capabilities
4. **Memory-Persistent** - Learns and remembers across sessions
5. **Error-Resilient** - Graceful degradation and recovery

---

## Memory Architecture (Critical Component)

### Two-Tier Memory System

#### 1. Core Memory (Shared Across ALL Conversations)
```json
{
  "user_profile": {
    "name": "...",
    "preferences": {},
    "important_facts": [],
    "learned_behaviors": []
  },
  "learned_knowledge": [
    {
      "fact": "User prefers Python over JavaScript",
      "timestamp": "2024-11-02T10:30:00",
      "confidence": 0.95,
      "source": "conversation_5"
    }
  ],
  "skills_unlocked": [
    "web_search",
    "file_operations",
    "code_execution"
  ],
  "conversation_summaries": {
    "conversation_1": "Discussed building AI assistant...",
    "conversation_2": "Helped debug Python code..."
  }
}
```

**Storage:**
- `core_memory.json` - Structured data
- ChromaDB - Vector embeddings for semantic search
- Always loaded into every conversation
- Assistant can write to it when learning important things

#### 2. Conversation Threads (Individual Contexts)
```sql
-- SQLite Schema
conversations
├── id (PRIMARY KEY)
├── title
├── created_at
├── updated_at
└── metadata (JSON)

messages
├── id (PRIMARY KEY)
├── conversation_id (FOREIGN KEY)
├── role (user/assistant/system/tool)
├── content
├── timestamp
├── metadata (JSON)
└── tool_calls (JSON)
```

**How It Works:**
- Each conversation is isolated
- User can start new conversations on different topics
- Core memory provides context to all conversations
- Important learnings from any conversation → Core memory

---

## Project Structure

```
ai-assistant/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Configuration management
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── brain.py         # AI model interface (Groq/Ollama)
│   │   │   ├── memory.py        # Memory management system
│   │   │   ├── planner.py       # Task planning & orchestration
│   │   │   └── executor.py      # Tool execution engine
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Base tool class
│   │   │   ├── web_search.py    # DuckDuckGo, Wikipedia
│   │   │   ├── file_ops.py      # File operations
│   │   │   ├── code_exec.py     # Safe code execution
│   │   │   ├── calendar.py      # Schedule management
│   │   │   └── system.py        # System operations
│   │   ├── memory/
│   │   │   ├── __init__.py
│   │   │   ├── vector_store.py  # ChromaDB interface
│   │   │   ├── conversation.py  # SQLite conversation manager
│   │   │   └── core_memory.py   # Core memory handler
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py        # API endpoints
│   │   │   ├── websocket.py     # WebSocket handler
│   │   │   └── models.py        # Pydantic models
│   │   └── speech/
│   │       ├── __init__.py
│   │       ├── stt.py           # Faster-Whisper STT
│   │       └── tts.py           # Piper TTS
│   ├── data/
│   │   ├── core_memory.json     # Core memory storage
│   │   ├── conversations.db     # SQLite database
│   │   └── vector_store/        # ChromaDB data
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── components/
│   │   │   ├── Chat/
│   │   │   │   ├── ChatInterface.jsx
│   │   │   │   ├── MessageList.jsx
│   │   │   │   ├── MessageInput.jsx
│   │   │   │   └── VoiceInput.jsx
│   │   │   ├── Sidebar/
│   │   │   │   ├── ConversationList.jsx
│   │   │   │   └── NewConversation.jsx
│   │   │   ├── Settings/
│   │   │   │   └── SettingsPanel.jsx
│   │   │   └── shared/
│   │   │       └── LoadingSpinner.jsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js
│   │   │   ├── useConversations.js
│   │   │   └── useVoice.js
│   │   ├── store/
│   │   │   └── appStore.js      # Zustand store
│   │   ├── services/
│   │   │   ├── api.js           # API client
│   │   │   └── websocket.js     # WebSocket client
│   │   └── styles/
│   │       └── globals.css
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
│
└── docs/
    ├── architecture.md
    ├── api-reference.md
    ├── tool-development.md
    └── deployment.md
```

---

## Agent Architecture (Not Just Chatbot)

### Traditional Chatbot vs Agent
```
Chatbot:
User: "Search for Python tutorials"
Bot: "Here are some Python tutorials..."

Agent:
User: "I want to learn Python"
Agent: 
  1. Plans: Search tutorials → Analyze user level → Create learning path
  2. Executes: Uses web_search tool → Processes results
  3. Stores: Saves to core memory (user wants to learn Python)
  4. Responds: Provides structured learning plan
  5. Proactive: "Would you like me to remind you daily?"
```

### Agent Components

#### 1. Intent Parser
- Understands what user wants
- Extracts entities and parameters
- Determines if multi-step task

#### 2. Task Planner (LangGraph)
```python
# Example planning flow
User: "Find the latest AI news and summarize it"

Plan:
├── Step 1: web_search("latest AI news 2024")
├── Step 2: Analyze results (top 5 sources)
├── Step 3: Extract key points
├── Step 4: Generate summary
└── Step 5: Store in core memory (user interested in AI news)
```

#### 3. Tool Executor
- Sandboxed execution
- Error handling
- Parallel execution when possible
- Result validation

#### 4. Response Generator
- Synthesizes tool results
- Natural language generation
- Context-aware responses

---

## Tool System

### Base Tool Structure
```python
class BaseTool:
    name: str
    description: str
    parameters: dict
    
    async def execute(self, **kwargs):
        """Override this method"""
        pass
    
    async def validate(self, **kwargs):
        """Validate parameters"""
        pass
```

### Available Tools (Initial Set)

1. **Web Search**
   - DuckDuckGo search
   - Wikipedia lookup
   - Returns structured results

2. **File Operations**
   - Read/write files
   - List directories
   - File search
   - Safe path handling

3. **Code Execution**
   - Python code execution
   - Sandboxed environment
   - Timeout protection
   - Output capture

4. **Calendar/Tasks**
   - Schedule reminders
   - Task management
   - Deadline tracking

5. **System Operations**
   - System info
   - Process management
   - Resource monitoring

### Adding New Tools
```python
# Easy to extend!
class WeatherTool(BaseTool):
    name = "get_weather"
    description = "Get weather for a location"
    parameters = {
        "location": {"type": "string", "required": True}
    }
    
    async def execute(self, location: str):
        # Implementation
        pass
```

---

## API Design

### REST Endpoints

```
POST   /api/conversations          # Create new conversation
GET    /api/conversations          # List all conversations
GET    /api/conversations/{id}     # Get conversation details
DELETE /api/conversations/{id}     # Delete conversation
PUT    /api/conversations/{id}     # Update conversation title

POST   /api/messages               # Send message (non-streaming)
GET    /api/messages/{conv_id}     # Get conversation messages

GET    /api/memory/core            # Get core memory
POST   /api/memory/core            # Update core memory

POST   /api/speech/transcribe      # STT
POST   /api/speech/synthesize      # TTS

GET    /api/tools                  # List available tools
POST   /api/tools/{name}           # Execute tool directly

GET    /api/settings               # Get settings
PUT    /api/settings               # Update settings
```

### WebSocket Protocol

```javascript
// Client → Server
{
  "type": "message",
  "conversation_id": "conv_123",
  "content": "Hello, assistant!",
  "metadata": {}
}

// Server → Client (streaming)
{
  "type": "token",
  "content": "Hello",
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
  "type": "complete",
  "message_id": "msg_456",
  "conversation_id": "conv_123"
}

{
  "type": "error",
  "error": "...",
  "code": 500
}
```

---

## Memory System Implementation Details

### Core Memory Workflow

```python
# When user says something important
User: "I prefer dark mode and concise responses"

Assistant Brain:
1. Identifies important preference
2. Calls memory.update_core()
3. Stores in core_memory.json
4. Adds to vector store for semantic search
5. Confirms to user (optional)

# In next conversation (even different topic)
System loads core memory → Assistant remembers preference
```

### Vector Store Usage

```python
# Store important facts
await memory.store_fact(
    content="User is learning Python and prefers practical examples",
    metadata={"category": "preference", "timestamp": "..."}
)

# Semantic search when needed
relevant_facts = await memory.search(
    query="How should I explain code?",
    limit=5
)
# Returns: ["User prefers practical examples", ...]
```

### Conversation Management

```python
# Create new conversation
conv_id = await conversations.create(
    title="Building AI Assistant"
)

# Add messages
await conversations.add_message(
    conversation_id=conv_id,
    role="user",
    content="How do I setup FastAPI?"
)

# Auto-generate summaries for core memory
summary = await conversations.summarize(conv_id)
await core_memory.add_summary(conv_id, summary)
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal:** Basic working assistant

- [ ] FastAPI backend setup
- [ ] Groq API integration
- [ ] Basic conversation (no memory)
- [ ] Simple React UI
- [ ] WebSocket communication
- [ ] 2-3 basic tools (search, files)

**Deliverable:** Can chat and use basic tools

### Phase 2: Intelligence (Week 2)
**Goal:** Real agent capabilities

- [ ] LangGraph orchestration
- [ ] Function calling / tool use
- [ ] Core memory system
- [ ] Conversation threads
- [ ] Multi-step planning
- [ ] Error recovery

**Deliverable:** Acts like an agent, not chatbot

### Phase 3: Advanced Features (Week 3)
**Goal:** Production-ready assistant

- [ ] Ollama integration (local models)
- [ ] Faster-Whisper STT
- [ ] Piper TTS
- [ ] Voice UI
- [ ] Advanced tools (calendar, code exec)
- [ ] Proactive suggestions
- [ ] Learning from feedback

**Deliverable:** Full-featured AI assistant

### Phase 4: Polish (Week 4+)
**Goal:** Amazing UX

- [ ] Beautiful UI (use Bolt/Lovable here!)
- [ ] Animations and transitions
- [ ] Mobile responsive
- [ ] Settings and customization
- [ ] Performance optimization
- [ ] Documentation

**Deliverable:** Production-ready, user-friendly

---

## Development Workflow with Bolt/Lovable

### Strategy
1. **Architecture First** (Claude provides this)
2. **Component-by-Component** generation (Bolt/Lovable)
3. **Integration** (Claude helps here)
4. **Testing & Debugging** (Both)

### Prompt Template for Bolt/Lovable

```
Context: I'm building [COMPONENT NAME] for an AI assistant application.

Tech Stack: [React/FastAPI/etc]

Requirements:
- [Specific requirement 1]
- [Specific requirement 2]
- [Specific requirement 3]

API Contract: [If applicable]
- Endpoint: POST /api/...
- Request: {...}
- Response: {...}

Please create [COMPONENT NAME] with:
1. [Feature 1]
2. [Feature 2]
3. [Feature 3]

Important:
- Use TypeScript/Python type hints
- Include error handling
- Add comments for complex logic
- Make it modular and testable
```

### What to Generate with Bolt/Lovable
- ✅ UI Components (ChatInterface, Sidebar, Settings)
- ✅ API routes (REST endpoints)
- ✅ WebSocket handlers
- ✅ Simple tool implementations
- ✅ Utility functions
- ✅ Styling and layouts

### What to Get from Claude (Me)
- ✅ System architecture
- ✅ Ollama integration code
- ✅ Faster-Whisper setup
- ✅ LangGraph workflows
- ✅ Complex memory logic
- ✅ Integration glue code
- ✅ Debugging complex issues

---

## Key Configuration Files

### Backend: requirements.txt
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pydantic==2.5.0
groq==0.4.0
langchain==0.1.0
langgraph==0.0.20
chromadb==0.4.18
aiosqlite==0.19.0
faster-whisper==0.10.0
piper-tts==1.2.0
duckduckgo-search==4.0.0
wikipedia==1.4.0
```

### Backend: .env
```env
# API Keys
GROQ_API_KEY=your_groq_api_key_here

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Memory
CHROMA_PERSIST_DIR=./data/vector_store
SQLITE_DB=./data/conversations.db
CORE_MEMORY_FILE=./data/core_memory.json

# Speech
WHISPER_MODEL=base
PIPER_MODEL=en_US-lessac-medium

# Server
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:5173
```

### Frontend: package.json
```json
{
  "name": "ai-assistant-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "zustand": "^4.4.7",
    "axios": "^1.6.2",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.0.8",
    "tailwindcss": "^3.3.6",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  }
}
```

---

## Important Considerations

### 1. AI Model Selection Logic
```python
# Intelligent model routing
def select_model(task_type, complexity):
    if complexity == "high" or task_type in ["reasoning", "planning"]:
        return "groq"  # Use Groq for complex tasks
    elif task_type in ["chat", "simple_query"]:
        return "ollama"  # Use local Ollama for simple tasks
    else:
        return "groq"  # Default to Groq
```

### 2. Error Handling Strategy
- Graceful degradation (Groq down? Use Ollama)
- Retry logic with exponential backoff
- User-friendly error messages
- Log everything for debugging

### 3. Performance Optimization
- Cache frequent queries
- Stream responses (don't wait for complete response)
- Parallel tool execution when possible
- Lazy load components

### 4. Security
- Sandbox code execution
- Validate all user inputs
- Rate limiting
- No arbitrary file system access
- Environment variable secrets

### 5. Testing Strategy
- Unit tests for tools
- Integration tests for API
- E2E tests for critical flows
- Manual testing for UX

---

## Next Steps

### Immediate Actions:
1. ✅ **Review this document** - Make sure you understand the architecture
2. **Set up local environment**:
   - Install Python 3.11+
   - Install Node.js 18+
   - Install Ollama
   - Get Groq API key
3. **Create project structure** (folders)
4. **Get component-specific prompts** for Bolt/Lovable
5. **Start with backend foundation**
6. **Then build frontend**
7. **Integrate and test**

### Questions to Answer Before Starting:
- Which Ollama model to use? (llama3.1:8b recommended for start)
- Voice features in Phase 1 or Phase 3?
- Which tools are highest priority?
- Desktop app or web app first?

---

## Resources & References

### Documentation Links:
- FastAPI: https://fastapi.tiangolo.com/
- Groq API: https://console.groq.com/docs
- Ollama: https://ollama.ai/
- LangGraph: https://langchain-ai.github.io/langgraph/
- ChromaDB: https://docs.trychroma.com/
- Faster-Whisper: https://github.com/guillaumekln/faster-whisper
- Piper TTS: https://github.com/rhasspy/piper

### Learning Resources:
- LangChain Agents: https://python.langchain.com/docs/modules/agents/
- Vector Databases: https://www.pinecone.io/learn/vector-database/
- WebSocket with FastAPI: https://fastapi.tiangolo.com/advanced/websockets/

---

## Troubleshooting Common Issues

### Issue: Ollama not responding
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull model if not exists
ollama pull llama3.1:8b
```

### Issue: Groq rate limit
```python
# Implement fallback
try:
    response = await groq_client.chat(...)
except RateLimitError:
    # Fall back to Ollama
    response = await ollama_client.chat(...)
```

### Issue: Memory/ChromaDB errors
```bash
# Clear and reinitialize
rm -rf ./data/vector_store
# Restart backend - will auto-create
```

### Issue: WebSocket disconnections
```javascript
// Implement reconnection logic
const connectWebSocket = () => {
  ws = new WebSocket(WS_URL);
  
  ws.onclose = () => {
    setTimeout(connectWebSocket, 3000); // Reconnect after 3s
  };
};
```

---

## Success Metrics

### How to Know It's Working:
- ✅ Can start multiple conversations
- ✅ Core memory persists across conversations
- ✅ Tools execute successfully
- ✅ Responses stream in real-time
- ✅ Voice input/output works
- ✅ No crashes or data loss
- ✅ Fast response times (<2s for simple queries)

### What "100x Better" Means:
- **Architecture**: Clean, modular, extensible
- **Memory**: Actually remembers and learns
- **Tools**: Really works, not just demos
- **UX**: Smooth, fast, beautiful
- **Reliability**: Doesn't break, handles errors
- **Intelligence**: Plans tasks, not just responds

---

## Final Notes

This is a **living document**. As we build and discover issues or improvements, update this file.

**Remember:**
- Start simple, iterate fast
- Test each component before integrating
- Document as you go
- Ask for help when stuck (that's what I'm here for!)

**You got this!** 🚀

---

*Last Updated: 2024-11-02*
*Project Status: Architecture Phase*
*Next Milestone: Backend Foundation*