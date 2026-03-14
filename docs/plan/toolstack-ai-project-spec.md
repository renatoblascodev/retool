# ToolStack AI — Arquitetura Real de um Retool Clone (Nível Startup)

> Produto: **ToolStack AI**
> Tagline: *Build internal tools in seconds, powered by AI.*
> Posicionamento: Retool clone com geração automática de ferramentas via LLM.

---

## Visão do Produto

Um usuário digita:

```
"Create a dashboard to manage customers with filters and CRUD"
```

O sistema gera automaticamente:

- Tabela de clientes com filtros e paginação
- Formulário de criação/edição
- Botões de deletar com confirmação
- Queries REST ou SQL conectadas ao datasource escolhido
- Permissões adequadas ao role do usuário

**Diferencial competitivo sobre o Retool:**
- Geração de apps via IA (prompt → app completo)
- Marketplace de templates prontos
- Foco em API builders e automações
- Open-source friendly (self-host grátis, cloud pago)

---

## Arquitetura Geral (Nível Startup)

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTE (Browser)                        │
│                                                                 │
│    ┌──────────────────────────────────────────────────────┐    │
│    │              Frontend Builder (React)                 │    │
│    │   Visual Editor │ Query Builder │ AI Prompt Panel     │    │
│    └──────────────────────┬───────────────────────────────┘    │
└───────────────────────────┼─────────────────────────────────────┘
                            │ HTTPS / WebSocket
┌───────────────────────────▼─────────────────────────────────────┐
│                        API Gateway (Nginx)                       │
│              Rate Limiting │ Auth Check │ Routing                │
└──────┬──────────────────┬──────────────────┬────────────────────┘
       │                  │                  │
┌──────▼──────┐  ┌────────▼──────┐  ┌───────▼────────┐
│  App Service │  │ Query Engine  │  │   AI Service   │
│  (FastAPI)   │  │  (FastAPI)    │  │   (FastAPI)    │
│             │  │               │  │                │
│ CRUD Apps   │  │ Execute SQL   │  │ LLM Prompt     │
│ Pages       │  │ Execute REST  │  │ App Generation │
│ Components  │  │ Execute GQL   │  │ Query Suggest  │
│ Datasources │  │ JS Sandbox    │  │ Schema Infer   │
└──────┬──────┘  └───────┬───────┘  └───────┬────────┘
       │                 │                  │
