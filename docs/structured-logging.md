# Structured Logging

Structlog kütüphanesi kullanılarak implement edilmiş structured logging sistemi. JSON formatında log çıktısı, correlation ID desteği ve context binding sağlar.

## Özellikler

- ✅ **Structured Output** - JSON formatında log'lar
- ✅ **Correlation ID** - Otomatik request tracking
- ✅ **Context Binding** - Context vars otomatik ekleme
- ✅ **Multiple Formats** - Console (dev) ve JSON (prod)
- ✅ **Backward Compatible** - Eski logging API'i korur
- ✅ **Easy Integration** - Mevcut kodda değişiklik gerektirmez

## Konfigürasyon

### Environment Variables

```bash
# .env dosyası
API_ENV=production        # development|production
API_LOG_LEVEL=INFO        # DEBUG|INFO|WARNING|ERROR|CRITICAL
LOG_FORMAT=json           # json|text
```

## Başlatma

### Otomatik Başlatma (main.py)

```python
from src.utils import setup_logging

setup_logging(
    level="INFO",
    log_file="logs/api.log",
    use_structured=True  # Structlog kullan
)
```

### Manual Başlatma

```python
from src.utils.structured_logging import setup_structured_logging

setup_structured_logging(
    level="INFO",
    log_file="logs/api.log",
    json_format=True,  # JSON format
    include_timestamp=True,
    include_caller_info=True,
)
```

## Kullanım

### Basit Logging (Eski Stil - Hala Çalışır)

```python
from src.utils import get_logger

logger = get_logger(__name__)
logger.info("User logged in")
logger.error("Database connection failed")
logger.warning("High memory usage")
```

### Structured Logging (Yeni Stil - Önerilen)

```python
from src.utils import get_logger

logger = get_logger(__name__)

# Context ekleyerek log
logger.info("User logged in", user_id="123", ip="192.168.1.1")
logger.error("API call failed", endpoint="/chat", status_code=500, error="timeout")
logger.warning("Cache miss", key="user:123")
```

### Context Binding

```python
from src.utils import bind_correlation_id, clear_context

# Correlation ID'yi tüm log'lara ekle
bind_correlation_id("abc-123-def-456")

logger.info("Processing request")  # correlation_id otomatik eklenir
logger.info("Database query", query="SELECT * FROM users")

# Context temizle
clear_context()
```

### Context Manager ile

```python
from src.utils import RequestContext

# Otomatik temizlik ile
with RequestContext(correlation_id="abc-123", user_id="456"):
    logger.info("Processing in context")
    logger.info("Another log in context")
# Context otomatik temizlenir
```

## Log Formatları

### Development (Console Format)

```
2025-12-23 23:15:05 [info     ] User logged in                   user_id=123 ip=192.168.1.1
2025-12-23 23:15:06 [error    ] API call failed                  endpoint=/chat status_code=500 error=timeout
```

### Production (JSON Format)

```json
{
  "timestamp": "2025-12-23T23:15:05.123456Z",
  "level": "info",
  "logger": "src.api.v1.endpoints.chat",
  "message": "User logged in",
  "correlation_id": "abc-123-def-456",
  "app": "ai_mono",
  "user_id": "123",
  "ip": "192.168.1.1"
}
```

## Otomatik Context Eklenmesi

### Correlation ID Middleware

```python
# src/api/v1/middleware/correlation.py
# Correlation ID otomatik olarak tüm log'lara eklenir

# Endpoint'te logger kullanın
logger.info("Processing request", user_id="123")
# Çıktı: {"correlation_id": "abc-123", "user_id": "123", ...}
```

### App Context

```python
# Tüm log'lara otomatik eklenir
{
  "app": "ai_mono",
  "logger": "module.name",
  "level": "info",
  "timestamp": "2025-12-23T23:15:05.123Z"
}
```

### Caller Info

```python
# Dosya adı, fonksiyon, satır numarası
{
  "module": "src.api.v1.endpoints.chat",
  "function": "chat_stream",
  "lineno": 42
}
```

## Log Levels

