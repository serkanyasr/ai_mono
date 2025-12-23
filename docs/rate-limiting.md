# Rate Limiting Middleware

Slowapi kütüphanesi kullanılarak implement edilmiş rate limiting middleware. API endpoint'lerini aşırı kullanıma karşı korur ve adil kaynak dağıtımı sağlar.

## Özellikler

- ✅ **Decorator-based** - Endpoint seviyesinde rate limiting
- ✅ **Flexible Storage** - In-memory veya Redis storage
- ✅ **Multiple Strategies** - IP, User ID, API key bazlı
- ✅ **Predefined Limits** - Ortak endpoint tipleri için hazır limitler
- ✅ **Custom Handlers** - Özelleştirilebilir 429 response'ları
- ✅ **Graceful Degradation** - Redis yoksa in-memory storage

## Konfigürasyon

### Environment Variables

```bash
# Rate limiting Redis storage (opsiyonel)
REDIS_URL=redis://localhost:6379/0
```

## Kullanım

### Basit Rate Limit

```python
from src.api.v1.middleware.rate_limit import RateLimiter
from fastapi import APIRouter

router = APIRouter()

@router.post("/chat/stream")
@RateLimiter.limit("10/minute")  # 10 istek/dakika
async def chat_stream():
    pass
```

### User Bazlı Rate Limit

```python
@router.get("/user/profile")
@RateLimiter.limit("100/minute", key_func=lambda r: r.headers.get("X-User-ID"))
async def get_profile():
    pass
```

### Predefined Rate Limits Kullanımı

```python
from src.api.v1.middleware.rate_limit import RateLimits

@router.post("/chat/stream")
@RateLimiter.limit(RateLimits.CHAT)  # 10/minute
async def chat_stream():
    pass

@router.get("/sessions")
@RateLimiter.limit(RateLimits.SESSIONS)  # 60/minute
async def list_sessions():
    pass
```

### Rate Limit'den Muaf Tutma

```python
@router.get("/health")
@RateLimiter.exempt()
async def health_check():
    pass
```

## Predefined Rate Limits

| Limit | Değer | Açıklama |
|-------|-------|----------|
| `RateLimits.HEALTH` | 1000/minute | Health check'ler |
| `RateLimits.CHAT` | 10/minute | Chat endpoint'leri |
| `RateLimits.CHAT_PREMIUM` | 60/minute | Premium kullanıcılar |
| `RateLimits.SESSIONS` | 60/minute | Session işlemleri |
| `RateLimits.CACHE` | 30/minute | Cache işlemleri |
| `RateLimits.ADMIN` | 100/minute | Admin işlemleri |
| `RateLimits.BURST` | 10/second | Kısa burst'ler |

## Rate Limit Strategies

### Per IP (Varsayılan)

```python
@RateLimiter.limit("10/minute")
async def my_endpoint():
    pass
```

### Per User ID

```python
@RateLimiter.limit("100/minute", key_func=lambda r: r.headers.get("X-User-ID"))
async def user_endpoint():
    pass
```

### Per API Key

```python
@RateLimits.per_api_key("1000/hour")
async def api_endpoint():
    pass
```

## Storage Backend

### In-Memory (Varsayılan)

```python
# Development ortamı için uygundur
# Restart sonrası sayaçlar sıfırlanır
```

### Redis (Production Önerilen)

```python
# src/api/main.py'de otomatik konfigürasyon

# Redis varsa otomatik kullanılır
await RedisConnectionManager.initialize()

# Rate limiter Redis storage kullanır
redis_limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url,
    storage=RedisStorage(uri=settings.redis_url, prefix="rate_limit:")
)
```

## Rate Limit Exceeded Response

Rate limit aşıldığında HTTP 429 döner:

```json
{
  "error": "Rate limit exceeded",
  "error_type": "RateLimitExceeded",
  "detail": "Rate limit exceeded: 10 per 1 minute",
  "correlation_id": "abc-123-def-456",
  "retry_after": 60
}
```

## Rate Limit Bilgileri Endpoint'i

```bash
GET /api/v1/limits
```

```json
{
  "rate_limits": {
    "health": "1000/minute",
    "chat": "10/minute",
    "chat_premium": "60/minute",
    "sessions": "60/minute",
    "cache": "30/minute",
    "admin": "100/minute",
    "burst": "10/second"
  },
  "descriptions": {
    "health": "Health check endpoints (very permissive)",
    "chat": "Chat endpoints (restrictive)"
  }
}
```

## Özelleştirme

### Custom Handler

```python
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

async def custom_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too many requests",
            "retry_after": 60
        }
    )

# main.py'de
app.add_exception_handler(RateLimitExceeded, custom_handler)
```

### Custom Rate Limit String Formatları

```
10/minute    # 10 istek her dakika
100/hour     # 100 istek her saat
1000/day     # 1000 istek her gün
10/second    # 10 istek her saniye
```

## Best Practices

1. **Health Check'leri Muaf Tut** - `@RateLimiter.exempt()`
2. **Predefined Limits Kullan** - `RateLimits.CHAT` gibi
3. **Production'da Redis Kullan** - Distributed rate limiting
4. **Per-User Limits** - Kullanıcı bazlı ayrıcalıklar
5. **Reasonable Defaults** - Çok restrictive olma

## Örnek Implementation

```python
# src/api/v1/endpoints/chat.py
from fastapi import APIRouter
from src.api.v1.middleware.rate_limit import RateLimiter, RateLimits

router = APIRouter()

@router.post("/chat/stream")
@RateLimiter.limit(RateLimits.CHAT)  # Standart kullanıcı
async def chat_stream(request: ChatRequest):
    pass

@router.post("/chat/stream")
@RateLimiter.limit(RateLimits.CHAT_PREMIUM)  # Premium kullanıcı
async def chat_stream_premium(request: ChatRequest):
    pass

@router.get("/health")
@RateLimiter.exempt()  # Rate limit'den muaf
async def health_check():
    pass
```

## Troubleshooting

### Rate Limit Çalışmıyor

```python
# Limiter'in app state'e eklendiğinden emin ol
app.state.limiter = limiter
```

### Redis Bağlanamıyor

```python
# Redis graceful degradation
# In-memory storage'a düşer
logger.warning("Redis connection failed")
```

### Custom Key Function

```python
# Complex key extraction
def get_key(request):
    return f"{request.client.host}:{request.headers.get('X-Tenant-ID')}"

@RateLimiter.limit("10/minute", key_func=get_key)
async def endpoint():
    pass
```

## Referanslar

- [slowapi Documentation](https://slowapi.readthedocs.io/)
- [FastAPI Rate Limiting](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Rate Limiting Best Practices](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
