import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Phone, Settings, Mic, User, MessageCircle } from 'lucide-react-native';

// Screens
import HomeScreen from './screens/HomeScreen';
import VoiceCloneScreen from './screens/VoiceCloneScreen';
import CallSettingsScreen from './screens/CallSettingsScreen';
import InboxScreen from './screens/InboxScreen';
import ProfileScreen from './screens/ProfileScreen';
import ActiveCallScreen from './screens/ActiveCallScreen';
import CloneLLMScreen from './screens/CloneLLMScreen';

// Contexts
import { CallProvider } from './contexts/CallContext';
import { VoiceProvider } from './contexts/VoiceContext';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }: { route: { name: string } }) => ({
        tabBarIcon: ({ color, size }: { color: string; size: number }) => {
          if (route.name === 'Home') return <Phone size={size} color={color} />;
          if (route.name === 'Inbox') return <MessageCircle size={size} color={color} />;
          if (route.name === 'Voice') return <Mic size={size} color={color} />;
          if (route.name === 'Settings') return <Settings size={size} color={color} />;
          if (route.name === 'Profile') return <User size={size} color={color} />;
          return null;
        },
        tabBarActiveTintColor: '#6366f1',
        tabBarInactiveTintColor: '#6b7280',
        headerShown: false,
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Inbox" component={InboxScreen} />
      <Tab.Screen name="Voice" component={VoiceCloneScreen} />
      <Tab.Screen name="Settings" component={CallSettingsScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <VoiceProvider>
        <CallProvider>
          <NavigationContainer>
            <Stack.Navigator screenOptions={{ headerShown: false }}>
              <Stack.Screen name="Main" component={TabNavigator} />
              <Stack.Screen 
                name="ActiveCall" 
                component={ActiveCallScreen}
                options={{ 
                  presentation: 'fullScreenModal',
                  animation: 'slide_from_bottom'
                }}
              />
              <Stack.Screen 
                name="CloneLLM" 
                component={CloneLLMScreen}
                options={{ 
                  animation: 'slide_from_right'
                }}
              />
            </Stack.Navigator>
          </NavigationContainer>
          <StatusBar style="auto" />
        </CallProvider>
      </VoiceProvider>
    </SafeAreaProvider>
  );
}
