# AIZEN — Pre-GitHub Deep Audit Report
**Auditor Role:** Senior Principal AI Engineer & Security Auditor  
**Date:** 2026-04-26  
**Target:** `c:\Projects\Aizen` → public GitHub push readiness  

---

## EXECUTIVE SUMMARY

AIZEN has solid architectural ambitions — multi-provider routing, RAG pipeline, approval-gated system operations, real-time WebSocket streaming. However, **it is not safe to push to a public repo today.** Live API keys are sitting in a committed `.env` file, the root `.gitignore` has only 1 line (`node_modules`), and `gitignore.txt` — the properly-written ignore file — is **never actually named `.gitignore`** and thus ignored by Git entirely.

---

## 🔴 [CRITICAL] — Fix Before Any Public Push

### CRIT-1 · Three live API keys hardcoded in a committed `.env`

**File:** `backend/.env`

```
PERPLEXITY_API_KEY="[REDACTED]"
GEMINI_API_KEY="[REDACTED]"
GROQ_API_KEY="[REDACTED]"
```

These are **real, active keys**. The moment this repo goes public, automated scrapers (e.g., `trufflesecurity/trufflehog`, GitHub's own secret scanning) will detect and potentially abuse them — resulting in unexpected API bills and rate-limit bans.

**Immediate actions:**
1. Rotate all three keys in your provider dashboards **right now**.
2. Rename `gitignore.txt` → `.gitignore` (see CRIT-2) so the file is excluded.
3. Add a `.env.example` with placeholder values as documentation.

> [!CAUTION]
> Even after rotating the keys and fixing `.gitignore`, the **git history** retains the old values. You must rewrite history with `git filter-repo --path backend/.env --invert-paths` before publishing.

---

### CRIT-2 · `.gitignore` has only 1 line; the real one is named wrong

**File:** `c:\Projects\Aizen\.gitignore` (root)
```
node_modules
```

The properly-written 80-line ignore file is saved as `gitignore.txt` — a plain text file that Git **completely ignores**. As a result, Git is currently tracking:

| Path | Why it's dangerous |
|---|---|
| `backend/.env` | Live API keys |
| `backend/venv/` | ~hundreds of MB of Python packages |
| `backend/__pycache__/` | Compiled bytecode |
| `backend/data/` | User conversations, ChromaDB vectors, `core_memory.json` — **private user data** |
| `backend/pip_install_log.txt` | 35 KB of debug noise |
| `frontend/dist/` | Build artifacts |
| `frontend/eslint_report.json` / `lint_results.json` | 330+ KB debug artifacts |
| Root `*.exe` (`Aizen-Launcher.exe`, `start-aizen.exe`) | Binary blobs, should not be in source control |
| Root `*.md` (44 files!) | Internal dev notes, debug logs |

**Fix:**
```bash
# 1. Rename the real gitignore
mv gitignore.txt .gitignore
# Merge with root .gitignore and add missing entries:
echo "backend/.env" >> .gitignore
echo "backend/data/" >> .gitignore
echo "backend/venv/" >> .gitignore
echo "*.exe" >> .gitignore
# 2. Untrack already-tracked files
git rm -r --cached backend/.env backend/venv backend/data frontend/dist frontend/eslint_report.json
```

---

### CRIT-3 · CORS is set to `"*"` in production

**File:** `backend/.env` line 3 and `backend/app/main.py` line 141-146

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(','),   # splits "*" → ["*"]
    allow_credentials=True,  # ← THIS IS THE PROBLEM
    ...
)
```

`allow_credentials=True` with `allow_origins=["*"]` is **rejected by browsers** (CORS spec §3.2) and is a security misconfiguration. Any browser making cross-origin credentialed requests will fail. More importantly, it signals no thought was put into origin control.

**Fix:** Use a proper allowlist in `.env.example`:
```env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

### CRIT-4 · `/health` endpoint leaks API key configuration status publicly

**File:** `backend/app/main.py` lines 165-174

