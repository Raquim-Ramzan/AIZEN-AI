# Full-Stack Integration & Advanced Features - Implementation Plan

## 🎯 Your Vision

Transform Aizen into a **fully-featured, voice-activated, multi-modal AI assistant** with:

1. ✅ **Multi-Provider Backend Integration** (Already done!)
2. 🔄 **Frontend-Backend Connection** (Connect all buttons)
3. 🎤 **Voice Commands** (Wake word "Aizen", continuous listening)
4. 📸 **Screen Capture** (Backend + Frontend)
5. 🎬 **Vision & Video Analysis** (Multi-modal inputs)
6. 🧠 **Complex Workflows** (e.g., "Aizen, capture screen and summarize this video")

## 📋 Implementation Phases

### Phase 1: Frontend-Backend Integration ⏳
**Connect existing UI to new backend capabilities**

#### Files to Update:
1. `services/chat.service.ts` - Add provider selection
2. `services/system.service.ts` - Add model management endpoints
3. `hooks/useChat.ts` - Support new chat features
4. `components/InputBar.tsx` - Add provider selection UI
5. `components/ChatInterface.tsx` - Show provider/model metadata
6. `components/SettingsPanel.tsx` - Model selection interface

#### New Features:
- Display which provider/model was used
- Let users manually select providers
- Show available models
- Provider status indicators

---

### Phase 2: Screen Capture (Backend + Frontend) ⏳

#### Backend (New):
1. `app/tools/screen_capture.py` - Screen capture tool
2. `app/tools/vision_analyzer.py` - Gemini Vision analysis
3. `app/api/routes.py` - Add `/api/vision/analyze` endpoint

#### Frontend (New/Update):
1. `services/vision.service.ts` - Screen capture & vision API
2. `components/ScreenCaptureButton.tsx` - Enhanced capture UI
3. `hooks/useScreenCapture.ts` - Screen capture logic
4. Connect to InputBar screen capture button (already exists!)

#### Capabilities:
- Capture full screen or window
- Send to Gemini Vision for analysis
- Extract text, objects, UI elements
- Understand what's on screen

---

### Phase 3: Voice Commands (Wake Word + Continuous) ⏳

#### Backend (New):
1. `app/tools/wake_word.py` - Wake word detection ("Aizen")
2. `app/api/routes.py` - Add `/api/voice/stream` WebSocket endpoint
3. Continuous STT streaming

#### Frontend (New/Update):
1. `services/voice.service.ts` - Wake word + continuous voice
2. `hooks/useVoiceCommands.ts` - Voice command detection
3. `components/VoiceVisualizer.tsx` - Update for continuous listening
4. Connect to sphere activation (already has button!)

#### Capabilities:
- Always-on wake word detection ("Aizen")
- Continuous voice input after wake word
- Voice output (TTS)
- Visual feedback on sphere

---

### Phase 4: Multi-Modal Processing ⏳

#### Backend (New):
1. `app/tools/youtube_analyzer.py` - YouTube video processing
2. `app/tools/url_extractor.py` - Extract URLs from screenshots
3. `app/tools/multi_modal_workflow.py` - Complex workflows
4. `app/core/planner.py` - Add multi-modal task types

#### Frontend (New):
1. `components/MultiModalInput.tsx` - Combined voice + image input
2. `hooks/useMultiModal.ts` - Handle complex workflows

#### Example Workflow:
```
User: "Aizen, capture my screen and summarize this video"
  ↓
1. Wake word detected → Start listening
2. Capture screen automatically
3. Vision API extracts YouTube URL from screenshot
4. Backend fetches video transcript
5. Sonar Deep Research analyzes video
6. Return detailed summary with citations
  ↓
Voice output: "I've analyzed the video..."
```

---

## 🚀 Implementation Order

### **Stage 1: Basics (Now)**
1. Connect existing chat to new providers
2. Add model selection UI
3. Show provider metadata in responses

