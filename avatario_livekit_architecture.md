# Vakeels AI Lawyer: LiveKit Voice Agent Architecture

This document describes the target architecture for migrating our custom WebSocket-based Voice UI to a robust, enterprise-grade WebRTC Voice Agent using **LiveKit** and **Sarvam AI**.

## 1. Why LiveKit?

Currently, our implementation uses a custom FastAPI WebSocket router to receive raw audio bytes and push them into Sarvam's HTTP API. This introduces potential latency, connection drop risks, and cross-platform (Web vs. Native) audio formatting complexities.

LiveKit provides an open-source WebRTC infrastructure that handles:

- **Ultra-low latency** bi-directional audio streaming.
- **Native client SDKs** for both Next.js (`@livekit/components-react`) and React Native (`@livekit/react-native`).
- **Voice Activity Detection (VAD)** and echo cancellation out of the box.

## 2. Backend Agent Architecture (Python)

Instead of a standard FastAPI app route, the backend becomes a standalone LiveKit Worker process utilizing the `livekit-agents` framework.

### Dependencies

```bash
pip install "livekit-agents[sarvam,openai,silero]" python-dotenv
```

### Agent Configuration (`agent.py`)

We will instantiate a `VoiceAgent` that connects STT, LLM, and TTS seamlessly:

1. **STT (Speech-to-Text):** `sarvam.STT(language="unknown", model="saaras:v3", mode="transcribe")`
   - Automatically detects user language (Hindi, English, etc.) and transcribes it.
   - Alternatively, `mode="translate"` can be used to convert all spoken Indian languages directly into English text for the LLM.
2. **LLM (Language Model):** `openai.LLM(model="gpt-4o")` (or our LangGraph orchestration).
3. **TTS (Text-to-Speech):** `sarvam.TTS(target_language_code="hi-IN", model="bulbul:v3", speaker="meera")`
   - The speaker will be dynamically selected based on the persona (`meera` for Advocate Anya, `amrit`/`shubh` for Senior Counsel Vikram).

## 3. Frontend Architecture

### Next.js Web (`vakeels.ai.lawyer-web`)

- **SDK:** `@livekit/components-react`
- Replace `useVoiceChat.ts` with the official `<LiveKitRoom />` provider.
- Use the `useVoiceAssistant` hook to automatically tie the avatar pulsing CSS to the LiveKit audio track's volume level.

### React Native App (`vakeels.ai.lawyer-app`)

- **SDK:** `@livekit/react-native` and `@livekit/react-native-expo`
- Connect to the identical LiveKit Room URL.
- Use the native `TrackReference` to bind the incoming audio stream to the React Native Reanimated pulsing rings.

## 4. Required Steps

1. **Obtain LiveKit Credentials:** Create a free project on LiveKit Cloud to get `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET`.
2. **Rewrite Backend:** Transition LangGraph logic into the `VoiceAgent` class inside `agent.py`.
3. **Update Frontends:** Refactor the UI components to drop `MediaRecorder`/`expo-av` manual chunking in favor of connecting to the LiveKit Room.