| Level | Kullanım | Örnek |
|-------|----------|-------|
| `DEBUG` | Detaylı debug bilgisi | `logger.debug("Variable value", x=123)` |
| `INFO` | Bilgilendirme | `logger.info("User logged in", user_id="123")` |
| `WARNING` | Uyarı | `logger.warning("High memory usage", usage="85%")` |
| `ERROR` | Hata (uygulama devam eder) | `logger.error("API timeout", endpoint="/chat")` |
| `CRITICAL` | Kritik hata | `logger.critical("Database down")` |

## Örnek Kullanım Senaryoları

### API Endpoint

```python
from fastapi import APIRouter
from src.utils import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    logger.info("Chat request received", session_id=request.session_id)

    try:
        result = await process_chat(request)
        logger.info("Chat processed", message_count=len(result))
        return result
    except Exception as e:
        logger.error("Chat processing failed", error=str(e))
        raise
```

### Background Task

```python
from src.utils import get_logger, RequestContext

logger = get_logger(__name__)

async def background_task(user_id: str):
    with RequestContext(user_id=user_id):
        logger.info("Task started")

        try:
            await process()
            logger.info("Task completed")
        except Exception as e:
            logger.error("Task failed", error=str(e))
```

### Service Layer

```python
from src.utils import get_logger

class ChatService:
    def __init__(self):
        self._logger = get_logger(__name__)

    async def stream_chat(self, message: str):
        self._logger.info("Starting chat stream", message_len=len(message))

        # Processing...

        self._logger.info("Stream completed", token_count=100)
```

## Structured Logging Avantajları

### 1. Log Aggregation

```bash
# JSON log'ları ELK/Loki ile kolay parse
grep "correlation_id" logs/api.log | jq '.user_id, .message'
```

### 2. Filterable

```bash
# Kullanıcı bazlı filtreleme
jq 'select(.user_id == "123")' logs/api.log

# Error log'ları
jq 'select(.level == "error")' logs/api.log
```

### 3. Request Tracing

```bash
# Correlation ID ile request takibi
grep "abc-123" logs/api.log
# Tüm request log'ları correlation ID ile ilişkili
```

## File Logging

### Console + File

```python
setup_logging(
    level="INFO",
    log_file="logs/api.log",  # File'a da yaz
    use_structured=True
)
```

### File Rotation (Production)

```python
import logging
from logging.handlers import RotatingFileHandler

# Log rotation ile
handler = RotatingFileHandler(
    "logs/api.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

## Best Practices

1. **Structured Fields Kullan** - `logger.info("Event", user_id="123")`
2. **Sensitive Data Loglama** - Password, token loglama
3. **Appropriate Level** - INFO, WARNING, ERROR doğru kullan
4. **Correlation ID** - Request tracking için kullan
5. **Context Manager** - `RequestContext` ile otomatik temizlik

## Migration Guide

### Eski Koddan Yeni Koda Geçiş

```python
# ÖNCESİ (standart logging)
import logging
logger = logging.getLogger(__name__)
logger.info("User logged in")

# SONRASI (structured logging - aynı API)
from src.utils import get_logger
logger = get_logger(__name__)
logger.info("User logged in", user_id="123")  # Context eklenebilir
```

### Mevcut Kodda Değişiklik Gerekmez

```python
# Bu kod hala çalışır ve structured logging kullanır
from src.utils import get_logger

logger = get_logger(__name__)
logger.info("Message")
```

## Troubleshooting

### Correlation ID Gözükmüyor

```python
# CorrelationIDMiddleware ekli olduğundan emin ol
app.add_middleware(CorrelationIDMiddleware)
```

### JSON Format İstemiyorsan

```python
# Console format için
setup_logging(use_structured=False)
```

### Context Temizlenmiyor

```python
# Context manager kullan
with RequestContext(correlation_id="abc"):
    logger.info("Message")
# Otomatik temizlenir
```

## Performans Notları

- Structlog logging overhead'i minimaldır (~0.1ms)
- JSON serialization async çalışır
- File logging blocking olabilir - dikkatli kullan

## Referanslar

- [Structlog Documentation](https://www.structlog.org/)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)
- [JSON Logging](https://medium.com/better-programming/better-logging-in-python-577e3e8e5e1e)
