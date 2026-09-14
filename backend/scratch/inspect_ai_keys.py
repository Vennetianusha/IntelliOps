import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.cache.client import redis_client

r = redis_client.client
if r:
    keys = r.keys("ai:*")
    print("Found AI Triage Keys in Redis:", len(keys))
    for k in keys:
        try:
            val = r.get(k)
            print(f"\nKEY: {k}")
            print(f"VAL: {val}")
        except Exception as e:
            print(f"KEY: {k} | Error reading: {e}")
else:
    print("Redis client not available.")