```python
@app.get("/health")
async def health_check():
    return {
        "gemini": "configured" if settings.gemini_api_key else "missing_key",
        "perplexity": "configured" if settings.perplexity_api_key else "missing_key",
```

An unauthenticated public endpoint that tells attackers exactly which providers are live. This is reconnaissance on a silver platter.

**Fix:** Return only a simple `{"status": "ok"}` on the public health endpoint. Move detailed diagnostics behind authentication.

---

### CRIT-5 · `user_id=None` hardcoded — authentication is entirely absent

**File:** `backend/app/api/routes.py` line 262

```python
result = await system_executor.execute_tool_call(
    func_name,
    func_args,
    user_id=None  # TODO: Get from auth
```

This is not just a TODO — it means **any unauthenticated caller** can trigger system operations (file writes, process starts). The security approval layer in `SecurityManager` is well-designed, but it's bypassed at the entry point because there is no auth.

**Fix:** Implement at minimum an API key header check (FastAPI `Security()` dependency) or JWT middleware before this goes public.

---

## 🟠 [REFACTOR] — Structural Improvements for GitHub-Readiness

### REF-1 · `ConversationManager` is re-instantiated on **every single API request**

**File:** `backend/app/api/routes.py` — every route handler

```python
@router.get("/conversations")
async def get_conversations(request: Request):
    conv_manager = ConversationManager()   # ← new instance every call
    await conv_manager.initialize()        # ← re-opens DB connection every call
```

There are 8+ route handlers that do this. Each call opens a fresh SQLite connection. This pattern will cause connection pool exhaustion under any real load. The `app.state` pattern is already used correctly for `ai_brain`, `vector_store`, and `rag_manager` — `conv_manager` must join them.

**Fix:** Initialize `conv_manager` once in `lifespan()` (already done: `app.state.conv_manager = conv_manager`) and inject it via `request.app.state.conv_manager` in routes, exactly like the other singletons.

---

### REF-2 · The "Reranker" is just another LLM call — it adds latency, not cross-encoder precision

**File:** `backend/app/memory/reranker.py`

