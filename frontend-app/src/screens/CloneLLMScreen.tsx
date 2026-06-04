import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Switch,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { 
  ChevronLeft, 
  Upload, 
  FileText, 
  MessageCircle, 
  Brain, 
  Check, 
  Play,
  Plus,
  Trash2,
  User,
  Briefcase,
  Sparkles
} from 'lucide-react-native';
import { apiUrl } from '../config/api';

interface Clone {
  id: string;
  name: string;
  status: string;
  documents_count: number;
  personality?: {
    communication_style: string;
    formality_level: number;
    response_length: string;
  };
}

export default function CloneLLMScreen({ navigation }: any) {
  const [activeTab, setActiveTab] = useState<'create' | 'train' | 'test'>('create');
  const [cloneName, setCloneName] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [company, setCompany] = useState('');
  const [bio, setBio] = useState('');
  const [expertise, setExpertise] = useState('');
  const [documents, setDocuments] = useState<string[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [testMessage, setTestMessage] = useState('');
  const [testResponse, setTestResponse] = useState('');
  const [isTesting, setIsTesting] = useState(false);
  const [clones, setClones] = useState<Clone[]>([]);
  const [selectedClone, setSelectedClone] = useState<Clone | null>(null);
  const [useForCalls, setUseForCalls] = useState(false);

  const handleCreateClone = async () => {
    if (!cloneName.trim()) {
      Alert.alert('Error', 'Please enter your name');
      return;
    }

    setIsCreating(true);
    try {
      const response = await fetch(apiUrl('/clone/create'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'mobile_user',
          name: cloneName,
          job_title: jobTitle,
          company: company,
          bio: bio,
          expertise: expertise.split(',').map(s => s.trim()).filter(s => s),
        }),
      });

      const data = await response.json();
      if (data.success) {
        const newClone: Clone = {
          id: data.clone_id,
          name: data.name,
          status: 'created',
          documents_count: 0,
        };
        setClones([...clones, newClone]);
        setSelectedClone(newClone);
        Alert.alert('Success', 'AI Clone created! Now train it with your documents.');
        setActiveTab('train');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to create clone');
    } finally {
      setIsCreating(false);
    }
  };

  const handleUploadText = async () => {
    if (!selectedClone) return;
    
    // Show text input dialog
    Alert.prompt(
      'Upload Text',
      'Paste text about yourself (emails, articles, bio, etc.)',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Upload',
          onPress: async (text?: string) => {
            if (text && text.trim()) {
              setIsUploading(true);
              try {
                const response = await fetch(apiUrl(`/clone/${selectedClone.id}/upload-text`), {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                  body: `text_content=${encodeURIComponent(text)}&source_name=manual_upload`,
                });
                
                const data = await response.json();
                if (data.success) {
                  Alert.alert('Success', `Added ${data.chunks_created} text chunks to your clone!`);
                  setDocuments([...documents, `Text upload (${data.chunks_created} chunks)`]);
                }
              } catch (error) {
                Alert.alert('Error', 'Failed to upload text');
              } finally {
                setIsUploading(false);
              }
            }
          }
        }
      ],
      'plain-text'
    );
  };

  const handleTestClone = async () => {
    if (!selectedClone || !testMessage.trim()) return;

    setIsTesting(true);
    setTestResponse('');
    
    try {
      const response = await fetch(apiUrl(`/clone/${selectedClone.id}/chat`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: testMessage }),
      });

      const data = await response.json();
      if (data.success) {
        setTestResponse(data.response);
      }
    } catch (error) {
      setTestResponse('Error: Could not get response from clone');
    } finally {
      setIsTesting(false);
    }
  };

  const handleEnableForCalls = async () => {
    if (!selectedClone) return;

    try {
      const response = await fetch(apiUrl(`/clone/${selectedClone.id}/enable-for-calls`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'mobile_user' }),
      });

      const data = await response.json();
      if (data.success) {
        Alert.alert(
          'Clone Active for Calls!',
          'Your AI clone will now answer phone calls using your personality and knowledge.'
        );
        setUseForCalls(true);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to enable clone for calls');
    }
  };

  const renderCreateTab = () => (
    <View style={styles.tabContent}>
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Brain size={24} color="#6366f1" />
          <Text style={styles.cardTitle}>Create Your AI Clone</Text>
        </View>
        
        <Text style={styles.cardSubtitle}>
          Build an AI that learns your personality, knowledge, and communication style
        </Text>

        <TextInput
          style={styles.input}
          placeholder="Your Name *"
          value={cloneName}
          onChangeText={setCloneName}
        />

        <TextInput
          style={styles.input}
          placeholder="Job Title (e.g., Software Engineer)"
          value={jobTitle}
          onChangeText={setJobTitle}
        />

        <TextInput
          style={styles.input}
          placeholder="Company"
          value={company}
          onChangeText={setCompany}
        />

        <TextInput
          style={[styles.input, styles.textArea]}
          placeholder="Bio - Tell us about yourself"
          multiline
          numberOfLines={4}
          value={bio}
          onChangeText={setBio}
        />

        <TextInput
          style={styles.input}
          placeholder="Expertise (comma separated: AI, Marketing, Sales...)"
          value={expertise}
          onChangeText={setExpertise}
        />

        <TouchableOpacity
          style={[styles.button, isCreating && styles.buttonDisabled]}
          onPress={handleCreateClone}
          disabled={isCreating}
        >
          {isCreating ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <>
              <Sparkles size={20} color="#ffffff" />
              <Text style={styles.buttonText}>Create AI Clone</Text>
            </>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderTrainTab = () => (
    <View style={styles.tabContent}>
      {selectedClone ? (
        <>
          <View style={styles.card}>
            <View style={styles.cloneHeader}>
              <User size={40} color="#6366f1" />
              <View style={styles.cloneInfo}>
                <Text style={styles.cloneName}>{selectedClone.name}</Text>
                <Text style={styles.cloneStatus}>
                  {selectedClone.documents_count > 0 ? 'Trained' : 'Needs Training'}
                </Text>
              </View>
            </View>
          </View>

          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Train Your Clone</Text>
            <Text style={styles.sectionDesc}>
              Upload documents, emails, or chat history so your clone learns your style
            </Text>

            <TouchableOpacity 
              style={styles.uploadButton}
              onPress={handleUploadText}
              disabled={isUploading}
            >
              <FileText size={20} color="#6366f1" />
              <Text style={styles.uploadText}>Paste Text / Bio / Emails</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.uploadButton}>
              <MessageCircle size={20} color="#22c55e" />
              <Text style={styles.uploadText}>Import Chat History</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.uploadButton}>
              <Upload size={20} color="#f59e0b" />
              <Text style={styles.uploadText}>Upload Files (PDF, TXT)</Text>
            </TouchableOpacity>

            {isUploading && (
              <View style={styles.loadingContainer}>
                <ActivityIndicator color="#6366f1" />
                <Text style={styles.loadingText}>Training your clone...</Text>
              </View>
            )}

            {documents.length > 0 && (
              <View style={styles.documentsList}>
                <Text style={styles.documentsTitle}>Uploaded Documents:</Text>
                {documents.map((doc, index) => (
                  <View key={index} style={styles.documentItem}>
                    <Check size={16} color="#22c55e" />
                    <Text style={styles.documentText}>{doc}</Text>
                  </View>
                ))}
              </View>
            )}
          </View>

          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Use for Phone Calls</Text>
            <Text style={styles.sectionDesc}>
              Enable your clone to answer calls with your personality
            </Text>

            <TouchableOpacity
              style={[styles.enableButton, useForCalls && styles.enableButtonActive]}
              onPress={handleEnableForCalls}
            >
              <Text style={[styles.enableText, useForCalls && styles.enableTextActive]}>
                {useForCalls ? '✓ Enabled for Calls' : 'Enable for Calls'}
              </Text>
            </TouchableOpacity>
          </View>
        </>
      ) : (
        <View style={styles.emptyState}>
          <Text style={styles.emptyTitle}>No Clone Created Yet</Text>
          <Text style={styles.emptySubtitle}>Go to "Create" tab to build your AI clone</Text>
        </View>
      )}
    </View>
  );

  const renderTestTab = () => (
    <View style={styles.tabContent}>
      {selectedClone ? (
        <>
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Test Your Clone</Text>
            <Text style={styles.sectionDesc}>
              Chat with your clone to see if it responds like you
            </Text>

            <TextInput
              style={[styles.input, styles.textArea]}
              placeholder="Ask your clone something... (e.g., What do you do for work? Tell me about your expertise.)"
              multiline
              numberOfLines={3}
              value={testMessage}
              onChangeText={setTestMessage}
            />

            <TouchableOpacity
              style={[styles.button, isTesting && styles.buttonDisabled]}
              onPress={handleTestClone}
              disabled={isTesting || !testMessage.trim()}
            >
              {isTesting ? (
                <ActivityIndicator color="#ffffff" />
              ) : (
                <>
                  <Play size={20} color="#ffffff" />
                  <Text style={styles.buttonText}>Test Clone</Text>
                </>
              )}
            </TouchableOpacity>

            {testResponse ? (
              <View style={styles.responseContainer}>
                <Text style={styles.responseLabel}>Clone Response:</Text>
                <View style={styles.responseBubble}>
                  <Text style={styles.responseText}>{testResponse}</Text>
                </View>
              </View>
            ) : null}
          </View>

          {selectedClone.personality && (
            <View style={styles.card}>
              <Text style={styles.sectionTitle}>Personality Analysis</Text>
              
              <View style={styles.traitRow}>
                <Text style={styles.traitLabel}>Communication Style:</Text>
                <Text style={styles.traitValue}>{selectedClone.personality.communication_style}</Text>
              </View>

              <View style={styles.traitRow}>
                <Text style={styles.traitLabel}>Response Length:</Text>
                <Text style={styles.traitValue}>{selectedClone.personality.response_length}</Text>
              </View>

              <View style={styles.traitRow}>
                <Text style={styles.traitLabel}>Formality:</Text>
                <View style={styles.progressBar}>
                  <View 
                    style={[
                      styles.progressFill, 
                      { width: `${selectedClone.personality.formality_level * 100}%` }
                    ]} 
                  />
                </View>
              </View>
            </View>
          )}
        </>
      ) : (
        <View style={styles.emptyState}>
          <Text style={styles.emptyTitle}>No Clone to Test</Text>
          <Text style={styles.emptySubtitle}>Create and train a clone first</Text>
        </View>
      )}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <ChevronLeft size={24} color="#111827" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>AI Clone (Digital Twin)</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        {(['create', 'train', 'test'] as const).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.tabActive]}
            onPress={() => setActiveTab(tab)}
          >
            <Text style={[styles.tabText, activeTab === tab && styles.tabTextActive]}>
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      <ScrollView style={styles.scrollView}>
        {activeTab === 'create' && renderCreateTab()}
        {activeTab === 'train' && renderTrainTab()}
        {activeTab === 'test' && renderTestTab()}
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
  tabs: {
    flexDirection: 'row',
    padding: 8,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  tabActive: {
    backgroundColor: '#eef2ff',
  },
  tabText: {
    fontSize: 14,
    color: '#6b7280',
    fontWeight: '500',
  },
  tabTextActive: {
    color: '#6366f1',
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  tabContent: {
    padding: 16,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
    marginLeft: 12,
  },
  cardSubtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 20,
    lineHeight: 20,
  },
  input: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#374151',
    marginBottom: 12,
  },
  textArea: {
    minHeight: 100,
    textAlignVertical: 'top',
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#6366f1',
    paddingVertical: 14,
    borderRadius: 8,
    gap: 8,
    marginTop: 8,
  },
  buttonDisabled: {
    backgroundColor: '#a5b4fc',
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  cloneHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  cloneInfo: {
    marginLeft: 12,
  },
  cloneName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
  },
  cloneStatus: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 8,
  },
  sectionDesc: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 16,
  },
  uploadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderStyle: 'dashed',
  },
  uploadText: {
    fontSize: 14,
    color: '#374151',
    marginLeft: 12,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 16,
    gap: 8,
  },
  loadingText: {
    fontSize: 14,
    color: '#6366f1',
  },
  documentsList: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#f3f4f6',
  },
  documentsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  documentItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  },
  documentText: {
    fontSize: 14,
    color: '#6b7280',
  },
  enableButton: {
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    backgroundColor: '#f3f4f6',
    alignItems: 'center',
  },
  enableButtonActive: {
    backgroundColor: '#dcfce7',
  },
  enableText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  enableTextActive: {
    color: '#166534',
  },
  emptyState: {
    alignItems: 'center',
    padding: 48,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#6b7280',
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 8,
  },
  responseContainer: {
    marginTop: 20,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#f3f4f6',
  },
  responseLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  responseBubble: {
    backgroundColor: '#eef2ff',
    padding: 16,
    borderRadius: 12,
    borderTopLeftRadius: 4,
  },
  responseText: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
  traitRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  traitLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  traitValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  progressBar: {
    width: 100,
    height: 8,
    backgroundColor: '#e5e7eb',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#6366f1',
    borderRadius: 4,
  },
});
