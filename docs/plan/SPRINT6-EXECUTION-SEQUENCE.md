# Sprint 6 — Sequência de Execução

> **Sprint:** Sprint 6 — Templates, Runtime Engine e Publish
> **Início:** 2026-03-17 | **Fim:** 2026-03-31
>
> Leia este documento junto com `docs/plan/SPRINT6-BACKLOG.md` para entender os critérios
> de aceitação de cada US. Aqui o foco é **como e em que ordem** executar.

---

## Mapa de Dependências

```
Sprint 6A ──────────────────────────────────────► US-400 Runtime Binding
Sprint 6A ──────────────────────────────────────► US-401 Query Execution Runtime
                                                   (US-401 backend deve chegar antes do US-400 frontend)

Sprint 6B ──────────────────────────────────────► US-410 Templates Backend
Sprint 6B ──────────────────────────────────────► US-411 Template Picker UI
                                                   (US-411 depende de US-410 estar rodando)

Sprint 6C ──────────────────────────────────────► US-420 Publish Backend
Sprint 6C ──────────────────────────────────────► US-421 Publish Button UI
                                                   (US-421 depende de US-420 estar rodando)

Sprint 6D ──────────────────────────────────────► US-430 Rate Limiting AI
Sprint 6D ──────────────────────────────────────► US-431 Sandbox SEC-007
Sprint 6D ──────────────────────────────────────► US-432 CI e Cobertura
                                                   (US-432 depende de todas as outras estarem concluídas)
```

**Paralelismo máximo:** 6A (frontend) ‖ 6B backend ‖ 6C backend ‖ 6D segurança.
O único sequenciamento obrigatório é: backend antes do frontend correpondente.

---

## Dia 1-2 (2026-03-17 / 18) — Alicerce

### Tarefa 1: Migration e seed de templates [python-integrations-senior]

```bash
# Criar migration
cd backend
alembic revision --autogenerate -m "app_templates"
# Checar e renomear para 0006_app_templates.py
# Adicionar seed na migration (INSERT INTO app_templates)
alembic upgrade head
```

Arquivo: `backend/migrations/versions/0006_app_templates.py`

Template seeds mínimos (layout_json simplificado):
```python
CRUD_TEMPLATE = {
  "widgets": [
    {"id": "t1", "type": "Table",  "x":0,"y":0,"w":12,"h":8, "props":{"data":"{{query1.data}}","columns":[{"key":"id"},{"key":"name"}]}},
    {"id": "t2", "type": "Button", "x":0,"y":9,"w":2, "h":1, "props":{"label":"Add Row"}}
  ]
}

KPI_TEMPLATE = {
  "widgets": [
    {"id": "k1", "type": "Stat",  "x":0,"y":0,"w":4,"h":2, "props":{"label":"Total","value":"{{query1.data[0].total}}"}},
    {"id": "k2", "type": "Stat",  "x":4,"y":0,"w":4,"h":2, "props":{"label":"Active","value":"{{query1.data[0].active}}"}},
    {"id": "k3", "type": "Stat",  "x":8,"y":0,"w":4,"h":2, "props":{"label":"New","value":"{{query1.data[0].new_count}}"}},
    {"id": "k4", "type": "Table", "x":0,"y":3,"w":12,"h":8,"props":{"data":"{{query1.data}}"}}
  ]
}

FORM_TEMPLATE = {
  "widgets": [
    {"id": "f1", "type": "TextInput","x":0,"y":0,"w":6,"h":1,"props":{"label":"Name","placeholder":"Your name"}},
    {"id": "f2", "type": "TextInput","x":0,"y":2,"w":6,"h":1,"props":{"label":"Email","placeholder":"your@email.com"}},
    {"id": "f3", "type": "Button",   "x":0,"y":4,"w":2,"h":1,"props":{"label":"Submit"}}
  ]
}
```

### Tarefa 2: Migration publish [python-integrations-senior]

```bash
alembic revision --autogenerate -m "app_publish"
# Renomear para 0007_app_publish.py
# Adicionar is_published, published_at, slug manualmente se não detectado
alembic upgrade head
```

Arquivo: `backend/migrations/versions/0007_app_publish.py`

