import json
from typing import Any

import redis.asyncio as redis

from .config import settings

_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


async def publish_event(channel: str, data: dict[str, Any]):
    r = await get_redis()
    await r.publish(channel, json.dumps(data, default=str))


async def subscribe_event(channel: str):
    r = await get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)
    return pubsub
