import os
import uuid
from dotenv import load_dotenv
from redis import Redis


load_dotenv()

redis_url = os.getenv("REDIS_URL")

if not redis_url:
    print("FAIL: REDIS_URL is not set in the .env file.")
    raise SystemExit(1)

try:
    client = Redis.from_url(redis_url, decode_responses=False, socket_timeout=3, socket_connect_timeout=3)
    ping = client.ping()
    if not ping:
        print("FAIL: Redis ping returned False.")
        raise SystemExit(1)

    test_key = f"verify_redis:{uuid.uuid4().hex}"
    test_value = "redis-cache-check"
    client.set(test_key, test_value, ex=30)
    retrieved_value = client.get(test_key)

    if retrieved_value != test_value.encode("utf-8"):
        print(f"FAIL: Redis set/get verification mismatch. Expected {test_value!r}, got {retrieved_value!r}.")
        raise SystemExit(1)

    print("✅ Redis Connection Successful")
except Exception as exc:
    print(f"FAIL: Redis connection error: {exc}")
    raise SystemExit(1)
