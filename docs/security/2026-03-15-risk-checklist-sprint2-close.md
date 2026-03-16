# Risk Checklist — Sprint 2 Close

## Data

2026-03-15

## Escopo

- Datasource CRUD UI (US-030)
- Empty State CTA (US-002)
- Testes de integração backend (datasource router, secrets, query service)
- Testes E2E frontend (datasource-crud, empty-state, query-binding-runtime)

---

## Checklist de Risco

### Segurança

| # | Item | Status |
|---|------|--------|
| 1 | `auth_config` não é exposto na resposta de GET/LIST datasources (apenas `has_auth_config`) | ✅ |
| 2 | Credentials de bearer/basic são criptografados em repouso (Fernet) antes de persistir | ✅ |
| 3 | Endpoints de datasource exigem autenticação JWT válida | ✅ |
| 4 | PATCH/DELETE verificam `owner_id` do datasource antes de agir | ✅ |
| 5 | Executor de query REST não aceita targets SSRF fora de `development` | ✅ |
| 6 | SEC-003 (sem RBAC) não bloqueante para MVP interno (isolamento por owner_id) | ✅ aceitável |

### Qualidade

| # | Item | Status |
|---|------|--------|
| 7 | Build TypeScript sem erros (`pnpm build`) | ✅ |
| 8 | 21 testes unitários frontend passando | ✅ |
| 9 | 11 testes E2E Playwright passando (2 query-binding + 5 datasource + 4 empty-state) | ✅ |
| 10 | 17 testes backend passando (5 secrets + 3 query service + 12 datasource router) | ✅ |
| 11 | Nenhum teste bloqueado ou ignorado (`skip`/`xfail`) | ✅ |

### Operação

| # | Item | Status |
|---|------|--------|
| 12 | Ambiente local sobe via `docker compose up -d` | ✅ |
| 13 | `GET /health` responde 200 | ✅ |
| 14 | Frontend build de produção gerado com sucesso | ✅ |
| 15 | Bug 204 No Content em DELETE corrigido (`apiRequest` não chama `.json()` em 204) | ✅ |

### Riscos Abertos (não bloqueantes para MVP interno)

| ID | Descrição | Severidade | Plano |
|----|-----------|------------|-------|
| SEC-003 | Sem RBAC/escopos finos por colaborador | non-blocking | Pós-MVP Sprint 3 |
| OPS-001 | Rotação automática de `DATASOURCE_ENCRYPTION_KEY` não implementada | non-blocking | Pré-release externo |
| OPS-002 | Allowlist explícita de hosts SSRF não configurada para produção | non-blocking | Pré-release externo |

## Decisão

**Go with constraints** para MVP interno.

Restrições:
- Ambiente deve permanecer em `development` para execução de queries remotas.
- Não usar credenciais de produção em datasources antes de OPS-001 resolvido.
- Release externo requer resolução de OPS-002 (allowlist SSRF).