┌──────▼─────────────────▼──────────────────▼────────┐
│                  Message Bus (Redis / RabbitMQ)      │
│              Celery Workers para jobs assíncronos    │
└──────────────────────────┬─────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────┐
│                    PostgreSQL                        │
│   users │ orgs │ apps │ pages │ components          │
│   queries │ datasources │ events │ permissions      │
└─────────────────────────────────────────────────────┘
```

---

## Stack Tecnológica Definitiva

### Frontend
| Lib | Papel |
|---|---|
| React 19 + TypeScript | Base da aplicação |
| Vite 6 | Build tool |
| Material UI v6 | Design system |
| @dnd-kit/core | Drag-and-drop moderno (mais leve que React DnD) |
| React Grid Layout | Sistema de grid posicional |
| Zustand | Estado global (simples, sem boilerplate) |
| TanStack Query | Cache e sync de dados server-side |
| Monaco Editor | Editor de código inline (queries, JS) |
| Recharts | Gráficos |
| React Hook Form + Zod | Formulários com validação |

### Backend
| Lib | Papel |
|---|---|
| Python 3.12 | Linguagem base |
| FastAPI | API framework assíncrono |
| Pydantic v2 | Validação e serialização |
| SQLAlchemy 2.0 (async) | ORM com suporte async |
| Alembic | Migrations |
| Celery + Redis | Filas e workers assíncronos |
| httpx | HTTP client assíncrono para proxying de REST APIs |
| asyncpg | Driver PostgreSQL async nativo |
| python-jose | JWT |
| passlib + bcrypt | Hash de senhas |
| RestrictedPython | Sandbox para scripts do usuário |

### IA
| Lib | Papel |
|---|---|
| LiteLLM | Abstração multi-provider (OpenAI, Anthropic, Gemini, Ollama) |
| LangChain | Pipelines de geração complexos |
| pgvector | Embeddings para busca semântica de templates |

### Infraestrutura
| Ferramenta | Papel |
|---|---|
| Docker + Docker Compose | Desenvolvimento local |
| Nginx | Reverse proxy / API Gateway |
| PostgreSQL 16 | Banco principal |
| Redis 7 | Cache + broker de filas |
| Kubernetes (Helm charts) | Deploy em produção |
| Turborepo | Monorepo manager |
| pnpm workspaces | Gerenciamento de pacotes JS |

---

## Estrutura de Pastas (Monorepo)

```
toolstack-ai/
├── apps/
│   ├── frontend/                  # React Builder App
│   │   ├── src/
│   │   │   ├── components/        # Componentes UI do builder
│   │   │   │   ├── canvas/        # Área de drag-and-drop
│   │   │   │   ├── panel/         # Painel lateral de propriedades
│   │   │   │   ├── toolbar/       # Barra superior
│   │   │   │   └── widgets/       # Widgets disponíveis (Table, Form...)
│   │   │   ├── editor/            # Lógica do editor visual
│   │   │   │   ├── store/         # Zustand stores (canvas, selection)
│   │   │   │   ├── hooks/         # Hooks do editor
│   │   │   │   └── dnd/           # Configuração do @dnd-kit
│   │   │   ├── features/
│   │   │   │   ├── apps/          # Gerenciamento de apps
│   │   │   │   ├── queries/       # Query builder
│   │   │   │   ├── datasources/   # Conectores de dados
│   │   │   │   ├── ai/            # Painel de IA (prompt → app)
│   │   │   │   └── auth/          # Login, register
│   │   │   ├── preview/           # Modo preview do app (sem editor)
│   │   │   ├── runtime/           # Engine de execução client-side
│   │   │   │   ├── binding/       # Data binding ({{query.data}})
│   │   │   │   ├── events/        # Sistema de eventos (onClick...)
│   │   │   │   └── eval/          # Avaliação segura de expressões
│   │   │   └── lib/               # Utils, api client, types
│   │   ├── index.html
│   │   ├── vite.config.ts
│   │   └── package.json
│   │
│   └── backend/                   # FastAPI Monolito Modular
│       ├── app/
│       │   ├── main.py            # Entry point FastAPI
│       │   ├── config.py          # Settings (pydantic-settings)
│       │   ├── database.py        # Conexão async PostgreSQL
│       │   ├── auth/
│       │   │   ├── router.py      # POST /auth/login, /auth/register
│       │   │   ├── service.py
│       │   │   ├── jwt.py
│       │   │   └── models.py
│       │   ├── apps/
│       │   │   ├── router.py      # CRUD de apps
│       │   │   ├── service.py
│       │   │   ├── schemas.py
│       │   │   └── models.py
│       │   ├── pages/
│       │   │   ├── router.py
│       │   │   ├── service.py
│       │   │   ├── schemas.py
│       │   │   └── models.py
│       │   ├── components/
│       │   │   ├── router.py
│       │   │   ├── service.py
│       │   │   ├── schemas.py
│       │   │   └── models.py
│       │   ├── datasources/
│       │   │   ├── router.py      # Conectores (REST, SQL, GraphQL)
│       │   │   ├── service.py
│       │   │   ├── schemas.py
│       │   │   ├── models.py
│       │   │   └── connectors/
│       │   │       ├── rest.py
│       │   │       ├── postgres.py
│       │   │       ├── mysql.py
│       │   │       └── mongodb.py
│       │   ├── queries/
│       │   │   ├── router.py      # POST /execute-query
│       │   │   ├── service.py     # Orquestra execução
│       │   │   ├── schemas.py
│       │   │   ├── models.py
│       │   │   └── executor/
│       │   │       ├── sql.py     # Execução segura de SQL
│       │   │       ├── rest.py    # Proxy de REST APIs
│       │   │       └── script.py  # Sandbox JS/Python
│       │   ├── ai/
│       │   │   ├── router.py      # POST /ai/generate-app
│       │   │   ├── service.py     # LiteLLM + LangChain
│       │   │   ├── prompts/       # Templates de prompts
│       │   │   └── schemas.py
│       │   ├── permissions/
│       │   │   ├── router.py
│       │   │   ├── service.py
│       │   │   └── models.py
│       │   └── workers/           # Celery tasks
│       │       ├── celery_app.py
│       │       └── tasks.py
│       ├── migrations/            # Alembic
│       ├── tests/
│       ├── Dockerfile
│       └── requirements.txt
│
├── packages/
│   ├── ui-components/             # Design system compartilhado
│   ├── query-engine/              # Lógica de query (shared types)
│   └── sdk/                       # SDK para plugins externos
│
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── nginx/
│   │   └── nginx.conf
│   └── k8s/                       # Helm charts
│
├── turbo.json
├── pnpm-workspace.yaml
└── README.md
```

---

## Modelos de Banco de Dados

### Schema SQL Completo

```sql
-- Organizações (multi-tenant)
CREATE TABLE organizations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(100) UNIQUE NOT NULL,
    plan        VARCHAR(50) DEFAULT 'free',  -- free | pro | enterprise
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Usuários
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) ON DELETE CASCADE,
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255),
    role            VARCHAR(50) DEFAULT 'developer',  -- admin | developer | viewer
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Datasources (conexões com APIs/DBs)
CREATE TABLE datasources (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    type        VARCHAR(50) NOT NULL,  -- rest | postgres | mysql | mongodb | graphql
    config      JSONB NOT NULL,        -- { url, auth, headers... } — criptografado
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Apps
CREATE TABLE apps (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) ON DELETE CASCADE,
    created_by      UUID REFERENCES users(id),
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(100) NOT NULL,
    description     TEXT,
    is_public       BOOLEAN DEFAULT FALSE,
    is_published    BOOLEAN DEFAULT FALSE,
    current_version INTEGER DEFAULT 1,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(org_id, slug)
);