---

## Dia 2-4 (2026-03-18 / 20) — Backends

### Tarefa 3: Módulo de templates [python-integrations-senior]

Criar `backend/app/templates/`:
```
backend/app/templates/
  __init__.py
  router.py   ← GET /api/templates, POST /api/apps (extended)
  schemas.py  ← TemplateResponse, TemplateListResponse
  service.py  ← clone_template_layout(template_id, target_app_id, db)
```

Registrar em `app/main.py`:
```python
from app.templates.router import router as templates_router
app.include_router(templates_router, prefix="/api", tags=["templates"])
```

`POST /api/apps` precisa aceitar `template_id` opcional — isso requer modificar
`app/apps/router.py` para chamar `service.clone_template_layout` quando `template_id`
estiver presente.

### Tarefa 4: Módulo de publish [python-integrations-senior]

Criar `backend/app/publish/`:
```
backend/app/publish/
  __init__.py
  router.py   ← POST /publish, DELETE /publish, GET /r/{slug}
  schemas.py  ← PublishResponse, PublicAppSnapshot
  service.py  ← generate_slug(name), get_public_app(slug, db)
```

Registrar em `app/main.py`.

`generate_slug(name)` deve:
1. Slugify (lowercase, remove especiais, troca espaços por `-`).
2. Verificar colisão no DB.
3. Se colidir, adicionar sufixo `-2`, `-3`, etc.

### Tarefa 5: Endpoint GET /api/apps/{appId}/queries [python-integrations-senior]

Este endpoint é necessário para o runtime frontend (US-401).

Adicionar em `app/queries/router.py`:
```python
@router.get("/apps/{app_id}/queries")
async def list_app_queries(app_id: str, ...):
    ...
```

Retorna:
```json
[
  {
    "id": "...",
    "name": "query1",
    "datasource_id": "...",
    "type": "REST",
    "config": {...},
    "transform_js": null,
    "run_on_load": true
  }
]
```

### Tarefa 6: Rate limiting e SEC-007 [python-integrations-senior]

Rate limiting (US-430):
```bash
pip install slowapi
# Adicionar limits ao requirements.txt
```

Configurar em `app/main.py`:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=lambda request: request.state.current_user.id)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

Decorar endpoints AI:
```python
@limiter.limit("10/minute")
async def generate_app(request: Request, ...):
```

SEC-007 sandbox fix (US-431):
Modificar `app/queries/transform.py` para executar em subprocesso:
```python
import subprocess, resource, json, sys, textwrap

def _run_script_isolated(code: str, data: dict) -> dict:
    wrapper = textwrap.dedent(f"""
        import resource, json, sys
        resource.setrlimit(resource.RLIMIT_AS, (256*1024*1024, 256*1024*1024))
        data = {json.dumps(data)}
        {code}
        print(json.dumps(result))
    """)
    result = subprocess.run(
        [sys.executable, "-c", wrapper],
        capture_output=True, text=True, timeout=3
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[:500])
    return json.loads(result.stdout)
```

---

## Dia 3-6 (2026-03-19 / 24) — Frontend

### Tarefa 7: Runtime engine [frontend-react-mobile]

Criar `frontend/src/runtime/`:
```
frontend/src/runtime/
  engine.ts           ← evaluate(expr, context)
  context.ts          ← RuntimeContext type
  useRuntimeContext.ts ← hook que orquestra queries
  useRuntimeQueries.ts ← fetch + executa queries
```

`engine.ts` — avaliação segura:
```typescript
export function evaluate(expr: string, context: RuntimeContext): unknown {
  const trimmed = expr.trim();
  // Detecta expressão template: {{...}}
  const match = trimmed.match(/^\{\{([\s\S]+)\}\}$/);
  if (!match) return trimmed; // valor literal
  
  try {
    // Sandbox: apenas acesso ao contexto
    const fn = new Function(...Object.keys(context), `"use strict"; return (${match[1]})`);
    return fn(...Object.values(context));
  } catch {
    return undefined; // retorna undefined em erro — widget mostra estado de erro
  }
}
```

