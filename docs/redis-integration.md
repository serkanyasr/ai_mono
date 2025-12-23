# Redis Integration

Redis cache provider ve distributed state management için entegrasyon. Caching, rate limiting, ve session storage için kullanılır.

## Özellikler

- ✅ **Async/Support** - Asyncio ile tam uyumlu
- ✅ **Connection Pooling** - Efficient connection management
- ✅ **JSON Serialization** - Otomatik serialize/deserialize
- ✅ **TTL Support** - Expiration time management
- ✅ **Specialized Caches** - Session, User, RateLimit cache'leri
- ✅ **Graceful Degradation** - Redis yoksa uygulama çalışmaya devam eder
- ✅ **Distributed Rate Limiting** - Multi-instance deploy'da rate limit paylaşımı

## Konfigürasyon

### Environment Variables

```bash
# .env dosyası
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600  # Varsayılan TTL (saniye)
```

### Redis URL Formatları

```
redis://localhost:6379/0           # Standart
redis://password@localhost:6379/0  # Password ile
redis://host:6379/1                # Farklı DB
rediss://localhost:6379/0          # SSL/TLS
```

## Başlatma

### Otomatik Başlatma (main.py)

```python
# Uygulama başladığında otomatik
await RedisConnectionManager.initialize()
logger.info("Redis initialized")

# Rate limiter Redis storage kullanır
redis_limiter = Limiter(
    storage_uri=settings.redis_url,
    storage=RedisStorage(uri=settings.redis_url)
)
```

### Manual Başlatma

```python
from src.cache.redis_provider import RedisConnectionManager

await RedisConnectionManager.initialize()

# Client al
client = await RedisConnectionManager.get_client()
await client.ping()
```

### Kapatma

```python
# Shutdown'da
await RedisConnectionManager.close()
logger.info("Redis connection closed")
```

## RedisCache Kullanımı

### Basic Operations

```python
from src.cache import RedisCache

cache = RedisCache(prefix="myapp")

# Set (JSON otomatik serialize)
await cache.set("key", {"data": "value"}, ttl=3600)

# Get (JSON otomatik deserialize)
value = await cache.get("key")  # {"data": "value"}

# Exists
exists = await cache.exists("key")  # True

# Delete
deleted = await cache.delete("key")  # True
```

### TTL Operations

```python
# Set with custom TTL
await cache.set("session:123", {"user": "john"}, ttl=1800)  # 30 dakika

# Get remaining TTL
ttl = await cache.ttl("session:123")  # 1795 (saniye)

# Update TTL
await cache.expire("session:123", 3600)  # 1 saat uzat
```

### Pattern Operations

```python
# Tüm kullanıcı session'larını sil
await cache.clear_pattern("session:*")

# Tüm cache'i temizle
await cache.clear_pattern("*")
```

### Batch Operations

```python
# Multiple get
data = await cache.get_many(["user:123", "user:456", "user:789"])
# {"user:123": {...}, "user:456": {...}}

# Multiple set
await cache.set_many({
    "user:123": {"name": "John"},
    "user:456": {"name": "Jane"},
}, ttl=3600)
```

### Counter Operations

```python
# Increment counter
count = await cache.increment("api_calls:123")  # 1
count = await cache.increment("api_calls:123", 5)  # 6

# Rate limiting için
calls = await cache.increment("rate_limit:user:123")
if calls > 100:
    raise Exception("Rate limit exceeded")
```

## Specialized Cache Sınıfları

### SessionCache

```python
from src.cache import get_session_cache

session_cache = get_session_cache()

# Session kaydet
await session_cache.set("abc-123", {
    "user_id": "123",
    "created_at": "2025-12-23T23:15:05Z"
}, ttl=3600)

# Session al
session = await session_cache.get("abc-123")

# Session sil
await session_cache.delete("abc-123")

# Tüm session'ları sil
await session_cache.clear_pattern("abc-*")
```

### UserCache

```python
from src.cache import get_user_cache

user_cache = get_user_cache()

# User data cache
await user_cache.set("user:123", {
    "name": "John",
    "email": "john@example.com"
}, ttl=1800)  # 30 dakika

user = await user_cache.get("user:123")
```

### RateLimitCache

```python
from src.cache import get_rate_limit_cache

rate_cache = get_rate_limit_cache()

# Rate limiting counter
key = f"ip:{request.client.host}:endpoint:/chat"
count = await rate_cache.increment(key, ttl=60)

if count > 10:
    raise RateLimitExceeded("Too many requests")
```

## Örnek Implementations

### API Response Caching

```python
from fastapi import APIRouter
from src.cache import get_user_cache

router = APIRouter()
cache = get_user_cache()

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    # Cache'te var mı?
    cached = await cache.get(f"user:{user_id}")
    if cached:
        return cached

    # DB'den al
    user = await db.get_user(user_id)

    # Cache'e yaz (5 dakika)
    await cache.set(f"user:{user_id}", user, ttl=300)

    return user
```

### Session Management

```python
from src.cache import get_session_cache
import uuid

session_cache = get_session_cache()

async def create_session(user_id: str):
    session_id = str(uuid.uuid4())

    session = {
        "user_id": user_id,
        "created_at": datetime.now().isoformat(),
        "last_access": datetime.now().isoformat()
    }

    await session_cache.set(session_id, session, ttl=3600)
    return session_id

async def get_session(session_id: str):
    return await session_cache.get(session_id)

async def delete_user_sessions(user_id: str):
    # Kullanıcının tüm session'larını sil
    await session_cache.clear_pattern(f"user:{user_id}:*")
```

### Distributed Lock

