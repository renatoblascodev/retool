# Current Status

## Data

2026-03-17

## Em Progresso

- Nenhum item aberto. Sprint 5 completo.

## Sprint 5 — Concluído

### Backend

- **AI module** (`app/ai/`): endpoints `POST /api/ai/generate-app` e `POST /api/ai/suggest-query` implementados com LiteLLM.
- **JS Transform sandbox** (`app/queries/transform.py`): sandbox RestrictedPython com timeout de 2s via thread daemon. Integrado ao `POST /api/queries/execute` via campo `transform_js`.
- **Testes backend**: 113 testes passando (101 pré-Sprint 5 + 12 de transform sandbox + 14 de AI endpoints → totalizando 113 com sobreposição de fixture).

### Frontend

- **AI Prompt Panel**: botão "Generate" com ícone Sparkles no `BuilderHeader`, drawer lateral `AIPromptPanel.tsx` com textarea de prompt, select de datasource, e exibição do resultado da IA.
- **Transform (Python) editor**: seção colapsável `<details>` na `QueryPanel` com textarea para scripts de transformação de resultado. Campo `transform_js` é enviado ao backend na execução da query.
- **0 erros TypeScript**, build Vite limpo.

## Status das US do MVP + Sprint 5

| US    | Feature                          | Status |
|-------|----------------------------------|--------|
| US-001 | Auth/login                     | ✅ |
| US-002 | Empty state CTA                | ✅ |
| US-010 | Criar app                      | ✅ |
| US-011 | Criar página                   | ✅ |
| US-020 | Adicionar Table widget         | ✅ |
| US-021 | Editar propriedades            | ✅ |
| US-030 | Criar datasource REST          | ✅ |
| US-031 | Criar e executar query         | ✅ |
| US-040 | Bindar query na tabela         | ✅ |
| US-041 | Abrir preview                  | ✅ |
| US-050 | Ambiente local completo        | ✅ |
| US-051 | Smoke test + testes backend    | ✅ |
| US-201 | RBAC (owner/viewer)            | ✅ |
| US-203 | Redirect viewer para runtime   | ✅ |
| US-210 | SQL datasource                 | ✅ |
| US-211 | GraphQL datasource             | ✅ |
| US-212 | Rotação de credenciais         | ✅ |
| US-301 | AI generate-app endpoint       | ✅ |
| US-302 | AI Prompt Panel (frontend)     | ✅ |
| US-311 | Transform sandbox (backend)    | ✅ |
| US-312 | Transform editor (frontend)    | ✅ |

## Riscos Ativos

- `SEC-003` RBAC de escopos finos: isolamento por `owner_id` e role suficiente para MVP.
- Transform sandbox usa RestrictedPython (Python puro); não permite JS real — nome renomeado para "Transform (Python)" na UI.
- Rotação de chave de criptografia (`DATASOURCE_ENCRYPTION_KEY`) ainda não automatizada para produção.


## Em Progresso

- Nenhum item aberto. MVP completo.

## Concluído Recentemente

- US-030 Datasource CRUD UI:
  - `DataSourcePanel.tsx` criado com formulário de create (nome, base URL, auth type/token/basic) e lista com delete.
  - `useBuilderOrchestrator` estendido com estado e handlers de datasource.
  - `BuilderWorkspace` renderiza `DataSourcePanel` no grid de painéis.
- US-002 Empty State:
  - `EmptyState.tsx` criado — CTA centralizado com formulário de criação de app.
  - Canvas renderiza `EmptyState` quando `apps.length === 0 && !appsLoading`.
  - CSS `.empty-state*` adicionado ao `styles.css`.
- Cobertura de testes ampliada (Sprint 2):
  - 12 testes de integração em `backend/tests/test_datasource_router.py` (via `TestClient` + dependency overrides).
  - 5 testes E2E em `frontend/tests/e2e/datasource-crud.spec.ts`.
  - 4 testes E2E em `frontend/tests/e2e/empty-state.spec.ts`.
  - Totais: 17 testes backend / 21 unit / 11 E2E — todos passando.
- Bug fix: `apiRequest` crashava em respostas 204 No Content ao chamar `.json()`. Corrigido em `frontend/src/lib/api.ts`.

## Status das US do MVP

| US    | Feature                  | Status |
|-------|--------------------------|--------|
| US-001 | Auth/login              | ✅ |
| US-002 | Empty state CTA         | ✅ |
| US-010 | Criar app               | ✅ |
| US-011 | Criar página            | ✅ |
| US-020 | Adicionar Table widget  | ✅ |
| US-021 | Editar propriedades     | ✅ |
| US-030 | Criar datasource REST   | ✅ |
| US-031 | Criar e executar query  | ✅ |
| US-040 | Bindar query na tabela  | ✅ |
| US-041 | Abrir preview           | ✅ |
| US-050 | Ambiente local completo | ✅ |
| US-051 | Smoke test + testes backend | ✅ |