**Importante:** O sandbox via `new Function` no browser é suficiente para esta fase —
não há acesso a `fetch`, `XMLHttpRequest`, etc. a não ser que passados explicitamente.
O contexto passado contém apenas `{ [queryName]: { data, loading, error } }`.

`useRuntimeContext.ts`:
```typescript
export function useRuntimeContext(appId: string, pageId: string): RuntimeContext {
  const queries = useRuntimeQueries(appId, pageId);
  return Object.fromEntries(queries.map(q => [q.name, {
    data: q.data,
    loading: q.loading,
    error: q.error,
  }]));
}
```

### Tarefa 8: WidgetRenderer com binding [frontend-react-mobile]

Modificar `frontend/src/features/runtime/WidgetRenderer.tsx` (ou equivalente):

Cada widget que renderiza na página pública deve chamar `evaluate()` nos props:
```typescript
const resolvedData = evaluate(widget.props.data ?? "", context);
const resolvedColumns = evaluate(widget.props.columns ?? "[]", context);
```

Tratar `undefined` retornado por `evaluate()` com estado visual de erro (borda vermelha,
tooltip "Expression error").

### Tarefa 9: Template Picker [frontend-react-mobile]

Criar `frontend/src/features/apps/TemplatePickerModal.tsx`:
- Fetch `GET /api/templates` com TanStack Query (`useQuery`).
- `TemplateCard` com thumbnail, nome, descrição, categoria.
- Filtro por categoria via tabs ou chips.
- "Blank App" sempre visível como primeira opção.
- Ao confirmar: `useMutation` → `POST /api/apps` com `template_id`.

Integrar em `frontend/src/features/apps/AppListPage.tsx`:
- Botão "New App" abre `TemplatePickerModal`.

### Tarefa 10: Botão Publish no builder [frontend-react-mobile]

Modificar `frontend/src/features/builder/BuilderHeader.tsx`:
- Adicionar `publishMutation` via `useMutation`.
- Lógica de visibilidade: só aparece se `userRole === "owner"`.
- Estado "Published ✓": buscar `isPublished` do app context.
- Toast com URL pública e botão "Copy".
- Dropdown "Unpublish" via `DELETE /api/apps/{id}/publish`.

---

## Dia 6-8 (2026-03-24 / 26) — Integração e Testes

### Tarefa 11: Testes backend Sprint 6 [python-integrations-senior]

Mínimo de novos testes por módulo:

| Arquivo                          | Novos testes | Target total |
|----------------------------------|-------------|--------------|
| `tests/test_templates.py`        | 8           | 8            |
| `tests/test_publish.py`          | 10          | 10           |
| `tests/test_queries.py`          | +6          | existente +6 |
| `tests/test_ai.py`               | 4           | existente +4 |
| `tests/test_transform.py`        | +3          | existente +3 |

**Meta: ≥ 145 testes passando.**

Rodar:
```bash
cd backend && python -m pytest -v --tb=short 2>&1 | tail -20
```

### Tarefa 12: Testes E2E Sprint 6 [qa-test-automation]

Criar/expandir arquivos:

| Arquivo E2E                               | Specs | Foco                              |
|-------------------------------------------|-------|-----------------------------------|
| `frontend/tests/e2e/runtime-binding.spec.ts` | 6  | data binding, queries run_on_load |
| `frontend/tests/e2e/template-picker.spec.ts` | 5  | abrir modal, filtro, criação      |
| `frontend/tests/e2e/publish-flow.spec.ts`    | 6  | publish, unpublish, /r/{slug}     |

**Meta: ≥ 42 specs E2E.**

### Tarefa 13: Testes unitários Vitest [frontend-react-mobile]

Criar `frontend/src/runtime/__tests__/engine.test.ts`:
```typescript
describe("evaluate()", () => {
  test("literal string passthrough")
  test("resolves {{query.data}}")
  test("resolves nested {{query.data[0].name}}")
  test("returns undefined for undefined property (no throw)")
  test("returns undefined for syntax error (no throw)")
  test("injection attempt: window.fetch blocked")
  test("resolves boolean expression")
  test("resolves array length")
})
```

---

## Dia 8-10 (2026-03-26 / 28) — CI/CD e Finalização

### Tarefa 14: CI GitHub Actions [devops]

