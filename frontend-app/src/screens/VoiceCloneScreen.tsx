import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  TextInput,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Mic, Play, Trash2, Check, X, Plus, ChevronLeft } from 'lucide-react-native';
import { useVoice } from '../contexts/VoiceContext';

export default function VoiceCloneScreen({ navigation }: any) {
  const {
    voices,
    isRecording,
    recordingDuration,
    startRecording,
    stopRecording,
    uploadVoiceSample,
    deleteVoice,
    previewVoice,
    selectedVoice,
    setSelectedVoice,
  } = useVoice();

  const [showNameModal, setShowNameModal] = useState(false);
  const [voiceName, setVoiceName] = useState('');
  const [recordingUri, setRecordingUri] = useState<string | null>(null);
  const [previewText, setPreviewText] = useState('Hello! This is my cloned voice speaking.');

  const handleStartRecording = async () => {
    await startRecording();
  };

  const handleStopRecording = async () => {
    const uri = await stopRecording();
    if (uri) {
      setRecordingUri(uri);
      setShowNameModal(true);
    }
  };

  const handleSaveVoice = async () => {
    if (!voiceName.trim()) {
      Alert.alert('Error', 'Please enter a name for your voice');
      return;
    }
    await uploadVoiceSample(voiceName.trim());
    setShowNameModal(false);
    setVoiceName('');
    setRecordingUri(null);
  };

  const handleDelete = (voiceId: string, voiceName: string) => {
    Alert.alert(
      'Delete Voice',
      `Are you sure you want to delete "${voiceName}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => deleteVoice(voiceId),
        },
      ]
    );
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <ChevronLeft size={24} color="#111827" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Voice Cloning</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.scrollView}>
        {/* Recording Section */}
        <View style={styles.recordingCard}>
          <Text style={styles.sectionTitle}>Record Your Voice</Text>
          <Text style={styles.sectionSubtitle}>
            Record at least 30 seconds of clear speech for best results
          </Text>

          <View style={styles.recordingVisualizer}>
            {isRecording ? (
              <View style={styles.waveform}>
                {[...Array(20)].map((_, i) => (
                  <View
                    key={i}
                    style={[
                      styles.waveBar,
                      {
                        height: 20 + Math.random() * 60,
                        backgroundColor: '#ef4444',
                      },
                    ]}
                  />
                ))}
              </View>
            ) : (
              <View style={styles.micButtonContainer}>
                <Mic size={48} color="#6b7280" />
              </View>
            )}
          </View>

          <Text style={styles.durationText}>
            {isRecording ? formatDuration(recordingDuration) : '00:00'}
          </Text>

          <TouchableOpacity
            style={[
              styles.recordButton,
              isRecording && styles.recordingButton,
            ]}
            onPress={isRecording ? handleStopRecording : handleStartRecording}
          >
            <View
              style={[
                styles.recordButtonInner,
                isRecording && styles.stopButtonInner,
              ]}
            />
          </TouchableOpacity>

          <Text style={styles.recordHint}>
            {isRecording ? 'Tap to stop recording' : 'Tap to start recording'}
          </Text>
        </View>

        {/* Voice List */}
        <View style={styles.voiceList}>
          <Text style={styles.sectionTitle}>Your Cloned Voices</Text>

          {voices.length === 0 ? (
            <View style={styles.emptyState}>
              <Mic size={48} color="#d1d5db" />
              <Text style={styles.emptyTitle}>No voices yet</Text>
              <Text style={styles.emptySubtitle}>
                Record your voice to create your AI clone
              </Text>
            </View>
          ) : (
            voices.map((voice) => (
              <View key={voice.id} style={styles.voiceCard}>
                <View style={styles.voiceInfo}>
                  <View style={styles.voiceIcon}>
                    <Mic size={20} color="#6366f1" />
                  </View>
                  <View style={styles.voiceDetails}>
                    <Text style={styles.voiceName}>{voice.name}</Text>
                    <Text style={styles.voiceStatus}>
                      {voice.status === 'ready'
                        ? 'Ready to use'
                        : voice.status === 'processing'
                        ? 'Processing...'
                        : voice.status === 'error'
                        ? 'Error - Try again'
                        : 'Recording'}
                    </Text>
                  </View>
                </View>

                <View style={styles.voiceActions}>
                  {voice.status === 'ready' && (
                    <>
                      <TouchableOpacity
                        style={[
                          styles.actionBtn,
                          selectedVoice?.id === voice.id && styles.selectedBtn,
                        ]}
                        onPress={() =>
                          setSelectedVoice(
                            selectedVoice?.id === voice.id ? null : voice
                          )
                        }
                      >
                        {selectedVoice?.id === voice.id ? (
                          <Check size={18} color="#22c55e" />
                        ) : (
                          <Text style={styles.useBtnText}>Use</Text>
                        )}
                      </TouchableOpacity>

                      <TouchableOpacity
                        style={styles.actionBtn}
                        onPress={() => previewVoice(voice.voiceId!, previewText)}
                      >
                        <Play size={18} color="#6366f1" />
                      </TouchableOpacity>
                    </>
                  )}

                  <TouchableOpacity
                    style={[styles.actionBtn, styles.deleteBtn]}
                    onPress={() => handleDelete(voice.voiceId!, voice.name)}
                  >
                    <Trash2 size={18} color="#ef4444" />
                  </TouchableOpacity>
                </View>
              </View>
            ))
          )}
        </View>

        {/* Preview Text */}
        <View style={styles.previewCard}>
          <Text style={styles.sectionTitle}>Preview Text</Text>
          <TextInput
            style={styles.previewInput}
            multiline
            value={previewText}
            onChangeText={setPreviewText}
            placeholder="Enter text to preview your cloned voice..."
          />
        </View>
      </ScrollView>

      {/* Name Modal */}
      <Modal
        visible={showNameModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowNameModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Name Your Voice</Text>
            <TextInput
              style={styles.nameInput}
              value={voiceName}
              onChangeText={setVoiceName}
              placeholder="e.g., My Professional Voice"
              autoFocus
            />
            <View style={styles.modalActions}>
              <TouchableOpacity
                style={[styles.modalBtn, styles.cancelBtn]}
                onPress={() => {
                  setShowNameModal(false);
                  setVoiceName('');
                }}
              >
                <Text style={styles.cancelBtnText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalBtn, styles.saveBtn]}
                onPress={handleSaveVoice}
              >
                <Text style={styles.saveBtnText}>Save</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
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
  recordingCard: {
    backgroundColor: '#ffffff',
    margin: 16,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 8,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 24,
  },
  recordingVisualizer: {
    width: '100%',
    height: 120,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  waveform: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
  },
  waveBar: {
    width: 4,
    borderRadius: 2,
  },
  micButtonContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  durationText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 24,
  },
  recordButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#fef2f2',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: '#ef4444',
  },
  recordingButton: {
    borderColor: '#dc2626',
  },
  recordButtonInner: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#ef4444',
  },
  stopButtonInner: {
    width: 24,
    height: 24,
    borderRadius: 4,
    backgroundColor: '#dc2626',
  },
  recordHint: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 16,
  },
  voiceList: {
    padding: 16,
  },
  emptyState: {
    alignItems: 'center',
    padding: 48,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#6b7280',
    marginTop: 16,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 4,
    textAlign: 'center',
  },
  voiceCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  voiceInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  voiceIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#eef2ff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  voiceDetails: {
    marginLeft: 12,
  },
  voiceName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  voiceStatus: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  voiceActions: {
    flexDirection: 'row',
    gap: 8,
  },
  actionBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  selectedBtn: {
    backgroundColor: '#dcfce7',
  },
  useBtnText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6366f1',
  },
  deleteBtn: {
    backgroundColor: '#fef2f2',
  },
  previewCard: {
    backgroundColor: '#ffffff',
    margin: 16,
    borderRadius: 16,
    padding: 16,
  },
  previewInput: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#374151',
    minHeight: 80,
    textAlignVertical: 'top',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalContent: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 400,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
    textAlign: 'center',
  },
  nameInput: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 16,
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
  },
  modalBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelBtn: {
    backgroundColor: '#f3f4f6',
  },
  cancelBtnText: {
    color: '#6b7280',
    fontSize: 16,
    fontWeight: '600',
  },
  saveBtn: {
    backgroundColor: '#6366f1',
  },
  saveBtnText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});
