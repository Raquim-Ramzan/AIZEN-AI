# 💠 AIZEN | Cognitive Intelligence Systems
**Production-hardened, Cloud-First AI Systems Architecture.**

AIZEN is a high-performance, asynchronous AI orchestration engine designed for professional-grade RAG (Retrieval-Augmented Generation) and system-level tool execution. Refactored from a 2025 prototype into a cloud-native architecture, AIZEN leverages a multi-provider routing strategy to deliver low-latency, resilient, and intelligent responses.

---

## 🏛️ Core Architecture

### ☁️ Cloud-First Orchestration
AIZEN implements a sophisticated **Multi-Provider Router** that orchestrates requests across **Gemini**, **Perplexity**, and **Groq**. 
- **Intelligent Fallback**: Automatic failover logic ensures system uptime even if a provider experiences latency or outages.
- **Task-Specific Routing**: Logic-heavy tasks route to reasoning models, while high-velocity streaming uses optimized groq-compounds.

### 🛡️ Production-Grade Security
Built with a security-first mindset, the system is hardened for public deployment:
- **FastAPI Security()**: Integrated dependency injection for system-level authentication.
- **Bearer Token Auth**: Mandatory session validation for all system-tool executions (File Ops, Code Execution).
- **Hardened CORS**: Strict origin-based policies (no wildcards) to prevent unauthorized cross-origin requests.
- **Sanitized Diagnostics**: Health endpoints are locked down to prevent configuration leaking.

### ♊ Native Gemini Integration
Unlike standard implementations that rely on string-concatenation for history, AIZEN uses **Native Content Objects**:
- **Multi-Turn State**: Preserves strict `user` and `model` role mapping.
- **System Instruction Injection**: Native handling of system prompts for higher instruction adherence.
- **Batch Processing**: Optimized embedding generation using `genai.embed_content` for high-throughput RAG indexing.

### 🧠 Optimized RAG Memory
The retrieval pipeline is engineered for precision and scale:
- **Token-Aware Budgeting**: Context windows are managed by real-time token count estimation (8000+ tokens) rather than arbitrary character limits.
- **High-Performance Reranking**: Replaced circular LLM-reranking with an **Embedding-based Cosine Similarity** engine, delivering ~10x faster retrieval validation.
- **Lifespan Management**: Singleton resources (ChromaDB, Vector Store, Connection Pools) are managed via FastAPI `lifespan` events, ensuring zero-leak instantiation.

---

## 🚀 Core Features

- **Recursive Task Planning**: Complex user requests are decomposed into executable plans.
- **Natural Language System Ops**: Direct file manipulation and code execution via natural language (fully audited).
- **Web-Intelligence**: Real-time web search integration via Perplexity Sonar.
- **Persistent Core Memory**: Long-term fact storage using ChromaDB for personalized context.
- **Holographic UI**: A Cyber-Minimalist liquid-glass frontend for immersive interaction.

---

## 🛠️ Technical Stack

- **Backend**: Python 3.11+ | FastAPI | Pydantic v2 (Settings Management)
- **AI Core**: Google Gemini 3.1+ | Groq | Perplexity AI
- **Memory**: ChromaDB (Vector) | SQLite (Relational) | MongoDB (Document)
- **Frontend**: TypeScript | Vite | Vanilla CSS (Liquid Glass Aesthetics)
- **Security**: FastAPI Security Dependencies | Bearer Auth | Dotenv Vaulting

---

## 🏁 Getting Started

### 1. Environment Setup
Clone the repository and initialize the configuration:
```bash
cp backend/.env.example backend/.env
```

### 2. Configure API Keys
Edit `backend/.env` and provide your credentials. 
*Note: Ensure `AIZEN_API_KEY` is set to a secure token for server-side authentication.*

### 3. Quick Start (Windows)
AIZEN includes a unified launcher for local development:
```powershell
.\start-aizen.ps1
```

### 4. Direct API Execution
If running manually, start the FastAPI server:
```bash
cd backend
python -m app.main
```
The API will be available at `http://localhost:8001/docs`.

---

## ⚖️ Security Warning
This system is capable of executing system-level operations. **Never** run the backend as root/administrator. Ensure `AIZEN_API_KEY` is properly configured in production environments to guard system tools.

---

<p align="center">
  <b>Developed by Raquim Ramzan an AI Systems Architect for the next generation of Intelligence.</b><br>
  <i>Refactored and Hardened for Public Release — April 2026</i>
</p>
