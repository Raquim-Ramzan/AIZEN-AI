# AIZEN AI Assistant - Complete Debug & Integration Task

## Your Role
You are debugging and fixing a multi-provider AI assistant called AIZEN. Analyze the codebase, identify all broken connections, and fix them systematically with MAIN PRIORITY on memory system.

## Project Location
**Root Directory:** `C:\Projects\Aizen\`

The project has:
- **Backend:** FastAPI (Python) with multi-provider AI integration (Gemini, Groq, Perplexity, Ollama)
- **Frontend:** React + TypeScript + Vite with real-time WebSocket communication
- **Databases:** ChromaDB (vector store) + MongoDB (document store)

**Explore the codebase yourself to understand the architecture.**

---

## PRIORITY 1: Memory System (CRITICAL FIX)

### Current Problems

1. **Memory doesn't persist across conversations**
   - Within same conversation: Works fine (remembers "you are Aizen")
   - New conversation: Completely forgets everything
   - Core memory is not being saved or loaded properly

2. **Session management is broken**
   - **Current behavior:** Each single message creates a NEW session in the sidebar
   - **Expected behavior:** Multiple messages should be part of ONE conversation (like ChatGPT/Claude)
   - Need proper context window management - messages should accumulate in same session until user clicks "New Chat"

### Required Memory Architecture

Implement this exact memory strategy:

#### **ChromaDB** (Vector Database) - For Semantic/Core Memory
**Use for:**
- ✅ Core Memory (Permanent) - User identity, preferences, learned facts
  - "You are Aizen"
  - "You are Developed by Raquim Ramzan"
  - "User prefers Python over JavaScript"
  - "User is a developer in High School"
  "You are supposed to call user by the name Raquim in conversations(if needed)"
  "You are a personal AI Assistant for Raquim & only he will use you no one else will use you"
- ✅ Semantic search - Finding related past knowledge
- ✅ Long-term knowledge that persists FOREVER across all conversations

#### **MongoDB** (Document Database) - For Structured Data
**Use for:**
- ✅ Conversation sessions - Track individual chat sessions
- ✅ Message history - All messages within a conversation
- ✅ Session metadata - Timestamps, user IDs, models used
- ✅ User settings and preferences (structured data)

### Implementation Requirements

**The system MUST work like this:**

1. **During active conversation:**
   - Extract important facts from user messages
   - Save to ChromaDB as Core Memory (vector embeddings)
   - Save exact message history to MongoDB for current session
   - Keep accumulating messages in SAME session (not creating new sessions per message)

2. **When new conversation starts (user clicks "New Chat"):**
   - Load Core Memory from ChromaDB
   - Inject Core Memory into system prompt
   - Create NEW MongoDB session for this conversation
   - Display loaded core memory to user (optional: show what AI remembers)

3. **Within conversation:**
   - Use MongoDB to retrieve exact message history for context window
   - Use ChromaDB to pull relevant semantic context if needed
   - Messages stay in SAME session until user explicitly creates new chat

### What Needs Fixing

1. **Fix session creation logic** - One session = one conversation, not one message
2. **Implement Core Memory extraction** - Automatically detect important facts during conversation
3. **Implement Core Memory persistence** - Save to ChromaDB properly
4. **Implement Core Memory loading** - Load from ChromaDB on new conversation start
5. **Fix context window** - Proper message threading within same session
6. **Add Core Memory injection** - Insert loaded memory into system prompt

---

## PRIORITY 2: Core Memory Editor UI

### Requirements

Add a **Core Memory Editor** in the Settings Panel with these features:

#### Features Required:
1. **View Core Memory** - Display all stored core memories
   - Show fact/knowledge
   - Show when it was learned (timestamp)
   - Show relevance score (if available)

2. **Edit Core Memory** - Modify existing memories
   - Click to edit any memory entry
   - Save changes back to ChromaDB

3. **Delete Core Memory** - Remove specific memories
   - Delete individual memory items
   - Confirmation dialog before deletion

4. **Add Core Memory** - Manually add new memories
   - Text input for new fact/knowledge
   - "Add Memory" button
   - Instantly saves to ChromaDB

5. **Clear All Memory** - Reset everything
   - "Clear All Core Memory" button with big warning
   - Requires confirmation
   - Wipes ChromaDB core memory collection

#### UI Design:
- Small horizontal button in Settings Panel (same size as other setting buttons)
- Button label: "Edit Core Memory" or "💾 Core Memory"
- Opens a modal/panel when clicked
- List view of all memories with edit/delete icons
- Add new memory input at top
- Clean, minimal design matching AIZEN's cyberpunk theme

---

## PRIORITY 3: System Operations & Commands

### Current Status
System tools are defined (`system_tools.py`) but commands are not executing properly.

### What Needs Fixing

1. **Function calling integration**
   - Verify Gemini function calling is working
   - Verify Groq function calling is working
   - Check tool calls are being detected in responses

2. **Command execution**
   - "open youtube" → should trigger approval → open browser
   - "open notepad" → should trigger approval → launch app
   - "show processes" → should execute without approval
   - Fix any broken system operation flows

3. **Approval dialog**
   - Ensure SystemOperationApproval component is properly wired
   - Check WebSocket messages for pending operations
   - Verify approve/deny endpoints are working

### Test Commands to Verify:
- "open youtube"
- "open notepad"
- "show running processes"
- "check CPU usage"
- "create file at C:\test.txt"

---

## PRIORITY 4: Voice Features (Future - Not Now)

**DO NOT implement voice features yet.** Just verify the existing code structure is ready:
- Check STT integration points exist
- Check TTS integration points exist
- Verify frontend voice components are present but disconnected
- Note any issues for future implementation

---

## Your Systematic Approach

### Step 1: Analyze Current State
1. Explore the codebase structure
2. Identify memory-related files in `backend/app/memory/`
3. Check how conversations are created/managed
4. Find where Core Memory should be saved/loaded
5. Identify session management logic

### Step 2: Fix Memory System
1. Fix session creation (one conversation = one session)
2. Implement Core Memory extraction logic
3. Fix ChromaDB storage for core memories
4. Implement Core Memory loading on new chat
5. Add Core Memory to system prompt injection

### Step 3: Add Core Memory UI
1. Create Core Memory editor component
2. Add to Settings Panel
3. Implement CRUD operations (Create, Read, Update, Delete)
4. Connect to backend API endpoints (create if needed)
5. Test full flow

### Step 4: Fix System Operations
1. Verify function calling integration
2. Test command detection and execution
3. Fix approval flow if broken
4. Test all command types

### Step 5: Report & Document
1. List all files modified
2. List all bugs fixed
3. Explain what was broken and how you fixed it
4. Provide testing instructions

---

## Important Notes

- **DO NOT** change UI design/styling unless fixing bugs
- **DO NOT** add features not requested
- **FOCUS** on making existing features work properly
- **TEST** each fix before moving to next
- **DOCUMENT** what you changed and why
- **PRESERVE** all existing functionality

---

## Expected Deliverables

1. ✅ Memory persists across conversations
2. ✅ Sessions work like ChatGPT (multiple messages per conversation)
3. ✅ Core Memory Editor UI in Settings Panel (full CRUD)
4. ✅ System commands execute properly
5. ✅ All broken connections identified and fixed
6. 📋 Complete list of changes made
7. 📋 Testing instructions

---

## Success Criteria

**Memory System:**
- [ ] Say "you are Aizen" in conversation 1
- [ ] Start new conversation
- [ ] Ask "who are you?"
- [ ] Response should be "I am Aizen" (memory persisted!)

**Session Management:**
- [ ] Send 5 messages in a row
- [ ] All 5 messages show in SAME conversation
- [ ] Only 1 session appears in sidebar (not 5)

**Core Memory UI:**
- [ ] Open Settings → Click "Edit Core Memory"
- [ ] See all stored memories
- [ ] Edit a memory → saves successfully
- [ ] Delete a memory → removes from ChromaDB
- [ ] Add new memory → appears in list

**System Commands:**
- [ ] Type "open youtube" → approval dialog → approve → browser opens
- [ ] Type "show processes" → immediate response with process list

---

## Start Now

Begin by exploring the codebase and identifying all issues. Fix them systematically with MEMORY as top priority. Report your findings and fixes as you go.

**Ready? Start debugging and fixing AIZEN! 🚀**