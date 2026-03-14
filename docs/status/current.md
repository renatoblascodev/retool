# Current Status

## Data

2026-03-13

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
