# AI Mono - Dökümantasyon

Bu proje için geliştirilmiş tüm middleware, pattern ve entegrasyonların dökümantasyonu.

## İçindekiler

### Middleware ve Infrastructure
- **[Rate Limiting](./rate-limiting.md)** - slowapi ile rate limiting middleware
- **[Structured Logging](./structured-logging.md)** - structlog ile structured logging
- **[Resilience Patterns](./resilience-patterns.md)** - Retry ve Circuit Breaker pattern'leri
- **[Redis Integration](./redis-integration.md)** - Redis cache ve distributed state management

## Proje Yapısı

```
src/
├── api/
│   ├── main.py                          # FastAPI uygulama giriş noktası
│   └── v1/
│       ├── middleware/
│       │   ├── rate_limit.py            # Rate limiting middleware
│       │   ├── correlation.py           # Correlation ID middleware
│       │   ├── logging_middleware.py    # Request logging middleware
│       │   └── error_handlers.py        # Merkezi error handling
│       └── endpoints/                   # API endpoint'leri
├── cache/
│   ├── agent_cache.py                   # In-memory agent cache
│   └── redis_provider.py                # Redis cache provider
├── utils/
│   ├── logging.py                       # Backward compatible logging
│   ├── structured_logging.py            # Structlog ile structured logging
│   └── resilience.py                    # Retry ve Circuit Breaker
└── config/
    └── settings.py                      # Konfigürasyon yönetimi
```

## Quick Start

### 1. Environment Variables

```bash
# .env dosyası
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600
API_ENV=development
API_LOG_LEVEL=INFO
```

### 2. Başlatma

Uygulama başlatıldığında otomatik olarak:
- Structured logging konfigürasyonu yapılır
- Redis bağlantısı kurulur (varsa)
- Rate limiting Redis storage'a bağlanır
- Correlation ID middleware aktif olur

### 3. Kullanım

```python
from src.utils import get_logger, resilient
from src.cache import get_user_cache

logger = get_logger(__name__)
cache = get_user_cache()

# Structured logging
logger.info("User action", user_id="123", action="login")

# Cache
await cache.set("session:123", {"data": "value"}, ttl=3600)

# Resilience
@resilient(max_attempts=3, failure_threshold=5)
async def external_api_call():
    pass
```

## Architecture Principles

1. **Backward Compatibility** - Mevcut kodu bozmadan yeni özellikler
2. **Graceful Degradation** - Redis yoksa in-memory storage
3. **Structured Logging** - Tüm log'lar JSON formatında, correlation ID ile
4. **Resilience** - Retry ve circuit breaker pattern'leri
5. **Dependency Injection** - FastAPI Depends ile loose coupling

## Middleware Execution Order

```
Request → CORSMiddleware → GZipMiddleware → CorrelationIDMiddleware
        → LoggingMiddleware → RateLimiter → Endpoint
```

## Production Checklist

- [ ] Redis kurulumu ve konfigürasyonu
- [ ] Structured logging JSON format aktif
- [ ] Rate limiting Redis storage
- [ ] Circuit breaker threshold'leri ayarla
- [ ] Log aggregation (ELK, Loki, etc.)
- [ ] Monitoring ve alerting
