import os
import json
import redis

class CacheManager:
    def __init__(self):
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        try:
            self.client = redis.Redis.from_url(redis_url, socket_timeout=2)
            # Test connection
            self.client.ping()
            print("Connected to Redis successfully for caching.")
            self.use_redis = True
        except Exception as e:
            print(f"Redis is not available. Falling back to In-Memory Cache. Error: {e}")
            self.use_redis = False
            self.memory_cache = {}

    def get(self, key):
        if self.use_redis:
            try:
                val = self.client.get(key)
                return json.loads(val) if val else None
            except Exception:
                return self.memory_cache.get(key)
        return self.memory_cache.get(key)

    def set(self, key, value, timeout=300):
        if self.use_redis:
            try:
                self.client.setex(key, timeout, json.dumps(value))
            except Exception:
                self.memory_cache[key] = value
        else:
            self.memory_cache[key] = value

    def delete(self, key):
        if self.use_redis:
            try:
                self.client.delete(key)
            except Exception:
                if key in self.memory_cache:
                    del self.memory_cache[key]
        elif key in self.memory_cache:
            del self.memory_cache[key]
