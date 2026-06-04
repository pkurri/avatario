# Avatario Pending Tasks

## Deployment tasks

- [ ] Push the `aiofiles` dependency fix from [backend/requirements.txt](/Users/aak/avatario/backend/requirements.txt) to GitHub so Render can build the current backend successfully.
- [ ] Redeploy the Render backend service `avatario` after the GitHub push.
- [ ] Add `NEXT_PUBLIC_API_URL=https://avatario.onrender.com` to the Vercel project `avatario`.
- [ ] Add `NEXT_PUBLIC_WS_URL=wss://avatario.onrender.com` to the Vercel project `avatario`.
- [ ] Trigger a new Vercel deployment after saving the frontend environment variables.

## Backend environment tasks

- [ ] Add `LLM_INSTANCE_ID` to the Render service environment.
- [ ] Add `AWS_ACCESS_KEY_ID` to the Render service environment.
- [ ] Add `AWS_SECRET_ACCESS_KEY` to the Render service environment.
- [ ] Confirm `AWS_REGION=ap-south-1` remains set on Render.
- [ ] Confirm `BASE_URL=https://avatario.onrender.com` remains set on Render.
- [ ] Confirm `PUBLIC_BASE_URL=https://avatario.onrender.com` remains set on Render.

## Verification tasks

- [ ] Verify backend health at `https://avatario.onrender.com/health`.
- [ ] Verify backend readiness at `https://avatario.onrender.com/readiness`.
- [ ] Verify `POST https://avatario.onrender.com/wake_llm` works after AWS values are added.
- [ ] Verify the frontend uses the Render backend URL after Vercel redeploy.
- [ ] Re-test demo login, WebSocket/chat, and Supabase-backed flows against deployed services.

## External blockers

- [ ] AWS wake-control credentials are still required:
  - `LLM_INSTANCE_ID`
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
- [ ] Vercel project environment variable access is still needed to set:
  - `NEXT_PUBLIC_API_URL`
  - `NEXT_PUBLIC_WS_URL`

## Code-side work already handled

- [x] Added `aiofiles` to [backend/requirements.txt](/Users/aak/avatario/backend/requirements.txt).
- [x] Added Render backend URL environment variables:
  - `AWS_REGION`
  - `BASE_URL`
  - `PUBLIC_BASE_URL`
