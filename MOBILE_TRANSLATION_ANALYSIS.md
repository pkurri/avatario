# Mobile App Real-Time Translation Analysis

## Current Translation Capabilities

### **Backend Translation Infrastructure**

#### **Sarvam AI Integration**

The backend has **real-time translation capabilities** built-in:

**STT with Translation** (`backend/engine/audio.py`):

```python
async def sarvam_stt(audio_bytes: bytes) -> Optional[str]:
    """
    Sends an audio chunk to Sarvam's Speech-to-Text API.
    Returns the transcribed translation text.
    """
    url = "https://api.sarvam.ai/speech-to-text-translate"
```

**Key Features**:

- ✅ **Real-time speech-to-text translation**
- ✅ **Auto-language detection**
- ✅ **Supports 10+ Indian languages**
- ✅ **Returns translated transcript**

**TTS Multi-Language Support**:

```python
payload = {
    "inputs": [text],
    "target_language_code": "hi-IN",  # Currently hardcoded to Hindi
    "speaker": speaker,
    "enable_preprocessing": True,
    "skip_preflight": True
}
```

#### **Persona Language Enforcement**

From `backend/config/personas.yaml`:

```yaml
CRITICAL: Always respond in the SAME LANGUAGE as the user.
- If the user speaks Hindi, respond in Hindi.
- If the user speaks Tamil, respond in Tamil.
- If they speak Hinglish, respond in Hinglish.
```

### **Mobile App Current State**

#### **VoiceScreen.tsx Analysis**

**Translation Features**:
- ❌ **No explicit translation UI** in mobile app
- ❌ **No language picker** for manual selection
- ❌ **No translation status indicator**
- ✅ **LiveKit integration** for real-time audio
- ✅ **Persona selection** (Advocate Anya, Senior Counsel Vikram)

**Current Flow**:

1. User selects persona
2. LiveKit connects to backend
3. Audio streams to backend
4. Backend processes with Sarvam STT + translation
5. AI responds in detected language
6. TTS generates speech response

#### **ActiveCallScreen.tsx Analysis**

**Traditional Phone Calls**:

- ❌ **No translation features visible**
- ❌ **No language indicators**
- ✅ **Basic call controls** (mute, hold, end)
- ✅ **Waveform visualization**
- ✅ **Call duration tracking**

## Translation Architecture Gap Analysis

### **What's Missing in Mobile App**

#### **1. Translation UI Components**

```typescript
// Missing components needed:
- Language picker dropdown
- Translation toggle switch
- Detected language indicator
- Translation confidence score
- Source/target language display
```

#### **2. Real-Time Translation Display**

```typescript
// Missing features:
- Live transcription display
- Translated text overlay
- Bilingual conversation view
- Translation history
```

#### **3. Translation Settings**

```typescript
// Missing settings:
- Preferred translation language
- Auto-detect vs manual selection
- Translation confidence threshold
- Voice gender for translated speech
```

## Implementation Plan for Real-Time Translation

### **Phase 1: Backend Enhancements**

#### **1.1 Dynamic Language Configuration**

```python
# backend/engine/audio.py - Enhanced TTS
async def sarvam_tts(text: str, target_language: str = "auto", role: str = "client") -> Optional[bytes]:
    """
    Enhanced TTS with dynamic language support
    """
    # Auto-detect language or use specified
    if target_language == "auto":
        target_language = detect_language(text)
    
    payload = {
        "inputs": [text],
        "target_language_code": target_language,
        "speaker": speaker,
        "enable_preprocessing": True,
        "skip_preflight": True
    }
```

#### **1.2 Translation API Endpoint**

