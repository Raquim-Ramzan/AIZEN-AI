# 🚀 AIZEN: The Multi-Provider AI Assistant

## 🌟 Overview
**AIZEN** is a production-ready, full-stack AI assistant designed with a cyberpunk aesthetic and high-performance multi-model capabilities. It integrates leading AI providers like **Gemini**, **Groq**, **Perplexity**, and **Ollama** to provide a seamless, intelligent, and robust user experience.

Whether it's complex reasoning, ultra-fast coding assistance, deep research, or voice-activated system control, AIZEN intelligently routes every task to the most capable model while maintaining redundant fallbacks.

---

## 🏗️ Architecture
AIZEN follows a modern distributed architecture:

### 1. **Frontend (The Interface)**
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS & ShadeCN UI
- **Key Features**:
  - **Holographic Sphere**: A dynamic, audio-reactive 3D visualization.
  - **Real-time Chat**: WebSocket-based streaming interface.
  - **Voice Integration**: Direct connection to LiveKit for low-latency voice interaction.

### 2. **Backend (The Brain)**
- **Framework**: FastAPI (Python 3.11+)
- **Core Engine**: `AIBrain` handles multi-provider routing and fallbacks.
- **Task Planner**: Analyzes user intent (Coding, Research, Chat, etc.) to select the best provider.
- **System Executor**: A secure layer for executing real-world commands (files, processes, browser).
- **Memory**: ChromaDB for vector-based long-term memory and context retrieval.

### 3. **Voice Agent (The Persona)**
- **Platform**: LiveKit Cloud
- **Model**: Gemini Live GA (`gemini-2.5-flash-native-audio`)
- **Voice**: "Charon" (Native high-fidelity voice)
- **Features**: Native STT/TTS pipeline, Barge-in support, and Tool Calling.

---

## 🧠 Intelligent Model Routing
AIZEN doesn't just use one AI; it uses the *right* AI for the job:

| Task Type | Primary Provider | Primary Model | Fallback Chain |
| :--- | :--- | :--- | :--- |
| **Coding** | Gemini | Gemini 3 Pro | Groq Llama 3.3 70B → Ollama |
| **Reasoning** | Gemini | Gemini 3 Pro | Groq Llama 3.3 70B → Ollama |
| **General Chat** | Gemini | Gemini 2.5 Flash | Groq Compound → Ollama |
| **Web Search** | Perplexity | Sonar Pro | Gemini 2.5 Flash → Ollama |
| **Deep Research**| Perplexity | Deep Research | Sonar Pro → Gemini 3 Pro |
| **Speech (Voice)**| Gemini | Gemini Live GA | Standard STT/TTS Pipeline |

---

## 🛠️ Key Components & Capabilities

### 📡 System Operations (Tool Calling)
AIZEN can interact with your computer through a secure execution layer:
- **Web**: Open URLs, Perform deep searches.
- **Files**: Read, Write, Search, and Delete files.
- **Processes**: Start/Kill applications, Monitor system stats (CPU, RAM).
- **Automation**: Type text, Press keys (Hotkeys).
- **Security**: Built-in `SecurityManager` for risk-based approvals on sensitive operations.

### 🎙️ Voice Interaction
- Powered by **Gemini Live**, providing a "human-like" conversation experience.
- Supports **Barge-in** (you can interrupt AIZEN while it's speaking).
- Deeply integrated with system tools—you can ask AIZEN to "Open Chrome" or "Create a Python script" using just your voice.

### 💾 Memory & Context
- **Conversation Manager**: Maintains session history and context.
- **Vector Store**: Uses Gemini embeddings to store and retrieve long-term knowledge.
- **Core Memory**: Persistent storage for user preferences and system state.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **API Keys**: Gemini, LiveKit (Cloud), Groq (Optional), Perplexity (Optional).

### 2. Setup
1. Clone the repository.
2. Configure `backend/.env` with your API keys.
3. Run the master start script:
   ```powershell
   .\start-aizen.ps1
   ```

### 3. Components
The start script will launch:
- **Backend API**: `http://localhost:8001`
- **Frontend UI**: `http://localhost:8080`
- **Voice Agent**: Connection to LiveKit Cloud.

---

## 📂 Project Structure
```text
AIZEN/
├── backend/                # Python FastAPI Service
│   ├── app/                # Core Application Logic
│   │   ├── api/            # REST & WebSocket Endpoints
│   │   ├── core/           # Brain, Router, System Executor
│   │   ├── memory/         # Vector Store & Conversation
│   │   ├── speech/         # STT/TTS handling
│   │   └── agent.py        # LiveKit Voice Agent
│   └── data/               # Persistent storage (DBs, Logs)
├── frontend/               # React Vite Application
│   ├── src/
│   │   ├── components/     # UI Components (HolographicSphere, etc.)
│   │   ├── hooks/          # React Hooks
│   │   └── services/       # API & WebSocket Clients
├── start-aizen.ps1         # Master Startup Script
└── ARCHITECTURE.md         # Detailed technical documentation
```

---

## 🎨 Design Philosophy
AIZEN is built to be **FAST**, **SMART**, and **STUNNING**. 
- **Performance**: Groq integration ensures near-instant text and speech responses.
- **Reliability**: Multi-tier fallbacks ensure AIZEN works even if one provider is down.
- **Aesthetics**: A dark, glowing, futuristic UI that feels like an OS from the future.
