# Release Decision: mvp-batch

## Data

2026-03-13

## Escopo

- CRUD de datasources REST no backend.
- Executor de query REST real com fallback mock legado.
- Query panel configurável no frontend.
- Runtime com `run_on_load` e binding `{{query_name.data}}` em table.

## Qualidade

- Status QA: aprovado para MVP interno.
- Cobertura crítica:
  - `python -m unittest backend/tests/test_query_service.py`
  - `python backend/tests/smoke_api.py`
  - `npm run build` (frontend)
- Risco funcional: médio (feature nova de execução remota).

## Segurança

- Findings bloqueantes: nenhum.
- Major risks: `SEC-002` credenciais sem criptografia em repouso.
- Status Security Review: Go with constraints.

## Operação

- Status deploy: ambiente local validado.
- Smoke checks: aprovados.
- Rollback pronto: Sim

## Decisão

Go with constraints

## Condições (se houver)

- Não usar segredos de produção em datasources até criptografia de `auth_config`.
- Configurar política de host allowlist para produção antes de release externo.

## Donos

- Release Manager: Engineering
- QA: Engineering
- DevOps: Engineering
- Product: Product Owner
