# AIZEN AI Assistant - Critical Fixes PRD

## Project Context
You previously fixed the memory system and core memory UI. Now there are 4 critical issues that need fixing in the AIZEN AI Assistant.

**Project Root:** `C:\Projects\Aizen\`

---

## ISSUE 1: AI Unaware of Current Date/Time (HIGH)

### Problem
The AI doesn't know the current date and time, which causes issues when users ask date-sensitive questions like:
- "What's today's date?"
- "What day is it?"
- "What time is it?"
- "What happened today?" (news queries)

### Solution Required

#### Part A: Inject Current DateTime into System Prompt
Add current date/time information to the system prompt so the AI is always aware of:
- Current date 
- Current time 
- Day of week
- Current year

**Implementation:**
- Update `backend/app/api/websocket.py` and `backend/app/api/routes.py`
- Add datetime context to system prompt alongside core memory
- Format example: "Current date and time: Friday, December 13, 2024, 10:30 AM IST"

#### Part B: Intelligent Routing for Real-Time Queries
Enhance the LLM-based router (`backend/app/core/planner.py`) to detect real-time/current information queries:

**Queries that need real-time data should route to Sonar Pro:**
- Date/time questions: "what's the date?", "what time is it?"
- Current events: "latest news", "what happened today?", "current weather"
- Live data: "stock prices", "sports scores", "trending topics"
- "Today's" or "latest" or "current" keywords in query

**Detection Logic:**
Use the classification LLM to detect these keywords/patterns:
- `today`, `now`, `current`, `latest`, `recent`, `this week`, `this month`
- `date`, `time`, `weather`, `news`, `stock`, `price`
- Any query about events that change frequently

**Routing:**
- If detected â†' Use **Perplexity Sonar Pro** (has access to real-time web data)
- Otherwise â†' Use normal routing (Gemini for coding, chat, etc.)

---

## ISSUE 2: Function Calling Broken (CRITICAL)

### Problem
When user says "open youtube" or "open notepad", the system fails with this error:

```
ERROR:app.core.brain:Gemini streaming error: Could not convert `part.function_call` to text.
ERROR:app.core.brain:AI streaming error with ModelProvider.GEMINI/gemini-2.5-flash: Could not convert `part.function_call` to text.
```

**Current behavior:** Blank reply, nothing opens, error in backend terminal.

### Root Cause
The Gemini streaming method in `backend/app/core/brain.py` is trying to convert function calls to text, which fails. Function calls need special handling in streaming mode.

### Solution Required

#### Fix Gemini Streaming Function Call Handling
**File:** `backend/app/core/brain.py` - Method: `_gemini_generate()` streaming section

**Current issue:** When Gemini wants to call a function during streaming, the code tries to yield it as text, causing the error.

**Fix needed:**
1. Detect if the streaming chunk contains a function call
2. Buffer the function call separately (don't try to convert to text)
3. Yield text chunks normally
4. After streaming completes, yield the buffered function calls as a dict
5. Ensure WebSocket handler (`websocket.py`) processes these function calls

**Reference:** Check how Groq streaming handles function calls - it already works correctly. Apply similar logic to Gemini streaming.

---

## ISSUE 3: Case-Insensitive & Abbreviation-Aware Command Handling

### Problem
System commands are case-sensitive and don't understand abbreviations:
- "open youtube" 
- "Open Youtube" ❌ fails (capitalization)
- "open yt" ❌ fails (abbreviation)
- "launch notepad" ❌ fails (different verb)

### Solution Required

#### Part A: Add Command Normalization Layer
Create a new module: `backend/app/core/command_normalizer.py`

**Purpose:** Use a lightweight LLM (Gemini 2.5 Flash) to convert user's natural language into standardized system commands.

**Flow:**
```
User says: "Open yt" or "launch youtube" or "open YouTube"
    ↓
