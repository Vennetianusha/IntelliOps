import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.cache.client import redis_client

r = redis_client.client
if r:
    keys = r.keys("*")
    print("Found Redis Keys:", len(keys))
    for k in keys:
        print(f"Key: {k} | Value: {r.get(k)}")
else:
    print("Redis client not available.")
