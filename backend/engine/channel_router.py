"""
Channel Router - Unified Inbox for Multi-Channel Support
Routes messages between WhatsApp, Phone, Web Widget, and other channels
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid
import asyncio

class Channel(Enum):
    WHATSAPP = "whatsapp"
    PHONE = "phone"
    WEB_WIDGET = "web_widget"
    SMS = "sms"
    EMAIL = "email"
    TELEGRAM = "telegram"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"

class MessageType(Enum):
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"

@dataclass
class Message:
    id: str
    channel: Channel
    direction: str  # "inbound" or "outbound"
    sender_id: str  # phone number, widget_id, etc.
    recipient_id: str
    message_type: MessageType
    content: str
    media_url: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    conversation_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    read: bool = False
    delivered: bool = False

@dataclass
class Conversation:
    id: str
    channel: Channel
    customer_id: str  # phone number or widget user id
    business_id: str
    persona_id: str = "anya"
    messages: List[Message] = field(default_factory=list)
    status: str = "active"  # active, closed, waiting
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_message_at: Optional[str] = None
    assigned_to: Optional[str] = None  # human agent ID if escalated
    priority: str = "normal"  # low, normal, high, urgent
    tags: List[str] = field(default_factory=list)
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None

class ChannelRouter:
    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
        self.messages: Dict[str, Message] = {}
        self.channel_handlers: Dict[Channel, Any] = {}
        self.message_callbacks: List[Callable] = []
        self.conversation_callbacks: List[Callable] = []
        
        # Channel statistics
        self.channel_stats: Dict[Channel, Dict] = {
            channel: {"total": 0, "today": 0, "active": 0}
            for channel in Channel
        }
    
    def register_channel_handler(self, channel: Channel, handler: Any):
        """Register a handler for a specific channel"""
        self.channel_handlers[channel] = handler
    
    def on_message(self, callback: Callable[[Message], None]):
        """Register a callback for new messages"""
        self.message_callbacks.append(callback)
    
    def on_conversation_update(self, callback: Callable[[Conversation], None]):
        """Register a callback for conversation updates"""
        self.conversation_callbacks.append(callback)
    
    def route_inbound_message(
        self,
        channel: Channel,
        sender_id: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        media_url: Optional[str] = None,
        metadata: Optional[Dict] = None,
        recipient_id: Optional[str] = None
    ) -> Message:
        """Route an inbound message to the appropriate conversation"""
        
        # Find or create conversation
        conversation = self._find_or_create_conversation(
            channel=channel,
            customer_id=sender_id,
            business_id=recipient_id or "default",
            metadata=metadata
        )
        
        # Create message
        message_id = f"MSG_{uuid.uuid4().hex[:16]}"
        message = Message(
            id=message_id,
            channel=channel,
            direction="inbound",
            sender_id=sender_id,
            recipient_id=recipient_id or "default",
            message_type=message_type,
            content=content,
            media_url=media_url,
            conversation_id=conversation.id,
            metadata=metadata or {}
        )
        
        # Store message
        self.messages[message_id] = message
        conversation.messages.append(message)
        conversation.last_message_at = message.timestamp
        conversation.updated_at = message.timestamp
        
        # Update stats
        self.channel_stats[channel]["total"] += 1
        self.channel_stats[channel]["today"] += 1
        
        # Notify callbacks
        for callback in self.message_callbacks:
            try:
                asyncio.create_task(callback(message))
            except:
                pass
        
        for callback in self.conversation_callbacks:
            try:
                asyncio.create_task(callback(conversation))
            except:
                pass
        
        return message
    
    def route_outbound_message(
        self,
        conversation_id: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        media_url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Message]:
        """Route an outbound message through the appropriate channel"""
        
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return None
        
        # Create message
        message_id = f"MSG_{uuid.uuid4().hex[:16]}"
        message = Message(
            id=message_id,
            channel=conversation.channel,
            direction="outbound",
            sender_id=conversation.business_id,
            recipient_id=conversation.customer_id,
            message_type=message_type,
            content=content,
            media_url=media_url,
            conversation_id=conversation_id,
            metadata=metadata or {}
        )
        
        # Store message
        self.messages[message_id] = message
        conversation.messages.append(message)
        conversation.last_message_at = message.timestamp
        conversation.updated_at = message.timestamp
        
        # Send through channel handler
        handler = self.channel_handlers.get(conversation.channel)
        if handler:
            try:
                asyncio.create_task(
                    handler.send_message(
                        recipient=conversation.customer_id,
                        content=content,
                        media_url=media_url,
                        message_type=message_type
                    )
                )
                message.delivered = True
            except Exception as e:
                print(f"[ChannelRouter] Failed to send via {conversation.channel}: {e}")
        
        return message
    
    def _find_or_create_conversation(
        self,
        channel: Channel,
        customer_id: str,
        business_id: str,
        metadata: Optional[Dict] = None
    ) -> Conversation:
        """Find existing conversation or create new one"""
        
        # Look for active conversation
        for conv in self.conversations.values():
            if (conv.channel == channel and 
                conv.customer_id == customer_id and 
                conv.business_id == business_id and
                conv.status == "active"):
                return conv
        
        # Create new conversation
        conversation_id = f"CONV_{uuid.uuid4().hex[:12]}"
        conversation = Conversation(
            id=conversation_id,
            channel=channel,
            customer_id=customer_id,
            business_id=business_id,
            persona_id=metadata.get("persona_id", "anya") if metadata else "anya",
            customer_name=metadata.get("customer_name") if metadata else None,
            customer_email=metadata.get("customer_email") if metadata else None,
            tags=metadata.get("tags", []) if metadata else []
        )
        
        self.conversations[conversation_id] = conversation
        self.channel_stats[channel]["active"] += 1
        
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.conversations.get(conversation_id)
    
    def list_conversations(
        self,
        channel: Optional[Channel] = None,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        business_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Conversation]:
        """List conversations with filters"""
        conversations = list(self.conversations.values())
        
        if channel:
            conversations = [c for c in conversations if c.channel == channel]
        
        if status:
            conversations = [c for c in conversations if c.status == status]
        
        if assigned_to:
            conversations = [c for c in conversations if c.assigned_to == assigned_to]
        
        if business_id:
            conversations = [c for c in conversations if c.business_id == business_id]
        
        # Sort by last message time (newest first)
        conversations.sort(
            key=lambda c: c.last_message_at or c.created_at,
            reverse=True
        )
        
        return conversations[offset:offset + limit]
    
    def close_conversation(self, conversation_id: str, reason: str = "") -> bool:
        """Close a conversation"""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return False
        
        conversation.status = "closed"
        conversation.updated_at = datetime.utcnow().isoformat()
        
        # Update stats
        if conversation.channel in self.channel_stats:
            self.channel_stats[conversation.channel]["active"] -= 1
        
        return True
    
    def assign_conversation(
        self,
        conversation_id: str,
        agent_id: str,
        priority: Optional[str] = None
    ) -> bool:
        """Assign conversation to a human agent"""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return False
        
        conversation.assigned_to = agent_id
        if priority:
            conversation.priority = priority
        
        conversation.updated_at = datetime.utcnow().isoformat()
        
        return True
    
    def add_conversation_tag(self, conversation_id: str, tag: str) -> bool:
        """Add a tag to a conversation"""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return False
        
        if tag not in conversation.tags:
            conversation.tags.append(tag)
        
        return True
    
    def get_conversation_history(
        self,
        conversation_id: str,
        message_limit: int = 100
    ) -> Optional[Dict]:
        """Get full conversation history"""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return None
        
        messages = conversation.messages[-message_limit:]
        
        return {
            "conversation": conversation,
            "messages": messages,
            "total_messages": len(conversation.messages)
        }
    
    def get_unified_inbox(
        self,
        business_id: Optional[str] = None,
        show_closed: bool = False,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get unified inbox view across all channels"""
        
        # Get all conversations
        conversations = list(self.conversations.values())
        
        if business_id:
            conversations = [c for c in conversations if c.business_id == business_id]
        
        if not show_closed:
            conversations = [c for c in conversations if c.status != "closed"]
        
        # Organize by channel
        inbox = {
            "all": [],
            "channels": {}
        }
        
        for channel in Channel:
            channel_conversations = [c for c in conversations if c.channel == channel]
            
            # Sort by priority and time
            channel_conversations.sort(
                key=lambda c: (
                    {"urgent": 0, "high": 1, "normal": 2, "low": 3}.get(c.priority, 2),
                    c.last_message_at or c.created_at
                ),
                reverse=True
            )
            
            inbox["channels"][channel.value] = {
                "total": len(channel_conversations),
                "conversations": channel_conversations,
                "unread": len([c for c in channel_conversations if any(not m.read for m in c.messages)])
            }
            
            inbox["all"].extend(channel_conversations)
        
        # Sort all conversations
        inbox["all"].sort(
            key=lambda c: c.last_message_at or c.created_at,
            reverse=True
        )
        
        inbox["all"] = inbox["all"][:limit]
        inbox["total"] = len(conversations)
        inbox["active"] = len([c for c in conversations if c.status == "active"])
        inbox["waiting"] = len([c for c in conversations if c.status == "waiting"])
        inbox["escalated"] = len([c for c in conversations if c.assigned_to])
        
        return inbox
    
    def get_channel_stats(self) -> Dict[str, Any]:
        """Get statistics for all channels"""
        return {
            channel.value: stats
            for channel, stats in self.channel_stats.items()
        }
    
    def search_conversations(
        self,
        query: str,
        business_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Conversation]:
        """Search conversations by content"""
        results = []
        query_lower = query.lower()
        
        for conversation in self.conversations.values():
            if business_id and conversation.business_id != business_id:
                continue
            
            # Search in messages
            for message in conversation.messages:
                if query_lower in message.content.lower():
                    results.append(conversation)
                    break
            
            # Search in customer info
            if conversation.customer_name and query_lower in conversation.customer_name.lower():
                if conversation not in results:
                    results.append(conversation)
        
        return results[:limit]
    
    def merge_conversations(
        self,
        primary_id: str,
        secondary_id: str
    ) -> Optional[Conversation]:
        """Merge two conversations into one"""
        primary = self.conversations.get(primary_id)
        secondary = self.conversations.get(secondary_id)
        
        if not primary or not secondary:
            return None
        
        # Merge messages
        all_messages = primary.messages + secondary.messages
        all_messages.sort(key=lambda m: m.timestamp)
        
        primary.messages = all_messages
        primary.updated_at = datetime.utcnow().isoformat()
        
        # Merge tags
        primary.tags = list(set(primary.tags + secondary.tags))
        
        # Mark secondary as merged
        secondary.status = "merged"
        secondary.metadata["merged_into"] = primary_id
        
        return primary


