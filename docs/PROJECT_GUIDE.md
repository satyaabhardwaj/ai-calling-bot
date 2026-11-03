# AI Calling Bot: Project Guide

Everything about this project in one place: what it does, what you need, the
tech stack, how each piece is used, and the learning roadmap. Keep this file
updated as the project grows.

---

## 1. What we are building

A voice AI agent that:

1. **Talks** to a person in real time (in the browser first, real phone calls later)
2. **Records a transcript** of every call
3. **Extracts structured fields** from the call (name, requirement, budget, callback time, ...)
4. **Runs workflows** based on those fields (e.g. hot lead → send a WhatsApp follow-up)
5. **Shows everything on a dashboard** (calls, transcripts, fields, latency)

Rule for this project: **everything is free and runs on your own laptop.**

### The bigger goal: a SaaS platform

The voice bot is the first module of a **multi-channel AI engagement SaaS**:
businesses sign up, configure their AI agent, and the platform talks to their
leads by **voice and WhatsApp**, then runs **workflows** automatically.

```
                         ┌──────────────── SaaS PLATFORM ────────────────┐
                         │                                               │
  Channels               │   Core                     Automation         │   Business UI
 ┌────────────┐          │  ┌──────────────┐         ┌───────────────┐   │  ┌─────────────────┐
 │ Voice bot  │──events──┼─►│ Event bus    │────────►│ Workflow      │   │  │ Dashboard       │
 │ (calls)    │          │  │              │         │ engine        │   │  │ - leads         │
 ├────────────┤          │  │ Contacts /   │         │ trigger →     │   │  │ - calls         │
 │ WhatsApp   │──events──┼─►│ leads, calls,│         │ conditions →  │   │  │ - WhatsApp inbox│
 │ bot        │◄─actions─┼──│ messages,    │◄────────│ actions       │   │  │ - workflow      │
 └────────────┘          │  │ fields (DB)  │         └───────────────┘   │  │   builder       │
                         │  └──────────────┘                             │  │ - bot settings  │
                         │   Organizations (one per business customer)   │  │ - analytics     │
                         └───────────────────────────────────────────────┘  └─────────────────┘
```

#### How workflows work

A workflow = **trigger** → **conditions** → **actions**, stored as data (JSON) so
businesses can create their own from the dashboard.

| Part | Examples |
|---|---|
| **Triggers** (events) | `call.completed`, `fields.extracted`, `whatsapp.message.received`, `lead.created`, `no_reply.24h` |
| **Conditions** | `intent == "interested"`, `budget > 50000`, `callback_time is set`, `language == "hindi"` |
| **Actions** | send WhatsApp template, send WhatsApp Flow (form), schedule a call, update lead status, notify a salesperson, call an external webhook (CRM, n8n) |

Example: *When `fields.extracted` and `intent == "interested"` → send a WhatsApp
brochure → if no reply in 24h → schedule a follow-up AI call.*

#### What "SaaS" adds on top of the bot

| SaaS feature | What it means |
|---|---|
| **Multi-tenancy** | Many businesses on one platform; each only sees its own data (`organization_id` on every row) |
| **Auth** | Sign-up, login, team members, roles |
| **Configuration UI** | Each business sets its own bot persona, call script, fields to extract, workflows |
| **Background jobs** | Calls, messages and delayed workflow steps run in a queue, not in the web request |
| **Swappable providers** | Whisper ↔ Sarvam, Ollama ↔ Groq/Claude, browser ↔ Twilio/Exotel, chosen per business |
| **Deployment** | Hosted online, with monitoring and logs |
| **Billing** (later) | Plans and usage limits (Stripe test mode, free to build) |

**Honest cost note:** building and demoing all of this is free (local + free tiers).
Hosting it for *real customers* would cost money, mainly because running AI models
for many callers needs servers with GPUs, or paid APIs. That's exactly why the
providers are designed to be swappable.

---

## 2. Requirements

### Hardware (your laptop)

| Item | You have | Why it matters |
|---|---|---|
| Chip | Apple M2 | Apple Silicon runs AI models fast using its GPU (via Metal / MLX) |
| RAM | 16 GB | An 8B AI model needs ~5–6 GB RAM, plus Whisper and TTS |
| Free disk | ~36 GB | Model (~5 GB) + Python packages and speech models (~2–3 GB) |
| Microphone + speakers | Built in | To talk to the bot. Headphones recommended to avoid echo |

### Software

