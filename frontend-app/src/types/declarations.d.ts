// Type declarations for modules without types

declare namespace NodeJS {
  interface ProcessEnv {
    EXPO_PUBLIC_API_URL?: string;
    EXPO_PUBLIC_ELEVENLABS_API_KEY?: string;
  }
}

declare const process: {
  env: NodeJS.ProcessEnv;
};

declare module 'react-native-safe-area-context' {
  import { ReactNode } from 'react';
  import { ViewProps } from 'react-native';
  
  export interface SafeAreaViewProps extends ViewProps {
    children?: ReactNode;
  }
  
  export function SafeAreaProvider(props: { children: ReactNode }): JSX.Element;
  export function SafeAreaView(props: SafeAreaViewProps): JSX.Element;
  
  export interface EdgeInsets {
    top: number;
    right: number;
    bottom: number;
    left: number;
  }
  
  export function useSafeAreaInsets(): EdgeInsets;
  export function useSafeAreaFrame(): { x: number; y: number; width: number; height: number };
}

declare module '@react-native-async-storage/async-storage' {
  export default class AsyncStorage {
    static getItem(key: string): Promise<string | null>;
    static setItem(key: string, value: string): Promise<void>;
    static removeItem(key: string): Promise<void>;
    static clear(): Promise<void>;
    static getAllKeys(): Promise<string[]>;
    static multiGet(keys: string[]): Promise<[string, string | null][]>;
    static multiSet(keyValuePairs: [string, string][]): Promise<void>;
    static multiRemove(keys: string[]): Promise<void>;
  }
}

declare module 'expo-notifications' {
  export interface Notification {
    request: {
      identifier: string;
      content: {
        title: string | null;
        body: string | null;
        data: Record<string, unknown>;
      };
    };
  }
  
  export interface NotificationRequest {
    identifier: string;
    content: {
      title: string;
      body: string;
      data?: Record<string, unknown>;
    };
    trigger: unknown;
  }
  
  export function requestPermissionsAsync(): Promise<{ status: string; granted: boolean }>;
  export function getPermissionsAsync(): Promise<{ status: string; granted: boolean }>;
  export function getExpoPushTokenAsync(): Promise<{ data: string }>;
  export function scheduleNotificationAsync(request: NotificationRequest): Promise<string>;
  export function cancelScheduledNotificationAsync(identifier: string): Promise<void>;
  export function addNotificationReceivedListener(listener: (notification: Notification) => void): { remove: () => void };
  export function addNotificationResponseReceivedListener(listener: (response: { notification: Notification }) => void): { remove: () => void };
  export function setNotificationHandler(handler: {
    handleNotification: () => Promise<{
      shouldShowAlert: boolean;
      shouldPlaySound: boolean;
      shouldSetBadge: boolean;
    }>;
  }): void;
}

declare module 'expo-av' {
  export interface Recording {
    startAsync(): Promise<void>;
    stopAndUnloadAsync(): Promise<void>;
    getURI(): string | null;
    getStatusAsync(): Promise<{
      isRecording: boolean;
      isDoneRecording: boolean;
      durationMillis: number;
    }>;
    createNewLoadedSoundAsync(): Promise<{ sound: Sound }>;
  }
  
  export interface Sound {
    playAsync(): Promise<void>;
    pauseAsync(): Promise<void>;
    stopAsync(): Promise<void>;
    unloadAsync(): Promise<void>;
    setPositionAsync(positionMillis: number): Promise<void>;
    getStatusAsync(): Promise<{
      isLoaded: boolean;
      isPlaying: boolean;
      durationMillis: number;
      positionMillis: number;
    }>;
  }
  
  export function Audio(): void;
  export namespace Audio {
    function requestPermissionsAsync(): Promise<{ status: string; granted: boolean }>;
    function setAudioModeAsync(mode: {
      allowsRecordingIOS?: boolean;
      playsInSilentModeIOS?: boolean;
      staysActiveInBackground?: boolean;
      shouldDuckAndroid?: boolean;
      playThroughEarpieceAndroid?: boolean;
    }): Promise<void>;
    
    type Recording = import('./expo-av').Recording;
    
    const Recording: {
      createAsync(options?: {
        android?: {
          extension: string;
          outputFormat: number;
          audioEncoder: number;
        };
        ios?: {
          extension: string;
          audioQuality: number;
          sampleRate: number;
          numberOfChannels: number;
          bitRate: number;
          linearPCMBitDepth: number;
          linearPCMIsBigEndian: boolean;
          linearPCMIsFloat: boolean;
        };
        web?: {
          mimeType: string;
          bitsPerSecond: number;
        };
      }): Promise<{ recording: Recording }>;
    };
    
    const RecordingOptionsPresets: {
      HIGH_QUALITY: any;
      LOW_QUALITY: any;
    };
    
    const Sound: {
      createAsync(source: { uri: string } | number, initialStatus?: { shouldPlay?: boolean; isLooping?: boolean }): Promise<{ sound: Sound }>;
    };
  }
}

