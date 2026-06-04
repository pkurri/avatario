# Exotel Configuration Guide

## Your ngrok URL
**Public URL:** `https://wad-mutilator-hybrid.ngrok-free.dev`

## Step 1: Login to Exotel Dashboard
1. Go to: https://my.exotel.com
2. Login with your credentials

## Step 2: Configure Webhooks

### Option A: App Bazaar (Recommended)

1. Click **"App Bazaar"** in left sidebar
2. Find your app or click **"Create New App"**
3. Fill in:
   - **App Name:** AI Receptionist
   - **Voice URL:** `https://wad-mutilator-hybrid.ngrok-free.dev/webhooks/exotel/inbound`
   - **Status Callback:** `https://wad-mutilator-hybrid.ngrok-free.dev/webhooks/exotel/status`
   - **HTTP Method:** POST
4. Click **"Save"**

### Option B: Phone Number Settings

1. Go to **"Phone Numbers"** → **"Manage"**
2. Click on your trial number: `+91-9513886363`
3. Under **"Voice & Fax"**:
   - **Webhook URL:** `https://wad-mutilator-hybrid.ngrok-free.dev/webhooks/exotel/inbound`
   - **HTTP Method:** POST
4. Under **"Status Callback"**:
   - **URL:** `https://wad-mutilator-hybrid.ngrok-free.dev/webhooks/exotel/status`
5. Click **"Save"**

## Step 3: Test the Configuration

### Test from Dashboard:
1. Go to **"API"** → **"API Explorer"** or **"Test"**
2. Click **"Make Test Call"**
3. Enter your phone number: `+91XXXXXXXXXX`
4. Click **"Call"**

### Or call your Exotel number:
```
Dial: +91-9513886363
```

Your AI should answer!

## Step 4: Verify in Terminal

Watch for incoming webhooks:
```bash
# Check backend logs
tail -f /tmp/backend_ngrok.log
```

You should see:
```
POST /webhooks/exotel/inbound - 200 OK
POST /webhooks/exotel/status - 200 OK
```

## Quick Reference

| What | Value |
|------|-------|
| **Exotel Trial Number** | +91-9513886363 |
| **Exotel Toggle Number** | +91-9513885656 |
| **ngrok URL** | https://wad-mutilator-hybrid.ngrok-free.dev |
| **Inbound Webhook** | /webhooks/exotel/inbound |
| **Status Webhook** | /webhooks/exotel/status |

## Troubleshooting

### If calls don't connect:
1. Check ngrok is running: `ps aux | grep ngrok`
2. Check backend is running: `curl http://localhost:8000/health`
3. Check BASE_URL in .env: `grep BASE_URL /Users/aak/avatario/.env`
4. Re-save Exotel configuration

### If ngrok URL changes:
```bash
# Get new URL
curl http://localhost:4040/api/tunnels

# Update .env and restart backend
```

## Ready to Test!

Once configured, call **+91-9513886363** and your AI will answer! 🎉