Verificar/criar `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: toolstack
          POSTGRES_PASSWORD: toolstack_secret
          POSTGRES_DB: toolstack
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: cd backend && pip install -r requirements.txt
      - run: cd backend && alembic upgrade head
        env:
          DATABASE_URL: postgresql+asyncpg://toolstack:toolstack_secret@localhost/toolstack
      - run: cd backend && python -m pytest -v --tb=short
        env:
          DATABASE_URL: postgresql+asyncpg://toolstack:toolstack_secret@localhost/toolstack
          SECRET_KEY: ci-secret-key
          AI_PROVIDER: litellm
          AI_MODEL: gpt-4o-mini

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: cd frontend && npm ci
      - run: cd frontend && npx tsc --noEmit
      - run: cd frontend && npx playwright install --with-deps chromium
      - run: cd frontend && npx playwright test
        env:
          CI: true
```

### Tarefa 15: Documentação e risk register [security-reviewer]

1. Atualizar `docs/security/risk-register.md`:
   - SEC-004: `status: remediated` (rate limiting implementado).
   - SEC-007: `status: remediated` (subprocess + resource limits).
   - SEC-008: `status: open` (referrer-policy ainda não implementado; aceito para este sprint).

2. Atualizar `docs/status/current.md` com Sprint 6 status.

3. Commit final:
   ```bash
   git add -A
   git commit -m "Sprint 6 complete: runtime binding, templates, publish, rate limiting, SEC-007 remediated"
   ```

---

## Ordem de Entrega Recomendada

| Dia | Tarefa | Agente              | Depende de |
|-----|--------|---------------------|------------|
| 1   | T01 Migration templates | python-senior | - |
| 1   | T02 Migration publish   | python-senior | - |
| 2   | T03 Templates backend   | python-senior | T01 |
| 2   | T04 Publish backend     | python-senior | T02 |
| 2   | T05 GET /queries endpoint | python-senior | - |
| 2   | T06 Rate limiting + SEC-007 | python-senior | - |
| 3   | T07 Runtime engine (frontend) | react-frontend | T05 |
| 4   | T08 WidgetRenderer binding | react-frontend | T07 |
| 4   | T09 Template Picker | react-frontend | T03 |
| 5   | T10 Publish button  | react-frontend | T04 |
| 6   | T11 Backend tests   | python-senior | T03, T04, T05, T06 |
| 7   | T12 E2E tests       | qa-engineer   | T07-T10 |
| 8   | T13 Unit tests Vitest | react-frontend | T07 |
| 9   | T14 CI/CD           | devops        | T11, T12 |
| 10  | T15 Docs + risk register | security | T14 |

---

## Checklist de Saída do Sprint 6

Backend:
- [ ] `alembic upgrade head` roda sem erros (migrations 0006 e 0007 aplicadas)
- [ ] `GET /api/templates` retorna 3 templates com `layout_json`
- [ ] `POST /api/apps` com `template_id` cria app com layout clonado
- [ ] `POST /api/apps/{id}/publish` retorna `public_url`
- [ ] `GET /api/r/{slug}` responde 200 sem auth para app publicado
- [ ] `GET /api/apps/{id}/queries` lista queries da página
- [ ] AI endpoints retornam 429 após exceder limite
- [ ] SEC-007: transform executa em subprocesso com `RLIMIT_AS`
- [ ] ≥ 145 pytest passando

Frontend:
- [ ] `evaluate("{{query.data}}", context)` funciona sem lançar exceptions
- [ ] TableWidget popula dados via data binding
- [ ] `<TemplatePickerModal>` abre ao clicar "New App"
- [ ] Seleção de template cria app com layout pré-definido
- [ ] Botão Publish visível para owner, ausente para editor/viewer
- [ ] Toast com URL pública exibido após publish
- [ ] ≥ 42 E2E specs passando
- [ ] `tsc --noEmit` sem erros

CI/CD:
- [ ] `.github/workflows/ci.yml` presente e rodando
- [ ] Badge verde no README

Docs:
- [ ] `docs/status/current.md` atualizado
- [ ] `docs/security/risk-register.md` com SEC-004 e SEC-007 remediados