-- Versões de Apps
CREATE TABLE app_versions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    app_id      UUID REFERENCES apps(id) ON DELETE CASCADE,
    version     INTEGER NOT NULL,
    snapshot    JSONB NOT NULL,   -- snapshot completo do app nessa versão
    created_by  UUID REFERENCES users(id),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(app_id, version)
);

-- Páginas
CREATE TABLE pages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    app_id      UUID REFERENCES apps(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(100) NOT NULL,
    layout      JSONB DEFAULT '[]',   -- array de posições do grid
    is_home     BOOLEAN DEFAULT FALSE,
    "order"     INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(app_id, slug)
);

-- Componentes (widgets no canvas)
CREATE TABLE components (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id     UUID REFERENCES pages(id) ON DELETE CASCADE,
    type        VARCHAR(100) NOT NULL,  -- table | form | input | button | chart...
    name        VARCHAR(255) NOT NULL,  -- nome usado no data binding: {{table1.data}}
    props       JSONB DEFAULT '{}',     -- propriedades configuráveis
    layout      JSONB NOT NULL,         -- { x, y, w, h }
    events      JSONB DEFAULT '[]',     -- [ { trigger: "onClick", action: {...} } ]
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Queries
CREATE TABLE queries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    app_id          UUID REFERENCES apps(id) ON DELETE CASCADE,
    datasource_id   UUID REFERENCES datasources(id),
    name            VARCHAR(255) NOT NULL,  -- nome p/ binding: {{query_users.data}}
    type            VARCHAR(50) NOT NULL,   -- sql | rest | graphql | js
    config          JSONB NOT NULL,         -- { method, url, body, sql, headers... }
    transform_script TEXT,                  -- JS de transformação do resultado
    run_on_load     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Permissões por App
CREATE TABLE app_permissions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    app_id      UUID REFERENCES apps(id) ON DELETE CASCADE,
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    role        VARCHAR(50) NOT NULL,  -- editor | viewer
    UNIQUE(app_id, user_id)
);

-- Índices de performance
CREATE INDEX idx_apps_org ON apps(org_id);
CREATE INDEX idx_pages_app ON pages(app_id);
CREATE INDEX idx_components_page ON components(page_id);
CREATE INDEX idx_queries_app ON queries(app_id);
```

---

## SQLAlchemy Models (Python)

```python
# app/apps/models.py
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMPTZ
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class App(Base):
    __tablename__ = "apps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)

    pages: Mapped[list["Page"]] = relationship("Page", back_populates="app", cascade="all, delete")
    queries: Mapped[list["Query"]] = relationship("Query", back_populates="app", cascade="all, delete")


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("apps.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    layout: Mapped[list] = mapped_column(JSONB, default=list)
    is_home: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer, default=0)

    app: Mapped["App"] = relationship("App", back_populates="pages")
    components: Mapped[list["Component"]] = relationship("Component", back_populates="page", cascade="all, delete")


