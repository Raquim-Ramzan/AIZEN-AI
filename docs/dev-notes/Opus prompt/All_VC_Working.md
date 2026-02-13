# AIZEN COMPLETE RESTORATION & COMPLETION BLUEPRINT

## YOUR ROLE
You are a Senior AI Systems Architect with expertise in full-stack development, real-time communication systems, and voice AI. You have complete autonomy to restructure, refactor, and complete the AIZEN project.

## PROJECT CONTEXT
AIZEN is an AI assistant in Advanced MVP phase with:
- Multi-Brain routing system (working)
- Core memory systems (working)
- Voice assistant (90% complete but throwing errors)
- Vision module (Phase 2 - NOT to be touched)
- Multiple zombie code sections and incomplete implementations

Reference: PROJECT_HEALTH_ARTIFACT.md for known issues

## MISSION: COMPLETE PROJECT RESTORATION

### PHASE 1: DIAGNOSTIC & CLEANUP (Do First)
**Objective:** Assess entire codebase health and remove all dead code

1. **Full Codebase Scan:**
   - Traverse the entire AIZEN folder recursively
   - Identify ALL errors, warnings, and broken imports
   - Map all incomplete functions, TODO comments, and stub implementations
   - Find all zombie code (defined but unused modules/functions/endpoints)

2. **Graveyard Migration:**
   - Move all truly unused code to a `/graveyard` or `/deprecated` folder
   - This includes:
     * Unused MongoDB client initialization
     * Disconnected Speech API endpoints (if replaced by LiveKit)
     * tools.service.ts (if unused)
     * Any other imports/modules with zero references
   - Document what was moved and why in `GRAVEYARD_LOG.md`

3. **Critical Bug Resolution:**
   - Fix Windows path compatibility (backend/app/main.py Line 43 - use pathlib)
   - Fix metadata propagation (selectedProvider, selectedModel through useChat)
   - Remove ALL simulated/setTimeout-based UI states
   - Resolve all TypeScript `any` types in critical paths (API responses, WebSocket messages)

### PHASE 2: VOICE ASSISTANT COMPLETION (Primary Focus)
**Objective:** Debug and complete the 90% finished voice system

4. **Error Analysis & Resolution:**
   - The user will provide specific voice assistant error logs
   - Analyze the error systematically
   - Identify root cause (dependency? configuration? logic flaw?)
   - Implement fix with proper error handling

5. **LiveKit + Piper/XTTS Integration:**
   - Verify LiveKit server SDK integration (Python backend)
   - Verify LiveKit React hooks integration (frontend)
   - Complete the audio pipeline: STT → LLM → TTS (Piper/XTTS) → Output
   - Connect LiveKit events to holographic sphere states (real-time, not simulated):
     * Audio input → "Listening" state
     * LLM processing → "Processing" state  
     * TTS output → "Speaking" state
     * Audio levels → Sphere pulsation intensity

6. **Voice System Testing:**
   - Test microphone permissions and device detection
   - Test voice activity detection (VAD)
   - Test full conversation loop (speak → response → speak)
   - Add graceful error handling for:
     * Connection drops
     * Audio device failures
     * LiveKit server unavailability
     * TTS generation failures

### PHASE 3: COMPLETION OF INCOMPLETE FEATURES
**Objective:** Finish all started but incomplete implementations

7. **Incomplete Feature Audit:**
   - Scan for all functions returning `NotImplementedError`, `501`, or TODO comments
   - List all UI elements with no backend logic
   - Identify all half-connected services

8. **Feature Completion Priority:**
   - Complete metadata propagation through entire stack
   - Wire up any disconnected event handlers
   - Implement proper WebSocket error recovery
   - Add React error boundaries for crash protection
   - Complete any half-finished API endpoints (except image generation if truly not needed)

### PHASE 4: SELF-AUDIT & OPTIMIZATION
**Objective:** Analyze your own implementations for bugs and improvements

9. **Code Quality Self-Check:**
   - Run through your own code changes like an antivirus scan
   - Check for:
     * Race conditions in async code
     * Memory leaks in WebSocket/LiveKit connections
     * Unhandled promise rejections
     * Missing null/undefined checks
     * TypeScript type safety violations
     * Improper cleanup in React useEffect hooks

10. **Performance Analysis:**
    - Identify bottlenecks in voice pipeline (latency points)
    - Check for unnecessary re-renders in React components
    - Optimize WebSocket message handling
    - Profile TTS generation times (Piper vs XTTS if both implemented)

### PHASE 5: RECOMMENDATIONS & OPTIONAL ENHANCEMENTS

11. **Deliver Final Report with:**
    - All errors found and fixed (with locations)
    - All incomplete features completed (with descriptions)
    - Code quality improvements made
    - Performance optimizations applied
    
12. **Optional Feature Suggestions (Present as Options):**
    - Suggest improvements for voice naturalness (interruption handling, etc.)
    - Suggest UI/UX enhancements for holographic sphere
    - Suggest additional error recovery mechanisms
    - Suggest monitoring/logging improvements
    - Suggest future scalability improvements
    
    **Format:** "OPTIONAL ENHANCEMENTS - implement only if user approves"

## STRICT CONSTRAINTS

### ❌ DO NOT TOUCH:
- **Phase 2 Vision Module** - Leave completely alone, do not modify, refactor, or "improve"
- **LLM Models/Providers** - Do not change model selections or provider configurations (they are latest/correct)
- **Core Multi-Brain routing** - It works, don't break it
- **Memory systems** - They work, don't break them

### ✅ YOU MUST:
- Fix every error you find
- Complete every incomplete feature (except Vision)
- Remove all zombie code to graveyard
- Make holographic sphere respond to REAL events only
- Make voice assistant work flawlessly
- Self-audit your own code for bugs
- Provide optional suggestions separately (not auto-implemented)

## EXECUTION ORDER
1. Scan → Diagnose → Document current state
2. Clean graveyard → Fix critical bugs
3. Debug voice errors (user will provide logs)
4. Complete voice system end-to-end
5. Complete all other incomplete features
6. Self-audit and optimize
7. Deliver report with optional suggestions

## OUTPUT REQUIREMENTS
- Provide clear progress updates for each phase
- Explain what you're fixing and why
- Document all moved/deleted code in GRAVEYARD_LOG.md
- Create COMPLETION_REPORT.md with:
  * What was broken (and how you fixed it)
  * What was incomplete (and how you completed it)
  * Self-audit findings and fixes
  * Optional enhancement suggestions
  
Begin with Phase 1: Full diagnostic scan of the AIZEN folder.