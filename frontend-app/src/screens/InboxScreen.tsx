import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Search, Phone, MessageCircle, ChevronRight } from 'lucide-react-native';

interface Conversation {
  id: string;
  contactName: string;
  phoneNumber: string;
  lastMessage: string;
  timestamp: Date;
  unread: number;
  channel: 'phone' | 'whatsapp' | 'widget' | 'sms';
  type: 'call' | 'message';
}

// Mock data
const mockConversations: Conversation[] = [
  {
    id: '1',
    contactName: 'John Smith',
    phoneNumber: '+1 555-0123',
    lastMessage: 'Appointment confirmed for tomorrow at 2 PM',
    timestamp: new Date(Date.now() - 1000 * 60 * 5), // 5 mins ago
    unread: 2,
    channel: 'phone',
    type: 'call',
  },
  {
    id: '2',
    contactName: 'Sarah Johnson',
    phoneNumber: '+1 555-0456',
    lastMessage: 'Thanks for the information!',
    timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30 mins ago
    unread: 0,
    channel: 'whatsapp',
    type: 'message',
  },
  {
    id: '3',
    contactName: 'Mike Davis',
    phoneNumber: '+1 555-0789',
    lastMessage: 'Voicemail: Please call me back about the quote',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
    unread: 1,
    channel: 'phone',
    type: 'call',
  },
  {
    id: '4',
    contactName: 'Website Visitor',
    phoneNumber: 'Web Widget',
    lastMessage: 'Can you tell me about pricing?',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 4), // 4 hours ago
    unread: 0,
    channel: 'widget',
    type: 'message',
  },
];

export default function InboxScreen() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'calls' | 'messages'>('all');

  const filteredConversations = mockConversations.filter((conv) => {
    const matchesSearch = 
      conv.contactName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conv.phoneNumber.includes(searchQuery);
    
    const matchesFilter = 
      selectedFilter === 'all' ||
      (selectedFilter === 'calls' && conv.type === 'call') ||
      (selectedFilter === 'messages' && conv.type === 'message');
    
    return matchesSearch && matchesFilter;
  });

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'phone': return <Phone size={16} color="#6b7280" />;
      case 'whatsapp': return <MessageCircle size={16} color="#22c55e" />;
      default: return <MessageCircle size={16} color="#6b7280" />;
    }
  };

  const renderItem = ({ item }: { item: Conversation }) => (
    <TouchableOpacity style={styles.conversationItem}>
      <View style={styles.avatar}>
        <Text style={styles.avatarText}>
          {item.contactName.charAt(0)}
        </Text>
      </View>
      
      <View style={styles.content}>
        <View style={styles.itemHeader}>
          <Text style={styles.name}>{item.contactName}</Text>
          <Text style={styles.time}>{formatTime(item.timestamp)}</Text>
        </View>
        
        <View style={styles.messageRow}>
          {getChannelIcon(item.channel)}
          <Text 
            style={[styles.message, item.unread > 0 && styles.unreadMessage]}
            numberOfLines={1}
          >
            {item.lastMessage}
          </Text>
        </View>
      </View>

      {item.unread > 0 && (
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{item.unread}</Text>
        </View>
      )}
      
      <ChevronRight size={20} color="#d1d5db" />
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Inbox</Text>
      </View>

      {/* Search */}
      <View style={styles.searchContainer}>
        <Search size={20} color="#9ca3af" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search conversations..."
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>

      {/* Filters */}
      <View style={styles.filters}>
        {(['all', 'calls', 'messages'] as const).map((filter) => (
          <TouchableOpacity
            key={filter}
            style={[
              styles.filterButton,
              selectedFilter === filter && styles.filterButtonActive,
            ]}
            onPress={() => setSelectedFilter(filter)}
          >
            <Text
              style={[
                styles.filterText,
                selectedFilter === filter && styles.filterTextActive,
              ]}
            >
              {filter.charAt(0).toUpperCase() + filter.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Conversation List */}
      <FlatList
        data={filteredConversations}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  header: {
    padding: 16,
    backgroundColor: '#ffffff',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#111827',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    marginHorizontal: 16,
    marginVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    height: 44,
    fontSize: 16,
    color: '#374151',
  },
  filters: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingBottom: 12,
    gap: 8,
  },
  filterButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  filterButtonActive: {
    backgroundColor: '#6366f1',
    borderColor: '#6366f1',
  },
  filterText: {
    fontSize: 14,
    color: '#6b7280',
    fontWeight: '500',
  },
  filterTextActive: {
    color: '#ffffff',
  },
  list: {
    padding: 16,
  },
  conversationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#6366f1',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  content: {
    flex: 1,
    marginLeft: 12,
    marginRight: 8,
  },
  itemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  name: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  time: {
    fontSize: 12,
    color: '#9ca3af',
  },
  messageRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  message: {
    flex: 1,
    fontSize: 14,
    color: '#6b7280',
  },
  unreadMessage: {
    color: '#374151',
    fontWeight: '500',
  },
  badge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#ef4444',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#ffffff',
  },
});
