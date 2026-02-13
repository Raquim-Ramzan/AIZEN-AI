import asyncio
import os
import json
import logging
import sqlite3
from typing import Dict, Any, List
import uuid
import chromadb
from datetime import datetime, timezone
from pathlib import Path

# Set up environment and config
from dotenv import load_dotenv
load_dotenv()

from app.core.supabase import get_supabase_client
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default user ID for existing single-user local data
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000000"

async def migrate_core_memory(client):
    """Migrate core_memory.json to profiles and memories tables"""
    logger.info("Migrating core_memory.json...")
    memory_path = Path("data/core_memory.json")
    
    if not memory_path.exists():
        logger.warning(f"{memory_path} not found. Skipping.")
        return
        
    try:
        with open(memory_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Migrate identity to profiles table
        identity = data.get("identity", {})
        preferences = data.get("preferences", {})
        metadata = data.get("metadata", {})
        
        # Check if profile exists
        response = client.table("profiles").select("*").eq("id", DEFAULT_USER_ID).execute()
        if not response.data:
            logger.info("Creating default user profile...")
            client.table("profiles").insert({
                "id": DEFAULT_USER_ID,
                "display_name": identity.get("name", "Raquim"),
                "identity_facts": [identity] if identity else [],
                "preferences": preferences,
                "metadata": metadata
            }).execute()
        else:
            logger.info("Profile already exists, updating...")
            client.table("profiles").update({
                "display_name": identity.get("name", "Raquim"),
                "identity_facts": [identity] if identity else [],
                "preferences": preferences,
                "metadata": metadata
            }).eq("id", DEFAULT_USER_ID).execute()
            
        # Migrate core_facts to vector store
        core_facts = data.get("core_facts", [])
        for fact in core_facts:
            # We skip embedding here; the backend vector_store add_document method
            # handles it when we rebuild the index, or we can just let it be rebuilt
            pass
            
        logger.info("core_memory.json migration complete.")
    except Exception as e:
        logger.error(f"Error migrating core_memory: {e}")

async def migrate_conversations(client):
    """Migrate SQLite conversations to Supabase"""
    logger.info("Migrating conversations.db...")
    settings = get_settings()
    db_path = settings.sqlite_db
    
    if not os.path.exists(db_path):
        logger.warning(f"{db_path} not found. Skipping.")
        return
        
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Migrate conversations
        cursor.execute("SELECT * FROM conversations")
        conv_rows = cursor.fetchall()
        
        conv_data = []
        for row in conv_rows:
            conv_data.append({
                "id": row["id"],
                "user_id": DEFAULT_USER_ID,
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            })
            
        if conv_data:
            # Supabase upsert
            client.table("conversations").upsert(conv_data).execute()
            logger.info(f"Migrated {len(conv_data)} conversations.")
            
        # Migrate messages
        cursor.execute("SELECT * FROM messages")
        msg_rows = cursor.fetchall()
        
        msg_data = []
        for row in msg_rows:
            msg_data.append({
                "id": row["id"],
                "conversation_id": row["conversation_id"],
                "role": row["role"],
                "content": row["content"],
                "created_at": row["timestamp"]
            })
            
        if msg_data:
            # Chunking because Supabase might limit batch sizes
            chunk_size = 500
            for i in range(0, len(msg_data), chunk_size):
                chunk = msg_data[i:i + chunk_size]
                client.table("messages").upsert(chunk).execute()
            logger.info(f"Migrated {len(msg_data)} messages.")
            
        conn.close()
        logger.info("conversations.db migration complete.")
    except Exception as e:
        logger.error(f"Error migrating conversations: {e}")

async def rebuild_vector_index():
    """Trigger the rag_manager rebuild_vector_index method to populate Supabase memories from core memory"""
    logger.info("Rebuilding vector index from core memory to Supabase...")
    from app.memory.vector_store import get_vector_store
    from app.memory.core_memory import get_core_memory
    from app.memory.rag_manager import get_rag_manager
    
    vector_store = get_vector_store()
    core_memory = get_core_memory()
    rag_manager = get_rag_manager()
    rag_manager.set_dependencies(vector_store, core_memory, None)
    
    try:
        await vector_store.initialize()
        await core_memory.initialize()
        
        result = await rag_manager.rebuild_vector_index(DEFAULT_USER_ID)
        logger.info(f"Vector index rebuild result: {result}")
    except Exception as e:
        logger.error(f"Error rebuilding vector index: {e}")

async def migrate_storage(client):
    """Migrate local files to Supabase Storage"""
    logger.info("Migrating local files to Supabase Storage...")
    
    # Define bucket names
    files_bucket = "user_files"
    audio_bucket = "voice_previews"
    
    # Try to create buckets (ignore if they already exist)
    try:
        client.storage.create_bucket(files_bucket, options={"public": False})
        client.storage.create_bucket(audio_bucket, options={"public": True})
    except Exception as e:
        logger.info(f"Buckets might already exist: {e}")
        
    # Migrate data/user_files
    data_dir = Path("data/user_files")
    if data_dir.exists():
        for file_path in data_dir.rglob("*"):
            if file_path.is_file():
                try:
                    rel_path = file_path.relative_to(data_dir)
                    with open(file_path, "rb") as f:
                        client.storage.from_(files_bucket).upload(
                            path=f"{DEFAULT_USER_ID}/{rel_path}",
                            file=f,
                            file_options={"upsert": "true"}
                        )
                    logger.info(f"Uploaded file {rel_path}")
                except Exception as e:
                    logger.error(f"Error uploading {file_path}: {e}")
                    
    # Migrate voice_previews
    voice_dir = Path("voice_previews")
    if voice_dir.exists():
        for file_path in voice_dir.rglob("*"):
            if file_path.is_file():
                try:
                    rel_path = file_path.relative_to(voice_dir)
                    with open(file_path, "rb") as f:
                        client.storage.from_(audio_bucket).upload(
                            path=str(rel_path),
                            file=f,
                            file_options={"upsert": "true"}
                        )
                    logger.info(f"Uploaded audio {rel_path}")
                except Exception as e:
                    logger.error(f"Error uploading {file_path}: {e}")
                    
    logger.info("Storage migration complete.")

async def main():
    logger.info("Starting Aizen Cloud Migration...")
    
    client = get_supabase_client()
    if not client:
        logger.error("Failed to initialize Supabase client. Check SUPABASE_URL and SUPABASE_KEY in .env")
        return
        
    await migrate_core_memory(client)
    await migrate_conversations(client)
    await migrate_storage(client)
    await rebuild_vector_index()
    
    logger.info("Migration finished successfully.")

if __name__ == "__main__":
    asyncio.run(main())
