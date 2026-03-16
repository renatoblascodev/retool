# Release Decision: sprint2-close

## Data

2026-03-15

## Escopo

- US-002 Empty state CTA (canvas mostra onboarding quando sem apps).
- US-030 Datasource CRUD UI (painel create/list/delete no builder).
- Testes de integração backend: 12 novos testes em `test_datasource_router.py`.
- Testes E2E: 9 novos testes (5 datasource-crud + 4 empty-state).
- Bug fix: `apiRequest` tratava 204 No Content como erro silencioso.

## Qualidade

- Status QA: aprovado.
- Cobertura crítica:
  - `python -m unittest discover backend/tests/` → 17 passando.
  - `pnpm test --run` → 21 passando.
  - `npx playwright test` → 11 passando.
  - `pnpm build` → 0 erros TypeScript.
- Risco funcional: baixo (UI sobre CRUD já testado no backend; empty state é view-only).

## Segurança

- Findings bloqueantes: nenhum.
- Major risks abertos:
  - `SEC-003` Sem RBAC (não bloqueante para MVP interno).
  - `OPS-001` Rotação de chave de criptografia (não bloqueante para MVP interno).
  - `OPS-002` Allowlist SSRF para produção (não bloqueante para MVP interno).
- Status Security Review: ver `docs/security/2026-03-15-risk-checklist-sprint2-close.md`.

## Operação

- Status deploy: ambiente local validado.
- Smoke checks: aprovados (health, auth, create app, create datasource, run query).
- Rollback pronto: Sim — nenhuma migração de DB neste batch (somente novas rotas e UI).

## Decisão

Go with constraints

## Condições

- Manter `ENV=development` para execução de queries externas.
- Não usar credenciais de produção em datasources até OPS-001 (rotação de chave) resolvido.
- Resolver OPS-002 (allowlist SSRF explícita) antes de release externo.

## Sprint 2 — Status Final

Todos os entregáveis do Sprint 2 completos:
- [x] Smoke test do fluxo principal
- [x] Testes backend essenciais (17 testes)
- [x] Checklist de risco (`2026-03-15-risk-checklist-sprint2-close.md`)
- [x] Decisão de release interna (este documento)

## Donos

- Release Manager: Engineering
- QA: Engineering
- DevOps: Engineering
- Product: Product Owner