## Próximos Passos

- Nenhum item de backlog MVP aberto.
- Próxima decisão de produto: Sprint 3 (pós-MVP) — RBAC, rotação de chave, SQL datasource, templates.

## Riscos Ativos

- `SEC-003` Sem RBAC/escopos finos: isolamento por `owner_id` protege MVP interno; não bloqueante.
- Rotação de chave de criptografia (`DATASOURCE_ENCRYPTION_KEY`) ainda não automatizada para produção.


## Em Progresso

- Evolução do MVP para hardening de segurança e cobertura de testes.
- Início da migração frontend premium (M0): base de design system e modularização.

## Concluído Recentemente

- Especificação principal do projeto foi movida para `docs/plan/toolstack-ai-project-spec.md`.
- Estrutura de pastas de `frontend`, `backend`, `packages` e `infra` foi materializada.
- Fluxo de agentes com orquestração, release e segurança foi configurado.
- ADR `ADR-0001-modular-monolith-first.md` criado e aceito.
- Bootstrap técnico validado:
  - Backend FastAPI com `GET /health` e `POST /api/queries/execute` (mock).
  - Frontend React/Vite com integração ao endpoint mock.
  - Build do frontend concluído com sucesso.
  - `docker compose config` válido para ambiente local.
- Slice vertical inicial entregue e validado em runtime:
  - Auth com JWT (`/api/auth/register`, `/api/auth/login`, `/api/auth/me`).
  - CRUD autenticado de apps (`/api/apps`) e páginas (`/api/apps/{app_id}/pages`).
  - Stack local em execução com `docker compose up -d` (Postgres, Redis, Backend e Frontend).
  - Fluxos HTTP validados ponta a ponta (health, auth, criação e listagem de app/página, query mock).
- Lote de execução MVP concluído:
  - CRUD de datasources REST implementado em `api/datasources`.
  - `POST /api/queries/execute` migrou para execução REST real com fallback mock legado.
  - Guardrail SSRF inicial no executor REST (bloqueio fora de `development`).
  - Frontend com query panel configurável e persistência de queries (`run_on_load`) em `layout_json`.
  - Runtime passou a executar queries `run_on_load` e aplicar binding `{{query_name.data}}` em widget table.
  - Testes executados com sucesso:
    - `python -m unittest backend/tests/test_query_service.py`
    - `python backend/tests/smoke_api.py`
    - `npm run build` no frontend
- Hardening de segredos de datasource concluído:
  - `auth_config` agora é criptografado em repouso com Fernet.
  - Execução de query decripta credenciais de datasource em runtime.
  - Testes de round-trip de criptografia adicionados em `backend/tests/test_datasource_secrets.py`.
  - Smoke test atualizado para datasource `bearer`.
- Frontend M0 iniciado:
  - Dependências premium adicionadas (`react-query`, `react-router-dom`, `zustand`, `dnd-kit`, `@xyflow/react`, `recharts`, base de testes).
  - `shadcn/ui` inicializado com `components.json`, `src/components/ui/button.tsx` e `src/lib/utils.ts`.
  - Tailwind configurado para tokens de design system e aliases `@/*` no TypeScript/Vite.
  - Estrutura modular criada (`src/app`, `src/features`, `src/editor`, `src/runtime`, `src/legacy`).
  - App monolítico movido para `src/legacy/LegacyApp.tsx` com `AppShell` + providers + rotas como nova entrada.
  - Build do frontend validado com sucesso após migração inicial.
- Frontend M0 avançado:
  - Painéis de `auth`, `apps` e `pages` extraídos de `LegacyApp` para `features/*`.
  - Componentes `shadcn/ui` aplicados nesses painéis (`button`, `card`, `input`).
  - `LegacyApp` agora consome componentes de feature com props, reduzindo acoplamento.
  - Build do frontend segue estável após extração.

## Próximos Passos

1. M0 frontend: extrair painéis de `LegacyApp` para módulos `features/auth`, `features/apps`, `features/pages`.
2. M0 frontend: extrair área de query panel + canvas toolbar em componentes de feature.
3. M1 frontend: implementar canvas V2 com `dnd-kit` (multi-select, snap/grid, teclado).
4. M2 frontend: integrar `React Flow` para query graph e `Recharts` para widgets chart.

## Riscos Ativos

- Não há RBAC/escopos finos ainda, apenas autenticação básica por usuário.
- Estratégia de rotação de chave de criptografia ainda não definida para produção.

## Decisões Pendentes

- Definir estratégia final de hardening para allowlist de hosts em produção.
