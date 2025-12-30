from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.settings import settings
from utils.logger import logger
import json
from datetime import datetime, timedelta
from redis import Redis

engine = create_engine(settings.POSTGRES_DSN, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class MemoryService:
    """
    PostgreSQL-based conversation history storage
    
    Features:
    - Persistent storage (survives service restarts)
    - Automatic cleanup of old conversations (30 days)
    - Per-user conversation isolation
    """
    
    def __init__(self):
        self.redis = self._init_redis()
        self.redis_ttl = settings.REDIS_HISTORY_TTL_SECONDS
        self.redis_max_items = settings.REDIS_HISTORY_MAX_ITEMS
        self._ensure_table_exists()

    def _init_redis(self) -> Optional[Redis]:
        if not settings.REDIS_URL:
            return None
        try:
            client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
            client.ping()
            logger.info("[MemoryService] Redis cache enabled")
            return client
        except Exception as e:
            logger.warning(f"[MemoryService] Redis unavailable, cache disabled: {e}")
            return None

    def _redis_key(self, user_id: str) -> str:
        return f"conversation_history:{user_id}"

    def _cache_append(self, user_id: str, role: str, content: str):
        if not self.redis:
            return
        try:
            key = self._redis_key(user_id)
            payload = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.redis.rpush(key, json.dumps(payload))
            if self.redis_max_items > 0:
                self.redis.ltrim(key, -self.redis_max_items, -1)
            if self.redis_ttl > 0:
                self.redis.expire(key, self.redis_ttl)
        except Exception as e:
            logger.warning(f"[MemoryService] Redis cache append failed: {e}")

    def _cache_set(self, user_id: str, history: List[Dict[str, Any]]):
        if not self.redis:
            return
        try:
            key = self._redis_key(user_id)
            self.redis.delete(key)
            if not history:
                return
            for item in history:
                self.redis.rpush(key, json.dumps(item))
            if self.redis_ttl > 0:
                self.redis.expire(key, self.redis_ttl)
        except Exception as e:
            logger.warning(f"[MemoryService] Redis cache set failed: {e}")

    def _ensure_table_exists(self):
        """Create conversation_history table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS conversation_history (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'
        );
        
        CREATE INDEX IF NOT EXISTS idx_conversation_user_created 
        ON conversation_history(user_id, created_at DESC);
        """
        try:
            with SessionLocal() as session:
                session.execute(text(create_table_sql))
                session.commit()
                logger.info("[MemoryService] Conversation history table ready")
        except Exception as e:
            logger.error(f"[MemoryService] Table creation error: {e}")

    def add_message(self, user_id: str, role: str, content: str, metadata: dict = None):
        """Add a message to user's conversation history in PostgreSQL"""
        try:
            insert_sql = """
            INSERT INTO conversation_history (user_id, role, content, metadata)
            VALUES (:user_id, :role, :content, :metadata)
            """
            with SessionLocal() as session:
                session.execute(text(insert_sql), {
                    "user_id": user_id,
                    "role": role,
                    "content": content,
                    "metadata": json.dumps(metadata or {})
                })
                session.commit()
            self._cache_append(user_id, role, content)
        except Exception as e:
            logger.error(f"[MemoryService] Error adding message: {e}")

    def get_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get last N messages from user's conversation history"""
        if self.redis:
            try:
                key = self._redis_key(user_id)
                cached = self.redis.lrange(key, 0, -1)
                # print(f"[MemoryService] Redis key {key}")
                # print(f"cached: {cached}")
                if cached:
                    history = [json.loads(item) for item in cached]
                    # print(f"[MemoryService] Redis cached: {history}")
                    return history[-limit:] if limit else history
            except Exception as e:
                logger.warning(f"[MemoryService] Redis cache read failed: {e}")
        try:
            query_sql = """
            SELECT role, content, created_at, metadata
            FROM conversation_history
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit
            """
            with SessionLocal() as session:
                result = session.execute(text(query_sql), {
                    "user_id": user_id,
                    "limit": limit
                })
                rows = result.fetchall()
                
                # Reverse to get chronological order
                history = []
                for row in reversed(rows):
                    history.append({
                        "role": row[0],
                        "content": row[1],
                        "timestamp": row[2].isoformat() if row[2] else None
                    })
                self._cache_set(user_id, history[-self.redis_max_items:] if self.redis_max_items > 0 else history)
                return history
        except Exception as e:
            logger.error(f"[MemoryService] Error getting history: {e}")
            return []
    
    def clear_history(self, user_id: str):
        """Clear all conversation history for a user"""
        try:
            delete_sql = "DELETE FROM conversation_history WHERE user_id = :user_id"
            with SessionLocal() as session:
                session.execute(text(delete_sql), {"user_id": user_id})
                session.commit()
                logger.info(f"[MemoryService] Cleared history for user {user_id}")
            if self.redis:
                try:
                    self.redis.delete(self._redis_key(user_id))
                except Exception as e:
                    logger.warning(f"[MemoryService] Redis cache delete failed: {e}")
        except Exception as e:
            logger.error(f"[MemoryService] Error clearing history: {e}")
    
    def cleanup_old_conversations(self, days: int = 30):
        """
        Delete conversations older than specified days
        Call this periodically (e.g., daily cron job)
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            delete_sql = """
            DELETE FROM conversation_history 
            WHERE created_at < :cutoff_date
            """
            with SessionLocal() as session:
                result = session.execute(text(delete_sql), {"cutoff_date": cutoff_date})
                deleted_count = result.rowcount
                session.commit()
                logger.info(f"[MemoryService] Cleaned up {deleted_count} old messages (>{days} days)")
                return deleted_count
        except Exception as e:
            logger.error(f"[MemoryService] Error during cleanup: {e}")
            return 0

memory_service = MemoryService()