Command Normalizer (Gemini 2.5 Flash):
    - Detects intent: "user wants to open YouTube"
    - Returns normalized command: "open_url" with parameter "https://youtube.com"
    ↓
System Executor: Executes the normalized command
```

**Implementation:**
1. Create `CommandNormalizer` class with method `normalize_command(user_input: str)`
2. Use Gemini 2.5 Flash (fast, cheap, good for simple tasks)
3. Provide it with a list of available system commands and their variations
4. Return structured output: `{"tool": "open_url", "parameters": {"url": "https://youtube.com"}}`

**Examples to handle:**
- "open yt" → `open_url("https://youtube.com")`
- "launch chrome" → `start_process("chrome.exe")`
- "show me CPU usage" → `get_cpu_info()`
- "open google" → `open_url("https://google.com")`
- "start notepad" → `start_process("notepad.exe")`

#### Part B: Integrate into System Executor
**File:** `backend/app/core/system_executor.py`

Before executing any command:
1. Pass user's original message through `CommandNormalizer`
2. Get normalized command structure
3. Execute the normalized command
4. This ensures case-insensitivity and abbreviation support

---

## ISSUE 4: NEW SESSION Button Not Working + Conversation Naming

### Problem 1: New Session Not Creating
When clicking "NEW SESSION" button:
- Toast notification appears ✅
- But no new session is actually created ❌
- Messages continue in old conversation

### Problem 2: Poor Conversation Naming
Current conversation names are generic:
- "Conversation 1", "Conversation 2" (boring)
- Or just greeting text if conversation starts with "Hi"

**Desired:** Like ChatGPT/Claude - use LLM to generate meaningful conversation titles based on first message or conversation context.

### Solution Required

#### Part A: Fix NEW SESSION Button
**Files:** `frontend/src/pages/Index.tsx` and related hooks

**Current issue:** Button triggers frontend toast but doesn't properly communicate with backend to create new session.

**Fix needed:**
1. When "NEW SESSION" clicked:
   - Clear frontend message state
   - Send WebSocket message with type `new_session` to backend
   - Backend creates new MongoDB session
   - Backend returns new session ID
   - Frontend updates active session ID
   - Sidebar shows new conversation

2. Verify the flow:
   ```
   User clicks "NEW SESSION"
       ↓
   Frontend: Clear messages, send new_session WS message
       ↓
   Backend: Create new MongoDB session, return session_id
       ↓
   Frontend: Update UI with new session
       ↓
   Next message goes to NEW session (not old one)
   ```

#### Part B: Implement Smart Conversation Naming
**File:** Create new `backend/app/core/conversation_namer.py`

**Purpose:** Use lightweight LLM (Gemini 2.5 Flash) to generate meaningful conversation titles.

**Implementation:**
1. Create `ConversationNamer` class with method `generate_title(first_message: str)`
2. Use Gemini 2.5 Flash with prompt:
   ```
   Generate a short, descriptive title (max 5 words) for a conversation that starts with: "{first_message}"
   
   Examples:
   - "Write a Python sorting function" → "Python Sorting Function"
   - "Help me plan a trip to Paris" → "Paris Trip Planning"
   - "What's the weather today?" → "Weather Information"
   - "Open YouTube" → "YouTube Access"
   
   Return ONLY the title, nothing else.
   ```

3. Generate title after first user message is sent
4. Update MongoDB session document with generated title
5. Frontend displays the generated title in sidebar

**Integration Points:**
- In `backend/app/api/websocket.py`: After first message in a new session, call `ConversationNamer.generate_title()`
- Update session in MongoDB with the generated title
- Emit WebSocket event to frontend with new title
- Frontend updates sidebar conversation name

**Fallback:** If title generation fails, use "Conversation {date}" format.

---

## Implementation Priority

1. **HIGHEST:** Fix function calling (Issue 2) - Critical for system commands
2. **HIGH:** Fix NEW SESSION button (Issue 4A) - Core UX issue
3. **HIGH:** Add date/time awareness (Issue 1A) - Basic functionality
4. **MEDIUM:** Implement conversation naming (Issue 4B) - Better UX
5. **MEDIUM:** Add command normalization (Issue 3) - Better command handling
6. **MEDIUM:** Real-time query routing (Issue 1B) - Enhanced routing

---

## Success Criteria

### Issue 1 - Date/Time Awareness:
- [ ] Ask "what's today's date?" → AI responds with correct date
- [ ] Ask "what time is it?" → AI responds with current time
- [ ] Ask "latest news about AI" → Routes to Sonar Pro, returns current news

### Issue 2 - Function Calling:
- [ ] Say "open youtube" → Approval dialog appears → YouTube opens
- [ ] Say "open notepad" → Approval dialog appears → Notepad launches
- [ ] No errors in backend terminal about function_call conversion

### Issue 3 - Command Normalization:
- [ ] Say "Open YouTube" (capital O) → Still works
- [ ] Say "open yt" → Opens YouTube (recognizes abbreviation)
- [ ] Say "launch chrome" → Opens Chrome (different verb)
- [ ] Say "show cpu" → Shows CPU info (abbreviated command)

### Issue 4 - Session & Naming:
- [ ] Click "NEW SESSION" → New conversation actually created
- [ ] New conversation appears in sidebar
- [ ] Next message goes to new conversation (not old one)
- [ ] First message: "Help me code" → Conversation titled "Coding Assistance"
- [ ] First message: "What's the weather?" → Conversation titled "Weather Information"

---

## Files That Need Modification

### New Files to Create:
1. `backend/app/core/command_normalizer.py` - Command normalization
2. `backend/app/core/conversation_namer.py` - Conversation title generation

### Files to Modify:
1. `backend/app/core/brain.py` - Fix Gemini streaming function calls
2. `backend/app/core/planner.py` - Add real-time query detection
3. `backend/app/core/system_executor.py` - Integrate command normalizer
4. `backend/app/api/websocket.py` - Add datetime to system prompt, integrate conversation naming
5. `backend/app/api/routes.py` - Add datetime to system prompt (non-streaming endpoint)
6. `frontend/src/pages/Index.tsx` - Fix NEW SESSION button
7. `frontend/src/hooks/useChat.ts` - Handle new_session properly
8. `frontend/src/hooks/useSessions.ts` - Update session list when title changes

---

## Testing Instructions

After implementation, test each fix:

### Test 1: Date/Time
```
1. Ask: "What's today's date?"
2. Expected: Correct date (e.g., "December 13, 2024")

