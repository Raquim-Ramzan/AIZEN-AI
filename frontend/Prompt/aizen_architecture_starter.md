# AIZEN - Architecture Deep-Dive Context

## 🎯 Context Purpose
This context is dedicated to creating comprehensive architecture documentation for AIZEN, a personal AI assistant. The goal is to provide detailed technical specifications, diagrams, and integration guides before any code implementation.

---

## 📋 Project Brief

### Project Name: AIZEN
Personal AI assistant with advanced capabilities, designed to be 100x better than typical implementations.

### Current Status:
- ✅ Master planning document created (reference available)
- ✅ UI prototype started (cyberpunk theme, voice activation)
- ⏳ Backend architecture needed (this context)
- ⏳ Implementation pending

### Key Requirements:
- **Budget:** $0 (using free tools only)
- **Primary Language:** Python (backend)
- **Frontend:** React with cyberpunk/sci-fi aesthetic
- **Deployment:** Local laptop
- **User Model:** Single user (no authentication needed)
- **Voice:** Core feature (Faster-Whisper STT + Piper TTS)

---

## 🏗️ Technical Stack

### Backend (Python)
```
- FastAPI (REST API + WebSocket)
- Groq API (fast inference for complex tasks)
- Ollama (local models for quick/private tasks)
- LangGraph (orchestration & planning)
- ChromaDB (vector database for semantic memory)
- SQLite (conversation storage)
- Faster-Whisper (speech-to-text)
- Piper TTS (text-to-speech)
```

### Frontend (React)
```
- Vite + React
- TailwindCSS
- Zustand (state management)
- WebSocket client
- Cyberpunk/sci-fi theme (cyan/teal primary colors)
```

### Tools & Capabilities
```
- Web search (DuckDuckGo, Wikipedia)
- File operations (read, write, search)
- Code execution (sandboxed Python)
- Calendar/Tasks/Reminders
- System operations
- Extensible tool framework
```

---

## 🎨 UI/UX Reference

### Current UI Elements:
- Dark theme with cyan/teal accents
- "AIZEN" branding with futuristic logo
- Sidebar with session management
- Animated circular HUD in center
- Message display (green bubbles, right-aligned)
- Input bar with SEND/SCREEN/FILE buttons
- Voice activation: Alt + PgUp
- "READY" status indicator
- Session history panel

### UI Improvement Areas (Secondary Priority):
- HUD animation functionality
- Message display polish
- Tool usage visualization
- Loading states
- Error handling UI
- Settings panel

---

## 📊 Required Deliverables

### 1. System Architecture Diagram
**What to Include:**
- Complete visual map of AIZEN's components
- Data flow from user input to AI response
- Integration points between frontend, backend, AI models
- Memory system architecture
- Tool execution pipeline
- Error handling and fallback mechanisms

**Format:** Clear, labeled diagram (text-based or visual description)

### 2. Component Breakdown
**For Each Component, Explain:**
- **Purpose:** What does it do?
- **Responsibilities:** What is it responsible for?
- **Dependencies:** What does it need?
- **Interfaces:** How do other components interact with it?
- **Failure Modes:** What can go wrong?
- **Extension Points:** How can it be enhanced?

**Components to Cover:**
- FastAPI Backend Server
- AI Brain (Groq/Ollama Router)
- Memory System (Core + Conversations)
- Tool Framework
- WebSocket Handler
- Speech System (STT/TTS)
- React Frontend
- State Management

### 3. Data Flow Charts

**Critical Flows to Document:**

**A. User Message Flow:**
```
User types/speaks → Frontend → Backend → AI Brain → Tools? → Memory → Response → Frontend
```

**B. Memory System Flow:**
```
How core memory is loaded
When/how conversations are saved
Vector search process
Core memory updates
```

**C. Tool Execution Flow:**
```
AI decides tool needed → Tool selection → Parameter extraction → Execution → Result processing → Response integration
```

**D. Voice Flow:**
```
Voice input → STT → Text processing → AI response → TTS → Audio output
```

**E. Groq/Ollama Switching:**
```
Task analysis → Complexity assessment → Model selection → Fallback handling
```

### 4. API Contract Specifications

**REST Endpoints:**
Document each endpoint with:
- HTTP method and path
- Request body schema
- Response body schema
- Error responses
- Example requests/responses

**Required Endpoints:**
```
POST   /api/conversations          # Create new conversation
GET    /api/conversations          # List conversations
GET    /api/conversations/{id}     # Get conversation details
DELETE /api/conversations/{id}     # Delete conversation
PUT    /api/conversations/{id}     # Update conversation

POST   /api/messages               # Send message (non-streaming)
GET    /api/messages/{conv_id}     # Get messages

GET    /api/memory/core            # Get core memory
POST   /api/memory/core            # Update core memory

POST   /api/speech/transcribe      # STT
POST   /api/speech/synthesize      # TTS

GET    /api/tools                  # List available tools
POST   /api/tools/{name}           # Execute tool directly

GET    /api/settings               # Get settings
PUT    /api/settings               # Update settings
```