```python
from src.cache import get_redis_client

async def acquire_lock(lock_key: str, ttl: int = 10):
    client = await get_redis_client()

    # SETNX - Sadece key yoksa set et
    acquired = await client.set(lock_key, "1", nx=True, ex=ttl)

    return acquired

async def release_lock(lock_key: str):
    client = await get_redis_client()
    await client.delete(lock_key)

# Kullanımı
async def critical_operation():
    lock_key = "lock:critical_operation"

    acquired = await acquire_lock(lock_key, ttl=30)
    if not acquired:
        raise Exception("Operation already in progress")

    try:
        # Critical operation
        await do_something()
    finally:
        await release_lock(lock_key)
```

### Pub/Sub (Mesajlaşma)

```python
from src.cache import get_redis_client

async def publish_message(channel: str, message: dict):
    client = await get_redis_client()
    await client.publish(channel, json.dumps(message))

async def subscribe_channel(channel: str):
    client = await get_redis_client()
    pubsub = client.pubsub()

    await pubsub.subscribe(channel)

    async for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            print(f"Received: {data}")
```

## Rate Limiting ile Entegrasyon

### Redis-based Rate Limiting

```python
# main.py'de otomatik konfigürasyon

# Redis çalışıyorsa rate limiter Redis storage kullanır
await RedisConnectionManager.initialize()

redis_limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url,
    storage=RedisStorage(
        uri=settings.redis_url,
        prefix="rate_limit:"
    )
)
app.state.limiter = redis_limiter
```

### Distributed Rate Limiting

```python
# Multi-instance deploy'da tüm instance'lar rate limit'i paylaşır

# Instance 1
@RateLimiter.limit("10/minute")
async def endpoint():
    pass

# Instance 2 (aynı rate limit)
# Her iki instance da aynı Redis Redis'i kullanır
# Toplam 10 request/dakika (tüm instance'lar için)
```

## Graceful Degradation

### Redis Bağlanamazsa

```python
# main.py'de

try:
    await RedisConnectionManager.initialize()
    logger.info("Redis initialized")
except Exception as redis_err:
    logger.warning(f"Redis initialization failed: {redis_err}")
    logger.info("Rate limiting using in-memory storage")
    # Uygulama çalışmaya devam eder
    # Rate limiting in-memory storage'a düşer
```

### Fallback Logic

```python
from src.cache import RedisConnectionManager

async def get_data(key: str):
    try:
        client = await RedisConnectionManager.get_client()
        value = await client.get(key)
        if value:
            return json.loads(value)
    except Exception:
        # Redis hatası - fallback to DB
        pass

    # Fallback to database
    return await db.get_data(key)
```

## Monitoring

### Health Check

```python
@router.get("/health/redis")
async def redis_health():
    try:
        client = await RedisConnectionManager.get_client()
        await client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "redis": "disconnected",
            "error": str(e)
        }
```

### Cache Statistics

```python
@router.get("/api/v1/cache/stats")
async def cache_stats():
    client = await RedisConnectionManager.get_client()

    info = await client.info("stats")
    keyspace = await client.info("keyspace")

    return {
        "total_keys": info.get("keyspace_hits", 0),
        "hits": info.get("keyspace_hits", 0),
        "misses": info.get("keyspace_misses", 0),
        "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_misses", 1), 1),
        "databases": keyspace
    }
```

## Best Practices

### 1. TTL Kullan

```python
# ❌ Sonsuz cache - memory leak
await cache.set("key", value)

# ✅ TTL ile - otomatik temizlenir
await cache.set("key", value, ttl=3600)
```

### 2. Prefix Kullan

```python
# ❌ Karışık key'ler
cache.set("user:123", user)
cache.set("session:abc", session)

# ✅ Organize prefix'ler
user_cache = UserCache()  # "user:*"
session_cache = SessionCache()  # "session:*"
```

### 3. JSON Serialization

```python
# ❌ Manual serialization
await cache.set("key", json.dumps(value))
value = json.loads(await cache.get("key"))

# ✅ Otomatik serialization
await cache.set("key", value)
value = await cache.get("key")
```

### 4. Graceful Degradation

```python
# ❌ Redis yoksa çöker
client = await get_client()
await client.get(key)

# ✅ Fallback ile
try:
    value = await cache.get(key)
except Exception:
    value = await db.get(key)
```

### 5. Batch Operations

```python
# ❌ Tek tek çağrı
for key in keys:
    await cache.get(key)

# ✅ Batch çağrı
await cache.get_many(keys)
```

## Troubleshooting

### Redis Bağlanamıyor

```bash
# Redis çalışıyor mu?
redis-cli ping
# PONG

# URL doğru mu?
echo $REDIS_URL
# redis://localhost:6379/0
```

### Cache Temizlenmiyor

```python
# Manuel temizleme
await cache.clear_pattern("*")

# Redis CLI'den
redis-cli FLUSHDB
```

### High Memory Usage

```python
# TTL'leri düşür
await cache.set("key", value, ttl=300)  # 5 dakika

# Max memory policy ayarla
# redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

## Production Deployment

### Docker Compose

```yaml
services:
  api:
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

### Redis Sentinel (HA)

```python
# Sentinel ile high availability
REDIS_URL=redis://sentinel1:26379,sentinel2:26379,master1
```

### Redis Cluster

```python
# Cluster mode
REDIS_URL=redis://cluster-node1:7000,cluster-node2:7001
```

## Referanslar

- [Redis Documentation](https://redis.io/docs/)
- [redis-py (Async)](https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
- [Redis Caching Strategies](https://redis.io/docs/manual/eviction/)