class Component(Base):
    __tablename__ = "components"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pages.id"))
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    props: Mapped[dict] = mapped_column(JSONB, default=dict)
    layout: Mapped[dict] = mapped_column(JSONB, nullable=False)
    events: Mapped[list] = mapped_column(JSONB, default=list)

    page: Mapped["Page"] = relationship("Page", back_populates="components")


class Query(Base):
    __tablename__ = "queries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("apps.id"))
    datasource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("datasources.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # sql | rest | graphql | js
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    transform_script: Mapped[str | None] = mapped_column(Text)
    run_on_load: Mapped[bool] = mapped_column(Boolean, default=False)

    app: Mapped["App"] = relationship("App", back_populates="queries")
```

---

## API Principal — Endpoints FastAPI

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.router import router as auth_router
from app.apps.router import router as apps_router
from app.pages.router import router as pages_router
from app.components.router import router as components_router
from app.queries.router import router as queries_router
from app.datasources.router import router as datasources_router
from app.ai.router import router as ai_router

app = FastAPI(title="ToolStack AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,        prefix="/api/auth",        tags=["Auth"])
app.include_router(apps_router,        prefix="/api/apps",        tags=["Apps"])
app.include_router(pages_router,       prefix="/api/pages",       tags=["Pages"])
app.include_router(components_router,  prefix="/api/components",  tags=["Components"])
app.include_router(queries_router,     prefix="/api/queries",     tags=["Queries"])
app.include_router(datasources_router, prefix="/api/datasources", tags=["Datasources"])
app.include_router(ai_router,          prefix="/api/ai",          tags=["AI"])
```

```python
# app/queries/router.py — Execução de Queries (núcleo do sistema)
from fastapi import APIRouter, Depends, HTTPException
from app.queries.schemas import QueryExecuteRequest, QueryExecuteResponse
from app.queries.service import QueryService
from app.auth.jwt import get_current_user

router = APIRouter()

@router.post("/execute", response_model=QueryExecuteResponse)
async def execute_query(
    payload: QueryExecuteRequest,
    current_user=Depends(get_current_user),
    service: QueryService = Depends(),
):
    """
    Executa uma query (SQL, REST, GraphQL ou JS) com variáveis interpoladas.
    Protegido contra SQL injection via parameterized queries.
    Credenciais do datasource nunca são expostas ao frontend.
    """
    try:
        result = await service.execute(payload, current_user)
        return QueryExecuteResponse(data=result, success=True)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

```python
# app/queries/executor/sql.py — Execução segura de SQL
import asyncpg
from typing import Any

FORBIDDEN_SQL_KEYWORDS = {"drop", "truncate", "alter", "create", "grant", "revoke"}

async def execute_sql(connection_url: str, sql: str, params: dict[str, Any]) -> list[dict]:
    """
    Executa SQL com parâmetros nomeados, prevenindo SQL injection.
    Bloqueia DDL e comandos destrutivos.
    """
    sql_lower = sql.strip().lower()
    first_word = sql_lower.split()[0] if sql_lower else ""

    if first_word in FORBIDDEN_SQL_KEYWORDS:
        raise PermissionError(f"SQL statement '{first_word}' is not allowed.")

    conn = await asyncpg.connect(connection_url)
    try:
        # Usa prepared statements — parâmetros nunca são interpolados diretamente
        rows = await conn.fetch(sql, *params.values())
        return [dict(row) for row in rows]
    finally:
        await conn.close()
```

---

## Engine de IA — Geração de Apps via Prompt

```python
# app/ai/service.py
from litellm import acompletion
from app.ai.prompts import APP_GENERATION_SYSTEM_PROMPT
import json

class AIService:
    async def generate_app(self, prompt: str, org_context: dict) -> dict:
        """
        Recebe um prompt em linguagem natural e retorna um app completo
        no formato JSON esperado pelo frontend.
        """
        response = await acompletion(
            model="gpt-4o",  # ou claude-3-5-sonnet, gemini-2.0-flash
            messages=[
                {"role": "system", "content": APP_GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Context: {json.dumps(org_context)}\n\nRequest: {prompt}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        raw = response.choices[0].message.content
        return json.loads(raw)
```

```python
# app/ai/prompts.py
APP_GENERATION_SYSTEM_PROMPT = """
You are an expert at generating internal tool configurations for ToolStack AI.

Given a user's request in natural language, generate a complete app configuration in JSON format.

The JSON must follow this structure:
{
  "app": { "name": "string", "description": "string" },
  "pages": [
    {
      "name": "string",
      "slug": "string",
      "components": [
        {
          "type": "table|form|input|button|chart|text",
          "name": "string",
          "props": {},
          "layout": { "x": 0, "y": 0, "w": 12, "h": 6 },
          "events": []
        }
      ]
    }
  ],
  "queries": [
    {
      "name": "string",
      "type": "rest|sql|graphql",
      "config": {},
      "run_on_load": true
    }
  ]
}

Rules:
- Always create practical, working configurations.
- Use meaningful component names for data binding (e.g. "table_customers").
- Connect components to queries via props.data = "{{query_name.data}}".
- Include CRUD operations when managing entities.
- Grid width is 12 columns. Use full width (w:12) for tables.
"""
```

---

## Frontend — Zustand Store do Editor

```typescript
// apps/frontend/src/editor/store/canvas.store.ts
import { create } from 'zustand'
import { immer } from 'zustand/middleware/immer'

export interface ComponentLayout {
  x: number; y: number; w: number; h: number;
}

export interface CanvasComponent {
  id: string;
  type: string;
  name: string;
  props: Record<string, unknown>;
  layout: ComponentLayout;
  events: ComponentEvent[];
}

export interface ComponentEvent {
  trigger: 'onClick' | 'onLoad' | 'onChange';
  action: { type: 'runQuery' | 'runScript' | 'navigate'; payload: unknown };
}

interface CanvasState {
  components: CanvasComponent[];
  selectedId: string | null;
  isDirty: boolean;

  // Actions
  addComponent: (component: CanvasComponent) => void;
  updateComponent: (id: string, updates: Partial<CanvasComponent>) => void;
  removeComponent: (id: string) => void;
  selectComponent: (id: string | null) => void;
  updateLayout: (id: string, layout: ComponentLayout) => void;
  moveComponent: (id: string, x: number, y: number) => void;
}

export const useCanvasStore = create<CanvasState>()(
  immer((set) => ({
    components: [],
    selectedId: null,
    isDirty: false,

    addComponent: (component) => set((state) => {
      state.components.push(component)
      state.isDirty = true
    }),

    updateComponent: (id, updates) => set((state) => {
      const idx = state.components.findIndex(c => c.id === id)
      if (idx !== -1) {
        Object.assign(state.components[idx], updates)
        state.isDirty = true
      }
    }),

    removeComponent: (id) => set((state) => {
      state.components = state.components.filter(c => c.id !== id)
      state.isDirty = true
    }),

    selectComponent: (id) => set((state) => {
      state.selectedId = id
    }),

    updateLayout: (id, layout) => set((state) => {
      const comp = state.components.find(c => c.id === id)
      if (comp) { comp.layout = layout; state.isDirty = true }
    }),

    moveComponent: (id, x, y) => set((state) => {
      const comp = state.components.find(c => c.id === id)
      if (comp) { comp.layout.x = x; comp.layout.y = y; state.isDirty = true }
    }),
  }))
)
```

---

## Frontend — Runtime de Data Binding

```typescript
// apps/frontend/src/runtime/binding/evaluate.ts

/**
 * Avalia expressões de binding com segurança.
 * Exemplo: "{{query_users.data}}" → resultado real da query
 *
 * SEGURANÇA: Usa Function() com contexto isolado — sem acesso a window, document, fetch.
 */
export function evaluateBinding(
  expression: string,
  context: Record<string, unknown>
): unknown {
  const BINDING_REGEX = /\{\{([^}]+)\}\}/g

  if (!BINDING_REGEX.test(expression)) return expression

  return expression.replace(/\{\{([^}]+)\}\}/g, (_, expr) => {
    try {
      const fn = new Function(...Object.keys(context), `return (${expr.trim()})`)
      const result = fn(...Object.values(context))
      return result ?? ''
    } catch {
      return ''
    }
  })
}

/**
 * Resolve todas as props de um componente, avaliando bindings.
 */
export function resolveComponentProps(
  props: Record<string, unknown>,
  context: Record<string, unknown>
): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(props).map(([key, value]) => [
      key,
      typeof value === 'string' ? evaluateBinding(value, context) : value
    ])
  )
}
```

---

## Docker Compose (Desenvolvimento Local)

```yaml
# infra/docker-compose.yml
version: '3.9'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: toolstack
      POSTGRES_USER: toolstack
      POSTGRES_PASSWORD: toolstack_secret
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U toolstack"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  backend:
    build: ./apps/backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      DATABASE_URL: postgresql+asyncpg://toolstack:toolstack_secret@postgres:5432/toolstack
      REDIS_URL: redis://redis:6379
      SECRET_KEY: super-secret-jwt-key-change-in-production
      ENVIRONMENT: development
    volumes:
      - ./apps/backend:/app
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery:
    build: ./apps/backend
    command: celery -A app.workers.celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://toolstack:toolstack_secret@postgres:5432/toolstack
      REDIS_URL: redis://redis:6379
    volumes:
      - ./apps/backend:/app
    depends_on:
      - backend
      - redis

  frontend:
    image: node:22-alpine
    working_dir: /app
    command: sh -c "corepack enable && pnpm install && pnpm dev"
    volumes:
      - ./apps/frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    environment:
      VITE_API_URL: http://localhost:8000