### **Stage 2: Screen Capture**
1. Backend vision endpoint with Gemini
2. Frontend screen capture
3. Display vision analysis results

### **Stage 3: Voice**
1. Wake word detection
2. Continuous voice input
3. Voice output integration

### **Stage 4: Advanced**
1. YouTube video analysis
2. URL extraction from images
3. Complex multi-modal workflows

---

## 🔧 Technical Details

### Backend Additions Needed:

```python
# New Tools
app/tools/
  ├── screen_capture.py      # Capture screen (desktop API)
  ├── vision_analyzer.py     # Gemini Vision API
  ├── youtube_analyzer.py    # YouTube transcript + analysis
  ├── url_extractor.py       # Extract URLs from text/images
  └── multi_modal.py         # Complex workflow orchestration

# New Endpoints
/api/vision/analyze          # POST: Analyze image
/api/vision/extract-url      # POST: Extract URLs from image
/api/youtube/analyze         # POST: Analyze video
/api/voice/wake-word         # WS: Wake word detection
/api/voice/stream            # WS: Continuous voice I/O
```

### Frontend Additions Needed:

```typescript
// New Services
services/
  ├── vision.service.ts      # Screen capture + vision API
  ├── voice.service.ts       # Enhanced voice (+ wake word)
  └── youtube.service.ts     # YouTube integration

// New Hooks
hooks/
  ├── useScreenCapture.ts    # Screen capture logic
  ├── useVoiceCommands.ts    # Wake word + commands
  └── useMultiModal.ts       # Complex workflows

// New Components
components/
  ├── ProviderSelector.tsx   # Select AI provider/model
  ├── VisionAnalysisCard.tsx # Show vision results
  ├── WakeWordIndicator.tsx  # "Listening for Aizen..."
  └── MultiModalInput.tsx    # Combined input types
```

---

## 🎬 Example Use Cases

### Use Case 1: Simple Chat with Provider Selection
```
User: "Write a Python function" [Selects: Gemini 3 Pro]
→ Uses Gemini 3 Pro
→ Shows: "Provider: Gemini | Model: gemini-3-pro-preview
"
```

### Use Case 2: Screen Capture & Analysis
```
User: [Clicks screen capture button]
→ Captures screen
→ Sends to Gemini Vision
→ Response: "I see you're on YouTube watching a tutorial about..."
```

### Use Case 3: Voice-Activated Screenshot
```
User: "Aizen" [Wake word detected]
User: "What's on my screen?"
→ Automatically captures screen
→ Analyzes with Gemini Vision
→ Voice response: "You're viewing a code editor with Python..."
```

### Use Case 4: Complex Multi-Modal
```
User: "Aizen, capture my screen and summarize this video"
→ Wake word → Capture screen
→ Vision extracts YouTube URL
→ Fetch video transcript
→ Sonar Deep Research analyzes
→ Voice output: Detailed summary
```

---

## 📊 Complexity Estimate

| Phase | Backend Work | Frontend Work | Total Time |
|-------|-------------|---------------|------------|
| 1. Connect existing UI | 1 hr | 3 hrs | 4 hrs |
| 2. Screen capture | 3 hrs | 2 hrs | 5 hrs |
| 3. Voice commands | 4 hrs | 3 hrs | 7 hrs |
| 4. Multi-modal | 5 hrs | 3 hrs | 8 hrs |
| **Total** | **13 hrs** | **11 hrs** | **24 hrs** |

---

## 🎯 What Should We Start With?

I recommend this order:

1. **First** → Connect existing frontend to new backend (Quick wins!)
2. **Second** → Add screen capture (Visual AI!)
3. **Third** → Voice commands (Voice AI!)
4. **Fourth** → Complex workflows ("Aizen, analyze this video")

**Ready to begin?** Let's start with Phase 1 - connecting the existing beautiful UI to all the new backend capabilities! 🚀

Which phase would you like me to tackle first, or should I do them all sequentially?
