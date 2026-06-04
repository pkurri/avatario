import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Switch,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, Clock, Moon, Phone, Voicemail, Mic, Check, Play, MessageCircle } from 'lucide-react-native';
import { useCall } from '../contexts/CallContext';
import { useVoice } from '../contexts/VoiceContext';
import { apiUrl } from '../config/api';
import { getLanguageLabel, TRANSLATION_LANGUAGE_OPTIONS } from '../constants/translation';

export default function CallSettingsScreen({ navigation }: any) {
  const { settings, updateSettings, isCallHandlingEnabled } = useCall();
  const { voices, selectedVoice, setSelectedVoice, previewVoice } = useVoice();
  const [testGreetingLoading, setTestGreetingLoading] = useState(false);

  const toggleSetting = (key: keyof typeof settings) => async (value: boolean) => {
    await updateSettings({ [key]: value });
  };

  const handleSelectVoice = async (voice: any) => {
    setSelectedVoice(voice);
    await updateSettings({ 
      selectedVoiceId: voice.voiceId,
      useClonedVoice: true 
    });
    
    // Sync with backend
    try {
      await fetch(apiUrl('/voice/calls/set-voice'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'mobile_user',
          voice_id: voice.voiceId,
          use_cloned_voice: true,
          greeting_script: settings.greetingScript
        })
      });
      Alert.alert('Success', 'Your cloned voice is now active for calls!');
    } catch (error) {
      console.error('Failed to set voice:', error);
    }
  };

  const handleTestGreeting = async () => {
    if (!settings.useClonedVoice || !settings.selectedVoiceId) {
      Alert.alert('No Voice Selected', 'Please select a cloned voice first');
      return;
    }
    
    setTestGreetingLoading(true);
    try {
      const response = await fetch(apiUrl('/voice/calls/test-greeting'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'mobile_user',
          custom_text: settings.greetingScript
        })
      });
      
      const data = await response.json();
      if (data.success && data.using_cloned_voice) {
        // Play the greeting
        await previewVoice(settings.selectedVoiceId, settings.greetingScript);
      }
    } catch (error) {
      console.error('Failed to test greeting:', error);
    } finally {
      setTestGreetingLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <ChevronLeft size={24} color="#111827" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Call Settings</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.scrollView}>
        {/* Main Toggle */}
        <View style={styles.section}>
          <View style={styles.mainToggle}>
            <View style={styles.toggleIcon}>
              <Phone size={24} color="#6366f1" />
            </View>
            <View style={styles.toggleContent}>
              <Text style={styles.toggleTitle}>Handle Incoming Calls</Text>
              <Text style={styles.toggleSubtitle}>
                {isCallHandlingEnabled() 
                  ? 'AI will answer calls for you' 
                  : 'Calls will go to voicemail'}
              </Text>
            </View>
            <Switch
              value={settings.enabled}
              onValueChange={toggleSetting('enabled')}
              trackColor={{ false: '#d1d5db', true: '#6366f1' }}
              thumbColor={settings.enabled ? '#ffffff' : '#f3f4f6'}
            />
          </View>
        </View>

        {/* Auto Answer */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Answering</Text>
          
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Auto Answer</Text>
              <Text style={styles.settingDesc}>AI answers after delay</Text>
            </View>
            <Switch
              value={settings.autoAnswer}
              onValueChange={toggleSetting('autoAnswer')}
              trackColor={{ false: '#d1d5db', true: '#6366f1' }}
              thumbColor={settings.autoAnswer ? '#ffffff' : '#f3f4f6'}
            />
          </View>

          {settings.autoAnswer && (
            <View style={styles.delayContainer}>
              <Text style={styles.delayLabel}>Answer after (seconds)</Text>
              <View style={styles.delayInput}>
                <TextInput
                  style={styles.numberInput}
                  value={settings.autoAnswerDelay.toString()}
                  onChangeText={(text) => updateSettings({ autoAnswerDelay: parseInt(text) || 5 })}
                  keyboardType="number-pad"
                  maxLength={2}
                />
              </View>
            </View>
          )}

          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <View style={styles.iconRow}>
                <Voicemail size={16} color="#6b7280" />
                <Text style={styles.settingLabel}>Voicemail</Text>
              </View>
              <Text style={styles.settingDesc}>Take messages when unavailable</Text>
            </View>
            <Switch
              value={settings.voicemailEnabled}
              onValueChange={toggleSetting('voicemailEnabled')}
              trackColor={{ false: '#d1d5db', true: '#6366f1' }}
              thumbColor={settings.voicemailEnabled ? '#ffffff' : '#f3f4f6'}
            />
          </View>
        </View>

        {/* Business Hours */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Schedule</Text>
          
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <View style={styles.iconRow}>
                <Clock size={16} color="#6b7280" />
                <Text style={styles.settingLabel}>Business Hours Only</Text>
              </View>
              <Text style={styles.settingDesc}>Only answer during set hours</Text>
            </View>
            <Switch
              value={settings.businessHoursOnly}
              onValueChange={toggleSetting('businessHoursOnly')}
              trackColor={{ false: '#d1d5db', true: '#6366f1' }}
              thumbColor={settings.businessHoursOnly ? '#ffffff' : '#f3f4f6'}
            />
          </View>

          {settings.businessHoursOnly && (
            <View style={styles.timeRange}>
              <View style={styles.timeInput}>
                <Text style={styles.timeLabel}>Start</Text>
                <TextInput
                  style={styles.timeField}
                  value={settings.businessHoursStart}
                  onChangeText={(text) => updateSettings({ businessHoursStart: text })}
                  placeholder="09:00"
                />
              </View>
              <Text style={styles.timeSeparator}>to</Text>
              <View style={styles.timeInput}>
                <Text style={styles.timeLabel}>End</Text>
                <TextInput
                  style={styles.timeField}
                  value={settings.businessHoursEnd}
                  onChangeText={(text) => updateSettings({ businessHoursEnd: text })}
                  placeholder="17:00"
                />
              </View>
            </View>
          )}

          {/* Do Not Disturb */}
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <View style={styles.iconRow}>
                <Moon size={16} color="#6b7280" />
                <Text style={styles.settingLabel}>Do Not Disturb</Text>
              </View>
              <Text style={styles.settingDesc}>Silence all calls</Text>
            </View>
            <Switch
              value={settings.doNotDisturb}
              onValueChange={toggleSetting('doNotDisturb')}
              trackColor={{ false: '#d1d5db', true: '#6366f1' }}
              thumbColor={settings.doNotDisturb ? '#ffffff' : '#f3f4f6'}
            />
          </View>

          {settings.doNotDisturb && (
            <View style={styles.timeRange}>
              <View style={styles.timeInput}>
                <Text style={styles.timeLabel}>DND Start</Text>
                <TextInput
                  style={styles.timeField}
                  value={settings.dndSchedule?.startTime || '22:00'}
                  onChangeText={(text) => updateSettings({ 
                    dndSchedule: { 
                      enabled: true, 
                      startTime: text,
                      endTime: settings.dndSchedule?.endTime || '08:00'
                    } 
                  })}
                  placeholder="22:00"
                />
              </View>
              <Text style={styles.timeSeparator}>to</Text>
              <View style={styles.timeInput}>
                <Text style={styles.timeLabel}>DND End</Text>
                <TextInput
                  style={styles.timeField}
                  value={settings.dndSchedule?.endTime || '08:00'}
                  onChangeText={(text) => updateSettings({ 
                    dndSchedule: { 
                      enabled: true, 
                      startTime: settings.dndSchedule?.startTime || '22:00',
                      endTime: text
                    } 
                  })}
                  placeholder="08:00"
                />
              </View>
            </View>
          )}
        </View>

        {/* Call Types */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Call Types</Text>
          
          <View style={styles.checkboxRow}>
            <TouchableOpacity
              style={[
                styles.checkbox,
                settings.allowedCallTypes.includes('inbound') && styles.checkboxChecked,
              ]}
              onPress={() => {
                const types: ('inbound' | 'outbound')[] = settings.allowedCallTypes.includes('inbound')
                  ? settings.allowedCallTypes.filter((t): t is 'inbound' | 'outbound' => t !== 'inbound')
                  : [...settings.allowedCallTypes, 'inbound'];
                updateSettings({ allowedCallTypes: types });
              }}
            >
              {settings.allowedCallTypes.includes('inbound') && (
                <Text style={styles.checkmark}>✓</Text>
              )}
            </TouchableOpacity>
            <Text style={styles.checkboxLabel}>Inbound Calls</Text>
          </View>

          <View style={styles.checkboxRow}>
            <TouchableOpacity
              style={[
                styles.checkbox,
                settings.allowedCallTypes.includes('outbound') && styles.checkboxChecked,
              ]}
              onPress={() => {
                const types: ('inbound' | 'outbound')[] = settings.allowedCallTypes.includes('outbound')
                  ? settings.allowedCallTypes.filter((t): t is 'inbound' | 'outbound' => t !== 'outbound')
                  : [...settings.allowedCallTypes, 'outbound'];
                updateSettings({ allowedCallTypes: types });
              }}
            >
              {settings.allowedCallTypes.includes('outbound') && (
                <Text style={styles.checkmark}>✓</Text>
              )}
            </TouchableOpacity>
            <Text style={styles.checkboxLabel}>Outbound Calls</Text>
          </View>
        </View>

        {/* Advanced */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Advanced</Text>
          
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Max Concurrent Calls</Text>
              <Text style={styles.settingDesc}>How many calls at once</Text>
            </View>
            <TextInput
              style={styles.numberField}
              value={settings.maxConcurrentCalls.toString()}
              onChangeText={(text) => updateSettings({ maxConcurrentCalls: parseInt(text) || 1 })}
              keyboardType="number-pad"
              maxLength={1}
            />
          </View>
        </View>

        {/* Your Voice - NEW SECTION */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your Voice</Text>
          
          {/* Use Cloned Voice Toggle */}
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <View style={styles.iconRow}>
                <Mic size={16} color="#6b7280" />
                <Text style={styles.settingLabel}>Use My Cloned Voice</Text>
              </View>
              <Text style={styles.settingDesc}>Answer calls with your voice</Text>
            </View>
            <Switch
              value={settings.useClonedVoice}
              onValueChange={toggleSetting('useClonedVoice')}
              trackColor={{ false: '#d1d5db', true: '#6366f1' }}
              thumbColor={settings.useClonedVoice ? '#ffffff' : '#f3f4f6'}
            />
          </View>

          {/* Voice Selection */}
          {settings.useClonedVoice && (
            <View style={styles.voiceSection}>
              <Text style={styles.voiceSectionTitle}>Select Voice for Calls</Text>
              
              {voices.length === 0 ? (
                <View style={styles.emptyVoice}>
                  <Text style={styles.emptyVoiceText}>No cloned voices yet</Text>
                  <TouchableOpacity 
                    style={styles.createVoiceButton}
                    onPress={() => navigation.navigate('Voice')}
                  >
                    <Text style={styles.createVoiceText}>Clone Your Voice</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                voices.map((voice) => (
                  <TouchableOpacity
                    key={voice.id}
                    style={[
                      styles.voiceCard,
                      settings.selectedVoiceId === voice.voiceId && styles.voiceCardSelected
                    ]}
                    onPress={() => handleSelectVoice(voice)}
                  >
                    <View style={styles.voiceInfo}>
                      <View style={styles.voiceIcon}>
                        <Mic size={20} color={settings.selectedVoiceId === voice.voiceId ? '#6366f1' : '#6b7280'} />
                      </View>
                      <View style={styles.voiceDetails}>
                        <Text style={styles.voiceName}>{voice.name}</Text>
                        <Text style={styles.voiceStatus}>
                          {voice.status === 'ready' ? 'Ready for calls' : voice.status}
                        </Text>
                      </View>
                    </View>
                    
                    {settings.selectedVoiceId === voice.voiceId && (
                      <View style={styles.selectedBadge}>
                        <Check size={16} color="#22c55e" />
                      </View>
                    )}
                  </TouchableOpacity>
                ))
              )}

              {/* Greeting Script */}
              <View style={styles.greetingSection}>
                <Text style={styles.greetingLabel}>Greeting Script</Text>
                <TextInput
                  style={styles.greetingInput}
                  multiline
                  value={settings.greetingScript}
                  onChangeText={(text) => updateSettings({ greetingScript: text })}
                  placeholder="What should the AI say when answering?"
                />
                
                {/* Test Greeting Button */}
                {settings.selectedVoiceId && (
                  <TouchableOpacity 
                    style={styles.testButton}
                    onPress={handleTestGreeting}
                    disabled={testGreetingLoading}
                  >
                    <Play size={16} color="#ffffff" />
                    <Text style={styles.testButtonText}>
                      {testGreetingLoading ? 'Generating...' : 'Test Greeting'}
                    </Text>
                  </TouchableOpacity>
                )}
              </View>
            </View>
          )}
        </View>

        {/* Info Card */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Live Translation</Text>

          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <View style={styles.iconRow}>
                <MessageCircle size={16} color="#6b7280" />
                <Text style={styles.settingLabel}>Translate Calls Live</Text>
              </View>
              <Text style={styles.settingDesc}>Bridge callers and your preferred language</Text>
            </View>
            <Switch
              value={settings.translationEnabled}
              onValueChange={toggleSetting('translationEnabled')}
              trackColor={{ false: '#d1d5db', true: '#6366f1' }}
              thumbColor={settings.translationEnabled ? '#ffffff' : '#f3f4f6'}
            />
          </View>

          {settings.translationEnabled && (
            <View style={styles.translationSection}>
              <Text style={styles.translationLabel}>Caller language</Text>
              <View style={styles.languageChipGroup}>
                {TRANSLATION_LANGUAGE_OPTIONS.map((option) => {
                  const isSelected = (settings.autoDetectCallerLanguage ? 'auto' : settings.callerLanguage) === option.code;
                  return (
                    <TouchableOpacity
                      key={option.code}
                      style={[styles.languageChip, isSelected && styles.languageChipSelected]}
                      onPress={() => updateSettings({
                        autoDetectCallerLanguage: option.code === 'auto',
                        callerLanguage: option.code === 'auto' ? settings.callerLanguage : option.code,
                      })}
                    >
                      <Text style={[styles.languageChipText, isSelected && styles.languageChipTextSelected]}>
                        {option.label}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>

              <Text style={styles.translationLabel}>Your preferred language</Text>
              <View style={styles.languageChipGroup}>
                {TRANSLATION_LANGUAGE_OPTIONS.filter((option) => option.code !== 'auto').map((option) => {
                  const isSelected = settings.userLanguage === option.code;
                  return (
                    <TouchableOpacity
                      key={option.code}
                      style={[styles.languageChip, isSelected && styles.languageChipSelected]}
                      onPress={() => updateSettings({ userLanguage: option.code })}
                    >
                      <Text style={[styles.languageChipText, isSelected && styles.languageChipTextSelected]}>
                        {option.label}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>

              <View style={styles.settingRowCompact}>
                <View style={styles.settingInfo}>
                  <Text style={styles.settingLabel}>Preserve your cloned voice</Text>
                  <Text style={styles.settingDesc}>
                    {settings.selectedVoiceId
                      ? `Translated replies use ${getLanguageLabel(settings.userLanguage)} while keeping your voice style`
                      : 'Select a cloned voice above to preserve delivery across languages'}
                  </Text>
                </View>
                <Switch
                  value={settings.voicePreservationEnabled}
                  onValueChange={toggleSetting('voicePreservationEnabled')}
                  trackColor={{ false: '#d1d5db', true: '#6366f1' }}
                  thumbColor={settings.voicePreservationEnabled ? '#ffffff' : '#f3f4f6'}
                />
              </View>
            </View>
          )}
        </View>

        <View style={styles.infoCard}>
          <Text style={styles.infoText}>
            When enabled, the AI will answer calls using your cloned voice. 
            All calls are recorded and available in your inbox.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    backgroundColor: '#ffffff',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  scrollView: {
    flex: 1,
  },
  section: {
    backgroundColor: '#ffffff',
    marginTop: 16,
    paddingVertical: 8,
  },
  mainToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  toggleIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#eef2ff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  toggleContent: {
    flex: 1,
    marginLeft: 12,
  },
  toggleTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  toggleSubtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  settingInfo: {
    flex: 1,
  },
  iconRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  settingLabel: {
    fontSize: 16,
    color: '#374151',
  },
  settingDesc: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 2,
  },
  delayContainer: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    paddingTop: 8,
  },
  delayLabel: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 8,
  },
  delayInput: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  numberInput: {
    width: 60,
    height: 44,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    textAlign: 'center',
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  timeRange: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingBottom: 16,
    gap: 12,
  },
  timeInput: {
    flex: 1,
  },
  timeLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 4,
  },
  timeField: {
    height: 44,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    textAlign: 'center',
    fontSize: 16,
    color: '#111827',
  },
  timeSeparator: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 16,
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: '#d1d5db',
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxChecked: {
    backgroundColor: '#6366f1',
    borderColor: '#6366f1',
  },
  checkmark: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  checkboxLabel: {
    fontSize: 16,
    color: '#374151',
    marginLeft: 12,
  },
  numberField: {
    width: 50,
    height: 36,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 6,
    textAlign: 'center',
    fontSize: 16,
    color: '#111827',
  },
  infoCard: {
    backgroundColor: '#eff6ff',
    margin: 16,
    padding: 16,
    borderRadius: 12,
  },
  infoText: {
    fontSize: 14,
    color: '#1e40af',
    lineHeight: 20,
  },
  // Voice section styles
  voiceSection: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  voiceSectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 12,
    marginTop: 8,
  },
  emptyVoice: {
    alignItems: 'center',
    padding: 24,
    backgroundColor: '#f9fafb',
    borderRadius: 12,
  },
  emptyVoiceText: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 12,
  },
  createVoiceButton: {
    backgroundColor: '#6366f1',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
  },
  createVoiceText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  voiceCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 2,
    borderColor: '#f3f4f6',
  },
  voiceCardSelected: {
    borderColor: '#6366f1',
    backgroundColor: '#eef2ff',
  },
  voiceInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  voiceIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#ffffff',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  voiceDetails: {
    flex: 1,
  },
  voiceName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  voiceStatus: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 2,
  },
  selectedBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#dcfce7',
    justifyContent: 'center',
    alignItems: 'center',
  },
  greetingSection: {
    marginTop: 16,
  },
  greetingLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 8,
  },
  greetingInput: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#374151',
    minHeight: 80,
    textAlignVertical: 'top',
  },
  testButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#6366f1',
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 12,
    gap: 8,
  },
  testButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  translationSection: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    gap: 12,
  },
  translationLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginTop: 4,
  },
  languageChipGroup: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  languageChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: '#d1d5db',
    backgroundColor: '#ffffff',
  },
  languageChipSelected: {
    backgroundColor: '#eef2ff',
    borderColor: '#6366f1',
  },
  languageChipText: {
    fontSize: 13,
    color: '#4b5563',
    fontWeight: '500',
  },
  languageChipTextSelected: {
    color: '#4338ca',
  },
  settingRowCompact: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 16,
    paddingTop: 8,
  },
});
