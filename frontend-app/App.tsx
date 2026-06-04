import { StatusBar } from 'expo-status-bar';
import React, { useMemo, useState } from 'react';
import { Text, TouchableOpacity, View, StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Phone, MessageCircle, Settings, User, Mic } from 'lucide-react-native';
import HomeScreen from './src/screens/HomeScreen';
import VoiceScreen from './src/screens/VoiceScreen';
import InboxScreen from './src/screens/InboxScreen';
import CallSettingsScreen from './src/screens/CallSettingsScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import ActiveCallScreen from './src/screens/ActiveCallScreen';
import { CallProvider } from './src/contexts/CallContext';
import { VoiceProvider } from './src/contexts/VoiceContext';

type ScreenName = 'Home' | 'Voice' | 'Inbox' | 'Settings' | 'Profile' | 'ActiveCall';

const tabs: Array<{ name: ScreenName; label: string; icon: React.ComponentType<{ size: number; color: string }> }> = [
  { name: 'Home', label: 'Calls', icon: Phone },
  { name: 'Voice', label: 'Video', icon: Mic },
  { name: 'Inbox', label: 'Chat', icon: MessageCircle },
  { name: 'Settings', label: 'Settings', icon: Settings },
  { name: 'Profile', label: 'Profile', icon: User },
];

export default function App() {
  const [screen, setScreen] = useState<ScreenName>('Home');
  const [routeParams, setRouteParams] = useState<Record<string, unknown>>({});

  const navigation = useMemo(() => ({
    navigate: (name: ScreenName, params?: Record<string, unknown>) => {
      setRouteParams(params || {});
      setScreen(name);
    },
    goBack: () => setScreen('Home'),
  }), []);

  const renderScreen = () => {
    switch (screen) {
      case 'Voice':
        return <VoiceScreen />;
      case 'Inbox':
        return <InboxScreen />;
      case 'Settings':
        return <CallSettingsScreen navigation={navigation} />;
      case 'Profile':
        return <ProfileScreen />;
      case 'ActiveCall':
        return <ActiveCallScreen navigation={navigation} route={{ params: routeParams }} />;
      case 'Home':
      default:
        return <HomeScreen navigation={navigation} />;
    }
  };

  return (
    <SafeAreaProvider>
      <VoiceProvider>
        <CallProvider>
          <View style={styles.shell}>
            <View style={styles.content}>{renderScreen()}</View>
            <View style={styles.tabs}>
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const active = screen === tab.name || (screen === 'ActiveCall' && tab.name === 'Home');
                return (
                  <TouchableOpacity key={tab.name} style={styles.tabButton} onPress={() => setScreen(tab.name)}>
                    <Icon size={20} color={active ? '#2563eb' : '#6b7280'} />
                    <Text style={[styles.tabLabel, active && styles.tabLabelActive]}>{tab.label}</Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>
          <StatusBar style="dark" />
        </CallProvider>
      </VoiceProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  shell: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  content: {
    flex: 1,
  },
  tabs: {
    flexDirection: 'row',
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#e5e7eb',
    backgroundColor: '#ffffff',
    paddingTop: 8,
    paddingBottom: 10,
  },
  tabButton: {
    flex: 1,
    alignItems: 'center',
    gap: 3,
  },
  tabLabel: {
    fontSize: 11,
    color: '#6b7280',
    fontWeight: '600',
  },
  tabLabelActive: {
    color: '#2563eb',
  },
});