3. Ask: "What's the latest AI news?"
4. Expected: Uses Sonar Pro, returns current news
```

### Test 2: Function Calling
```
1. Say: "open youtube"
2. Expected: Approval dialog → Approve → YouTube opens
3. Check backend logs: No "function_call" errors

4. Say: "open notepad"
5. Expected: Approval dialog → Approve → Notepad launches
```

### Test 3: Command Variations
```
1. Say: "Open YouTube" (capital letters)
2. Expected: Still works

3. Say: "open yt"
4. Expected: Opens YouTube

5. Say: "launch chrome"
6. Expected: Opens Chrome

7. Say: "show cpu usage"
8. Expected: Shows CPU info
```

### Test 4: New Session & Naming
```
1. Start conversation: "Help me write Python code"
2. Check sidebar: Should show title like "Python Coding Help"

3. Click "NEW SESSION"
4. Check sidebar: New conversation appears
5. Send message in new conversation
6. Expected: Goes to NEW conversation, not old one

7. Start new conversation: "What's the weather?"
8. Check sidebar: Should show title like "Weather Information"
```

---

## Start Implementation

Begin by fixing the issues in priority order. Focus on:
1. Function calling fix (most critical)
2. NEW SESSION button fix (core UX)
3. Then implement enhancements (naming, normalization, date awareness)

Report your progress as you complete each issue. Good luck! 🚀