# Multi-Provider AI Architecture

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER REQUEST                         │
│                   "Write a Python function"                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER (routes.py)                     │
│  /api/chat  |  /api/models/available  |  /api/settings     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                TASK PLANNER (planner.py)                     │
│         Analyzes intent → Detects "CODING" task              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              MODEL ROUTER (model_router.py)                  │
│   CODING → Gemini 3 Pro → Groq Llama 70B → Ollama          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   AI BRAIN (brain.py)                        │
│       Routes to selected provider with fallback logic        │
└──────────┬────────┬─────────┬──────────┬─────────────────────┘
           │        │         │          │
     ┌─────┘   ┌────┘    ┌────┘     ┌────┘
     ↓         ↓         ↓          ↓
┌─────────┐ ┌──────┐ ┌──────────┐ ┌────────┐
│ GEMINI  │ │ GROQ │ │PERPLEXITY│ │OLLAMA  │
│   API   │ │ API  │ │   API    │ │(local) │
├─────────┤ ├──────┤ ├──────────┤ ├────────┤
│3 Pro    │ │Llama │ │Sonar Pro │ │Llama   │
│2.5 Flash│ │70B   │ │Research  │ │3.2:3b  │
│Imagen 4 │ │Comp  │ │Reasoning │ │        │
│Text Emb │ │Whis  │ │          │ │        │
└─────────┘ └──────┘ └──────────┘ └────────┘
```

## 🔄 Request Flow

```
1. USER → API Endpoint
        ↓
2. Extract message + metadata
        ↓
3. Get conversation context + memory
        ↓
4. TASK PLANNER analyzes intent:
   - Looks for keywords
   - Determines task type (CODING, CHAT, SEARCH, etc.)
        ↓
5. MODEL ROUTER selects best model:
   - Checks task type
   - Checks provider availability
   - Returns (provider, model)
        ↓
6. AI BRAIN executes:
   - Calls selected provider
   - Handles errors
   - Falls back if needed
        ↓
7. Response with metadata:
   {
     "content": "...",
     "provider": "gemini",
     "model": "gemini-3-pro-preview"
   }
        ↓
8. Save to conversation history
        ↓
9. USER receives response
```

## 🧠 Task Detection Logic

```
analyze_intent(message):
│
├─ Contains ["write code", "function", "implement"]?
│  └─→ TaskType.CODING
│
├─ Contains ["analyze", "compare", "explain why"]?
│  └─→ TaskType.COMPLEX_REASONING
│
├─ Contains ["search", "find", "latest"]?
│  └─→ TaskType.WEB_SEARCH
│
├─ Contains ["research", "comprehensive", "in-depth"]?
│  └─→ TaskType.DEEP_RESEARCH
│
└─ Simple message?
   └─→ TaskType.GENERAL_CHAT
```

## 🎯 Model Selection Logic

```
select_model(task_type):
│
├─ Manual override provided?
│  └─→ Use manual selection
│
├─ Task type detected:
│  │
│  ├─ CODING:
│  │  Primary: Gemini 3 Pro
│  │  Fallback: Groq Llama 3.3 70B → Ollama
│  │
│  ├─ COMPLEX_REASONING:
│  │  Primary: Gemini 3 Pro
│  │  Fallback: Groq Llama 3.3 70B → Ollama
│  │
│  ├─ GENERAL_CHAT:
│  │  Primary: Gemini 2.5 Flash
│  │  Fallback: Groq Compound → Ollama
│  │
│  ├─ WEB_SEARCH:
│  │  Primary: Perplexity Sonar Pro
│  │  Fallback: Gemini 2.5 Flash → Ollama
│  │
│  └─ DEEP_RESEARCH:
│     Primary: Perplexity Deep Research
│     Fallback: Sonar Pro → Gemini 3 Pro
│
└─ Check provider availability:
   │
   ├─ Primary available? → Use it ✓
   ├─ Try fallback #1    → Use it ✓
   ├─ Try fallback #2    → Use it ✓
   └─ Last resort        → Ollama ✓
```

## 🔐 Provider Availability Check

```
is_provider_available(provider):
│
├─ GEMINI:  settings.gemini_api_key exists?
├─ GROQ:    settings.groq_api_key exists?
├─ PERPLEXITY: settings.perplexity_api_key exists?
└─ OLLAMA:  Always available (check at runtime)
```

## 📡 WebSocket Flow

```
Client connects → ws://localhost:8001/api/ws/{client_id}
       ↓
