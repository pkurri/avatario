# Avatario — AI Human Assistant Platform

Industry-agnostic AI human assistant platform. Deploy AI personas across **legal, healthcare, finance, education** and any domain — voice-first, multilingual, with talking avatar support.

---

## Project Structure

```
avatario/
├── backend/              # FastAPI + AI engine (Python)
│   ├── engine/           # Core AI engines
│   │   ├── lipsync_failover.py     # Tier 1→2→3 lip-sync failover chain
│   │   ├── lipsync_server.py       # Tier 1: local Mac CPU/MPS server
│   │   ├── talking_person_pipeline.py  # AI person generation
│   │   ├── face_clone.py           # Face cloning engine
│   │   ├── personas.py             # Persona loader
│   │   ├── graph.py                # LangGraph cognitive engine
│   │   └── audio.py                # Sarvam STT/TTS
│   ├── config/
│   │   └── personas.yaml           # Industry persona configuration
│   ├── main.py                     # FastAPI entrypoint
│   ├── agent.py                    # LiveKit voice agent
│   ├── requirements.txt
│   └── .env.example
│
├── frontend-web/         # Next.js 16 web app
│   └── src/
│       ├── app/          # Next.js App Router pages
│       ├── components/   # React components (avatar, voice, face clone)
│       └── hooks/        # useAudioLevel, useAnyaVoice
│
├── frontend-app/         # React Native / Expo mobile app
│   └── src/screens/
│       └── VoiceScreen.tsx
│
├── avatario_platform_strategy.md   # Architecture & roadmap
└── avatario_livekit_architecture.md
```

---

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in your API keys in .env

uvicorn main:app --reload --port 8001
```

### Lip-Sync Server (Tier 1 — local)

```bash
cd backend
source .venv/bin/activate
python engine/lipsync_server.py
```

### Web Frontend

```bash
cd frontend-web
npm install
npm run dev
```

### Mobile App

```bash
cd frontend-app
npm install
npx expo start
```

---

## Configuration

All industry/persona config lives in `backend/config/personas.yaml`.

**To switch verticals**, change the `vertical:` field and add persona blocks. No code changes required.

Supported verticals (built-in examples): `legal`, `healthcare`, `finance`, `education`

---

## Lip-Sync Failover Chain

| Tier | Provider | Cost | Requirement |
|------|----------|------|-------------|
| **Tier 1** | Local Mac CPU/MPS | Free | Runs locally |
| **Tier 2** | NVIDIA Audio2Face | Free credits | `NVIDIA_API_KEY` |
| **Tier 3** | D-ID | Paid | `DID_API_KEY` |

Health status: `GET http://localhost:8001/health`

---

## API Keys Required

| Service | Purpose | Where to get |
|---------|---------|-------------|
| `SARVAM_API_KEY` | STT + TTS (multilingual) | [sarvam.ai](https://sarvam.ai) |
| `LIVEKIT_*` | WebRTC transport | [livekit.io](https://livekit.io) |
| `NVIDIA_API_KEY` | Lip-sync Tier 2 | [build.nvidia.com](https://build.nvidia.com) |
| `DID_API_KEY` | Lip-sync Tier 3 (optional) | [d-id.com](https://d-id.com) |

---

## Tech Stack

- **Backend:** FastAPI, LangGraph, LangChain, httpx
- **Voice:** Sarvam AI (STT/TTS), LiveKit (WebRTC)
- **Visual:** FLUX image generation, Wav2Lip / NVIDIA Audio2Face / D-ID
- **Web:** Next.js 16, TailwindCSS v4, Framer Motion, LiveKit React SDK
- **Mobile:** React Native / Expo, LiveKit React Native SDK
