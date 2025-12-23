# Resilience Patterns

Tenacity kütüphanesi kullanılarak implement edilmiş retry ve circuit breaker pattern'leri. Dış servis çağrılarında (LLM, MCP, Database) transient failure'leri yönetmek için kullanılır.

## Özellikler

- ✅ **Retry with Exponential Backoff** - Otomatik yeniden deneme
- ✅ **Circuit Breaker** - Kademeli service degradation
- ✅ **Jitter Support** - Thundering herd önleme
- ✅ **Combined Decorator** - Retry + Circuit Breaker bir arada
- ✅ **Predefined Breakers** - Ortak servisler için hazır circuit breaker'lar
- ✅ **Async/Support** - Hem sync hem async fonksiyonlar

## Pattern'ler

### 1. Retry Pattern

Transient failure'lar için otomatik yeniden deneme.

```python
from src.utils import retry_on_exception

@retry_on_exception(
    max_attempts=3,
    wait_min=1.0,
    wait_max=10.0,
    exception_types=(TimeoutError, ConnectionError)
)
async def call_external_api():
    # Timeout olursa 1-10 saniye bekleyip tekrar dener (max 3 kez)
    pass
```

### 2. Circuit Breaker Pattern

Servis sürekli failing olduğunda request'leri blokelar.

**States:**
- **CLOSED** - Normal operation, request'ler geçer
- **OPEN** - Servis failing, request'ler bloke
- **HALF_OPEN** - Recovery testi

```python
from src.utils import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,    # 5 failure'dan sonra OPEN
    recovery_timeout=60,    # 60 saniye sonra HALF_OPEN
    expected_exception=Exception
)

@breaker
async def call_llm():
    # 5 failure olursa circuit açılır
    # 60 saniye request'ler bloke
    pass
```

### 3. Combined (@resilient)

Hem retry hem circuit breaker bir arada.

```python
from src.utils import resilient

@resilient(
    max_attempts=3,         # Retry: 3 kez dene
    failure_threshold=5,    # Circuit: 5 failure'da aç
    recovery_timeout=60,    # Circuit: 60 saniye recovery
    exception_types=(TimeoutError, ConnectionError)
)
async def critical_api_call():
    # Full resilience protection
    pass
```

## Kullanım Örnekleri

### LLM Çağrısı

```python
from src.utils import resilient, LLM_CIRCUIT_BREAKER

# Predefined circuit breaker kullan
@LLM_CIRCUIT_BREAKER
async def call_openai(prompt: str):
    response = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response
```

### Database Query

```python
from src.utils import retry_on_exception

@retry_on_exception(
    max_attempts=3,
    exception_types=(TimeoutError, OperationalError)
)
async def execute_query(query: str):
    result = await db.execute(query)
    return result
```

### MCP Server Çağrısı

```python
from src.utils import MCP_CIRCUIT_BREAKER

@MCP_CIRCUIT_BREAKER
async def call_mcp_server(method: str, params: dict):
    response = await mcp_client.call(method, params)
    return response
```

## Retry Decorator'leri

### retry_on_exception

Exponential backoff ile retry.

```python
@retry_on_exception(
    max_attempts=3,      # Max 3 deneme
    wait_min=1.0,        # Min 1 saniye wait
    wait_max=10.0,       # Max 10 saniye wait
    exception_types=(TimeoutError,)  # Sadece timeout'da retry
)
async def external_call():
    pass
```

**Wait Strategy:**
- Deneme 1: Hata olursa 1 saniye bekle
- Deneme 2: 2 saniye bekle
- Deneme 3: 4 saniye bekle
- ...

### retry_with_jitter

Random jitter ile thundering herd önleme.

```python
@retry_with_jitter(
    max_attempts=5,
    base_wait=2.0,       # Base 2 saniye
    max_wait=10.0,       # Max 10 saniye
    jitter=True          # Random jitter ekle
)
async def api_call():
    # 2, 3, 5, 8 saniye (random jitter ile)
    pass
```

## Circuit Breaker

### Manuel Circuit Breaker

```python
from src.utils import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=TimeoutError
)

@breaker
async def external_service():
    pass
```

### Circuit Breaker State

```python
breaker = CircuitBreaker(failure_threshold=3)

# State kontrol
if breaker.state == CircuitState.OPEN:
    print("Circuit açık, request'ler bloke")

# Failure count
print(f"Failure count: {breaker.failure_count}")

# Manual reset
breaker.reset()
```

### Predefined Circuit Breakers

```python
from src.utils import (
    LLM_CIRCUIT_BREAKER,
    MCP_CIRCUIT_BREAKER,
    DATABASE_CIRCUIT_BREAKER
)

# LLM çağrıları için
@LLM_CIRCUIT_BREAKER
async def call_llm():
    pass

# MCP server için
@MCP_CIRCUIT_BREAKER
async def call_mcp():
    pass

# Database için
@DATABASE_CIRCUIT_BREAKER
async def query_db():
    pass
```

## Circuit Breaker Flow

