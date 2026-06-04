# 🚀 SignalWire + Asterisk Setup Guide

**Best Value Setup Implemented** - Save 70% vs Twilio

---

## ✅ What Was Implemented

### 1. Voice Provider Abstraction Layer
- **File:** `backend/engine/voice_provider.py`
- **Features:**
  - Abstract base class for all providers
  - Automatic failover between providers
  - Runtime provider switching
  - Health monitoring

### 2. SignalWire Provider (Primary - 70% Cheaper)
- **File:** `backend/engine/signalwire_integration.py`
- **Cost:** $0.004/min vs Twilio $0.013/min
- **API:** Compatible with Twilio (drop-in replacement)
- **Features:**
  - Inbound/outbound calls
  - WebSocket audio streaming
  - LaML (TwiML equivalent)
  - Call transfer
  - Status tracking

### 3. Asterisk Provider (Self-Hosted Fallback)
- **File:** `backend/engine/asterisk_integration.py`
- **Cost:** $0/min + VPS (~$20-50/month)
- **Features:**
  - ARI (Asterisk REST Interface)
  - SIP/PSTN integration
  - Unlimited scale
  - Zero per-minute costs

### 4. New API Endpoints
- `GET /voice/providers/health` - Check all providers
- `GET /voice/providers/pricing` - Cost comparison
- `POST /voice/calls/outbound` - Make calls
- `GET /voice/calls/{id}/status` - Call status
- `POST /voice/providers/switch` - Switch provider
- `POST /webhooks/signalwire/inbound` - SignalWire webhook
- `WS /voice/stream/signalwire/{id}` - Audio streaming

---

## 🎯 Quick Start

### Step 1: Sign Up for SignalWire
```bash
# 1. Go to https://signalwire.com
# 2. Create account
# 3. Buy phone number ($1/month vs Twilio $1.15/month)
# 4. Get credentials from dashboard
```

### Step 2: Configure Environment
```bash
# Edit .env file with your credentials

PRIMARY_PROVIDER=signalwire
USE_SIGNALWIRE=true

SIGNALWIRE_PROJECT_ID=your_project_id
SIGNALWIRE_TOKEN=your_token
SIGNALWIRE_SPACE_URL=your-space.signalwire.com
SIGNALWIRE_PHONE_NUMBER=+1234567890

BASE_URL=https://yourdomain.com  # For webhooks
```

### Step 3: Install Dependencies
```bash
cd backend
pip install signalwire audioop-lts
```

### Step 4: Configure Webhook
In SignalWire Dashboard:
1. Go to Phone Numbers → Manage
2. Select your number
3. Set Voice Webhook to: `https://yourdomain.com/webhooks/signalwire/inbound`
4. Set Status Callback to: `https://yourdomain.com/webhooks/signalwire/status`

### Step 5: Start Backend
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Step 6: Test
```bash
# Check provider health
curl http://localhost:8000/voice/providers/health

# Make outbound call
curl -X POST http://localhost:8000/voice/calls/outbound \
  -H "Content-Type: application/json" \
  -d '{"to": "+1234567890", "provider": "signalwire"}'

# Check pricing comparison
curl http://localhost:8000/voice/providers/pricing
```

---

## 💰 Cost Comparison

| Provider | Inbound | Outbound | Monthly # | 1000 min/month |
|----------|---------|----------|-----------|----------------|
| **Twilio** | $0.013 | $0.013 | ~$1.15 | **$13.00** |
| **SignalWire** | $0.004 | $0.004 | ~$1.00 | **$4.00** |
| **Asterisk** | $0.000 | $0.005 | ~$25 | **$5.00** |

**Savings with SignalWire:** 70% ($9/month at 1000 minutes)

---

## 🔄 Provider Failover

The system automatically fails over if the primary provider fails:

```
Primary: SignalWire → Failover: Asterisk → Backup: Twilio
```

### Test Failover
```bash
# Switch to Asterisk manually
curl -X POST http://localhost:8000/voice/providers/switch \
  -H "Content-Type: application/json" \
  -d '{"provider": "asterisk"}'

# Check current provider
curl http://localhost:8000/voice/providers/list
```

---

## 🏗️ Asterisk Self-Hosted Setup (Optional)

For zero per-minute costs, set up Asterisk:

### 1. Install Asterisk
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install asterisk asterisk-config

# Enable ARI in /etc/asterisk/ari.conf
[general]
enabled = yes
pretty = yes

[ai_user]
type = user
read_only = no
password = your_secure_password
```

### 2. Configure SIP Trunk
```ini
; /etc/asterisk/pjsip.conf
[signalwire_trunk]
type = endpoint
disallow = all
allow = ulaw
context = from-trunk
outbound_auth = signalwire_auth
aors = signalwire_aor

[signalwire_auth]
type = auth
auth_type = userpass
username = your_sip_username
password = your_sip_password

[signalwire_aor]
type = aor
contact = sip:sip.signalwire.com
```

### 3. Enable in .env
```bash
PRIMARY_PROVIDER=asterisk
USE_ASTERISK=true
ASTERISK_HOST=localhost
ASTERISK_PORT=8088
ASTERISK_USER=ai_user
ASTERISK_PASSWORD=your_secure_password
```

---

## 📱 Mobile App Integration

Your mobile app works with any provider:

```typescript
// frontend-app/src/screens/CallSettingsScreen.tsx
const enableAIAnswering = async () => {
  await fetch(`${API_BASE}/voice/calls/enable-ai`, {
    method: 'POST',
    body: JSON.stringify({
      provider: 'signalwire',  // or 'asterisk', 'twilio'
      auto_answer: true,
      voice_id: selectedClone.id
    })
  });
};
```

---

## 🔧 API Reference

### Switch Provider
```bash
POST /voice/providers/switch
{
  "provider": "signalwire"  // or "asterisk", "twilio"
}
```

### List Providers
```bash
GET /voice/providers/list

Response:
{
  "providers": [
    {
      "name": "signalwire",
      "enabled": true,
      "is_primary": true,
      "fallback_order": 0
    }
  ],
  "primary": "signalwire",
  "fallback_chain": ["signalwire"]
}
```

### Make Outbound Call
```bash
POST /voice/calls/outbound
{
  "to": "+1234567890",
  "from_number": "+1987654321",  // Optional
  "provider": "signalwire",       // Optional (uses primary)
  "custom_data": {"user_id": "123"}
}
```

### Get Call Status
```bash
GET /voice/calls/{call_sid}/status?provider=signalwire
```

### Health Check
```bash
GET /voice/providers/health
```

---

## 📊 Monitoring

Check provider health:
```bash
# All providers
curl http://localhost:8000/voice/providers/health

# Pricing comparison
curl http://localhost:8000/voice/providers/pricing

# List configured providers
curl http://localhost:8000/voice/providers/list
```

---

## 🎉 Summary

✅ **SignalWire integration complete** - 70% cost savings  
✅ **Asterisk fallback ready** - Zero per-minute option  
✅ **Automatic failover** - Never miss a call  
✅ **Runtime switching** - Change providers without downtime  
✅ **Mobile compatible** - Works with existing app

**Next Steps:**
1. Sign up at signalwire.com
2. Add credentials to .env
3. Configure webhooks
4. Deploy and test

**Files Created:**
- `backend/engine/voice_provider.py` (Abstraction layer)
- `backend/engine/signalwire_integration.py` (SignalWire)
- `backend/engine/asterisk_integration.py` (Asterisk)
- Updated `backend/main.py` (New endpoints)
- Updated `.env` (Configuration)
- Updated `requirements.txt` (Dependencies)
