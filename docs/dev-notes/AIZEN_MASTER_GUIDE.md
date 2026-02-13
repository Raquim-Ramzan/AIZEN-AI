# 🌌 AIZEN - Advanced AI Assistant System
> **Master Project Documentation & Status Report**
> *Generated: November 25, 2025*

## 1. Executive Summary
**AIZEN** is a next-generation, voice-activated AI assistant designed to transcend simple chatbots. It features a holographic interface, real-time voice interaction, and a "Multi-Brain" architecture that intelligently routes tasks to the best available AI model (Gemini, Groq, Perplexity, or Ollama).

Unlike standard assistants, AIZEN possesses **Contextual Awareness**, **Memory**, and a **Professional Workspace** (Artifacts) to separate conversation from code generation.

---

## 2. System Architecture

### 🖥️ Frontend (The Interface)
- **Framework**: React + TypeScript + Vite
- **Styling**: TailwindCSS + Shadcn UI + Custom Neon/Holographic Theme
- **Key Components**:
  - **Holographic Sphere**: Central visual agent that reacts to voice/state.
  - **Artifacts Panel**: Dedicated workspace for code/documents.
  - **Chat Interface**: Real-time streaming chat with provider metadata.
  - **Settings Panel**: Live configuration of AI providers and models.

### 🧠 Backend (The Brain)
- **Framework**: FastAPI (Python)
- **Communication**: WebSockets (Real-time streaming)
- **Intelligence**: Multi-Provider Model Router
- **Memory**: ChromaDB (Vector Store) + SQLite (Session History)

---

## 3. Key Features Implemented (Phase 1 Complete)

### 🚀 A. Multi-Provider "Hive Mind"
AIZEN is not tied to a single AI. It integrates multiple providers:
1.  **Gemini (Google)**: Primary brain for reasoning, coding, and chat.
2.  **Groq**: Ultra-fast inference for quick tasks and TTS/STT.
3.  **Perplexity**: Real-time web search and deep research.
4.  **Ollama**: Local, offline fallback model.

### 🧠 B. Intelligent Model Routing (AI-Powered)
Instead of hardcoded rules, AIZEN uses a lightweight AI (Gemini 2.5 Flash) to **classify user intent** in real-time:
- **"Code me a calculator"** → Classified as `CODING` → Routes to **Gemini 3 Pro**
- **"Who is the CEO of Google?"** → Classified as `SEARCH` → Routes to **Perplexity**
- **"Hi there"** → Classified as `CHAT` → Routes to **Gemini Flash** (Fast/Cheap)

### 📂 C. Artifacts System (Professional Workspace)
To prevent chat clutter, code snippets are treated as "Artifacts":
- **Auto-Extraction**: Code blocks are automatically detected in responses.
- **Clean Chat**: Chat shows a sleek "VIEW ARTIFACT" button instead of raw code.
- **Dedicated Panel**: Clicking opens a side panel with syntax highlighting, copy, and download options.

### ⚙️ D. Live Configuration
- **Visual Status**: Settings panel shows which providers are active (Green/Red indicators).
- **Manual Override**: Users can force a specific provider (e.g., "Always use Groq") if desired.
- **Task Preferences**: View which model is assigned to which task type.

---

## 4. Detailed Implementation (Today's Work)

### Backend Updates
- **`model_router.py`**: Implemented the `ModelRouter` class with the routing table.
- **`planner.py`**: Added `_classify_task_with_ai` using Gemini Flash for intent detection.
- **`brain.py`**: Rewrote `AIBrain` to orchestrate multi-provider generation.
- **`vector_store.py`**: Fixed ChromaDB embedding function conflicts.

### Frontend Updates
- **`ArtifactsPanel.tsx`**: Created the new side panel component.
- **`Index.tsx`**:
    - Integrated `ArtifactsPanel`.
    - Added logic to extract code blocks from WebSocket messages.
    - Added "New Artifact" toast notifications.
- **`ChatInterface.tsx`**:
    - Implemented logic to **hide** raw code blocks.
    - Added "VIEW ARTIFACT" buttons.
    - Added "via [Provider]" metadata tags to messages.
- **`SettingsPanel.tsx`**: Connected to backend `/api/settings` to show real status.

---

## 5. How to Run AIZEN

### Prerequisites
- Python 3.11+
- Node.js 18+
- API Keys (Gemini, Groq, Perplexity) in `backend/.env`

### Start Backend
```powershell
cd backend
python -m app.main
# Server starts at http://localhost:8001
```

### Start Frontend
```powershell
cd frontend
npm run dev
# App opens at http://localhost:5173
```

---

## 6. Future Roadmap (Phase 2 & 3)

- **Phase 2: Vision & Screen**: Allow AIZEN to "see" your screen and analyze images.
- **Phase 3: Voice Mode**: Full duplex voice conversation (Wake word "Hey Aizen").
- **Phase 4: Desktop Control**: Allow AIZEN to click and type on your computer.and perform anything by LLM powered AI assistance so that it could read , write and create anything.

## 7. Project Structure Overview

```
c:\Projects\Aizen\
├── backend\
│   ├── app\
│   │   ├── core\
│   │   │   ├── brain.py        # Main AI orchestration
│   │   │   ├── model_router.py # Routing logic
│   │   │   └── planner.py      # Intent classification
│   │   ├── api\
│   │   │   └── websocket.py    # Real-time comms
│   │   └── memory\             # ChromaDB & SQLite
│   └── .env                    # API Keys
│
├── frontend\
│   ├── src\
│   │   ├── components\
│   │   │   ├── ArtifactsPanel.tsx # Code workspace
│   │   │   ├── ChatInterface.tsx  # Message rendering
│   │   │   ├── ModelSelector.tsx  # Provider dropdown
│   │   │   └── HolographicSphere  # Visual agent
│   │   ├── hooks\
│   │   │   └── useChat.ts         # Chat logic
│   │   └── pages\
│   │       └── Index.tsx          # Main layout
```
