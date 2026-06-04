import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Switch,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Phone, Mic, MessageCircle, Settings, ChevronRight } from 'lucide-react-native';
import { useCall } from '../contexts/CallContext';
import { useVoice } from '../contexts/VoiceContext';
import { getLanguageLabel } from '../constants/translation';

export default function HomeScreen({ navigation }: any) {
  const {
    settings,
    isCallHandlingEnabled,
    updateSettings,
    activeCalls,
    incomingCall,
    isAvailable,
    setAvailability,
    acceptCall,
    rejectCall,
    endCall,
  } = useCall();
  const { selectedVoice, voices } = useVoice();

  const toggleCallHandling = async (value: boolean) => {
    await updateSettings({ enabled: value });
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>AI Receptionist</Text>
          <Text style={styles.subtitle}>Your voice, your calls, automated</Text>
        </View>

        {/* Call Handling Toggle */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <View style={styles.iconContainer}>
              <Phone size={24} color="#6366f1" />
            </View>
            <View style={styles.cardContent}>
              <Text style={styles.cardTitle}>Handle Calls</Text>
              <Text style={styles.cardSubtitle}>
                {isCallHandlingEnabled() ? 'Active - Ready for calls' : 'Inactive'}
              </Text>
            </View>
            <Switch
              value={settings.enabled}
              onValueChange={toggleCallHandling}
              trackColor={{ false: '#d1d5db', true: '#6366f1' }}
              thumbColor={settings.enabled ? '#ffffff' : '#f3f4f6'}
            />
          </View>

          {isCallHandlingEnabled() && (
            <View style={styles.statusContainer}>
              <View style={[styles.statusBadge, { backgroundColor: '#dcfce7' }]}>
                <View style={[styles.statusDot, { backgroundColor: '#22c55e' }]} />
                <Text style={[styles.statusText, { color: '#166534' }]}>
                  {isAvailable ? 'Available' : 'Busy'}
                </Text>
              </View>

              <TouchableOpacity
                style={[styles.availabilityButton, { backgroundColor: isAvailable ? '#fee2e2' : '#dcfce7' }]}
                onPress={() => setAvailability(!isAvailable)}
              >
                <Text style={[styles.availabilityText, { color: isAvailable ? '#991b1b' : '#166534' }]}>
                  {isAvailable ? 'Set Busy' : 'Set Available'}
                </Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Active Calls */}
        {activeCalls.length > 0 && (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Active Calls</Text>
            {activeCalls.map((call) => (
              <View key={call.id} style={styles.callItem}>
                <View style={styles.callInfo}>
                  <Text style={styles.callNumber}>{call.phoneNumber}</Text>
                  <Text style={styles.callStatus}>
                    {call.status === 'connected' ? 'On Call' : 'On Hold'} • {formatDuration(call.duration)}
                  </Text>
                </View>
                <TouchableOpacity
                  style={styles.endCallButton}
                  onPress={() => endCall(call.id)}
                >
                  <Phone size={20} color="#ffffff" />
                </TouchableOpacity>
              </View>
            ))}
          </View>
        )}

        {/* Incoming Call Alert */}
        {incomingCall && (
          <View style={[styles.card, styles.incomingCard]}>
            <Text style={styles.incomingTitle}>Incoming Call</Text>
            <Text style={styles.incomingNumber}>{incomingCall.phoneNumber}</Text>
            <View style={styles.incomingActions}>
              <TouchableOpacity
                style={[styles.actionButton, styles.rejectButton]}
                onPress={() => rejectCall(incomingCall.id)}
              >
                <Phone size={24} color="#ffffff" />
                <Text style={styles.actionText}>Decline</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.actionButton, styles.acceptButton]}
                onPress={async () => {
                  await acceptCall(incomingCall.id);
                  navigation.navigate('ActiveCall', { callId: incomingCall.id });
                }}
              >
                <Phone size={24} color="#ffffff" />
                <Text style={styles.actionText}>Answer</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Voice Clone Status */}
        <TouchableOpacity
          style={styles.card}
          onPress={() => navigation.navigate('Voice')}
        >
          <View style={styles.cardHeader}>
            <View style={[styles.iconContainer, { backgroundColor: '#fef3c7' }]}>
              <Mic size={24} color="#f59e0b" />
            </View>
            <View style={styles.cardContent}>
              <Text style={styles.cardTitle}>Your Cloned Voice</Text>
              <Text style={styles.cardSubtitle}>
                {selectedVoice 
                  ? `Using: ${selectedVoice.name}` 
                  : `${voices.length} voice${voices.length !== 1 ? 's' : ''} available`}
              </Text>
            </View>
            <ChevronRight size={20} color="#9ca3af" />
          </View>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.card}
          onPress={() => navigation.navigate('Settings')}
        >
          <View style={styles.cardHeader}>
            <View style={[styles.iconContainer, { backgroundColor: '#ecfeff' }]}>
              <MessageCircle size={24} color="#0891b2" />
            </View>
            <View style={styles.cardContent}>
              <Text style={styles.cardTitle}>Live Translation</Text>
              <Text style={styles.cardSubtitle}>
                {settings.translationEnabled
                  ? `${settings.autoDetectCallerLanguage ? 'Auto detect' : getLanguageLabel(settings.callerLanguage)} -> ${getLanguageLabel(settings.userLanguage)}`
                  : 'Disabled'}
              </Text>
            </View>
            <ChevronRight size={20} color="#9ca3af" />
          </View>
        </TouchableOpacity>

        {/* Quick Actions */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          
          <TouchableOpacity 
            style={styles.actionRow}
            onPress={() => navigation.navigate('Settings')}
          >
            <Settings size={20} color="#6b7280" />
            <Text style={styles.actionRowText}>Call Settings</Text>
            <ChevronRight size={16} color="#9ca3af" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionRow}>
            <MessageCircle size={20} color="#6b7280" />
            <Text style={styles.actionRowText}>View Messages</Text>
            <ChevronRight size={16} color="#9ca3af" />
          </TouchableOpacity>
        </View>

        {/* Stats */}
        <View style={styles.statsContainer}>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>{activeCalls.length}</Text>
            <Text style={styles.statLabel}>Active</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>{voices.length}</Text>
            <Text style={styles.statLabel}>Voices</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>24</Text>
            <Text style={styles.statLabel}>Today</Text>
          </View>
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
  scrollView: {
    flex: 1,
  },
  header: {
    padding: 24,
    paddingTop: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#111827',
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
    marginTop: 4,
  },
  card: {
    backgroundColor: '#ffffff',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 16,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#eef2ff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  cardContent: {
    flex: 1,
    marginLeft: 12,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  cardSubtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#f3f4f6',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '500',
  },
  availabilityButton: {
    marginLeft: 'auto',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  availabilityText: {
    fontSize: 14,
    fontWeight: '600',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 12,
  },
  callItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  callInfo: {
    flex: 1,
  },
  callNumber: {
    fontSize: 16,
    fontWeight: '500',
    color: '#111827',
  },
  callStatus: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  endCallButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#ef4444',
    justifyContent: 'center',
    alignItems: 'center',
    transform: [{ rotate: '135deg' }],
  },
  incomingCard: {
    backgroundColor: '#fef3c7',
    borderWidth: 2,
    borderColor: '#fbbf24',
  },
  incomingTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#92400e',
    textAlign: 'center',
  },
  incomingNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    textAlign: 'center',
    marginTop: 8,
    marginBottom: 16,
  },
  incomingActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  actionButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  rejectButton: {
    backgroundColor: '#ef4444',
  },
  acceptButton: {
    backgroundColor: '#22c55e',
  },
  actionText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
    marginTop: 4,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  actionRowText: {
    flex: 1,
    fontSize: 16,
    color: '#374151',
    marginLeft: 12,
  },
  statsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#ffffff',
    marginHorizontal: 4,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  statLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
  },
});
