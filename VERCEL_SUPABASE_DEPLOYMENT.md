# Vercel + Supabase Deployment

## Recommended Production Shape

- Deploy `frontend-web` to Vercel.
- Deploy `backend` FastAPI separately on a long-running host such as Render, Fly.io, Railway, AWS ECS, EC2, or Cloud Run.
- Use Supabase Postgres for persistence.
- Use LiveKit Cloud for realtime media.

Vercel is a good fit for the Next.js frontend. The current FastAPI backend should not be Vercel-only because it serves WebSockets, voice flows, generated media, provider webhooks, and long-running LLM/EC2 wake operations.

## Vercel Settings

Set the Vercel project root directory to:

```text
frontend-web
```

Build command:

```text
npm run build
```

Output is handled by Next.js/Vercel automatically.

Required Vercel environment variables:

```text
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_WS_URL=wss://api.your-domain.com
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

`NEXT_PUBLIC_API_URL` must point to the deployed FastAPI backend, not localhost.

## Backend Environment

Set these on the backend host:

```text
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
VLLM_API_KEY=...
VLLM_API_BASE=...
VLLM_MODEL=...
LIVEKIT_URL=...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
AWS_REGION=ap-south-1
LLM_INSTANCE_ID=i-your-llm-ec2-instance-id
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

Keep `SUPABASE_SERVICE_ROLE_KEY`, AWS keys, LiveKit secret, Exotel/Twilio keys, and LLM keys server-side only.

## Supabase Setup

Apply:

```text
supabase/migrations/001_avatario_core.sql
```

This creates tables for demo users, sessions, call logs, transcripts, conversations, mobile settings, and push tokens. Row-level security is enabled with service-role-only write access for the backend.

## Backend Deployment Notes

The FastAPI service must allow CORS for the Vercel domain and must support WebSockets over TLS. Use a production command similar to:

```bash
uvicorn main:app --host 0.0.0.0 --port "$PORT"
```

For generated videos/images, prefer Supabase Storage or S3 instead of local filesystem paths.

## Verification

After deploy:

```bash
curl https://api.your-domain.com/health
curl https://api.your-domain.com/llm_status
curl -X POST https://api.your-domain.com/demo/login \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo User","email":"demo@avatario.local"}'
```

Then open the Vercel URL and verify demo login, widget actions, LiveKit token creation, and API-backed media features.
