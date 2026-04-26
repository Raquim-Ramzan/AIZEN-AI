# 🚀 Multi-Provider AI Assistant - Quick Reference

## 📋 Implementation Checklist

- ✅ Gemini API integration
- ✅ Groq API integration  
- ✅ Intelligent model routing
- ✅ Fallback chains
- ✅ Enhanced speech (STT/TTS)
- ✅ Better embeddings
- ✅ New API endpoints
- ✅ Backward compatibility
- ⏳ **Add API keys** (YOUR TODO)

## 🔑 Add Your API Keys

Edit `backend/.env` and add:

```bash
# Lines 10-11 in .env
GEMINI_API_KEY="YOUR_GEMINI_KEY_HERE"

# Lines 14-15 in .env  
GROQ_API_KEY="YOUR_GROQ_KEY_HERE"
```

## 🎯 Intelligent Model Selection

The system automatically chooses the best model:

| Your Message | Detected Task | Selected Model |
|--------------|---------------|----------------|
| "Write a function to..." | Coding | Gemini 3 Pro Preview |
| "Explain the difference..." | Reasoning | Gemini 3 Pro Preview |
| "Hello, how are you?" | Chat | Gemini 2.5 Flash |
| "Search for latest news" | Search | Perplexity Sonar Pro |
| "Research blockchain tech" | Deep Research | Sonar Deep Research |

## 🔧 New API Capabilities

### 1. Check Provider Status
```bash
curl http://localhost:8001/api/settings
```

### 2. List Available Models
```bash
curl http://localhost:8001/api/models/available
```

### 3. Test Model Selection
```bash
curl -X POST http://localhost:8001/api/models/select \
  -H "Content-Type: application/json" \
  -d '{"task_type": "coding"}'
```

### 4. Chat with Automatic Routing
```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write a Python function to calculate factorial"
  }'
```
Response will include `"provider": "gemini"` and `"model": "gemini-3-pro-preview"`

### 5. Manual Provider Selection
```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me a joke",
    "model_provider": "groq",
    "model_name": "groq/compound"
  }'
```

### 6. Speech with Groq
```bash
# Transcription with Groq Whisper
curl -X POST http://localhost:8001/api/speech/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "base64_audio_data",
    "provider": "groq"
  }'

# Synthesis with Groq PlayAI
curl -X POST http://localhost:8001/api/speech/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world",
    "provider": "groq"
  }'
```

## 🔄 Fallback Behavior

If a provider fails, the system automatically tries:

**For Coding/Reasoning:**
1. Gemini 3 Pro ❌
2. → Groq Llama 3.3 70B 🔄
3. → Ollama (local) ✅

**For Chat:**
1. Gemini 2.5 Flash ❌
2. → Groq Compound 🔄
3. → Ollama (local) ✅

**For Search:**
1. Perplexity Sonar Pro ❌
2. → Gemini 2.5 Flash 🔄
3. → Ollama (local) ✅

**For Speech:**
- STT: Groq Whisper ❌ → Local Faster-Whisper ✅
- TTS: Groq PlayAI ❌ → Local Piper ✅

## 📊 Response Format Changes

Chat responses now include provider metadata:

```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "content": "The response text...",
  "provider": "gemini",
  "model": "gemini-3-pro-preview"
}
```

WebSocket streams include:

```json
{
  "type": "stream_start",
  "provider": "gemini",
  "model": "gemini-2.5-flash"
}
```

## 🧪 Testing Commands

### Test Everything Works Without API Keys
```powershell
cd C:\Projects\Aizen\backend
python test_integration.py
```

### Start the Backend
```powershell
python -m app.main
```

### Quick Test Coding Task
```powershell
curl -X POST http://localhost:8001/api/chat `
  -H "Content-Type: application/json" `
  -d '{\"message\": \"Write a function to reverse a string\"}'
```

Should use Gemini 3 Pro if key is configured!

### Quick Test Chat Task
```powershell
curl -X POST http://localhost:8001/api/chat `
  -H "Content-Type: application-json" `
  -d '{\"message\": \"Hello!\"}'
```

Should use Gemini 2.5 Flash if key is configured!

## 🎨 Model Customization

Want to change which model is used for each task? Edit `.env`:

```bash
# Change the coding model
MODEL_CODING="gemini-2.5-pro"

# Change the chat model  
MODEL_CHAT="gemini-3-flash-exp"

# Change the search model
MODEL_SEARCH="sonar-reasoning-pro"
```

## 🛡️ Backward Compatibility

Old code still works:

```python
# This still forces Ollama
response = await chat({
    "message": "Hello",
    "use_ollama": True
})
```

## 📝 Model Name Reference

### Gemini Models
- `gemini-3-pro-preview` - Best for coding
- `gemini-2.5-flash` - Fast general chat
- `gemini-2.5-pro` - Advanced reasoning
- `gemini-3-flash-exp` - Experimental fast model

### Groq Models
- `groq/compound` - Ultra-fast streaming
- `groq/compound-mini` - Smaller, faster
- `llama-3.3-70b-versatile` - Large reasoning model
- `whisper-large-v3-turbo` - Speech-to-text
- `playai-tts` - Text-to-speech

### Perplexity Models
- `sonar-pro` - Advanced search
- `sonar` - Standard search
- `sonar-reasoning` - Search + reasoning
- `sonar-reasoning-pro` - Advanced reasoning + search
- `sonar-deep-research` - Comprehensive research

## 🚀 Next Steps

1. **Add API Keys** (see top of this file)
2. **Run Test**: `python test_integration.py`
3. **Start Backend**: `python -m app.main`
4. **Try Endpoints**: Use curl commands above
5. **Update Frontend**: Use new provider fields
6. **Monitor**: Check logs to see model selection

## 💡 Pro Tips

- **No API keys?** System works with Perplexity + Ollama
- **Want speed?** Groq is optimized for low latency
- **Want quality?** Gemini 3 Pro for complex tasks
- **Want search?** Perplexity has built-in web search
- **Want offline?** Ollama always available

Enjoy your supercharged AI assistant! 🎉