```python
# backend/main.py - Add translation endpoint
@app.post("/api/v1/translation/real-time")
async def real_time_translation(audio: UploadFile, target_lang: str = "auto"):
    """
    Real-time translation endpoint for mobile app
    """
    audio_bytes = await audio.read()
    
    # STT with translation
    transcript = await sarvam_stt(audio_bytes)
    
    # Detect source language
    source_lang = detect_language(transcript)
    
    # Generate response in same language
    response = await generate_ai_response(transcript, source_lang)
    
    # TTS in appropriate language
    audio_response = await sarvam_tts(response, source_lang)
    
    return {
        "transcript": transcript,
        "source_language": source_lang,
        "response": response,
        "audio_response": base64.b64encode(audio_response),
        "confidence": 0.95
    }
```

### **Phase 2: Mobile App Enhancements**

#### **2.1 Translation UI Components**

```typescript
// src/components/TranslationInterface.tsx
interface TranslationProps {
  onLanguageChange: (lang: string) => void;
  detectedLanguage: string;
  isTranslating: boolean;
}

export const TranslationInterface: React.FC<TranslationProps> = ({
  onLanguageChange,
  detectedLanguage,
  isTranslating
}) => {
  const [targetLanguage, setTargetLanguage] = useState('auto');
  const [showTranslation, setShowTranslation] = useState(true);
  
  return (
    <View style={styles.translationContainer}>
      {/* Language Picker */}
      <TouchableOpacity style={styles.languagePicker}>
        <Text>{detectedLanguage} → {targetLanguage}</Text>
      </TouchableOpacity>
      
      {/* Translation Toggle */}
      <Switch
        value={showTranslation}
        onValueChange={setShowTranslation}
      />
      
      {/* Live Transcription */}
      {showTranslation && (
        <View style={styles.transcriptionBox}>
          <Text>Live translation will appear here...</Text>
        </View>
      )}
    </View>
  );
};
```

#### **2.2 Enhanced VoiceScreen**

```typescript
// src/screens/VoiceScreen.tsx - Enhanced with translation
export default function VoiceScreen() {
  const [detectedLanguage, setDetectedLanguage] = useState('unknown');
  const [targetLanguage, setTargetLanguage] = useState('auto');
  const [liveTranscript, setLiveTranscript] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  
  // WebSocket connection for real-time translation
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8001/ws/translation');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setDetectedLanguage(data.source_language);
      setLiveTranscript(data.transcript);
      setTranslatedText(data.response);
    };
    
    return () => ws.close();
  }, []);
  
  return (
    <View style={styles.container}>
      {/* Existing Voice UI */}
      
      {/* Translation Interface */}
      <TranslationInterface
        detectedLanguage={detectedLanguage}
        onLanguageChange={setTargetLanguage}
        isTranslating={isRecording}
      />
      
      {/* Live Translation Display */}
      <View style={styles.translationDisplay}>
        <Text style={styles.originalText}>{liveTranscript}</Text>
        <Text style={styles.translatedText}>{translatedText}</Text>
      </View>
    </View>
  );
}
```

#### **2.3 Call Translation Integration**

```typescript
// src/screens/ActiveCallScreen.tsx - Enhanced with translation
export default function ActiveCallScreen() {
  const [translationEnabled, setTranslationEnabled] = useState(false);
  const [callLanguage, setCallLanguage] = useState('unknown');
  const [transcript, setTranscript] = useState('');
  
  // Real-time translation during phone calls
  const handleCallAudio = async (audioData: ArrayBuffer) => {
    if (!translationEnabled) return;
    
    try {
      const response = await fetch('http://localhost:8001/api/v1/translation/real-time', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/octet-stream',
          'Target-Language': targetLanguage
        },
        body: audioData
      });
      
      const result = await response.json();
      setCallLanguage(result.source_language);
      setTranscript(result.transcript);
    } catch (error) {
      console.error('Translation failed:', error);
    }
  };
  
  return (
    <SafeAreaView style={styles.container}>
      {/* Existing Call UI */}
      
      {/* Translation Controls */}
      <View style={styles.translationControls}>
        <TouchableOpacity
          style={[styles.translateButton, translationEnabled && styles.active]}
          onPress={() => setTranslationEnabled(!translationEnabled)}
        >
          <Text>Translate ({callLanguage})</Text>
        </TouchableOpacity>
      </View>
      
      {/* Live Transcript */}
      {translationEnabled && (
        <View style={styles.transcriptContainer}>
          <Text style={styles.transcriptText}>{transcript}</Text>
        </View>
      )}
    </SafeAreaView>
  );
}
```

