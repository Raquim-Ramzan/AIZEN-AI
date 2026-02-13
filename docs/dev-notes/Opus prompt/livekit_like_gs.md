# Using LiveKit Like Gaurav Sachdeva (For AIZEN + Charon)

This guide shows how to set up a **LiveKit voice AI agent** (like Gaurav Sachdeva’s Jarvis-style setup) using **Python + Gemini + Charon** for your AIZEN assistant.[web:46][web:175][web:183]

---

## 1. High-Level Architecture

Your stack will look like this:

- **Client (browser / LiveKit Playground)**  
  - Sends your mic audio to LiveKit over WebRTC and plays back TTS.[web:183][web:72]

- **LiveKit Cloud**  
  - Handles rooms, audio routing, and communication between client and your agent worker.[web:183]

- **Python Agent Worker** (running on your PC or server)  
  - Uses **LiveKit Agents SDK** to connect to LiveKit.  
  - Pipeline inside the worker:
    - VAD (voice activity detection)  
    - STT (speech-to-text)  
    - LLM (Gemini)  
    - TTS (Gemini TTS with **Charon** voice)  
    - Optional tools (system control, APIs).[web:46][web:175]

This is essentially what Gaurav wires up: LiveKit + Agents + Gemini + tools + a nice frontend.[web:174][web:45]

---

## 2. Prerequisites

1. **LiveKit Cloud account & project**  
   - Create a project on LiveKit Cloud.  
   - Note:
     - `LIVEKIT_URL`  
     - `LIVEKIT_API_KEY`  
     - `LIVEKIT_API_SECRET`.[web:183]

2. **Gemini API key**  
   - From Google AI Studio (you already use this for TTS previews).[web:142][web:91]

3. **Python environment**  
   - Recommended: Python 3.10+ with a virtual environment.

---

## 3. Clone the Starter (Like Gaurav)

LiveKit provides a Python starter very similar to what Gaurav uses in his tutorials.