```
CLOSED State
    ↓
    [Request] → Success → Reset failure count
    [Request] → Failure → Increment count
    [Failure count >= threshold] → OPEN
    ↓
OPEN State
    ↓
    [Request] → CircuitBreakerError (blocked)
    [Timeout elapsed] → HALF_OPEN
    ↓
HALF_OPEN State
    ↓
    [Request] → Success → CLOSED (recovered)
    [Request] → Failure → OPEN (failed again)
```

## Error Handling

### Circuit Breaker Error

```python
from src.utils import CircuitBreakerError

breaker = CircuitBreaker(failure_threshold=3)

@breaker
async def external_service():
    pass

try:
    await external_service()
except CircuitBreakerError:
    print("Circuit açık, service unavailable")
    # Fallback logic
    return cached_response
```

### Retry Exhausted

```python
from tenacity import RetryError

@retry_on_exception(max_attempts=3)
async def external_call():
    pass

try:
    await external_call()
except RetryError:
    print("Tüm retry denemeleri başarısız")
    # Fallback logic
```

## Best Practices

### 1. Uygun Exception Seç

```python
# ❌ Yanlış - Tüm exception'ları retry
@retry_on_exception(exception_types=(Exception,))

# ✅ Doğru - Sadece transient'leri retry
@retry_on_exception(exception_types=(TimeoutError, ConnectionError))
```

### 2. Uygun Threshold

```python
# ❌ Çok düşük - Sık sık açılır
breaker = CircuitBreaker(failure_threshold=2)

# ✅ Uygun - Realistic threshold
breaker = CircuitBreaker(failure_threshold=10)
```

### 3. Fallback Logic

```python
@LLM_CIRCUIT_BREAKER
async def get_ai_response(prompt: str):
    try:
        return await call_llm(prompt)
    except CircuitBreakerError:
        # Fallback: Cached response
        return await get_cached_response(prompt)
```

### 4. Monitoring

```python
breaker = CircuitBreaker(failure_threshold=10)

@breaker
async def external_call():
    pass

# Log circuit state
logger.info(
    "Circuit state",
    state=breaker.state.value,
    failure_count=breaker.failure_count
)
```

## Örnek Implementation

### Chat Service

```python
from src.utils import resilient, get_logger

logger = get_logger(__name__)

class ChatService:
    @resilient(
        max_attempts=3,
        failure_threshold=5,
        recovery_timeout=60,
        exception_types=(TimeoutError, APIError)
    )
    async def stream_chat(self, message: str):
        logger.info("Starting chat stream")

        try:
            response = await self.llm_client.chat(message)
            logger.info("Chat completed")
            return response
        except Exception as e:
            logger.error("Chat failed", error=str(e))
            raise
```

### Database Service

```python
from src.utils import retry_on_exception, DATABASE_CIRCUIT_BREAKER

class DatabaseService:
    @retry_on_exception(
        max_attempts=3,
        exception_types=(TimeoutError, OperationalError)
    )
    async def execute_query(self, query: str):
        return await self.db.execute(query)

    @DATABASE_CIRCUIT_BREAKER
    async def get_user(self, user_id: str):
        return await self.db.fetch_one(
            "SELECT * FROM users WHERE id = ?",
            user_id
        )
```

## Monitoring ve Debugging

### Circuit State Loglama

```python
import asyncio

async def monitor_circuit(breaker: CircuitBreaker):
    while True:
        logger.info(
            "Circuit monitor",
            state=breaker.state.value,
            failure_count=breaker.failure_count
        )
        await asyncio.sleep(60)
```

### Circuit Breaker Dashboard

```python
@router.get("/api/v1/circuits")
async def get_circuit_states():
    return {
        "llm": {
            "state": LLM_CIRCUIT_BREAKER.state.value,
            "failure_count": LLM_CIRCUIT_BREAKER.failure_count
        },
        "mcp": {
            "state": MCP_CIRCUIT_BREAKER.state.value,
            "failure_count": MCP_CIRCUIT_BREAKER.failure_count
        }
    }
```

## Troubleshooting

### Retry Çok Uzun Sürüyor

```python
# Max attempt ve wait time'ı düşür
@retry_on_exception(max_attempts=2, wait_max=5.0)
```

### Circuit Sık Sık Açılıyor

```python
# Threshold'u artır
breaker = CircuitBreaker(failure_threshold=20)
```

### Recovery Çok Uzun Sürüyor

```python
# Recovery timeout'u düşür
breaker = CircuitBreaker(recovery_timeout=30)  # 30 saniye
```

## Konfigürasyon

### Environment Variables

```bash
# .env dosyasında
CIRCUIT_BREAKER_FAILURE_THRESHOLD=10
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
RETRY_MAX_ATTEMPTS=3
RETRY_WAIT_MIN=1.0
RETRY_WAIT_MAX=10.0
```

### Settings.py

```python
class ResilienceSettings(BaseSettings):
    circuit_failure_threshold: int = 10
    circuit_recovery_timeout: int = 60
    retry_max_attempts: int = 3
    retry_wait_min: float = 1.0
    retry_wait_max: float = 10.0
```

## Referanslar

- [Tenacity Documentation](https://tenacity.readthedocs.io/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Retry Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/retry)
