# AI Calling Bot

A fully self-hosted voice AI agent that holds real-time conversations, records
transcripts, extracts structured fields from each call, and triggers follow-up
workflows (including WhatsApp). Runs entirely on free, open-source components.

## Architecture

```
Browser mic (WebRTC)
   │
   ▼
Pipecat pipeline (Python)
   VAD (Silero) → STT (Whisper, local) → LLM (Ollama, local) → TTS (Kokoro/Piper, local)
   │
   ▼ call ends
Transcript store (SQLite → Postgres)
   │
   ▼
Field extraction (LLM → JSON: name, intent, budget, callback time, ...)
   │
   ▼
Workflow engine (rules: hot lead → WhatsApp follow-up, callback → schedule, ...)
   │
   ▼
Dashboard (calls, transcripts, fields, latency, cost per call)
```

## Roadmap

- [ ] 1. Setup: uv, Python 3.12, Ollama + model, project skeleton
- [ ] 2. Talk to the bot in the browser (STT → LLM → TTS loop)
- [ ] 3. Give the bot a job: lead-qualification script + persona
- [ ] 4. Save transcripts for every call
- [ ] 5. Extract structured fields from each transcript
- [ ] 6. Workflow engine (rules + actions)
- [ ] 7. Dashboard with metrics (latency per turn, call duration, outcomes)
- [ ] 8. Optional: real phone calls via Twilio trial credit
- [ ] 9. Polish: architecture diagram, demo video, results

## Stack

| Layer | Tool |
|---|---|
| Voice pipeline | Pipecat |
| Speech-to-text | Whisper (local, MLX on Apple Silicon) |
| LLM | Ollama (Qwen / Llama 8B), Groq free tier as fast fallback |
| Text-to-speech | Kokoro or Piper (local) |
| Storage | SQLite, then Postgres |
| Workflows | Custom rules engine (+ n8n optional) |