# Global channel router instance
channel_router = ChannelRouter()


def get_channel_router() -> ChannelRouter:
    """Get the global channel router instance"""
    return channel_router


# Example usage and testing
async def test_channel_router():
    """Test the channel router"""
    router = ChannelRouter()
    
    # Simulate incoming WhatsApp message
    print("Simulating WhatsApp message...")
    msg1 = router.route_inbound_message(
        channel=Channel.WHATSAPP,
        sender_id="+919876543210",
        content="Hello, I need help with booking an appointment",
        metadata={"customer_name": "John Doe", "persona_id": "anya"}
    )
    print(f"Created message: {msg1.id} in conversation {msg1.conversation_id}")
    
    # Simulate phone call
    print("\nSimulating phone call...")
    msg2 = router.route_inbound_message(
        channel=Channel.PHONE,
        sender_id="+919876543210",
        content="Voice call started",
        message_type=MessageType.AUDIO,
        metadata={"call_sid": "CALL123"}
    )
    print(f"Created message: {msg2.id} in conversation {msg2.conversation_id}")
    
    # Get unified inbox
    print("\nUnified Inbox:")
    inbox = router.get_unified_inbox()
    print(f"Total conversations: {inbox['total']}")
    print(f"Active: {inbox['active']}, Waiting: {inbox['waiting']}, Escalated: {inbox['escalated']}")
    
    for channel_name, data in inbox['channels'].items():
        print(f"  {channel_name}: {data['total']} conversations, {data['unread']} unread")
    
    # List all conversations
    print("\nAll Conversations:")
    conversations = router.list_conversations()
    for conv in conversations:
        print(f"  - {conv.id} ({conv.channel.value}): {conv.customer_id}")
        print(f"    Messages: {len(conv.messages)}")
        print(f"    Status: {conv.status}")
    
    # Send outbound response
    print("\nSending outbound response...")
    response_msg = router.route_outbound_message(
        conversation_id=msg1.conversation_id,
        content="Hello! I'd be happy to help you book an appointment. What service do you need?"
    )
    print(f"Sent response: {response_msg.id if response_msg else 'Failed'}")
    
    # Get channel stats
    print("\nChannel Statistics:")
    stats = router.get_channel_stats()
    for channel, channel_stats in stats.items():
        print(f"  {channel}: {channel_stats}")


if __name__ == "__main__":
    asyncio.run(test_channel_router())
