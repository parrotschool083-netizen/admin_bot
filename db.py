import os
import asyncpg
import redis.asyncio as aioredis

DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

pool = None
redis = None

async def init_db():
    global pool, redis
    pool = await asyncpg.create_pool(DATABASE_URL)
    redis = await aioredis.from_url(REDIS_URL)
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS requests (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                name TEXT,
                phone TEXT,
                child_age TEXT,
                type TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

async def close_db():
    global pool, redis
    if pool:
        await pool.close()
    if redis:
        await redis.close()
