# Sprint 4 — Sequência de Execução

> Este documento define a ordem, as dependências e os responsáveis por cada
> bloco de trabalho do Sprint 4.

---

## Visão geral do fluxo

```
Sprint 4A (RBAC + Sharing) — PRIMEIRO (fecha risco SEC-003)
  ├─► Sprint 4B (GraphQL Datasource)  ─╮
  ├─► Sprint 4C (App Templates)        ├──► Quality (US-240/241/242)
  └─► Sprint 4D (CI/CD DevEx)  ────────╯
```

**4A é pré-requisito** para a review de segurança (US-240).
**4B, 4C, 4D** podem rodar em paralelo assim que o schema de 4A estiver estabilizado.
**Quality** roda após code-complete de 4A/4B/4C.

---

## Sprint 4A — RBAC e Compartilhamento

**Objetivo:** Introduzir papéis por app e UI de compartilhamento. Fecha SEC-003.

---

### Fase 1 — Arquitetura (Tech Lead Architect)

**Agente:** `tech-lead-architect`

**Tarefa:** Definir schema do banco, contratos de API e regras de autorização antes
da implementação. Registrar ADR.

**Decisões a documentar:**

| Ponto | Decisão recomendada |
|-------|---------------------|
| Tabela de membros | `app_members(app_id UUID, user_id UUID, role TEXT, joined_at TIMESTAMP)` com PK composta |
| Enum de roles | String check constraint: `owner \| editor \| viewer` (sem enum Postgres — mais flexível) |
| Verificação de role | Dependency FastAPI `require_role(min_role)` injetada nos routers |
| Migração | Script Alembic ou SQL manual em `backend/migrations/` |
| GET /api/apps | Requer JOIN com `app_members` — breaking change no endpoint existente |

**Entregáveis:**
- `docs/adr/ADR-0002-rbac-app-members.md`
- Contrato OpenAPI dos endpoints: `/members` CRUD + `/me/role`
- Confirmação de que GET /api/apps é backward-compatible (owner continua vendo seus apps)

**Arquivos a criar/modificar:**

| Arquivo | Ação |
|---------|------|
| `docs/adr/ADR-0002-rbac-app-members.md` | Criar |
| `backend/migrations/0002_app_members.sql` | Criar |

---

### Fase 2 — Backend RBAC (Python Senior)

**Agente:** `python-integrations-senior`

**Pré-requisito:** ADR-0002 aprovado.

**Arquivos a criar/modificar:**

| Arquivo | Ação |
|---------|------|
| `backend/app/models.py` | Adicionar `AppMember` model |
| `backend/app/routers/apps.py` | Adicionar `require_role` dependency + `/members` CRUD |
| `backend/app/routers/pages.py` | Adicionar verificação de role |
| `backend/app/routers/datasources.py` | Adicionar verificação de role |
| `backend/app/routers/queries.py` | Adicionar verificação de role |
| `backend/tests/test_rbac.py` | Criar — ≥ 12 testes |
| `backend/tests/test_members_router.py` | Criar — ≥ 9 testes |

**Ordem de implementação:**
1. `AppMember` model + migration SQL.
2. Dependency `get_app_membership(app_id, current_user)` → retorna role ou 404/403.
3. `require_role(min_role)` como FastAPI dependency fatorada.
4. Aplicar nos routers existentes (breaking change controlado).
5. Novo router `/api/apps/{app_id}/members` com GET/POST/PATCH/DELETE.
6. `GET /api/apps/{app_id}/me/role` para o frontend.
7. Testes de todos os cenários de privilégio.

---

### Fase 3 — Frontend Share UI (Frontend React)

**Agente:** `frontend-react-mobile`

**Pré-requisito:** Endpoints de `/members` no ar (ou mockados).

**Arquivos a criar/modificar:**

| Arquivo | Ação |
|---------|------|
| `frontend/src/features/sharing/ShareDrawer.tsx` | Criar |
| `frontend/src/features/sharing/useMembership.ts` | Criar — TanStack Query hooks |
| `frontend/src/features/builder/BuilderHeader.tsx` | Modificar — botão "Share" |
| `frontend/src/features/builder/BuilderWorkspace.tsx` | Modificar — injetar role |
| `frontend/src/features/runtime/RuntimeRoute.tsx` | Modificar — viewer redirect |
| `frontend/src/styles.css` | Modificar — estilos do drawer |

**Componentes:**
- `ShareDrawer` — drawer com: input de email, select de role, lista de membros com badge + botão remover.
- `useMembership` — hooks: `useAppRole()`, `useMembers()`, `useInviteMember()`, `useRevokeMember()`.
- Viewer redirect: lê `GET /api/apps/{appId}/me/role` ao abrir builder, redireciona se `viewer`.