**WebSocket Protocol:**
Document message types:
- Client → Server messages
- Server → Client messages
- Streaming format
- Tool execution notifications
- Error handling
- Reconnection strategy

### 5. Memory System Deep-Dive

**Core Memory Structure:**
- Exact JSON schema
- What gets stored
- When it updates
- How it's loaded
- Vector embedding strategy
- Semantic search implementation

**Conversation Storage:**
- SQLite schema
- Message structure
- Metadata tracking
- Query patterns
- Cleanup/archival strategy

**Integration Between Systems:**
- How core memory informs conversations
- When conversation summaries update core memory
- Cross-conversation knowledge sharing

### 6. Tool Execution Pipeline

**Tool Architecture:**
- Base tool class structure
- Tool registration system
- Parameter validation
- Execution sandboxing
- Result formatting
- Error handling

**AI Tool Selection:**
- How AI decides which tool to use
- Function calling implementation
- Parameter extraction
- Multi-tool orchestration
- Tool chaining for complex tasks

**Initial Tool Set:**
Document each tool:
- `web_search`: DuckDuckGo + Wikipedia
- `file_read`: Read file contents
- `file_write`: Write to files
- `file_search`: Search filesystem
- `code_execute`: Run Python code (sandboxed)
- `calendar_add`: Add reminders/events
- `system_info`: Get system information

### 7. Integration Points Map

**Critical Integration Points:**

**Frontend ↔ Backend:**
- WebSocket connection establishment
- Message streaming protocol
- File upload handling
- Voice data transmission
- State synchronization

**Backend ↔ AI Models:**
- Groq API integration
- Ollama local connection
- Model selection logic
- Prompt formatting
- Response parsing

**Backend ↔ Memory:**
- Core memory loading on startup
- Conversation CRUD operations
- Vector search queries
- Memory update triggers

**Backend ↔ Tools:**
- Tool discovery
- Dynamic tool loading
- Execution isolation
- Result handling

**Speech Integration:**
- Audio input capture (frontend)
- STT processing (backend)
- TTS generation (backend)
- Audio playback (frontend)

---

## 🎯 Key Architectural Principles

### 1. Modularity
Every component should be:
- Independently testable
- Loosely coupled
- Clearly defined interfaces
- Easy to replace/upgrade

### 2. Agent Architecture (Not Chatbot)
AIZEN should:
- Plan multi-step tasks
- Use tools autonomously
- Learn from interactions
- Handle errors gracefully
- Be proactive when appropriate

### 3. Memory-First Design
- Core memory is always loaded
- Every conversation has access to shared knowledge
- Important learnings are automatically saved
- Vector search enables semantic recall

### 4. Intelligent Model Routing
- Complex tasks → Groq (fast, powerful)
- Simple tasks → Ollama (local, private)
- Automatic fallback on failure
- Cost and latency optimization

### 5. Extensibility
- Easy to add new tools
- Plugin-based architecture for features
- Configuration-driven behavior
- API-first design

### 6. Zero Cost Operations
- All AI inference free (Groq free tier + Ollama local)
- No cloud storage costs
- No external service dependencies
- Open source tools only

---

## ⚠️ Important Constraints

### What Bolt/Lovable CAN'T Do Well:
- System-level integrations (Ollama, Faster-Whisper)
- Complex memory architecture
- LangGraph workflows
- Proper error handling
- Security sandboxing

### What Bolt/Lovable CAN Do Well:
- UI components
- REST API routes (simple)
- Frontend state management
- Styling and layouts
- Basic WebSocket clients

### Therefore:
The architecture must clearly separate what will be:
- Generated by Bolt/Lovable (UI, basic API)
- Hand-coded (system integration, memory, tools)
- Integration glue code (connecting the pieces)

---

## 📝 Documentation Standards

### For Each Section:
1. **Overview** - What is this component/flow?
2. **Visual Diagram** - Text-based representation or detailed description
3. **Detailed Explanation** - How does it work?
4. **Implementation Notes** - Key considerations
5. **Integration Points** - How does it connect?
6. **Error Scenarios** - What can go wrong?
7. **Testing Strategy** - How to verify it works?
8. **Extension Guidelines** - How to add features?

### Diagram Format:
Use clear ASCII diagrams or detailed textual descriptions that can be easily visualized:

```
Example:
┌─────────────┐
│   Frontend  │
│   (React)   │
└──────┬──────┘
       │ WebSocket
       ↓
┌─────────────┐
│   Backend   │
│  (FastAPI)  │
└──────┬──────┘
       │
   ┌───┴───┐
   ↓       ↓
┌──────┐ ┌──────┐
│ Groq │ │Ollama│
└──────┘ └──────┘
```