┌──────────────────────────────────────────┐
│  1. Send: {"type": "message", ...}       │
└──────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────┐
│  2. Receive: {"type": "thinking", ...}   │
│     Includes: selected_provider, model   │
└──────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────┐
│  3. Receive: {"type": "stream_start"}    │
│     Includes: provider, model            │
└──────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────┐
│  4. Receive: {"type": "token", ...}      │
│     (Multiple times as response streams) │
└──────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────┐
│  5. Receive: {"type": "complete", ...}   │
│     Includes: provider, model            │
└──────────────────────────────────────────┘
```

## 🗂️ File Organization

```
backend/
├── app/
│   ├── core/
│   │   ├── brain.py              # Multi-provider AI client
│   │   ├── model_router.py       # NEW! Intelligent routing
│   │   ├── planner.py            # Enhanced task detection
│   │   └── executor.py           # Tool execution
│   │
│   ├── api/
│   │   ├── models.py             # Enhanced with provider fields
│   │   ├── routes.py             # + 3 new endpoints
│   │   └── websocket.py          # Enhanced streaming
│   │
│   ├── memory/
│   │   ├── vector_store.py       # + Gemini embeddings
│   │   └── conversation.py
│   │
│   ├── speech/
│   │   ├── stt.py                # + Groq Whisper
│   │   └── tts.py                # + Groq PlayAI
│   │
│   ├── config.py                 # + Gemini/Groq config
│   └── main.py
│
├── .env                           # + API keys
├── requirements.txt               # + 2 new packages
└── test_integration.py            # NEW! Test script
```

## 🎨 Provider Capabilities Matrix

```
╔══════════════╦═════════╦════════╦═══════════╦════════╗
║   Feature    ║ Gemini  ║  Groq  ║Perplexity ║ Ollama ║
╠══════════════╬═════════╬════════╬═══════════╬════════╣
║ Coding       ║   ✓✓✓   ║   ✓✓   ║     ✓     ║   ✓    ║
║ Reasoning    ║   ✓✓✓   ║   ✓✓   ║    ✓✓     ║   ✓    ║
║ Chat         ║   ✓✓✓   ║   ✓✓   ║     ✓     ║   ✓    ║
║ Search       ║    ✓    ║   ✗    ║    ✓✓✓    ║   ✗    ║
║ Research     ║    ✓    ║   ✗    ║    ✓✓✓    ║   ✗    ║
║ Speed        ║   ✓✓    ║  ✓✓✓   ║    ✓✓     ║   ✓    ║
║ Quality      ║   ✓✓✓   ║   ✓✓   ║    ✓✓     ║   ✓    ║
║ Cost         ║   ✓✓    ║  ✓✓✓   ║    ✓✓     ║  ✓✓✓   ║
║ Embeddings   ║   ✓✓✓   ║   ✗    ║     ✗     ║   ✗    ║
║ Image Gen    ║   ✓✓✓   ║   ✗    ║     ✗     ║   ✗    ║
║ Speech (STT) ║    ✗    ║  ✓✓✓   ║     ✗     ║   ✗    ║
║ Speech (TTS) ║    ✗    ║  ✓✓✓   ║     ✗     ║   ✗    ║
║ Offline      ║    ✗    ║   ✗    ║     ✗     ║  ✓✓✓   ║
╚══════════════╩═════════╩════════╩═══════════╩════════╝

Legend: ✓✓✓ Excellent | ✓✓ Good | ✓ Basic | ✗ Not Available
```

## 🚀 Key Improvements

### ✅ Intelligent Routing
- Automatically picks best model for task
- No manual selection needed
- But manual override available

### ✅ Robust Fallbacks
- 3-tier fallback chain
- Never fails completely
- Always has offline option

### ✅ Provider Specialization
- Gemini → Coding & Reasoning
- Groq → Speed & Speech
- Perplexity → Search & Research
- Ollama → Offline & Privacy

### ✅ Cost Optimization
- Cheap models for simple tasks
- Premium models for complex tasks
- Automatic selection

### ✅ Enhanced Capabilities
- Cloud-based speech (faster)
- Better embeddings (Gemini)
- Image generation (Imagen)
- 25+ models available

### ✅ Developer Experience
- Transparent provider info
- Easy testing endpoints
- Detailed logging
- Backward compatible

## 🎯 The result?

**A production-ready, multi-provider AI assistant** that:
- Intelligently routes requests
- Never completely fails
- Optimizes for speed, quality, and cost
- Provides transparency
- Scales easily

**Your AI assistant just got SUPER POWERED! 🚀**