---

## Sprint 4B — GraphQL Datasource

**Objetivo:** Terceiro conector. REST ✅ SQL ✅ GraphQL novo.

---

### Backend GraphQL (Python Senior)

**Agente:** `python-integrations-senior`

**Pode rodar em paralelo com Frontend 4A.**

**Arquivos a criar/modificar:**

| Arquivo | Ação |
|---------|------|
| `backend/app/services/query_service.py` | Adicionar `execute_graphql()` + `fetch_graphql_schema()` |
| `backend/app/routers/queries.py` | Aceitar `type=graphql` no executor |
| `backend/app/routers/datasources.py` | Novo endpoint `POST /{id}/graphql/schema` |
| `backend/tests/test_graphql_executor.py` | Criar — ≥ 10 testes |

**Contrato de entrada:**
```json
{
  "datasource_id": "uuid",
  "type": "graphql",
  "config": {
    "query": "{ users { id name } }",
    "variables": {}
  }
}
```

**Contrato de resposta:** mesmo formato do REST — `{ "data": [...], "status": 200 }`.

**SSRF:** reutilizar `validate_url()` já existente em `query_service.py`.

---

### Frontend GraphQL UI (Frontend React)

**Agente:** `frontend-react-mobile`

**Pode rodar em paralelo com Backend 4B.**

**Arquivos a criar/modificar:**

| Arquivo | Ação |
|---------|------|
| `frontend/src/features/datasources/DataSourcePanel.tsx` | Adicionar tipo `graphql` |
| `frontend/src/features/queries/QueryPanel.tsx` | Modo GraphQL: textarea + variables |
| `frontend/src/features/queries/GraphQLQueryEditor.tsx` | Criar — editor GraphQL |
| `frontend/tests/e2e/graphql-datasource.spec.ts` | Criar — 1 E2E mock-to-widget |

---

## Sprint 4C — App Templates

**Objetivo:** Template picker que elimina a barreira do blank canvas.

---

### Backend Templates (Python Senior)

**Agente:** `python-integrations-senior`

**Pode rodar em paralelo com 4B.**

**Arquivos a criar/modificar:**

| Arquivo | Ação |
|---------|------|
| `backend/app/models.py` | Adicionar `Template` model |
| `backend/app/routers/templates.py` | Criar — GET /api/templates, POST /api/apps/from-template |
| `backend/app/routers/apps.py` | Adicionar POST /{app_id}/as-template |
| `backend/app/seed/templates.py` | Criar — 3 templates iniciais |
| `backend/tests/test_templates_router.py` | Criar — ≥ 5 testes |

**Seeds obrigatórios:**

| Slug | Nome | Categoria | Descrição |
|------|------|-----------|-----------|
| `crud-table` | CRUD Table | dados | Tabela com datasource REST de listagem |
| `kpi-dashboard` | KPI Dashboard | analytics | 3 Stats + 1 Chart + query de exemplo |
| `form-submit` | Form + Submit | formulários | Input + Select + Button com POST |

---

### UX dos Templates (UX Specialist)

**Agente:** `ux-specialist`

**Tarefa:** Definir o fluxo e estados visuais do template picker.

**Entregáveis esperados:**
- Documento de fluxo: empty state → template picker modal → nome do app → builder.
- Estados: loading de templates, template selecionado (highlight), erro de criação.
- Thumbnail placeholder padrão para templates sem imagem.
- Definição do grid de cards (quantas colunas, ordem de exibição).

---

### Frontend Template Picker (Frontend React)

**Agente:** `frontend-react-mobile`

**Pré-requisito:** UX flow definido + backend de templates no ar (ou mock).

**Arquivos a criar/modificar:**

| Arquivo | Ação |
|---------|------|
| `frontend/src/features/templates/TemplatePickerModal.tsx` | Criar |
| `frontend/src/features/templates/TemplateCard.tsx` | Criar |
| `frontend/src/features/templates/useTemplates.ts` | Criar — TanStack Query |
| `frontend/src/features/apps/EmptyState.tsx` | Modificar — botão "From template" |
| `frontend/src/features/builder/BuilderHeader.tsx` | Modificar — menu "…" com "Save as template" |

---

## Sprint 4D — CI/CD e Developer Experience

**Objetivo:** Pipeline reproduzível e onboarding rápido.

**Responsável:** `devops`

**Totalmente paralelo com 4A/4B/4C.**

---

