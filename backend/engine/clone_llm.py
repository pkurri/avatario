"""
Clone LLM Engine - Create an AI clone of a person
Learns from documents, emails, chat history to mimic personality and communication style
"""
import os
import uuid
import asyncio
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import hashlib

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter


class CloneStatus(str, Enum):
    CREATED = "created"
    INDEXING = "indexing"
    TRAINING = "training"
    READY = "ready"
    ERROR = "error"


@dataclass
class UserProfile:
    """User profile containing personal information"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    expertise: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    communication_style: Optional[str] = None  # formal, casual, friendly, professional
    tone_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CloneLLMConfig:
    """Configuration for Clone LLM"""
    clone_id: str
    user_id: str
    model_name: str = "gpt-4o"  # Can use any LiteLLM supported model
    embedding_model: str = "text-embedding-3-large"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    temperature: float = 0.7
    max_tokens: int = 1000
    top_k_retrieval: int = 5
    status: CloneStatus = CloneStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ConversationMemory:
    """Memory of past conversations"""
    messages: List[Dict] = field(default_factory=list)
    max_history: int = 20
    
    def add_exchange(self, user_message: str, ai_response: str, metadata: Optional[Dict] = None):
        """Add a conversation exchange"""
        self.messages.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "ai": ai_response,
            "metadata": metadata or {}
        })
        
        # Keep only recent history
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_context(self, last_n: int = 5) -> str:
        """Get recent conversation context"""
        recent = self.messages[-last_n:] if self.messages else []
        context_parts = []
        for msg in recent:
            context_parts.append(f"User: {msg['user']}")
            context_parts.append(f"AI: {msg['ai']}")
        return "\n".join(context_parts)


@dataclass
class PersonalityTraits:
    """Analyzed personality traits from user data"""
    formality_level: float = 0.5  # 0-1, 0=casual, 1=formal
    enthusiasm_level: float = 0.5  # 0-1, 0=calm, 1=enthusiastic
    humor_level: float = 0.3  # 0-1, likelihood of using humor
    emoji_usage: bool = False
    greeting_style: str = "standard"  # standard, enthusiastic, professional
    response_length_preference: str = "medium"  # short, medium, detailed
    common_phrases: List[str] = field(default_factory=list)
    vocabulary_style: str = "standard"  # simple, technical, academic
    question_style: str = "direct"  # direct, contextual, elaborate


class CloneLLMEngine:
    """
    Engine for creating AI clones that mimic a person's personality and knowledge
    """
    
    def __init__(self):
        self.clones: Dict[str, CloneLLMConfig] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        self.memories: Dict[str, ConversationMemory] = {}
        self.personality_profiles: Dict[str, PersonalityTraits] = {}
        self.vector_stores: Dict[str, VectorStore] = {}
        self.documents: Dict[str, List[Document]] = {}
        
        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    async def create_clone(
        self,
        user_id: str,
        model_name: str = "gpt-4o",
        user_profile: Optional[UserProfile] = None
    ) -> str:
        """Create a new AI clone for a user"""
        clone_id = str(uuid.uuid4())
        
        config = CloneLLMConfig(
            clone_id=clone_id,
            user_id=user_id,
            model_name=model_name
        )
        
        self.clones[clone_id] = config
        self.user_profiles[clone_id] = user_profile or UserProfile(name="User")
        self.memories[clone_id] = ConversationMemory()
        self.personality_profiles[clone_id] = PersonalityTraits()
        self.documents[clone_id] = []
        
        return clone_id
    
    async def ingest_documents(
        self,
        clone_id: str,
        documents: List[Document],
        source_type: str = "unknown"
    ) -> Dict[str, Any]:
        """Ingest documents to train the clone"""
        if clone_id not in self.clones:
            raise ValueError(f"Clone {clone_id} not found")
        
        config = self.clones[clone_id]
        config.status = CloneStatus.INDEXING
        
        try:
            # Add metadata to documents
            for doc in documents:
                doc.metadata["source_type"] = source_type
                doc.metadata["ingested_at"] = datetime.now().isoformat()
                doc.metadata["clone_id"] = clone_id
            
            # Split documents into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            # Add to document store
            if clone_id not in self.documents:
                self.documents[clone_id] = []
            self.documents[clone_id].extend(chunks)
            
            # Create embeddings and store in vector DB
            await self._create_vector_store(clone_id, chunks)
            
            # Analyze personality from documents
            await self._analyze_personality(clone_id, documents)
            
            config.status = CloneStatus.READY
            config.updated_at = datetime.now()
            
            return {
                "clone_id": clone_id,
                "documents_ingested": len(documents),
                "chunks_created": len(chunks),
                "status": config.status.value,
                "message": "Documents ingested successfully"
            }
            
        except Exception as e:
            config.status = CloneStatus.ERROR
            raise Exception(f"Failed to ingest documents: {str(e)}")
    
    async def _create_vector_store(self, clone_id: str, chunks: List[Document]):
        """Create vector store for RAG"""
        try:
            # Use in-memory store for now (can be replaced with Chroma, Pinecone, etc.)
            from langchain_community.vectorstores import FAISS
            from langchain_openai import OpenAIEmbeddings
            
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-large",
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
            
            # Create or update vector store
            if clone_id in self.vector_stores:
                # Add to existing store
                self.vector_stores[clone_id].add_documents(chunks)
            else:
                # Create new store
                self.vector_stores[clone_id] = FAISS.from_documents(
                    chunks, embeddings
                )
            
        except Exception as e:
            print(f"[CloneLLM] Vector store creation failed: {e}")
            # Continue without vector store - will use documents directly
    
    async def _analyze_personality(self, clone_id: str, documents: List[Document]):
        """Analyze user's personality from documents"""
        # Combine all text
        all_text = " ".join([doc.page_content for doc in documents[:10]])  # First 10 docs
        
        # Simple heuristic analysis (can be replaced with LLM-based analysis)
        text_lower = all_text.lower()
        
        traits = self.personality_profiles[clone_id]
        
        # Analyze formality
        formal_words = ["dear", "sincerely", "regards", "professional", "business"]
        casual_words = ["hey", "hi", "thanks", "cool", "awesome", "lol"]
        
        formal_count = sum(1 for w in formal_words if w in text_lower)
        casual_count = sum(1 for w in casual_words if w in text_lower)
        
        if formal_count > casual_count:
            traits.formality_level = 0.7
            traits.greeting_style = "professional"
        elif casual_count > formal_count:
            traits.formality_level = 0.3
            traits.greeting_style = "enthusiastic"
        
        # Analyze emoji usage
        emojis = ["😊", "👍", "🎉", "😂", "❤️", "🔥", "👋", "🙏"]
        emoji_count = sum(1 for e in emojis if e in all_text)
        traits.emoji_usage = emoji_count > 0
        
        # Analyze response length preference
        avg_length = sum(len(doc.page_content) for doc in documents[:5]) / 5
        if avg_length < 200:
            traits.response_length_preference = "short"
        elif avg_length < 500:
            traits.response_length_preference = "medium"
        else:
            traits.response_length_preference = "detailed"
        
        # Extract common phrases (simple approach)
        import re
        sentences = re.split(r'[.!?]+', all_text)
        phrase_candidates = [s.strip() for s in sentences if 20 < len(s.strip()) < 100]
        traits.common_phrases = phrase_candidates[:5] if phrase_candidates else []
    
    def _build_system_prompt(
        self,
        clone_id: str,
        include_memory: bool = True
    ) -> str:
        """Build system prompt based on user profile and personality"""
        profile = self.user_profiles.get(clone_id, UserProfile(name="User"))
        traits = self.personality_profiles.get(clone_id, PersonalityTraits())
        
        # Base system prompt
        system_parts = [
            f"You are an AI assistant representing {profile.name}.",
            f"Your goal is to communicate in {profile.name}'s style and provide helpful responses based on their knowledge and expertise.",
            "",
            "PERSONALITY GUIDELINES:",
        ]
        
        # Add formality guidance
        if traits.formality_level > 0.6:
            system_parts.append("- Use professional, formal language")
        elif traits.formality_level < 0.4:
            system_parts.append("- Use casual, conversational language")
        else:
            system_parts.append("- Use balanced, friendly professional language")
        
        # Add enthusiasm
        if traits.enthusiasm_level > 0.6:
            system_parts.append("- Show enthusiasm and energy in responses")
        else:
            system_parts.append("- Keep responses calm and measured")
        
        # Add emoji guidance
        if traits.emoji_usage:
            system_parts.append("- Use appropriate emojis occasionally")
        
        # Add response length guidance
        if traits.response_length_preference == "short":
            system_parts.append("- Keep responses brief and to the point")
        elif traits.response_length_preference == "detailed":
            system_parts.append("- Provide comprehensive, detailed responses")
        else:
            system_parts.append("- Provide balanced, medium-length responses")
        
        # Add user info
        if profile.job_title:
            system_parts.append(f"\nJob: {profile.job_title}")
        if profile.company:
            system_parts.append(f"Company: {profile.company}")
        if profile.expertise:
            system_parts.append(f"Areas of expertise: {', '.join(profile.expertise)}")
        
        return "\n".join(system_parts)
    
    async def generate_response(
        self,
        clone_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        stream: bool = False
    ) -> str:
        """Generate a response mimicking the user's style"""
        if clone_id not in self.clones:
            raise ValueError(f"Clone {clone_id} not found")
        
        config = self.clones[clone_id]
        
        if config.status != CloneStatus.READY:
            return f"I'm still learning about {self.user_profiles[clone_id].name}. Please try again in a moment."
        
        try:
            # Retrieve relevant context
            context = await self._retrieve_context(clone_id, message)
            
            # Get conversation memory
            memory_context = ""
            if clone_id in self.memories:
                memory_context = self.memories[clone_id].get_context(last_n=5)
            
            # Build system prompt
            system_prompt = self._build_system_prompt(clone_id)
            
            # Build full prompt
            messages = [
                SystemMessage(content=system_prompt),
            ]
            
            if context:
                messages.append(SystemMessage(content=f"Relevant information:\n{context}"))
            
            if memory_context:
                messages.append(SystemMessage(content=f"Recent conversation:\n{memory_context}"))
            
            messages.append(HumanMessage(content=message))
            
            # Generate response using LiteLLM
            from litellm import acompletion
            
            response = await acompletion(
                model=config.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context: {context}\n\nPrevious conversation: {memory_context}\n\nUser message: {message}"}
                ],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=os.getenv("OPENAI_API_KEY") if "gpt" in config.model_name else None
            )
            
            ai_response = response.choices[0].message.content
            
            # Store in memory
            if clone_id in self.memories:
                self.memories[clone_id].add_exchange(message, ai_response)
            
            return ai_response
            
        except Exception as e:
            print(f"[CloneLLM] Response generation failed: {e}")
            return "I'm having trouble accessing my knowledge right now. Could you try again?"
    
    async def _retrieve_context(self, clone_id: str, query: str) -> str:
        """Retrieve relevant context from vector store"""
        if clone_id not in self.vector_stores:
            # Fall back to simple document matching
            docs = self.documents.get(clone_id, [])
            if not docs:
                return ""
            
            # Simple keyword matching
            query_words = set(query.lower().split())
            relevant_docs = []
            
            for doc in docs[:20]:  # Check first 20 docs
                doc_words = set(doc.page_content.lower().split())
                overlap = len(query_words & doc_words)
                if overlap > 0:
                    relevant_docs.append((overlap, doc))
            
            # Sort by relevance and take top 3
            relevant_docs.sort(reverse=True)
            top_docs = [doc for _, doc in relevant_docs[:3]]
            
            return "\n\n".join([doc.page_content for doc in top_docs])
        
        # Use vector store retrieval
        try:
            results = self.vector_stores[clone_id].similarity_search(
                query, 
                k=self.clones[clone_id].top_k_retrieval
            )
            return "\n\n".join([doc.page_content for doc in results])
        except Exception as e:
            print(f"[CloneLLM] Retrieval failed: {e}")
            return ""
    
    async def ingest_chat_history(
        self,
        clone_id: str,
        chat_history: List[Dict[str, str]],
        platform: str = "unknown"
    ) -> Dict[str, Any]:
        """Ingest chat history to learn communication style"""
        documents = []
        
        for chat in chat_history:
            content = chat.get("content", "")
            sender = chat.get("sender", "unknown")
            
            # Create document from chat
            doc = Document(
                page_content=f"[{sender}]: {content}",
                metadata={
                    "platform": platform,
                    "sender": sender,
                    "type": "chat_message"
                }
            )
            documents.append(doc)
        
        return await self.ingest_documents(clone_id, documents, f"chat_{platform}")
    
    async def ingest_email(
        self,
        clone_id: str,
        emails: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Ingest emails to learn communication style"""
        documents = []
        
        for email in emails:
            subject = email.get("subject", "")
            body = email.get("body", "")
            from_addr = email.get("from", "")
            
            # Create document from email
            content = f"Subject: {subject}\n\n{body}"
            doc = Document(
                page_content=content,
                metadata={
                    "type": "email",
                    "from": from_addr,
                    "subject": subject
                }
            )
            documents.append(doc)
        
        return await self.ingest_documents(clone_id, documents, "email")
    
    def get_clone_info(self, clone_id: str) -> Dict[str, Any]:
        """Get information about a clone"""
        if clone_id not in self.clones:
            return {"error": "Clone not found"}
        
        config = self.clones[clone_id]
        profile = self.user_profiles.get(clone_id, UserProfile(name="Unknown"))
        traits = self.personality_profiles.get(clone_id, PersonalityTraits())
        
        return {
            "clone_id": clone_id,
            "user_id": config.user_id,
            "status": config.status.value,
            "model": config.model_name,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
            "documents_count": len(self.documents.get(clone_id, [])),
            "profile": {
                "name": profile.name,
                "job_title": profile.job_title,
                "company": profile.company,
                "expertise": profile.expertise
            },
            "personality": {
                "formality_level": traits.formality_level,
                "enthusiasm_level": traits.enthusiasm_level,
                "emoji_usage": traits.emoji_usage,
                "response_length": traits.response_length_preference,
                "greeting_style": traits.greeting_style
            }
        }
    
    def delete_clone(self, clone_id: str) -> bool:
        """Delete a clone and all associated data"""
        if clone_id not in self.clones:
            return False
        
        del self.clones[clone_id]
        if clone_id in self.user_profiles:
            del self.user_profiles[clone_id]
        if clone_id in self.memories:
            del self.memories[clone_id]
        if clone_id in self.personality_profiles:
            del self.personality_profiles[clone_id]
        if clone_id in self.vector_stores:
            del self.vector_stores[clone_id]
        if clone_id in self.documents:
            del self.documents[clone_id]
        
        return True


# Global instance
clone_llm_engine = CloneLLMEngine()