The reranker makes a **synchronous Gemini API call** on every query to score retrieved chunks. For 5 documents × ~600ms LLM latency = **3 seconds added to every response**. A real cross-encoder reranker (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2` via `sentence-transformers`) runs locally in ~50ms and is scientifically more accurate for this task.

**Fix:** Swap to a real cross-encoder:
```python
from sentence_transformers import CrossEncoder
model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
scores = model.predict([(query, doc) for doc in documents])
```
This eliminates network latency entirely and is the industry-standard approach.

---

### REF-3 · Gemini Chat History API is not being used — messages are stringified

**File:** `backend/app/core/brain.py` lines 348-362

```python
def _convert_to_gemini_messages(self, messages):
    combined = []
    for msg in messages:
        combined.append(f"System: {content}")
        combined.append(f"User: {content}")
        combined.append(f"Assistant: {content}")
    return "\n\n".join(combined)   # ← Returns a plain STRING
```

This concatenates the entire chat history into one giant string and sends it as a single `user` turn. You completely lose:
- Proper `system_instruction` support
- Gemini's native multi-turn conversation state
- Token counting accuracy
- Function call history tracking

**Fix:** Use the proper `genai.ChatSession` / multi-turn `contents` list with `role: user/model` dicts, not a flattened string.

---

### REF-4 · Embedding API is called one-by-one in a synchronous loop

**File:** `backend/app/memory/vector_store.py` lines 142-147

```python
def __call__(self, input: List[str]) -> List[List[float]]:
    embeddings = []
    for text in input:           # ← serial loop, no batching
        embeddings.append(self._embed_single(text))
    return embeddings
```

The Gemini Embedding API supports batch requests (`genai.embed_content` with a list). For indexing 20 conversation chunks, this is 20 sequential API calls instead of 1-2 batched calls.

**Fix:** Use the batch endpoint:
```python
result = genai.embed_content(
    model=f"models/{self.model_name}",
    content=texts,          # pass the whole list
    task_type="retrieval_document"
)
embeddings = result['embedding']
```

---

### REF-5 · Context is hard-truncated at 2000 characters — a lazy, content-destroying cutoff

**File:** `backend/app/memory/rag_manager.py` lines 161-162

```python
if len(result["full_context"]) > self.max_context_length:
    result["full_context"] = result["full_context"][:self.max_context_length] + "\n[...context truncated...]"
```

2000 characters is ~500 tokens. A Gemini 2.5 Flash context window is ~1 million tokens. This truncation will slice mid-sentence through facts, breaking the very memory system you built. The correct approach is to count tokens and budget by priority, not blindly truncate.

---

### REF-6 · `bare except: pass` silently swallows errors

**File:** `backend/app/memory/rag_manager.py` lines 239-244

```python
except Exception as e:
    logger.error(f"Smart memory processing failed: {e}")
    # Fallback to direct storage
    for fact_text in extracted_facts:
        try:
            await self.core_memory.add_learned_knowledge(fact_text, "normal", "conversation")
            result["facts_extracted"] += 1
        except:          # ← bare except, no logging, no re-raise
            pass
```

Silent exception swallowing is one of the hardest bugs to debug in production. Every `except:` without logging is a black hole.

---

### REF-7 · Root directory has 44 `.md` files — catastrophic repository hygiene

The root of the repo contains 44 markdown files (`PHASE1_COMPLETE.md`, `FIXES_COMPLETE.md`, `GEMINI_LIVE_GA.md`, `CRITICAL_FIXES_COMPLETE.md`, `SESSION_FIX_SUMMARY.md`, etc.). These are internal LLM-assisted dev notes. They communicate to any senior engineer reading this repo that:
1. The project was built iteratively by an AI assistant
2. No thought was given to what a public repository communicates

**Fix:**
```bash
mkdir docs/dev-notes
git mv *.md docs/dev-notes/
# Keep only: README.md, ARCHITECTURE.md, CHANGELOG.md at root
```

---

### REF-8 · `config.py` uses both `os.getenv()` AND `pydantic_settings.BaseSettings` redundantly

**File:** `backend/app/config.py`

```python
class Settings(BaseSettings):
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")  # ← redundant
```

`BaseSettings` already reads from `.env` and environment variables automatically. `os.getenv()` in field defaults is not just redundant — it reads the env at import time (bypassing `.env` file loading order) and defeats the purpose of `pydantic-settings`. 

**Fix:**
```python
class Settings(BaseSettings):
    gemini_api_key: str = ""   # pydantic-settings handles env var injection
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
```

---

### REF-9 · `settings` module-level singleton creates stale configs and test pollution

**Files:** `brain.py`, `vector_store.py`, `model_router.py`, `reranker.py`

```python
settings = get_settings()   # ← evaluated at module import time
```

`get_settings()` is `@lru_cache()`'d. This means:
- Tests cannot override settings without clearing the LRM cache
- If `.env` loads after first import, the cached value has empty strings
- Configuration is impossible to mock properly

**Fix:** Inject `settings` via FastAPI's `Depends()` or always call `get_settings()` inside functions, not at module scope.

---

### REF-10 · Frontend `.env` not in `frontend/.gitignore`

**File:** `frontend/.gitignore` (exists with 277 bytes) — check whether it excludes `.env`. The `frontend/.env` was readable and contains `VITE_API_BASE_URL` — this is harmless now, but if production URLs are ever uncommented, they'll be committed.

**Fix:** Ensure `frontend/.gitignore` contains:
```
.env
.env.local
.env.production
```

---

### REF-11 · `ConversationManager()` is called with `new ConversationManager()` pattern without dependency injection in FastAPI

The routes do not use FastAPI's `Depends()` pattern for dependency injection anywhere. This makes unit testing effectively impossible — you cannot mock `ConversationManager` without monkey-patching.

**Fix:** Create FastAPI dependencies:
```python
async def get_conv_manager(request: Request) -> ConversationManager:
    return request.app.state.conv_manager

@router.get("/conversations")
async def get_conversations(conv_manager: ConversationManager = Depends(get_conv_manager)):
    ...
```

---

## ⚫ [THE CTO VERDICT]

> **Verdict: Promising Architecture, Dangerous Execution. This is a "7 out of 10 for vision, 3 out of 10 for production discipline."**

**What a CTO would say:**

*"Someone clearly has good AI engineering instincts here. The multi-provider routing with fallback chains is thoughtful. RAG + reranking + smart deduplication shows genuine depth. The security approval layer for system operations is a legitimately interesting architecture. But the execution has classic signs of 'vibe-coded with an AI assistant and shipped':*

1. **The .gitignore tells the whole story.** A 44-file markdown soup in the root directory and a properly-written gitignore saved as a `.txt` file means nobody ever stepped back and looked at this as a product.

2. **Live API keys committed to git is a day-1 lesson.** This isn't a "junior mistake" — it's a "no code review ever happened" mistake. In a funded project this would be a P0 incident.

3. **The Gemini message formatting bug is the worst kind of bug** — it *mostly works* but degrades all multi-turn conversation quality silently. A developer who truly understood the API they were building on would have caught this immediately.

4. **Using an LLM to rerank LLM results is architecturally circular.** If Gemini is already being used for generation, adding another Gemini call for reranking before generation adds 600-1200ms of latency and costs money for a task that a 50ms cross-encoder handles better. This is a "I read about reranking but didn't read how to implement it" smell.

5. **`user_id=None # TODO: Get from auth`** in system operation execution means the permission model is theater. A system that can kill processes and write files with no auth is not a personal assistant — it's an RCE endpoint.*

**Bottom line:** Don't push until CRIT-1 through CRIT-5 are resolved. After that, REF-1, REF-3, REF-4 are the highest-ROI refactors before any public announcement."

---

## ACTION CHECKLIST

| # | Item | Severity | Est. Time |
|---|---|---|---|
| 1 | Rotate all 3 API keys in provider dashboards | 🔴 CRITICAL | 10 min |
| 2 | Rename `gitignore.txt` → `.gitignore`, rewrite git history | 🔴 CRITICAL | 30 min |
| 3 | Untrack `backend/.env`, `backend/data/`, `venv/` from git | 🔴 CRITICAL | 15 min |
| 4 | Fix CORS: remove `*`, add explicit origins | 🔴 CRITICAL | 5 min |
| 5 | Lock `/health` endpoint, remove key status exposure | 🔴 CRITICAL | 10 min |
| 6 | Add basic API key auth (FastAPI `Security()`) | 🔴 CRITICAL | 2-4 hrs |
| 7 | Move 44 root `.md` files to `docs/dev-notes/` | 🟠 REFACTOR | 10 min |
| 8 | Fix `ConversationManager` re-instantiation in routes | 🟠 REFACTOR | 1 hr |
| 9 | Fix Gemini multi-turn message formatting (`_convert_to_gemini_messages`) | 🟠 REFACTOR | 2 hrs |
| 10 | Replace LLM-reranker with `cross-encoder/ms-marco-MiniLM` | 🟠 REFACTOR | 3 hrs |
| 11 | Fix redundant `os.getenv()` in `config.py` | 🟠 REFACTOR | 20 min |
| 12 | Batch embedding calls in `GeminiEmbeddingFunction` | 🟠 REFACTOR | 1 hr |
| 13 | Remove `except: pass` blocks, add logging | 🟠 REFACTOR | 30 min |
| 14 | Add FastAPI `Depends()` pattern for dependency injection | 🟠 REFACTOR | 2 hrs |
| 15 | Raise context limit from 2000 chars to token-budgeted limit | 🟠 REFACTOR | 1 hr |
