"""
Supabase Client Wrapper for AIZEN
=================================
Initializes the Supabase client and provides access to it.
"""
import logging
from typing import Optional
from supabase import create_client, Client
from app.config import get_settings

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None

def get_supabase_client() -> Optional[Client]:
    """Get or initialize the Supabase client."""
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
        
    settings = get_settings()
    
    if not settings.supabase_url or not settings.supabase_key:
        logger.warning("Supabase URL or Key not set. Cloud features will be disabled.")
        return None
        
    try:
        _supabase_client = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("Supabase client initialized successfully.")
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None
