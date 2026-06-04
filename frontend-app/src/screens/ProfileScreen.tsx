import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { 
  User, 
  Bell, 
  Shield, 
  HelpCircle, 
  ChevronRight,
  LogOut,
  Moon,
  Globe
} from 'lucide-react-native';

export default function ProfileScreen() {
  const [darkMode, setDarkMode] = React.useState(false);
  const [notifications, setNotifications] = React.useState(true);

  const menuItems = [
    { icon: User, label: 'Account Settings', color: '#6366f1' },
    { icon: Bell, label: 'Notifications', color: '#f59e0b' },
    { icon: Shield, label: 'Privacy & Security', color: '#22c55e' },
    { icon: Globe, label: 'Language', value: 'English', color: '#3b82f6' },
    { icon: HelpCircle, label: 'Help & Support', color: '#8b5cf6' },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView}>
        {/* Profile Header */}
        <View style={styles.profileHeader}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>JD</Text>
          </View>
          <Text style={styles.name}>John Doe</Text>
          <Text style={styles.email}>john@example.com</Text>
          <TouchableOpacity style={styles.editButton}>
            <Text style={styles.editButtonText}>Edit Profile</Text>
          </TouchableOpacity>
        </View>

        {/* Stats */}
        <View style={styles.statsContainer}>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>156</Text>
            <Text style={styles.statLabel}>Calls</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>12h</Text>
            <Text style={styles.statLabel}>AI Hours</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>98%</Text>
            <Text style={styles.statLabel}>Satisfaction</Text>
          </View>
        </View>

        {/* Preferences */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Preferences</Text>
          
          <View style={styles.preferenceRow}>
            <View style={styles.preferenceInfo}>
              <Moon size={20} color="#6b7280" />
              <Text style={styles.preferenceLabel}>Dark Mode</Text>
            </View>
            <Switch
              value={darkMode}
              onValueChange={setDarkMode}
              trackColor={{ false: '#d1d5db', true: '#6366f1' }}
            />
          </View>

          <View style={styles.preferenceRow}>
            <View style={styles.preferenceInfo}>
              <Bell size={20} color="#6b7280" />
              <Text style={styles.preferenceLabel}>Push Notifications</Text>
            </View>
            <Switch
              value={notifications}
              onValueChange={setNotifications}
              trackColor={{ false: '#d1d5db', true: '#6366f1' }}
            />
          </View>
        </View>

        {/* Menu Items */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Settings</Text>
          
          {menuItems.map((item, index) => (
            <TouchableOpacity key={index} style={styles.menuItem}>
              <View style={[styles.menuIcon, { backgroundColor: `${item.color}15` }]}>
                <item.icon size={20} color={item.color} />
              </View>
              <Text style={styles.menuLabel}>{item.label}</Text>
              {item.value ? (
                <Text style={styles.menuValue}>{item.value}</Text>
              ) : null}
              <ChevronRight size={20} color="#d1d5db" />
            </TouchableOpacity>
          ))}
        </View>

        {/* App Info */}
        <View style={styles.appInfo}>
          <Text style={styles.appVersion}>Avatario AI v1.0.0</Text>
          <Text style={styles.appBuild}>Build 2024.5.1</Text>
        </View>

        {/* Logout */}
        <TouchableOpacity style={styles.logoutButton}>
          <LogOut size={20} color="#ef4444" />
          <Text style={styles.logoutText}>Sign Out</Text>
        </TouchableOpacity>
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
  profileHeader: {
    backgroundColor: '#ffffff',
    alignItems: 'center',
    padding: 24,
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#6366f1',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatarText: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  email: {
    fontSize: 16,
    color: '#6b7280',
    marginTop: 4,
  },
  editButton: {
    marginTop: 16,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: '#f3f4f6',
  },
  editButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  statsContainer: {
    flexDirection: 'row',
    backgroundColor: '#ffffff',
    padding: 24,
    marginTop: 1,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statDivider: {
    width: 1,
    backgroundColor: '#e5e7eb',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  statLabel: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 4,
  },
  section: {
    backgroundColor: '#ffffff',
    marginTop: 16,
    paddingVertical: 8,
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
  preferenceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  preferenceInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  preferenceLabel: {
    fontSize: 16,
    color: '#374151',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  menuIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  menuLabel: {
    flex: 1,
    fontSize: 16,
    color: '#374151',
    marginLeft: 12,
  },
  menuValue: {
    fontSize: 14,
    color: '#9ca3af',
    marginRight: 8,
  },
  appInfo: {
    alignItems: 'center',
    padding: 24,
  },
  appVersion: {
    fontSize: 14,
    color: '#6b7280',
  },
  appBuild: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 4,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ffffff',
    marginHorizontal: 16,
    marginVertical: 16,
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  logoutText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ef4444',
  },
});