declare module 'expo-file-system' {
  export function readAsStringAsync(uri: string, options?: { encoding?: 'utf8' | 'base64' }): Promise<string>;
  export function writeAsStringAsync(uri: string, content: string, options?: { encoding?: 'utf8' | 'base64' }): Promise<void>;
  export function deleteAsync(uri: string, options?: { idempotent?: boolean }): Promise<void>;
  export function moveAsync(options: { from: string; to: string }): Promise<void>;
  export function copyAsync(options: { from: string; to: string }): Promise<void>;
  export function makeDirectoryAsync(uri: string, options?: { intermediates?: boolean }): Promise<void>;
  export function getInfoAsync(uri: string, options?: { size?: boolean; md5?: boolean }): Promise<{ exists: boolean; uri: string; size?: number; isDirectory?: boolean }>;
  export function getFreeDiskStorageAsync(): Promise<number>;
  export function getTotalDiskCapacityAsync(): Promise<number>;
  export function downloadAsync(uri: string, fileUri: string, options?: { md5?: boolean; headers?: Record<string, string> }): Promise<{ uri: string; status: number; headers: Record<string, string>; md5?: string }>;
  export function uploadAsync(url: string, fileUri: string, options?: { httpMethod?: 'POST' | 'PUT'; headers?: Record<string, string>; sessionType?: 'BACKGROUND' | 'FOREGROUND' }): Promise<{ body: string; status: number; headers: Record<string, string> }>;
  
  export const documentDirectory: string | null;
  export const cacheDirectory: string | null;
  export const bundledResources: string | null;
  export const EncodingType: {
    UTF8: 'utf8';
    Base64: 'base64';
  };
}

declare module '@react-navigation/native' {
  export function NavigationContainer(props: { children: React.ReactNode }): JSX.Element;
}

declare module '@react-navigation/bottom-tabs' {
  import { ComponentType } from 'react';
  export function createBottomTabNavigator(): {
    Navigator: ComponentType<any>;
    Screen: ComponentType<any>;
  };
}

declare module '@react-navigation/native-stack' {
  import { ComponentType } from 'react';
  export function createNativeStackNavigator(): {
    Navigator: ComponentType<any>;
    Screen: ComponentType<any>;
  };
}

declare module 'lucide-react-native' {
  import { SvgProps } from 'react-native-svg';
  
  interface LucideProps extends SvgProps {
    size?: number;
    color?: string;
    strokeWidth?: number;
  }
  
  export function ChevronLeft(props: LucideProps): JSX.Element;
  export function Upload(props: LucideProps): JSX.Element;
  export function FileText(props: LucideProps): JSX.Element;
  export function MessageCircle(props: LucideProps): JSX.Element;
  export function Brain(props: LucideProps): JSX.Element;
  export function Check(props: LucideProps): JSX.Element;
  export function Play(props: LucideProps): JSX.Element;
  export function Plus(props: LucideProps): JSX.Element;
  export function Trash2(props: LucideProps): JSX.Element;
  export function User(props: LucideProps): JSX.Element;
  export function Briefcase(props: LucideProps): JSX.Element;
  export function Sparkles(props: LucideProps): JSX.Element;
  export function Phone(props: LucideProps): JSX.Element;
  export function Settings(props: LucideProps): JSX.Element;
  export function Mic(props: LucideProps): JSX.Element;
  export function Volume2(props: LucideProps): JSX.Element;
  export function Save(props: LucideProps): JSX.Element;
  export function RefreshCw(props: LucideProps): JSX.Element;
  export function Clock(props: LucideProps): JSX.Element;
  export function Bell(props: LucideProps): JSX.Element;
  export function Calendar(props: LucideProps): JSX.Element;
  export function Search(props: LucideProps): JSX.Element;
  export function Filter(props: LucideProps): JSX.Element;
  export function MoreHorizontal(props: LucideProps): JSX.Element;
  export function ArrowRight(props: LucideProps): JSX.Element;
  export function CreditCard(props: LucideProps): JSX.Element;
  export function Wallet(props: LucideProps): JSX.Element;
  export function Shield(props: LucideProps): JSX.Element;
  export function HelpCircle(props: LucideProps): JSX.Element;
  export function LogOut(props: LucideProps): JSX.Element;
  export function ChevronRight(props: LucideProps): JSX.Element;
  export function PhoneIncoming(props: LucideProps): JSX.Element;
  export function PhoneOutgoing(props: LucideProps): JSX.Element;
  export function MicOff(props: LucideProps): JSX.Element;
  export function Pause(props: LucideProps): JSX.Element;
  export function PhoneOff(props: LucideProps): JSX.Element;
  export function Menu(props: LucideProps): JSX.Element;
  export function X(props: LucideProps): JSX.Element;
  export function Moon(props: LucideProps): JSX.Element;
  export function Globe(props: LucideProps): JSX.Element;
  export function Voicemail(props: LucideProps): JSX.Element;
  export function MoreVertical(props: LucideProps): JSX.Element;
  export function ChevronDown(props: LucideProps): JSX.Element;
  export function Square(props: LucideProps): JSX.Element;
}
