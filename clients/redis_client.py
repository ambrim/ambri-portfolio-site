import os
import redis

def get_redis_client() -> redis.Redis:
    """
    Connect to Redis Cloud (or local Redis for development)
    """
    redis_url = os.getenv('REDIS_URL')
    
    if redis_url:
        return redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True
        )
    else:
        return redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )

redis_client = get_redis_client()