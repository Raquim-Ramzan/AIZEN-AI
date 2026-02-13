"""
Cloud Conversation Manager
==========================
Manages conversation history using Supabase Postgres tables.
Replaces the old SQLite implementation.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
import uuid

from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manage conversations using Supabase"""
    
    def __init__(self):
        self.client = None
    
    async def initialize(self):
        """Initialize Supabase client connection"""
        self.client = get_supabase_client()
        if not self.client:
            logger.error("Supabase client not initialized. Conversations will not be saved.")
        else:
            logger.info("Cloud Conversation Manager initialized")
    
    async def create_conversation(self, user_id: str, title: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new conversation"""
        if not self.client: return str(uuid.uuid4())
            
        conversation_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        try:
            self.client.table("conversations").insert({
                "id": conversation_id,
                "user_id": user_id,
                "title": title,
                "metadata": metadata or {},
                "created_at": now,
                "updated_at": now
            }).execute()
            
            logger.info(f"Created conversation {conversation_id} for user {user_id}")
            return conversation_id
        except Exception as e:
            logger.error(f"Create conversation error: {e}")
            return conversation_id
    
    async def get_conversations(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all conversations for a user"""
        if not self.client: return []
            
        try:
            response = self.client.table("conversations").select("*").eq("user_id", user_id).order("updated_at", desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"Get conversations error: {e}")
            return []
    
    async def get_conversation(self, user_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific conversation"""
        if not self.client: return None
            
        try:
            response = self.client.table("conversations").select("*").eq("user_id", user_id).eq("id", conversation_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Get conversation error: {e}")
            return None
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Add a message to a conversation"""
        if not self.client: return str(uuid.uuid4())
            
        message_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # Merge tool_calls into metadata if needed, since messages schema doesn't have a dedicated tool_calls column in our migration,
        # but wait, the prompt for messages schema: id, conversation_id, role, content, created_at. 
        # I'll just append it to the content or ignore tool calls storage for now as it's typically volatile,
        # or we could alter the messages schema. Let's stick to the prompt schema.
        try:
            self.client.table("messages").insert({
                "id": message_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "created_at": now
            }).execute()
            
            # Update conversation timestamp
            self.client.table("conversations").update({
                "updated_at": now
            }).eq("id", conversation_id).execute()
            
            return message_id
        except Exception as e:
            logger.error(f"Add message error: {e}")
            return message_id
    
    async def get_messages(self, conversation_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages from a conversation"""
        if not self.client: return []
            
        try:
            response = self.client.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"Get messages error: {e}")
            return []
    
    async def delete_conversation(self, user_id: str, conversation_id: str):
        """Delete a conversation"""
        if not self.client: return
        try:
            # RLS or foreign key cascading will handle messages deletion if setup properly. 
            # In our schema ON DELETE CASCADE is present for messages.
            self.client.table("conversations").delete().eq("user_id", user_id).eq("id", conversation_id).execute()
            logger.info(f"Deleted conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Delete conversation error: {e}")
    
    async def update_conversation_title(self, user_id: str, conversation_id: str, title: str) -> bool:
        """Update conversation title."""
        if not self.client: return False
        try:
            now = datetime.now(timezone.utc).isoformat()
            response = self.client.table("conversations").update({
                "title": title,
                "updated_at": now
            }).eq("user_id", user_id).eq("id", conversation_id).execute()
            
            if response.data:
                logger.info(f"Updated conversation {conversation_id} title to: {title}")
                return True
            return False
        except Exception as e:
            logger.error(f"Update conversation error: {e}")
            return False


# Singleton instance
_conversation_manager: Optional["ConversationManager"] = None


def get_conversation_manager() -> "ConversationManager":
    """Get or create the ConversationManager singleton"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