| Tool | Status | What it's for |
|---|---|---|
| Homebrew | ✅ installed | Installs developer tools on Mac |
| git | ✅ installed | Saves code history, pushes to GitHub |
| uv | ✅ installed (0.13.7) | Manages Python versions and packages per project |
| Python 3.12 | ⏳ uv downloads it on first `uv run` | The language for the bot |
| Ollama | ⚠️ installed, not running | Runs the AI model locally as an HTTP server |
| Node.js | ✅ installed | Only needed later for the dashboard (optional) |
| A code editor | — | VS Code or Cursor recommended |

### Accounts (all free, needed later)

| Account | When | Why |
|---|---|---|
| GitHub | End of project | Publish the code for your CV |
| Groq or Google AI Studio | Optional, Lesson 2+ | Free-tier cloud LLM if the local model feels slow |
| Meta for Developers | WhatsApp lesson | WhatsApp Cloud API test number (free) |
| Twilio | Optional, last | Free trial credit for a few real phone calls |
| Cloudflare | WhatsApp / phone lessons | Free tunnel so the internet can reach your laptop |

---

## 3. Architecture

```
                         ┌──────────────── ONE TURN OF CONVERSATION ────────────────┐
                         │                                                          │
 Browser mic ──audio──►  VAD  ──►  STT  ──text──►  LLM  ──text──►  TTS  ──audio──►  Browser speaker
 (WebRTC)               Silero    Whisper          Ollama          Kokoro/Piper
                         │                                                          │
                         └──────────────────── Pipecat pipeline ────────────────────┘
                                                    │
                                              call ends
                                                    ▼
                                    Transcript saved (SQLite)
                                                    ▼
                               Field extraction (LLM → JSON fields)
                                                    ▼
                          Workflow engine (rules → actions, e.g. WhatsApp)
                                                    ▼
                                Dashboard (FastAPI + simple web page)
```

### The 4 steps of every turn

| Step | Name | Input → Output | Tool |
|---|---|---|---|
| 1 | **LISTEN** (Voice Activity Detection) | audio → "person stopped talking" | Silero VAD |
| 2 | **HEAR** (Speech-to-Text) | audio → text | Whisper |
| 3 | **THINK** (Large Language Model) | text → reply text | Ollama + Qwen 3 8B |
| 4 | **SPEAK** (Text-to-Speech) | reply text → audio | Kokoro or Piper |

**Key challenge: latency.** Humans reply within ~1 second. Each step adds delay,
so we use **streaming**: start the next step before the previous one finishes.

---

## 4. Tech stack: what, why and how

| Layer | Tool | What it is | Why we chose it | How we use it | Cost |
|---|---|---|---|---|---|
| Package manager | **uv** | Python version + package manager | Fast, keeps each project isolated in `.venv` | `uv add <pkg>`, `uv run <cmd>` | Free |
| Language | **Python 3.12** | Programming language | Best AI/voice libraries; 3.14 too new for some | All bot code | Free |
| LLM server | **Ollama** | Runs AI models locally, exposes an HTTP API | Free, offline, unlimited, simple API | `POST http://localhost:11434/api/chat` | Free |
| LLM model | **Qwen 3 8B** | Open-weight language model | Good quality that fits in 16 GB RAM; handles Hindi + English | Pulled with `ollama pull qwen3:8b` | Free |
| HTTP client | **httpx** | Python library to send HTTP requests | Modern, supports streaming | Calls the Ollama API from Python | Free |
| Voice pipeline | **Pipecat** | Open-source framework that connects VAD → STT → LLM → TTS | Handles streaming, interruptions, audio transport | Builds the real-time bot | Free |
| Turn detection | **Silero VAD** | Detects when someone is speaking | Small, accurate, runs locally | Inside the Pipecat pipeline | Free |
| Speech-to-text | **Whisper** (MLX / faster-whisper) | Converts speech to text | Very accurate, runs on Apple Silicon | Inside the Pipecat pipeline | Free |
| Text-to-speech | **Kokoro** or **Piper** | Converts text to natural speech | Natural voice, runs locally | Inside the Pipecat pipeline | Free |
| Audio transport | **WebRTC** (browser) | Real-time audio between browser and server | No phone number or telecom cost | Talk to the bot from a web page | Free |
| Database | **SQLite** → Postgres later | Stores calls, transcripts, fields | SQLite is built into Python, zero setup | Save each call + extracted fields | Free |
| Web API + dashboard | **FastAPI** | Python web framework | Simple, fast, auto-generated API docs | Serves dashboard + webhooks | Free |
| Workflows | **Custom rules engine** (n8n optional) | "If field X then do action Y" | Writing it yourself shows engineering depth | Runs after field extraction | Free |
| WhatsApp | **Meta WhatsApp Cloud API** | Official WhatsApp API | Free test number, up to 5 recipients | Follow-up messages after calls | Free (test) |
| Tunnel | **Cloudflare Tunnel** / ngrok | Gives your laptop a public URL | Needed for webhooks from Meta/Twilio | Expose FastAPI to the internet | Free |
| Phone calls (optional) | **Twilio** trial | Telephone network API | Real calls for the demo video | Connect a phone number to Pipecat | Free trial credit |