### DevOps — CI/CD e DevContainer

**Agente:** `devops`

**Arquivos a criar/modificar:**

| Arquivo | Ação |
|---------|------|
| `.github/workflows/ci.yml` | Criar — backend + unit + E2E em paralelo |
| `.github/workflows/release.yml` | Criar — build + Docker image + GitHub Release |
| `.devcontainer/devcontainer.json` | Criar |
| `.devcontainer/postCreate.sh` | Criar |
| `README.md` | Modificar — seção "Get started" + badges de CI |
| `infra/Dockerfile.release` | Criar — imagem de produção com frontend embedded |

**Restrições importantes:**
- Playwright no CI precisa de `--no-sandbox` flag (já configurado no `playwright.config.ts`).
- Backend tests precisam de Postgres — usar `services: postgres` no workflow.
- Secrets: `DATASOURCE_ENCRYPTION_KEY` como GitHub Secret, nunca hardcoded.
- Docker image: multi-stage build (Node → build frontend → Python + dist/).

---

## Quality Sprint 4

### US-240 — Security Review (Security Reviewer)

**Agente:** `security-reviewer`

**Pré-requisito:** 4A code-complete.

**Escopo de auditoria:**
- Privilege escalation: usuário com role `viewer` tenta mutação → deve receber 403.
- IDOR: usuário A tenta acessar `/apps/B/members` onde não é membro → 404.
- Headers GraphQL: injection de headers maliciosos no datasource.
- SSRF no executor GraphQL: mesma proteção do REST aplicada.
- `is_public` em templates: template privado não vaza para outros usuários.

**Entregáveis:**
- Risk-register atualizado (`docs/security/risk-register.md`).
- SEC-003 fechado como `mitigated` (ou novo sub-finding criado se encontrar gap).
- Checklist em `docs/security/2026-03-16-risk-checklist-sprint4.md`.

---

### US-241 — Testes E2E (QA Test Automation)

**Agente:** `QA Test Automation`

**Pré-requisito:** 4A e 4C code-complete.

**Novos spec files:**

| Arquivo | Testes |
|---------|--------|
| `frontend/tests/e2e/rbac-sharing.spec.ts` | Convite, role, remoção, viewer redirect |
| `frontend/tests/e2e/template-picker.spec.ts` | Blank vs template, criação, redirect |
| `frontend/tests/e2e/graphql-datasource.spec.ts` | Mock GraphQL → widget binding |

**Meta:** ≥ 10 novos testes (total ≥ 35 E2E).

**Critério de cobertura mínima:**
- Happy path de cada US de 4A e 4C tem ao menos 1 E2E.
- Cenário de acesso negado (403/redirect) tem ao menos 1 E2E por role.

---

### US-242 — Release Note Sprint 4 (Release Manager)

**Agente:** `Release Manager`

**Pré-requisito:** US-240 e US-241 concluídos.

**Entregável:** `docs/release/2026-03-16-release-sprint4-close.md`

**Go/no-go criteria:**
- ≥ 70 backend tests passando.
- ≥ 30 unit tests passando.
- ≥ 35 E2E passando.
- Security review sem findings bloqueantes.
- CI workflow verde em branch `main`.

---

## Resumo de responsabilidades

| Agente | US responsável |
|--------|---------------|
| `tech-lead-architect` | Fase 1 de 4A: ADR-0002, schema, contrato de API |
| `python-integrations-senior` | US-200, 201, 202, 203 (backend), US-210, 220 |
| `frontend-react-mobile` | US-201, 202, 203 (frontend), US-211, 212, 221, 222 |
| `ux-specialist` | Fluxo UX de templates (US-221) e share drawer (US-201) |
| `devops` | US-230, 231, 232 |
| `security-reviewer` | US-240 |
| `QA Test Automation` | US-241 |
| `Release Manager` | US-242 |

---

## Sequência recomendada de invocação dos agentes

```
Semana 1:
  1. tech-lead-architect  → ADR-0002 + contratos 4A
  2. python-integrations-senior → backend 4A (RBAC + members)
  3. devops               → CI/CD workflows (paralelo)

Semana 2:
  4. python-integrations-senior → backend 4B (GraphQL) + 4C (Templates)
  5. ux-specialist        → UX de templates + share drawer
  6. frontend-react-mobile → UI 4A (share) + 4B (query GraphQL) + 4C (template picker)

Semana 3:
  7. security-reviewer    → auditoria RBAC + GraphQL headers
  8. QA Test Automation   → E2E spec files 4A/4C/4B
  9. Release Manager      → go/no-go sprint 4
```