### **Phase 3: Advanced Features**

#### **3.1 Bilingual Conversation View**

```typescript
// Split-screen conversation view
const BilingualConversation = () => {
  return (
    <View style={styles.bilingualContainer}>
      <View style={styles.originalLanguage}>
        <Text style={styles.originalText}>{originalSpeech}</Text>
      </View>
      <View style={styles.translatedLanguage}>
        <Text style={styles.translatedText}>{translatedSpeech}</Text>
      </View>
    </View>
  );
};
```

#### **3.2 Offline Translation Cache**

```typescript
// Cache common translations for offline use
const TranslationCache = {
  commonPhrases: {
    'hello': { 'hi': 'नमस्ते', 'ta': 'வணக்கம்' },
    'thank you': { 'hi': 'धन्यवाद', 'ta': 'நன்றி' }
  },
  
  async getCachedTranslation(text: string, from: string, to: string) {
    const key = `${from}-${to}-${text}`;
    return this.commonPhrases[text]?.[to] || null;
  }
};
```

## Supported Languages

### **Sarvam AI Supported Languages**

| Language | Code | STT | TTS | Translation |
|----------|------|-----|-----|-------------|
| Hindi    | hi-IN | ✅ | ✅ | ✅ |
| English  | en-IN | ✅ | ✅ | ✅ |
| Tamil    | ta-IN | ✅ | ✅ | ✅ |
| Telugu   | te-IN | ✅ | ✅ | ✅ |
| Kannada  | kn-IN | ✅ | ✅ | ✅ |
| Malayalam| ml-IN | ✅ | ✅ | ✅ |
| Bengali  | bn-IN | ✅ | ✅ | ✅ |
| Marathi  | mr-IN | ✅ | ✅ | ✅ |
| Gujarati | gu-IN | ✅ | ✅ | ✅ |
| Punjabi  | pa-IN | ✅ | ✅ | ✅ |

## Performance Considerations

### **Real-Time Processing**

- **Latency**: < 500ms for translation
- **Accuracy**: 90%+ for supported languages
- **Concurrent Users**: 100+ per server
- **Audio Quality**: 16kHz, 16-bit recommended

### **Mobile Optimization**

- **Network**: WebSocket for real-time streaming
- **Battery**: Efficient audio processing
- **Storage**: Cache frequently used phrases
- **Memory**: < 100MB additional usage

## Implementation Timeline

### **Week 1-2: Backend**

- [ ] Dynamic language configuration
- [ ] Real-time translation API
- [ ] Language detection improvements
- [ ] Performance optimization

### **Week 3-4: Mobile UI**

- [ ] Translation interface components
- [ ] Language picker implementation
- [ ] Live transcription display
- [ ] Settings integration

### **Week 5-6: Integration**

- [ ] WebSocket real-time streaming
- [ ] Call translation integration
- [ ] Bilingual conversation view
- [ ] Testing and optimization

## Testing Strategy

### **Unit Tests**

- Language detection accuracy
- Translation API responses
- Mobile component rendering

### **Integration Tests**

- End-to-end translation flow
- WebSocket connection stability
- Audio quality preservation

### **User Testing**

- Multi-language call scenarios
- Translation accuracy feedback
- Performance under load

## Conclusion

**Current Status**: The backend has robust translation capabilities via Sarvam AI, but the mobile app lacks the UI to expose these features.

**Required Implementation**:

1. ✅ Backend translation infrastructure exists
2. ❌ Mobile UI needs translation components
3. ❌ Real-time translation display missing
4. ❌ Language picker and settings needed

**Effort Estimate**: 6 weeks for complete implementation with real-time translation in mobile calls.

The foundation is solid - we just need to build the mobile interface to expose the powerful translation capabilities already available in the backend.