Free tiers and limits change; check each provider's current terms when signing up.

---

## 5. Planned folder structure

```
ai-calling-bot/
├── README.md                 ← short project summary (for GitHub)
├── docs/
│   └── PROJECT_GUIDE.md      ← this file
├── pyproject.toml            ← project ID card + dependency list
├── .python-version           ← "3.12"
├── .gitignore                ← files git must ignore (.venv, .env, ...)
├── .env                      ← secret keys (NEVER commit)
└── src/
    └── ai_calling_bot/
        ├── __init__.py       ← package entry point (main)
        ├── brain.py          ← Lesson 1: talks to the LLM
        ├── ears.py           ← Lesson 2: speech-to-text
        ├── voice.py          ← Lesson 3: text-to-speech
        ├── bot.py            ← Lesson 4: full Pipecat pipeline
        ├── storage.py        ← transcripts + fields in SQLite
        ├── extract.py        ← field extraction
        ├── workflows.py      ← rules engine
        └── dashboard.py      ← FastAPI dashboard
```

---

## 6. Learning roadmap

Built in **phases**. Each phase ends with something working and demo-able.

#### Phase 1: Core voice bot

| # | Lesson | What you build | What you learn | Status |
|---|---|---|---|---|
| 1 | Setup + the brain | uv project, Ollama, `brain.py` text chatbot | Packages, local AI server, HTTP APIs, chat memory | ✅ Done |
| 2 | The ears | Speech-to-text with Whisper (local), inside one swappable `transcribe()` function | Audio basics, sample rate, transcription | 🔄 In progress |
| 3 | The voice | Text-to-speech with Kokoro/Piper | Audio output, voices, streaming audio | ⏳ |
| 4 | Full voice loop | Pipecat pipeline in the browser | VAD, WebRTC, streaming, interruptions | ⏳ |
| 5 | The job | Lead-qualification script + persona | Prompt design, conversation flow | ⏳ |
| 6 | Transcripts | Save every call to a database | Databases, schemas | ⏳ |
| 7 | Field extraction | LLM → JSON fields | Structured output, validation | ⏳ |

#### Phase 2: Workflow engine

| # | Lesson | What you build | What you learn | Status |
|---|---|---|---|---|
| 8 | Events | Every call/message emits events (`call.completed`, ...) | Event-driven design | ⏳ |
| 9 | Workflows as data | Trigger → conditions → actions, stored as JSON | Rules engines, schemas | ⏳ |
| 10 | Actions + delays | Run actions; "wait 24h then..." steps | Background jobs, schedulers | ⏳ |
| 11 | Workflow runs log | See what ran, when, and why it failed | Observability, debugging | ⏳ |

#### Phase 3: WhatsApp channel

| # | Lesson | What you build | What you learn | Status |
|---|---|---|---|---|
| 12 | Send messages | Template messages via WhatsApp Cloud API | API keys, `.env`, external APIs | ⏳ |
| 13 | Receive messages | Webhook + tunnel; incoming messages become events | Webhooks, signatures, tunnels | ⏳ |
| 14 | WhatsApp bot | Same brain replies on WhatsApp | Reusing the core across channels | ⏳ |
| 15 | WhatsApp Flows | Forms inside WhatsApp (booking, lead details) | Structured interactive messages | ⏳ |
| 16 | Knowledge (RAG) | Bot answers from the business's own documents | Embeddings, vector search | ⏳ |

#### Phase 4: SaaS platform

| # | Lesson | What you build | What you learn | Status |
|---|---|---|---|---|
| 17 | Backend API | FastAPI + Postgres | REST APIs, migrations | ⏳ |
| 18 | Auth + multi-tenancy | Sign-up, login, organizations, team members | Security, data isolation | ⏳ |
| 19 | Dashboard | Leads, calls, transcripts, WhatsApp inbox, analytics | Frontend (Next.js), API integration | ⏳ |
| 20 | Workflow builder UI | Businesses create workflows visually | UI for rules, validation | ⏳ |
| 21 | Bot settings UI | Persona, call script, fields to extract, per business | Configurable systems | ⏳ |