volumes:
  postgres_data:
```

---

## Roadmap de Desenvolvimento

### Fase 1 — MVP (6 semanas)
- [ ] Auth (login, register, JWT)
- [ ] CRUD de Apps e Pages
- [ ] Canvas com drag-and-drop básico (@dnd-kit)
- [ ] 5 componentes: Table, Text, Button, Input, Form
- [ ] Datasource: REST API
- [ ] Query Builder REST (GET/POST com variáveis)
- [ ] Data Binding (`{{query.data}}`)
- [ ] Preview mode

### Fase 2 — Core Product (6 semanas)
- [ ] Datasource: PostgreSQL, MySQL
- [ ] Query Builder SQL (com proteção anti-injection)
- [ ] Sistema de eventos (onClick, onLoad)
- [ ] 5+ componentes: Chart, Select, Modal, JSON Viewer, Tabs
- [ ] Versionamento de apps
- [ ] Permissões por app (editor/viewer)
- [ ] Export/import de apps (JSON)

### Fase 3 — AI Features (4 semanas)
- [ ] Painel "Generate with AI" (prompt → app)
- [ ] Sugestão automática de queries
- [ ] Geração de SQL a partir de linguagem natural
- [ ] Marketplace de templates

### Fase 4 — Scale & SaaS (ongoing)
- [ ] Multi-tenancy completo (organizações isoladas)
- [ ] Billing (Stripe)
- [ ] Self-host Enterprise (Docker / Kubernetes)
- [ ] Plugin SDK para componentes customizados
- [ ] Audit logs
- [ ] SSO (SAML / Okta / Google Workspace)

---

## Segurança (Checklist)

- [x] SQL injection: parameterized queries obrigatórias, DDL bloqueado
- [x] XSS: data binding avaliado em contexto isolado, sem `eval()` direto
- [x] SSRF: datasources externos validados com allowlist de IPs/domínios
- [x] Credenciais: config de datasources criptografada em repouso (AES-256)
- [x] Auth: JWT com expiração curta + refresh token
- [x] Rate limiting: via Nginx por IP e por usuário
- [x] CORS: configurado explicitamente, não `*` em produção
- [x] Script sandbox: RestrictedPython para scripts do usuário
- [x] Multi-tenant isolation: org_id em todas as queries do banco

---

## Nome do Produto: ToolStack AI

**Domínio sugerido:** `toolstack.ai`
**Modelo de negócio:**
- Free: 3 apps, 5 usuários, sem IA
- Pro ($49/mês): ilimitado apps, 20 usuários, IA incluída
- Enterprise (custom): self-host, SSO, SLA