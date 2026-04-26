# 💠 AIZEN | Cognitive Intelligence Systems
**Production-hardened, Cloud-Native AI Systems Architecture.**

AIZEN is a high-performance, asynchronous AI orchestration engine designed for professional-grade RAG (Retrieval-Augmented Generation) and system-level tool execution. Refactored into a cloud-native architecture, AIZEN leverages a multi-provider routing strategy to deliver low-latency, resilient, and intelligent responses.

---

## 🏛️ 2026 Core Architecture

### ☁️ Cloud-Native Orchestration (Supabase)
AIZEN has migrated to a unified **Supabase** backend, providing enterprise-grade persistence and vector operations:
- **Vector Search**: High-performance semantic retrieval using PostgreSQL `pgvector`.
- **Hybrid Storage**: Unified management of profiles, conversations, and long-term memory in a single cloud instance.
- **Hardened RPC**: Vector matching is handled via hardened PostgreSQL functions with strict `search_path` security and `SECURITY DEFINER` scoping.

### 🤖 Multi-Provider Intelligence
The system implements a sophisticated **Intelligent Router** that orchestrates the 2026 model lineup:
- **Reasoning & Coding**: Powered by **Gemini 3.1 Pro** (optimized for agentic workflows).
- **High-Velocity Chat**: Powered by **Gemini 3 Flash** (ultra-low latency).
- **Intelligent Fallback**: Automatic failover to **Groq (Llama 3.3)** or **Ollama (Local)** ensures 100% uptime.

### 🧠 High-Performance RAG
The retrieval pipeline is engineered for sub-10ms response times:
- **Local-First Embeddings**: Uses **FastEmbed (BAAI/bge-small-en-v1.5)** for local vector generation, bypassing cloud latency.
- **Dimensionality Alignment**: Optimized 384-dimension vectors for the perfect balance of accuracy and storage efficiency.
- **Token-Aware Memory**: Real-time context management with a 32k+ token awareness for deep-context reasoning.

---

## 🚀 Core Features

- **Recursive Task Planning**: Complex user requests are decomposed into executable plans across multiple tools.
- **Voice-First Interaction**: Integrated STT/TTS with a **Holographic Sphere** UI and dedicated mic controls.
- **System-Level Control**: Secure file manipulation and desktop automation via natural language (fully audited).
- **Cyber-Minimalist UI**: A "Liquid Glass" frontend built with Vanilla CSS for maximum performance and aesthetics.

---

## 🛠️ Technical Stack

- **Backend**: Python 3.11+ | FastAPI | Pydantic v2
- **AI Core**: Google Gemini 3.1 Pro | Gemini 3 Flash | Groq | Perplexity
- **Database**: Supabase (Postgres + pgvector)
- **Embeddings**: FastEmbed (Local)
- **Frontend**: TypeScript | Vite | Vanilla CSS
- **Orchestration**: Custom Intelligent Router with JSON-Schema tool calling

---

## 🏁 Getting Started

### 1. Environment Setup
Clone the repository and initialize the configuration:
```bash
cp backend/.env.example backend/.env
```

### 2. Database Migration
1. Create a new **Supabase** project.
2. Run the provided `supabase_schema.sql` in the **SQL Editor**.
3. Copy your project URL and Service Role Key into `backend/.env`.

### 3. Quick Start (Unified Launcher)
AIZEN includes a unified PowerShell launcher that validates your environment and starts all services:
```powershell
.\start-aizen.ps1
```

### 4. Local AI Fallback
Ensure **Ollama** is running locally with `llama3.2` for offline support and system fallback.

---

## 🛡️ Security
Built for private deployment, AIZEN includes:
- **Hardened SQL**: Explicit schema qualification and search path pinning.
- **Local Auth Bypass**: Streamlined development mode for local-only execution.
- **System Audit Logs**: All tool executions are logged for transparency.

---

<p align="center">
  <b>Developed by Raquim Ramzan | AI Systems Architect</b><br>
  <i>Production Ready — April 2026</i>
</p>