---

## 🚀 Approach Guidelines

### Start with Big Picture
1. Show complete system architecture first
2. Then zoom into each component
3. Then show how data flows through
4. Finally, detail integration points

### Be Specific
- Don't say "memory system" - explain ChromaDB vs SQLite usage
- Don't say "API endpoints" - list exact routes with schemas
- Don't say "tool execution" - show the complete pipeline

### Think Integration
- Every component description should explain how it connects
- Every data flow should show all transformation points
- Every API should specify both sides of the contract

### Consider Failures
- What happens when Groq is down?
- What if Ollama isn't running?
- How to handle WebSocket disconnections?
- What if a tool fails?

### Plan for Extension
- How to add new tools?
- How to add new AI models?
- How to add new memory types?
- How to add new frontend features?

---

## 💡 Questions to Answer in This Context

### Architecture Questions:
1. How does the dual AI system (Groq + Ollama) work in practice?
2. What's the exact core memory schema and update mechanism?
3. How do conversations remain isolated while sharing core memory?
4. What's the tool registration and execution pipeline?
5. How does WebSocket streaming work for long responses?
6. What's the voice input/output complete flow?
7. How are errors propagated from backend to frontend?

### Implementation Questions:
8. What Python packages are needed for each component?
9. What's the startup sequence for the backend?
10. How is configuration managed (environment variables, files)?
11. What's the database initialization process?
12. How are tools discovered and loaded dynamically?

### Integration Questions:
13. What's the exact WebSocket message protocol?
14. How does frontend know when a tool is being executed?
15. How does frontend display streaming responses with tool usage?
16. What's the file upload flow for document analysis?
17. How does voice activation trigger backend processing?

---

## 📚 Reference Information

### Master Document
The complete planning document includes:
- Full tech stack details
- Memory system design principles
- Tool system overview
- Development phases
- Configuration examples
- Troubleshooting guide

*Refer to master document for context, but focus on detailed architecture here.*

### Current UI Screenshot Info
- Dark theme, cyan/teal accents
- Sidebar navigation
- Circular animated HUD
- Message bubbles (right-aligned, green)
- Bottom input bar with buttons
- Voice shortcut visible
- Session management visible

### Previous Context Decisions
- Using Bolt/Lovable as code generators
- Copying code locally for full control
- Budget is $0 (free tools only)
- Python for backend brain (learned from Alexus failure)
- Token efficiency strategy (multiple contexts)

---

## ✅ Success Criteria

This architecture documentation is successful when:

1. **Complete Understanding**
   - Anyone can understand how AIZEN works by reading it
   - No ambiguity in component responsibilities
   - Clear separation of concerns

2. **Implementation Ready**
   - Developer can start coding with confidence
   - All integration points are specified
   - API contracts are clear

3. **Bolt/Lovable Ready**
   - Know exactly what to ask Bolt/Lovable to generate
   - Know what must be hand-coded
   - Know how to integrate the pieces

4. **Future-Proof**
   - Easy to add new features
   - Clear extension points
   - Maintainable structure

5. **Debuggable**
   - Error scenarios documented
   - Failure modes understood
   - Testing strategy clear

---

## 🎬 Getting Started

**Recommended Flow:**

1. **Start with System Architecture Diagram**
   - Show the complete system
   - All major components
   - All connections
   - Data flow overview

2. **Deep-Dive Each Component**
   - One at a time
   - Complete specification
   - Integration points

3. **Document All Data Flows**
   - User message flow
   - Memory operations
   - Tool execution
   - Voice processing

4. **Specify All APIs**
   - REST endpoints
   - WebSocket protocol
   - Error responses

5. **Detail Memory System**
   - Core memory mechanics
   - Conversation storage
   - Vector search

6. **Explain Tool Pipeline**
   - Tool architecture
   - Execution flow
   - AI integration

7. **Map Integration Points**
   - Frontend ↔ Backend
   - Backend ↔ AI
   - Backend ↔ Memory
   - Backend ↔ Tools

---

## 📌 Final Notes

- **Priority:** Architecture clarity over code generation
- **Detail Level:** Enough to implement without guessing
- **Format:** Clear, organized, visual where helpful
- **Audience:** Developer who will implement this (me + Bolt/Lovable)

**Remember:** This is the foundation. If the architecture is solid, implementation is straightforward. If architecture is unclear, implementation becomes guesswork.

---

## 🚀 Ready to Begin!

Start with: **"Let's build the complete system architecture for AIZEN..."**

And work through each deliverable systematically.

---

*Context Type: Architecture & Design*  
*Next Context: Backend Implementation*  
*Project: AIZEN Personal AI Assistant*  
*Date: November 2024*