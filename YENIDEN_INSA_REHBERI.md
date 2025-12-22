# AI Multi-Agent Sistem - Yeniden İnşa Rehberi

## 📋 İçindekiler

1. [Sistem Genel Bakış](#sistem-genel-bakış)
2. [Mimari İlkeler](#mimari-ilkeler)
3. [Sistem Bileşenleri](#sistem-bileşenleri)
4. [Katmanlı Mimari Tasarımı](#katmanlı-mimari-tasarımı)
5. [Katmanlar Arası Akış](#katmanlar-arası-akış)
6. [Teknoloji Stack'i](#teknoloji-stacki)
7. [Proje Klasör Yapısı](#proje-klasör-yapısı)
8. [Geliştirme Adımları](#geliştirme-adımları)
9. [Sistem Şeması](#sistem-şeması)
10. [En İyi Uygulamalar](#en-iyi-uygulamalar)

---

## 🎯 Sistem Genel Bakış

### Hedefler

- ✅ **Sadelik** - Minimum karmaşıklık, maksimum netlik
- ✅ **Genişletilebilirlik** - Yeni özellikler eklemek kolay
- ✅ **Yönetilebilirlik** - Kodu anlamak ve bakımını yapmak basit
- ✅ **Ölçeklenebilirlik** - Yük arttığında sistem büyüyebilmeli
- ✅ **Gözlemlenebilirlik** - Sistem durumu net görülebilmeli

### Ana Özellikler

1. **Multi-Agent Architecture** - Birden fazla AI agent'ı birlikte çalışır
2. **LLM Provider Flexibility** - OpenAI, Anthropic, Local (Ollama) desteği
3. **MCP Integration** - Model Context Protocol ile agent yetenekleri
4. **RAG System** - Retrieval-Augmented Generation
5. **Memory Management** - Kullanıcı oturum ve global memory
6. **Session Management** - Kullanıcı bazlı izole oturumlar
7. **Caching Layer** - Performans optimizasyonu
8. **Monitoring** - Sistem sağlığı ve metrikler

---

## 🏛️ Mimari İlkeler

### 1. Separation of Concerns (Sorumluluk Ayrımı)

Her bileşen tek bir sorumluluğa sahip olmalı:
- **API Layer** → HTTP request/response
- **Business Logic** → İş kuralları
- **Data Access** → Veri erişimi
- **External Services** → LLM, DB, Cache

### 2. Dependency Inversion

- Üst katmanlar alt katmanlara bağımlı olmamalı
- Abstractions kullanın (interfaces, protocols)
- Implementation details üst seviyede olmamalı

### 3. Single Responsibility Principle

- Her sınıf/modül tek bir değişme nedeni olmalı
- "Cohesion" yüksek olsun
- "Coupling" düşük olsun

### 4. Configuration as Code

- Tüm konfigürasyonlar kod içinde
- Environment-based ayarlar
- Secrets yönetimi (vault, env vars)

### 5. Observability First

- Logging - Yapılandırılmış loglar
- Metrics - Prometheus metrikleri
- Tracing - İstek takibi
- Health checks - Sistem sağlığı

---

## 🧩 Sistem Bileşenleri

### 1. API Gateway Layer

**Görevi:** Dış dünya ile iletişim

**Bileşenler:**
- **HTTP Server** (FastAPI)
- **WebSocket** (Real-time communication)
- **Load Balancer** (NGINX/Traefik)
- **API Documentation** (Swagger/OpenAPI)
- **CORS Handler**
- **Request Rate Limiter**

### 2. Session Management

**Görevi:** Kullanıcı oturumları

**Bileşenler:**
- **Session Store** (Redis)
- **Session Factory** (Create/validate sessions)
- **Session Middleware**
- **User Context Manager**

### 3. Agent Orchestrator

**Görevi:** Multi-agent koordinasyonu

**Bileşenler:**
- **Agent Registry** - Hangi agent'lar mevcut
- **Agent Factory** - Agent oluşturma
- **Agent Lifecycle Manager** - Agent yaşam döngüsü
- **Agent Communication** - Agent'lar arası mesajlaşma

### 4. LLM Provider Layer

**Görevi:** LLM entegrasyonu

**Bileşenler:**
- **OpenAI Provider**
- **Anthropic Provider**
- **Ollama Provider** (Local)
- **Provider Factory** - Runtime'da seçim
- **Token Counter** - Kullanım takibi

### 5. MCP Integration Layer

**Görevi:** Model Context Protocol

**Bileşen:**
- **MCP Client** - MCP server'lara bağlanma
- **Tool Registry** - Kullanılabilir tool'lar
- **Tool Executor** - Tool'ları çalıştırma
- **MCP Transport** - HTTP, WebSocket, STDIO

### 6. RAG System

**Görevi:** Knowledge retrieval

**Bileşenler:**
- **Document Ingestion** - Belgeleri sisteme alma
- **Text Splitter** - Parçalara bölme
- **Embedding Service** - Vektör oluşturma
- **Vector Store** - Vektör depolama (pgvector/Pinecone)
- **Retriever** - Benzerlik arama
- **Reranker** - Sonuçları yeniden sıralama

### 7. Memory System

**Görevi:** Konuşma geçmişi ve user context

**Bileşenler:**
- **Short-term Memory** - Oturum içi bellek
- **Long-term Memory** - Kalıcı bellek
- **User Profile** - Kullanıcı profili
- **Memory Retriever** - Geçmişe erişim

### 8. Cache Layer

**Görevi:** Performans optimizasyonu

**Bileşenler:**
- **Agent Cache** - Oluşturulan agent'lar
- **Response Cache** - LLM cevapları
- **Embedding Cache** - Embedding sonuçları
- **Session Cache** - Oturum verileri

### 9. Data Layer

**Görevi:** Kalıcı veri depolama

**Bileşenler:**
- **PostgreSQL** - Session, messages, documents
- **pgvector** - Vector operations
- **Redis** - Cache, session store
- **S3/MinIO** - Document storage

### 10. Monitoring Layer

**Görevi:** Sistem izleme

**Bileşenler:**
- **Metrics Collector** (Prometheus)
- **Log Aggregator** (Structured logs)
- **Tracing** (Jaeger/Zipkin)
- **Health Checks**
- **Alert Manager**

### 11. Authentication Layer

**Görevi:** Kimlik doğrulama ve yetkilendirme

**Bileşenler:**
- **JWT Handler**
- **OAuth2 Provider**
- **API Key Management**
- **Role-based Access Control**

---

## 🏗️ Katmanlı Mimari Tasarımı

### Katman 1: Interface Layer (Arayüz)

**Responsibilities:**
- HTTP request handling
- WebSocket management
- API documentation
- Input validation
- Output formatting

**Components:**
```
src/
├── api/
│   ├── http/
│   │   ├── endpoints/          # REST endpoints
│   │   ├── middleware/         # CORS, auth, logging
│   │   ├── schemas/           # Request/Response models
│   │   └── validators/        # Input validation
│   ├── websocket/
│   │   ├── handlers/          # WS handlers
│   │   └── connection_manager.py
│   └── api_gateway.py         # Main API app
```

### Katman 2: Application Layer (Uygulama)

**Responsibilities:**
- Use case orchestration
- Business logic
- Transaction management
- Cross-cutting concerns (logging, metrics)

**Components:**
```
src/
├── application/
│   ├── services/
│   │   ├── chat_service.py         # Chat use case
│   │   ├── rag_service.py          # RAG use case
│   │   ├── session_service.py      # Session management
│   │   ├── agent_service.py        # Agent orchestration
│   │   └── memory_service.py       # Memory management
│   ├── workflows/
│   │   └── multi_agent_workflow.py # Complex workflows
│   ├── commands/                   # Command pattern
│   └── queries/                    # Query pattern
```

### Katman 3: Domain Layer (Alan)

**Responsibilities:**
- Core business rules
- Domain entities
- Value objects
- Domain events
- Business invariants

**Components:**
```
src/
├── domain/
│   ├── entities/
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── agent.py
│   │   ├── message.py
│   │   └── document.py
│   ├── value_objects/
│   │   ├── session_id.py
│   │   ├── user_id.py
│   │   └── message_type.py
│   ├── events/
│   │   ├── session_created.py
│   │   ├── message_sent.py
│   │   └── agent_invoked.py
│   └── repositories/
│       ├── session_repository.py      # Interfaces
│       ├── message_repository.py
│       └── document_repository.py
```

### Katman 4: Infrastructure Layer (Altyapı)

**Responsibilities:**
- External service integration
- Database access
- Third-party API calls
- Technical implementations

**Components:**
```
src/
├── infrastructure/
│   ├── database/
│   │   ├── postgresql/
│   │   │   ├── session_repository_impl.py
│   │   │   ├── message_repository_impl.py
│   │   │   └── connection.py
│   │   ├── redis/
│   │   │   ├── cache.py
│   │   │   └── session_store.py
│   │   └── migrations/
│   ├── llm_providers/
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── ollama_provider.py
│   │   └── provider_factory.py
│   ├── storage/
│   │   ├── vector_store.py      # pgvector/Pinecone
│   │   ├── document_store.py    # S3/MinIO
│   │   └── embedding_service.py
│   ├── mcp/
│   │   ├── mcp_client.py
│   │   ├── tool_registry.py
│   │   └── mcp_transport.py
│   ├── cache/
│   │   ├── agent_cache.py
│   │   ├── response_cache.py
│   │   └── cache_interface.py
│   └── monitoring/
│       ├── metrics.py
│       ├── logging.py
│       └── health_checks.py
```

### Katman 5: Configuration Layer (Konfigürasyon)

**Responsibilities:**
- Environment configuration
- Service configuration
- Feature flags
- Secrets management

**Components:**
```
src/
├── config/
│   ├── settings.py              # Pydantic settings
│   ├── providers/
│   │   ├── llm_config.py
│   │   ├── database_config.py
│   │   ├── cache_config.py
│   │   └── mcp_config.py
│   └── feature_flags.py
```

---

## 🔄 Katmanlar Arası Akış

### Chat Request Flow

```
┌─────────────────────────┐
│  1. Client Request      │
│  (HTTP/WebSocket)       │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  2. Interface Layer     │
│  - Validation           │
│  - Authentication       │
│  - Rate Limiting        │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  3. Session Middleware  │
│  - Get/Create Session   │
│  - Load User Context    │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  4. Application Layer   │
│  - ChatService.run()    │
│  - Orchestrate Flow     │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  5. Agent Orchestrator  │
│  - Get/Create Agent     │
│  - Check Cache          │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  6. RAG System          │
│  - Retrieve Context     │
│  - Search Vectors       │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  7. LLM Provider        │
│  - Generate Response    │
│  - Count Tokens         │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  8. MCP Tools           │
│  - Execute Tools        │
│  - Aggregate Results    │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  9. Memory System       │
│  - Store Conversation   │
│  - Update Context       │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  10. Cache Layer        │
│  - Cache Response       │
│  - Update Agent Cache   │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  11. Monitoring         │
│  - Record Metrics       │
│  - Log Events           │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  12. Response           │
│  (Reverse flow back)    │
└─────────────────────────┘
```

### Dependency Flow (Startup)

```
Configuration Layer
        │
        ▼
Infrastructure Layer
    ├─ Init Database
    ├─ Init Cache
    ├─ Init LLM Providers
    └─ Init Monitoring
        │
        ▼
Domain Layer
    ├─ Register Repositories
    ├─ Register Domain Events
    └─ Register Value Objects
        │
        ▼
Application Layer
    ├─ Register Services
    ├─ Register Use Cases
    └─ Register Workflows
        │
        ▼
Interface Layer
    ├─ Register Routes
    ├─ Register Middleware
    └─ Start Server
```

---

## 🛠️ Teknoloji Stack'i

### Backend Framework

**FastAPI** ✅
- Modern, fast (high-performance)
- Automatic API documentation
- Type hints support
- Async/await native
- WebSocket support

### LLM Integration

**PydanticAI / LangChain** ✅
- Agent framework
- Tool integration
- Chain composition
- Memory management

**Providers:**
- **OpenAI** - GPT-4, GPT-3.5
- **Anthropic** - Claude
- **Ollama** - Local models (Llama, Mistral, CodeLlama)

### Databases

**PostgreSQL** ✅
- ACID compliance
- JSON support
- Extensions (pgvector)
- Mature ecosystem

**pgvector** ✅
- Vector similarity search
- SQL integration
- Reliable

**Redis** ✅
- Session store
- Cache layer
- Pub/Sub
- High performance

### Vector Storage

**pgvector (PostgreSQL extension)** ✅
- Simple setup
- SQL queries
- ACID compliance

**Alternatives:**
- **Pinecone** - Cloud vector DB
- **Weaviate** - Vector search engine
- **Chroma** - Python vector DB
- **Qdrant** - Rust vector search

### MCP Framework

**FastMCP** ✅
- Python MCP framework
- Multiple transports
- Easy tool definition

### Monitoring

**Prometheus** ✅
- Metrics collection
- Time-series database
- Alerting rules

**Grafana** ✅
- Visualization
- Dashboards
- Data exploration

**Structured Logging**
- JSON logs
- Contextual information
- Log aggregation (ELK stack)

### Frontend

**Chainlit** ✅
- Python-native chat UI
- Easy to customize
- Real-time updates

**Alternatives:**
- **Streamlit** - General-purpose web app
- **Next.js** - React-based UI
- **Svelte** - Lightweight UI

### Infrastructure

**Docker** ✅
- Containerization
- Multi-stage builds
- GPU support

**Docker Compose** ✅
- Local orchestration
- Multi-service setup

**Alternatives for Production:**
- **Kubernetes** - Container orchestration
- **Helm** - K8s package manager
- **Terraform** - Infrastructure as Code

### Testing

**pytest** ✅
- Python testing framework
- Fixtures
- Markers
- Async testing

**Test Tools:**
- **HTTPie** / **curl** - API testing
- **Locust** - Load testing
- **Playwright** - E2E testing

---

## 📁 Proje Klasör Yapısı

```
ai-multi-agent-system/
├── README.md
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── Makefile
│
├── src/
│   └── ai_system/
│       ├── __init__.py
│       │
│       ├── config/
│       │   ├── __init__.py
│       │   ├── settings.py
│       │   ├── llm_config.py
│       │   ├── database_config.py
│       │   └── feature_flags.py
│       │
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── entities/
│       │   │   ├── __init__.py
│       │   │   ├── user.py
│       │   │   ├── session.py
│       │   │   ├── agent.py
│       │   │   ├── message.py
│       │   │   └── document.py
│       │   │
│       │   ├── value_objects/
│       │   │   ├── __init__.py
│       │   │   ├── session_id.py
│       │   │   ├── user_id.py
│       │   │   └── message_type.py
│       │   │
│       │   ├── events/
│       │   │   ├── __init__.py
│       │   │   ├── session_created.py
│       │   │   ├── message_sent.py
│       │   │   └── agent_invoked.py
│       │   │
│       │   └── repositories/
│       │       ├── __init__.py
│       │       ├── session_repository.py
│       │       ├── message_repository.py
│       │       └── document_repository.py
│       │
│       ├── application/
│       │   ├── __init__.py
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   ├── chat_service.py
│       │   │   ├── rag_service.py
│       │   │   ├── session_service.py
│       │   │   ├── agent_service.py
│       │   │   └── memory_service.py
│       │   │
│       │   ├── workflows/
│       │   │   ├── __init__.py
│       │   │   └── multi_agent_workflow.py
│       │   │
│       │   ├── commands/
│       │   │   └── __init__.py
│       │   │
│       │   └── queries/
│       │       └── __init__.py
│       │
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   │
│       │   ├── database/
│       │   │   ├── __init__.py
│       │   │   ├── postgresql/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── connection.py
│       │   │   │   ├── session_repository_impl.py
│       │   │   │   └── message_repository_impl.py
│       │   │   │
│       │   │   ├── redis/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── cache.py
│       │   │   │   └── session_store.py
│       │   │   │
│       │   │   └── migrations/
│       │   │       └── 001_initial.sql
│       │   │
│       │   ├── llm_providers/
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── openai_provider.py
│       │   │   ├── anthropic_provider.py
│       │   │   ├── ollama_provider.py
│       │   │   └── provider_factory.py
│       │   │
│       │   ├── storage/
│       │   │   ├── __init__.py
│       │   │   ├── vector_store.py
│       │   │   ├── document_store.py
│       │   │   └── embedding_service.py
│       │   │
│       │   ├── mcp/
│       │   │   ├── __init__.py
│       │   │   ├── mcp_client.py
│       │   │   ├── tool_registry.py
│       │   │   └── mcp_transport.py
│       │   │
│       │   ├── cache/
│       │   │   ├── __init__.py
│       │   │   ├── agent_cache.py
│       │   │   ├── response_cache.py
│       │   │   └── cache_interface.py
│       │   │
│       │   └── monitoring/
│       │       ├── __init__.py
│       │       ├── metrics.py
│       │       ├── logging.py
│       │       └── health_checks.py
│       │
│       ├── interface/
│       │   ├── __init__.py
│       │   ├── api/
│       │   │   ├── __init__.py
│       │   │   ├── http/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── main.py
│       │   │   │   ├── endpoints/
│       │   │   │   │   ├── __init__.py
│       │   │   │   │   ├── chat.py
│       │   │   │   │   ├── session.py
│       │   │   │   │   └── rag.py
│       │   │   │   ├── middleware/
│       │   │   │   │   ├── __init__.py
│       │   │   │   │   ├── auth.py
│       │   │   │   │   ├── cors.py
│       │   │   │   │   ├── rate_limit.py
│       │   │   │   │   └── logging.py
│       │   │   │   ├── schemas/
│       │   │   │   │   ├── __init__.py
│       │   │   │   │   ├── chat.py
│       │   │   │   │   └── session.py
│       │   │   │   └── validators/
│       │   │   │       └── __init__.py
│       │   │   │
│       │   │   └── websocket/
│       │   │       ├── __init__.py
│       │   │       ├── handlers/
│       │   │       │   ├── __init__.py
│       │   │       │   └── chat.py
│       │   │       └── connection_manager.py
│       │   │
│       │   └── ui/
│       │       ├── __init__.py
│       │       ├── chainlit_app.py
│       │       └── components/
│       │           ├── __init__.py
│       │           ├── chat_interface.py
│       │           └── session_list.py
│       │
│       └── shared/
│           ├── __init__.py
│           ├── exceptions.py
│           ├── types.py
│           └── utils.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_api.py
│   │   ├── test_database.py
│   │   └── test_llm_providers.py
│   └── e2e/
│       ├── __init__.py
│       └── test_chat_flow.py
│
├── scripts/
│   ├── setup.sh
│   ├── migrate.sh
│   └── healthcheck.sh
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── deployment.md
│
└── monitoring/
    ├── prometheus/
    │   └── prometheus.yml
    └── grafana/
        ├── dashboards/
        └── provisioning/
            ├── datasources/
            └── dashboards/
```

### Modülerlik Prensipleri

1. **Clear Boundaries** - Her modül net sınırlara sahip
2. **Public Interfaces** - `__init__.py` ile export'lar
3. **Dependency Rules** - Yukarıdan aşağı bağımlılık
4. **Separation of Concerns** - Her dosya tek sorumluluk
5. **Testability** - Her bileşen test edilebilir

---

## 🚀 Geliştirme Adımları

### Faz 1: Temel Altyapı (Week 1)

#### Day 1-2: Proje Setup
```bash
# 1. Proje oluştur
mkdir ai-multi-agent-system
cd ai-multi-agent-system

# 2. Poetry init
poetry init

# 3. Klasör yapısını oluştur
python scripts/create_structure.py

# 4. Git init
git init
```

#### Day 3-4: Configuration
- Pydantic settings setup
- Environment variables
- Database connection config
- LLM provider config

#### Day 5-6: Database Schema
- PostgreSQL schema design
- pgvector extension
- Migration scripts
- Repository interfaces

#### Day 7: Testing Infrastructure
- pytest setup
- Test database
- First unit test

### Faz 2: Core Domain (Week 2)

#### Day 8-10: Domain Layer
- Entity definitions
- Value objects
- Domain events
- Repository interfaces

#### Day 11-12: Application Layer
- Use cases
- Services
- Dependency injection

#### Day 13-14: Basic API
- FastAPI setup
- Simple endpoints
- Request/Response models

### Faz 3: LLM Integration (Week 3)

#### Day 15-17: LLM Providers
- OpenAI provider
- Ollama provider
- Provider factory
- Token counting

#### Day 18-19: Agent Framework
- Base agent class
- Tool system
- Agent factory
- Agent registry

#### Day 20-21: Agent Caching
- Redis setup
- Agent cache implementation
- TTL management

### Faz 4: Session & Memory (Week 4)

#### Day 22-24: Session Management
- Session repository
- Session service
- Session middleware
- User context

#### Day 25-26: Memory System
- Short-term memory
- Message storage
- Context management

#### Day 27-28: Chat Flow
- End-to-end chat
- Message persistence
- Response generation

### Faz 5: RAG System (Week 5)

#### Day 29-31: Vector Storage
- Document model
- Vector operations
- Embedding service

#### Day 32-33: Document Ingestion
- File upload
- Text splitting
- Embedding generation

#### Day 34-35: Retrieval
- Similarity search
- Reranking
- Context injection

### Faz 6: MCP Integration (Week 6)

#### Day 36-38: MCP Client
- FastMCP setup
- Tool registration
- Tool execution

#### Day 39-40: Tool Development
- RAG tool
- Memory tool
- Custom tools

### Faz 7: UI & Monitoring (Week 7)

#### Day 41-43: Chainlit UI
- Chat interface
- Session management
- Real-time updates

#### Day 44-45: Monitoring
- Prometheus metrics
- Structured logging
- Health checks

### Faz 8: Polish & Deploy (Week 8)

#### Day 46-48: Testing
- Integration tests
- E2E tests
- Load tests

#### Day 49-50: Documentation
- API docs
- Architecture docs
- Deployment guide

#### Day 51-56: Deployment
- Docker setup
- Docker Compose
- Production config

---

## 📊 Sistem Şeması

### Metinsel Sistem Şeması

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │   Browser    │  │  Mobile App  │  │    CLI       │                      │
│  │   (Chainlit) │  │              │  │              │                      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                      │
│         │                 │                  │                             │
│         └─────────────────┴──────────────────┘                             │
│                            │                                                │
└────────────────────────────┼────────────────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────────────┐
│                        API GATEWAY                                         │
├────────────────────────────┼────────────────────────────────────────────────┤
│                            │                                                │
│  ┌─────────────────────────▼─────────────────────────┐                     │
│  │         FastAPI HTTP Server                        │                     │
│  │  ┌──────────────────────────────────────────────┐  │                     │
│  │  │  Middleware Stack                            │  │                     │
│  │  │  1. CORS                                     │  │                     │
│  │  │  2. Authentication                           │  │                     │
│  │  │  3. Rate Limiting                            │  │                     │
│  │  │  4. Logging                                  │  │                     │
│  │  │  5. Metrics                                  │  │                     │
│  │  └──────────────────────────────────────────────┘  │                     │
│  │                                                     │                     │
│  │  ┌──────────────────────────────────────────────┐  │                     │
│  │  │  Endpoints                                   │  │                     │
│  │  │  • POST /chat                                │  │                     │
│  │  │  • POST /chat/stream                         │  │                     │
│  │  │  • POST /sessions                            │  │                     │
│  │  │  • GET /sessions/{id}                        │  │                     │
│  │  │  • POST /documents/upload                    │  │                     │
│  │  │  • GET /health                               │  │                     │
│  │  │  • GET /metrics                              │  │                     │
│  │  └──────────────────────────────────────────────┘  │                     │
│  └─────────────────────────┬─────────────────────────┘                     │
│                            │                                                │
└────────────────────────────┼────────────────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────────────┐
│                     SESSION MANAGEMENT                                      │
├────────────────────────────┼────────────────────────────────────────────────┤
│                            │                                                │
│  ┌─────────────────────────▼─────────────────────────┐                     │
│  │           Session Store (Redis)                    │                     │
│  │  ┌──────────────────────────────────────────────┐  │                     │
│  │  │  Session Data                                 │  │                     │
│  │  │  • User ID                                    │  │                     │
│  │  │  • Session State                              │  │                     │
│  │  │  • Current Agent                              │  │                     │
│  │  │  • Conversation Context                       │  │                     │
│  │  │  • Metadata                                   │  │                     │
│  │  └──────────────────────────────────────────────┘  │                     │
│  └─────────────────────────┬─────────────────────────┘                     │
│                            │                                                │
└────────────────────────────┼────────────────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────────────┐
│                   APPLICATION LAYER                                        │
├────────────────────────────┼────────────────────────────────────────────────┤
│                            │                                                │
│  ┌─────────────────────────▼─────────────────────────┐                     │
│  │          Chat Service                              │                     │
│  │  ┌──────────────────────────────────────────────┐  │                     │
│  │  │  Use Cases                                   │  │                     │
│  │  │  • Process Chat Request                      │  │                     │
│  │  │  • Orchestrate Agents                        │  │                     │
│  │  │  • Manage Flow                               │  │                     │
│  │  │  • Handle Errors                             │  │                     │
│  │  └──────────────────────────────────────────────┘  │                     │
│  └─────────────────────────┬─────────────────────────┘                     │
│                            │                                                │
│  ┌─────────────────────────▼─────────────────────────┐                     │
│  │         Agent Orchestrator                         │                     │
│  │  ┌──────────────────────────────────────────────┐  │                     │
│  │  │  Agent Registry                              │  │                     │
│  │  │  • Available Agents                          │  │                     │
│  │  │  • Agent Types                               │  │                     │
│  │  │  • Agent Config                              │  │                     │
│  │  └──────────────────────────────────────────────┘  │                     │
│  │                                                     │                     │
│  │  ┌──────────────────────────────────────────────┐  │                     │
│  │  │  Agent Factory                               │  │                     │
│  │  │  • Create Agents                             │  │                     │
│  │  │  • Configure Tools                           │  │                     │
│  │  │  • Set System Prompt                         │  │                     │
│  │  └──────────────────────────────────────────────┘  │                     │
│  └─────────────────────────┬─────────────────────────┘                     │
│                            │                                                │
└────────────────────────────┼────────────────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────────────┐
│                    DOMAIN LAYER                                            │
├────────────────────────────┼────────────────────────────────────────────────┤
│                            │                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │    User      │  │   Session    │  │    Agent     │                      │
│  │   Entity     │  │   Entity     │  │   Entity     │                      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                      │
│         │                 │                  │                             │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐                      │
│  │    User      │  │   Session    │  │    Agent     │                      │
│  │     ID       │  │      ID      │  │     Type     │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │   Message    │  │  Document    │  │   Message    │                      │
│  │   Entity     │  │   Entity     │  │    Type      │                      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                      │
│         │                 │                  │                             │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐                      │
│  │  Session     │  │   Vector     │  │    Role      │                      │
│  │   Created    │  │  Embedding   │  │   (user/     │                      │
│  │    Event     │  │              │  │  assistant)  │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────┐                   │
│  │        Repository Interfaces                        │                   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │                   │
│  │  │  Session    │  │  Message    │  │  Document   │ │                   │
│  │  │ Repository  │  │ Repository  │  │ Repository  │ │                   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │                   │
│  └─────────────────────────────────────────────────────┘                   │
│                                                                             │
└────────────────────────────┼────────────────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────────────┐
│                INFRASTRUCTURE LAYER                                         │
├────────────────────────────┼────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │  PostgreSQL  │  │    Redis     │  │  PostgreSQL  │                      │
│  │  (Sessions & │  │   (Cache &   │  │  (pgvector)  │                      │
│  │   Messages)  │  │   Sessions)  │  │              │                      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                      │
│         │                 │                  │                             │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐                      │
│  │  Session     │  │   Agent      │  │  Document    │                      │
│  │ Repository   │  │    Cache     │  │  Storage     │                      │
│  │   Impl       │  │   (Redis)    │  │   (S3/MinIO) │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              LLM Provider Layer                                      │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │   OpenAI     │  │  Anthropic   │  │   Ollama     │             │   │
│  │  │  Provider    │  │   Provider   │  │  Provider    │             │   │
│  │  │  (GPT-4)     │  │   (Claude)   │  │   (Local)    │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │              Provider Factory                                │   │   │
│  │  │  • Runtime provider selection                                │   │   │
│  │  │  • Token counting                                            │   │   │
│  │  │  • Cost tracking                                             │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              MCP Integration Layer                                  │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │  MCP Client  │  │  Tool        │  │   MCP        │             │   │
│  │  │             │  │  Registry    │  │  Transport   │             │   │
│  │  │  • HTTP      │  │             │  │             │             │   │
│  │  │  • WebSocket│  │  • RAG Tool  │  │  • HTTP      │             │   │
│  │  │  • STDIO     │  │  • Memory    │  │  • WebSocket│             │   │
│  │  │             │  │  • Custom     │  │  • STDIO     │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              RAG System                                              │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │  Document    │  │  Text        │  │  Embedding   │             │   │
│  │  │  Ingestion   │  │  Splitter    │  │  Service     │             │   │
│  │  │             │  │             │  │             │             │   │
│  │  │  • Upload    │  │  • Semantic  │  │  • OpenAI    │             │   │
│  │  │  • Parse     │  │  • Chunking  │  │  • Local     │             │   │
│  │  │  • Store     │  │  • Overlap   │  │  • Caching   │             │   │
│  │  └──────┬───────┘  └──────────────┘  └──────────────┘             │   │
│  │         │                                                          │   │
│  │  ┌──────▼─────────────────┐  ┌──────────────┐                      │   │
│  │  │  Vector Store          │  │  Retriever   │                      │   │
│  │  │  (pgvector)            │  │              │                      │   │
│  │  │                        │  │  • Similarity│                      │   │
│  │  │  • Store Vectors       │  │  • Reranking │                      │   │
│  │  │  • Index Management    │  │  • Filtering │                      │   │
│  │  │  • Query Optimization  │  └──────────────┘                      │   │
│  │  └────────────────────────┘                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              Memory System                                           │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │  Short-term  │  │  Long-term   │  │   User       │             │   │
│  │  │   Memory     │  │   Memory     │  │  Profile     │             │   │
│  │  │              │  │              │  │              │             │   │
│  │  │  • Current   │  │  • Persistent│  │  • Preferences│             │   │
│  │  │    Session   │  │    History   │  │  • Settings  │             │   │
│  │  │  • Context   │  │  • Knowledge │  │  • Tier      │             │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────────┘             │   │
│  │         │                 │                                      │   │
│  │  ┌──────▼───────┐  ┌──────▼───────┐                            │   │
│  │  │  Conversation│  │  Knowledge   │                            │   │
│  │  │  History     │  │  Base        │                            │   │
│  │  └──────────────┘  └──────────────┘                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              Monitoring Layer                                        │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │  Prometheus  │  │  Structured  │  │   Health     │             │   │
│  │  │   Metrics    │  │    Logging   │  │   Checks     │             │   │
│  │  │             │  │             │  │             │             │   │
│  │  │  • Request   │  │  • JSON Logs│  │  • Database  │             │   │
│  │  │    Count     │  │  • Context  │  │  • Redis     │             │   │
│  │  │  • Latency   │  │  • Trace ID │  │  • LLM       │             │   │
│  │  │  • Token     │  │  • User ID  │  │  Status      │             │   │
│  │  │    Usage     │  │             │  │             │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Veri Akışı Diyagramı

```
┌──────────────┐
│   Client     │
│  (Request)   │
└──────┬───────┘
       │
       ▼
┌────────────────────────────────────────┐
│        HTTP Request                     │
│   • Validation                         │
│   • Authentication                     │
│   • Rate Limiting                      │
└──────────┬─────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────┐
│      Session Middleware                │
│   1. Get/Create Session (Redis)        │
│   2. Load User Context                 │
│   3. Extract User ID                   │
└──────────┬─────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────┐
│      Application Layer                 │
│   ChatService.process_request()        │
│   • Parse request                      │
│   • Get session                        │
│   • Orchestrate flow                   │
└──────────┬─────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────┐
│     Agent Orchestrator                 │
│   1. Check Agent Cache (Redis)         │
│      ├─ HIT: Use cached agent          │
│      └─ MISS: Create new agent         │
│                                          │
│   2. Configure Agent                   │
│      • Set system prompt               │
│      • Register tools                  │
│      • Set memory                      │
└──────────┬─────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────┐
│        RAG System                      │
│   1. Query Vector Store                │
│      • Embed query                     │
│      • Search similar documents        │
│      • Retrieve top-k results          │
│                                          │
│   2. Rerank results                    │
│      • Score relevance                 │
│      • Filter duplicates               │
│                                          │
│   3. Format context                    │
│      • Combine documents               │
│      • Add metadata                    │
└──────────┬─────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────┐
│        LLM Provider                    │
│   1. Build prompt                      │
│      • System prompt                   │
│      • Context (RAG results)           │
│      • User message                    │
│      • Conversation history            │
│                                          │
│   2. Generate response                 │
│      • Call LLM API                    │
│      • Stream tokens (optional)        │
│      • Count tokens                    │
│                                          │
│   3. Post-process                      │
│      • Parse response                  │
│      • Extract tool calls              │
└──────────┬─────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────┐
│       MCP Tools (if needed)            │
│   1. Execute tool calls                │
│      • Call external APIs              │
│      • Query databases                 │
│      • Run custom functions            │
│                                          │
│   2. Aggregate results                 │
│      • Collect tool outputs            │
│      • Format for LLM                  │
└──────────┬─────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────┐
│        Memory System                   │
│   1. Update conversation               │
│      • Store user message              │
│      • Store assistant response        │
│                                          │
│   2. Update context                    │
│      • Add to short-term memory        │
│      • Persist important info          │
│                                          │
│   3. Save to database                  │
│      • PostgreSQL (messages table)     │
└──────────┬─────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────┐
│        Response                        │
│   1. Update cache                      │
│      • Cache LLM response              │
│      • Cache agent instance            │
│                                          │
│   2. Send response                     │
│      • Format output                   │
│      • Stream or direct                │
│                                          │
│   3. Update session                    │
│      • Set current agent               │
│      • Update timestamp                │
└──────────┬─────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────┐
│        Monitoring                      │
│   • Record metrics                     │
│     - Request count                    │
│     - Response time                    │
│     - Token usage                      │
│   • Log events                         │
│     - User action                      │
│     - Response generated               │
│   • Update health checks               │
└──────────┬─────────────────────────────┘
           │
           ▼
┌──────────────┐
│   Client     │
│ (Response)   │
└──────────────┘
```

---

## 💎 En İyi Uygulamalar

### 1. Kod Kalitesi

```python
# ✅ GOOD: Clear interface
class SessionRepository:
    async def create(self, user_id: str) -> SessionId:
        """Create new session for user"""
        pass

    async def get(self, session_id: SessionId) -> Optional[Session]:
        """Get session by ID"""
        pass

# ✅ GOOD: Type hints
async def process_chat(
    self,
    message: str,
    session_id: SessionId,
    user_id: UserId
) -> ChatResponse:
    pass
```

### 2. Error Handling

```python
# ✅ GOOD: Specific exceptions
class SessionNotFoundError(Exception):
    """Session does not exist"""

class LLMProviderError(Exception):
    """LLM provider failure"""

# ✅ GOOD: Error propagation
try:
    response = await self.llm_provider.generate(prompt)
except ProviderError as e:
    logger.error(f"LLM provider failed: {e}")
    raise ChatServiceError(f"Failed to generate response") from e
```

### 3. Configuration

```python
# ✅ GOOD: Type-safe config
class LLMSettings(BaseSettings):
    provider: Literal["openai", "anthropic", "ollama"]
    model: str
    api_key: str
    max_tokens: int = 1000
    temperature: float = 0.7

    class Config:
        env_prefix = "LLM_"
```

### 4. Logging

```python
# ✅ GOOD: Structured logging
logger.info(
    "Processing chat request",
    extra={
        "user_id": user_id,
        "session_id": session_id,
        "request_id": request_id,
        "action": "chat_request"
    }
)
```

### 5. Testing

```python
# ✅ GOOD: Unit test with mocks
@pytest.mark.asyncio
async def test_create_agent():
    # Given
    session_id = SessionId("test-id")
    agent_factory = AgentFactory(mock_provider)

    # When
    agent = await agent_factory.create(session_id)

    # Then
    assert agent is not None
    assert agent.session_id == session_id
```

### 6. Monitoring

```python
# ✅ GOOD: Metrics collection
REQUEST_COUNT.labels(
    method="POST",
    endpoint="/chat",
    status="success"
).inc()

REQUEST_DURATION.observe(duration)
```

---

## 📝 Sonuç

Bu rehber, **sade, genişletilebilir ve yönetimi kolay** bir AI multi-agent sistemi tasarlamak için gerekli tüm bilgileri içermektedir.

### Önemli Noktalar:

1. **Sadelik** - Karmaşıklığı minimize edin
2. **Net Sınırlar** - Her katmanın sorumlulukları net olsun
3. **Test Edilebilirlik** - Her bileşen test edilebilir olsun
4. **Gözlemlenebilirlik** - Sistem durumu net görülebilsin
5. **Iteratif Geliştirme** - Küçük adımlarla ilerleyin

### Önerilen İlerleyiş:

1. **Faz 1-2**: Temel altyapı ve domain
2. **Faz 3-4**: LLM ve session yönetimi
3. **Faz 5-6**: RAG ve MCP
4. **Faz 7-8**: UI, monitoring ve deployment

Bu yaklaşımla, sade ama güçlü bir sistem inşa edebilirsiniz!
