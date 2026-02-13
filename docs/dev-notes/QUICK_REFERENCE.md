# 🚀 AIZEN Quick Reference Card

## Start Commands

```powershell
# Quick Start (both servers)
.\start-aizen.ps1

# Manual Backend
cd backend && python -m app.main

# Manual Frontend  
cd frontend && npm run dev
```

## URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend UI | http://localhost:5173 | Main interface |
| Backend API | http://localhost:8001 | API server |
| API Docs | http://localhost:8001/docs | Swagger documentation |
| Health Check | http://localhost:8001/health | Backend status |

## Key Files

### Configuration
- `frontend/.env` - Frontend API URLs
- `backend/.env` - Backend settings & API keys

### Integration Files
- `frontend/src/pages/Index.tsx` - Main page (integrated)
- `frontend/src/hooks/useChat.ts` - Chat functionality
- `frontend/src/hooks/useSessions.ts` - Conversation management
- `frontend/src/lib/websocket-client.ts` - Real-time streaming

## API Endpoints

### Conversations
```
GET    /api/conversations          # List all
POST   /api/conversations          # Create new
GET    /api/conversations/{id}     # Get one
DELETE /api/conversations/{id}     # Delete
GET    /api/conversations/{id}/messages  # Get messages
```

### Chat
```
POST   /api/chat                   # Non-streaming
WS     /api/ws/{client_id}         # Streaming (WebSocket)
```

### Memory
```
GET    /api/memory/core            # Get core memory
POST   /api/memory/fact            # Store fact
GET    /api/memory/search?query=   # Search memory
```

## WebSocket Message Types

```typescript
// Send message
{
  type: "message",
  conversation_id: "abc123",
  content: "Hello!",
  metadata: {}
}

// Receive token (streaming)
{
  type: "token",
  content: "Hello"
}

// Receive complete
{
  type: "complete",
  full_response: "Hello there!",
  message_id: "msg123"
}

// Error
{
  type: "error",
  error: "Error message"
}
```

## Connection States

| State | Meaning |
|-------|---------|
| `connected` | Backend is reachable |
| `connecting` | Attempting to connect |
| `disconnected` | Connection lost |
| `error` | Connection error |

## Keyboard Shortcuts

| Keys | Action |
|------|--------|
| `Alt + PgUp` | Activate voice input |
| `F11` | Toggle fullscreen |
| `Esc` | Exit fullscreen / Stop listening |

## Common Tasks

### Create New Conversation
1. Click "+ New Chat" in sidebar
2. Automatically creates backend conversation
3. Clears message history

### Send Message
1. Type in input bar
2. Press Enter or click send
3. Message sent via WebSocket
4. Response streams back in real-time

### Switch Conversations
1. Click conversation in sidebar
2. Messages load from backend
3. WebSocket reconnects with new context

### Check Connection
- Look at top-right corner
- Green = Connected
- Yellow = Connecting
- Red = Disconnected/Error

## Debugging

### Backend Logs
Check terminal running `python -m app.main`

### Frontend Console
Press `F12` → Console tab

### WebSocket Traffic
Press `F12` → Network tab → WS tab

### API Calls
Press `F12` → Network tab → Fetch/XHR

## Environment Variables

### Frontend (.env)
```env
VITE_API_BASE_URL=http://localhost:8001
VITE_WS_BASE_URL=ws://localhost:8001
```

### Backend (.env)
```env
PERPLEXITY_API_KEY=your_key
OLLAMA_HOST=http://localhost:11434
MONGO_URL=mongodb://localhost:27017
HOST=0.0.0.0
PORT=8001
CORS_ORIGINS=*
```

## Troubleshooting

### Can't send messages
```powershell
# Check backend is running
curl http://localhost:8001/health

# Check WebSocket
# F12 → Network → WS → Should see connection
```

### Connection shows disconnected
```powershell
# Restart backend
cd backend
python -m app.main

# Check CORS in backend/.env
CORS_ORIGINS=*
```

### Build errors
```powershell
# Clear and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

## Quick Tests

### Test Backend
```powershell
curl http://localhost:8001/health
```

Expected:
```json
{
  "status": "operational",
  "perplexity": "configured",
  "ollama": "configured",
  "chromadb": "initialized",
  "mongodb": "connected"
}
```

### Test Frontend Build
```powershell
cd frontend
npm run build
```

Should complete without errors.

### Test WebSocket
```javascript
// Browser console
const ws = new WebSocket('ws://localhost:8001/api/ws/test123');
ws.onopen = () => console.log('Connected!');
ws.send(JSON.stringify({
  type: 'message',
  content: 'Test',
  conversation_id: null
}));
```

## File Structure

```
Aizen/
├── backend/
│   ├── app/
│   │   ├── api/          # REST & WebSocket routes
│   │   ├── core/         # AI brain
│   │   ├── memory/       # Memory system
│   │   └── main.py       # Entry point
│   └── .env             # Backend config
│
├── frontend/
│   ├── src/
│   │   ├── config/       # API config
│   │   ├── lib/          # API clients
│   │   ├── services/     # API services
│   │   ├── hooks/        # React hooks
│   │   ├── components/   # UI components
│   │   └── pages/        # App pages
│   └── .env             # Frontend config
│
├── start-aizen.ps1      # Quick start script
└── INTEGRATION_SUMMARY.md  # This guide
```

## Support

- **Backend Docs:** `backend/README.md`
- **Integration Guide:** `INTEGRATION_COMPLETE.md`
- **API Docs:** http://localhost:8001/docs (when running)

---

**Last Updated:** November 2025
**Status:** ✅ Fully Integrated & Operational