#### Phase 5: Production

| # | Lesson | What you build | What you learn | Status |
|---|---|---|---|---|
| 22 | Swappable providers | Sarvam STT, Groq/Claude LLM, chosen per business | Adapter pattern, benchmarking | ⏳ |
| 23 | Real phone calls | Twilio trial / Exotel | Telephony, audio codecs | ⏳ |
| 24 | Integrations | Outgoing webhooks, CRM sync, n8n | Integration design | ⏳ |
| 25 | Deploy | Hosted demo, logs, monitoring | Docker, deployment | ⏳ |
| 26 | Polish | Architecture diagram, demo video, README | Presenting your work | ⏳ |

### Lesson 1 steps

| Step | Task | Status |
|---|---|---|
| 1 | Install uv | ✅ Done |
| 2 | Create the Python project (`uv init`), run it, add `.gitignore` | ✅ Done |
| 3 | Start Ollama, download `qwen3:8b` | ✅ Done |
| 4 | Call the AI API by hand with `curl` | ✅ Done |
| 5 | Write `brain.py` (chat with memory) + first git commit | ✅ Done |

### Lesson 2 steps

| Step | Task | Type | Status |
|---|---|---|---|
| 2.1 | What audio is to a computer (samples, sample rate, channels) | Concept | ✅ Done |
| 2.2 | Install sounddevice, soundfile, numpy, mlx-whisper | Setup | ✅ Done |
| 2.3 | Record your voice to `test.wav` | Local | ✅ Done |
| 2.4 | Transcribe with Whisper | Library (local) | ✅ Done |
| 2.5 | Wrap it in one `transcribe(audio)` function (so engines can be swapped later) | Design | ✅ Done |
| 2.6 | Connect the ears to the brain (voice in, text out) | Integration | ⏳ |

### Later: Sarvam API lesson (after the core bot works)

Add Sarvam (cloud API) as a second speech-to-text engine in the same project:
API key in `.env`, sending audio files over HTTP, status codes and errors,
an `STT_ENGINE=whisper|sarvam` switch, and a Whisper vs Sarvam benchmark
(accuracy + speed on English, Hindi and Hinglish).

---

## 7. Command cheat sheet

| Command | What it does |
|---|---|
| `cd ~/Projects/ai-calling-bot` | Go to the project folder |
| `uv run ai-calling-bot` | Run the project's `main()` function |
| `uv add <package>` | Install a package into this project (updates `pyproject.toml`) |
| `uv remove <package>` | Uninstall a package |
| `uv run python -m ai_calling_bot.brain` | Run one module (file) of the package |
| `ollama serve` | Start the local AI server |
| `ollama pull <model>` | Download a model |
| `ollama list` | Show downloaded models |
| `ollama ps` | Show models currently loaded in memory |
| `git status` / `git add .` / `git commit -m "msg"` | Save your progress |

---

## 8. Glossary

| Term | Meaning |
|---|---|
| **API** | A way for one program to talk to another, usually by sending HTTP requests with JSON |
| **HTTP request / response** | A message sent to a server (request) and its answer (response) |
| **JSON** | Text format for data: `{"key": "value"}` |
| **localhost** | Your own computer, as seen from programs running on it |
| **Port** | A numbered "door" on a computer; Ollama listens on 11434 |
| **Package / library** | Code written by others that your project uses |
| **Virtual environment (`.venv`)** | A private folder of packages for one project |
| **LLM** | Large Language Model: AI that reads and writes text |
| **Parameters (8B)** | The model's learned numbers; 8B = 8 billion |
| **Quantization** | Storing model numbers at lower precision so it fits in less RAM |
| **Token** | A chunk of text (~¾ of a word) that LLMs read and write |
| **Streaming** | Sending output piece by piece as it's produced, instead of all at the end |
| **Latency** | Delay between a request and its response |
| **VAD** | Voice Activity Detection: is someone speaking right now? |
| **STT / ASR** | Speech-to-Text / Automatic Speech Recognition |
| **TTS** | Text-to-Speech |
| **WebRTC** | Browser technology for real-time audio/video |
| **Webhook** | A URL that another service calls when something happens (e.g. new WhatsApp message) |
| **System prompt** | Hidden instructions that set the AI's persona and rules |
