# Avatario AI - Mobile App

Cross-platform mobile app for AI Receptionist with voice cloning and call handling.

## Features

- **Voice Cloning**: Record your voice and clone it with ElevenLabs
- **Call Handling Toggle**: Enable/disable AI answering calls
- **Business Hours**: Set when AI should answer
- **Do Not Disturb**: Schedule quiet hours
- **Push Notifications**: Get alerts for incoming calls
- **Active Call Screen**: Mute, hold, end calls
- **Inbox**: View call/message history
- **Cross-Platform**: iOS & Android

## Screens

| Screen | Description |
|--------|-------------|
| **Home** | Dashboard with call toggle, active calls, quick stats |
| **Voice** | Record, clone, preview voices |
| **Inbox** | Call and message history |
| **Settings** | Call handling configuration |
| **Active Call** | In-call controls (answer, mute, hold, hangup) |
| **Profile** | User settings, app info |

## Quick Start

```bash
# Install dependencies
cd frontend-app
npm install

# Start development server
npm start

# Run on iOS
npm run ios

# Run on Android
npm run android
```

## Environment Setup

Create `.env` file:

```env
EXPO_PUBLIC_API_URL=https://your-api.com
EXPO_PUBLIC_ELEVENLABS_API_KEY=your_key_here
```

## Building for Production

### iOS

```bash
# Build with EAS
npm run build:ios

# Or manually:
expo prebuild --platform ios
cd ios
fastlane beta
```

### Android

```bash
# Build with EAS
npm run build:android

# Or manually:
expo prebuild --platform android
cd android
./gradlew assembleRelease
```

## App Store Deployment

### iOS App Store

1. Configure app.json:
```json
{
  "expo": {
    "ios": {
      "bundleIdentifier": "com.avatario.app",
      "buildNumber": "1.0.0"
    }
  }
}
```

2. Build and submit:
```bash
eas build --platform ios
eas submit --platform ios
```

### Google Play Store

1. Configure app.json:
```json
{
  "expo": {
    "android": {
      "package": "com.avatario.app",
      "versionCode": 1
    }
  }
}
```

2. Build and submit:
```bash
eas build --platform android
eas submit --platform android
```

## Voice Cloning Setup

### Prerequisites

1. ElevenLabs account: https://elevenlabs.io
2. API key from dashboard
3. Backend configured with `ELEVENLABS_API_KEY`

### Recording Tips

- Record in a quiet environment
- Speak clearly and naturally
- Record at least 30 seconds
- Avoid background noise
- Use high-quality microphone

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/voice/clone` | POST | Upload audio samples to clone |
| `/voice/clones/{user_id}` | GET | List user's cloned voices |
| `/voice/synthesize` | POST | Generate speech with cloned voice |
| `/mobile/settings` | POST | Update call handling settings |
| `/mobile/register-push` | POST | Register for push notifications |

## Call Handling Features

### Enable/Disable

Toggle in Home screen to enable/disable AI call handling:
- **On**: AI answers calls with your cloned voice
- **Off**: Calls go to voicemail or ring through

### Business Hours

Set specific hours when AI should answer:
- Define start/end times
- Choose timezone
- Different schedule for weekends

### Do Not Disturb

Schedule quiet hours:
- Set DND start/end times
- Override in emergencies
- Syncs with phone DND

### Auto-Answer

Configure automatic answering:
- Delay before answering (5-30 seconds)
- Gives you time to pickup first
- Configurable per contact

## Development

### Project Structure

```
frontend-app/
├── src/
│   ├── contexts/
│   │   ├── VoiceContext.tsx    # Voice cloning state
│   │   └── CallContext.tsx     # Call handling state
│   ├── screens/
│   │   ├── HomeScreen.tsx
│   │   ├── VoiceCloneScreen.tsx
│   │   ├── CallSettingsScreen.tsx
│   │   ├── ActiveCallScreen.tsx
│   │   ├── InboxScreen.tsx
│   │   └── ProfileScreen.tsx
│   └── App.tsx
├── app.json
└── package.json
```

### Adding New Features

1. Update contexts for state management
2. Create/modify screens
3. Add API endpoints to backend
4. Test on both iOS and Android

## Troubleshooting

### Push Notifications Not Working

1. Check push token registration
2. Verify Firebase/APNs configuration
3. Test with `expo push:send`

### Voice Cloning Fails

1. Check ElevenLabs API key
2. Ensure audio file format (MP3, WAV)
3. Verify minimum recording length (30s)
4. Check network connection

### Calls Not Coming Through

1. Verify call handling is enabled
2. Check business hours settings
3. Confirm push token is registered
4. Test with backend logs

## License

MIT

## Support

For issues and feature requests, visit:
https://github.com/avatario/mobile-app/issues
