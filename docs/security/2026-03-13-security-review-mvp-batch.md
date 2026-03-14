# Security Review: MVP Batch

## Data

2026-03-13

## Escopo

- `api/datasources` CRUD autenticado.
- Migração de `api/queries/execute` para execução REST real.
- Binding runtime `{{query_name.data}}` com `run_on_load`.

## Findings

- `SEC-001` SSRF no executor REST: mitigado com validação de scheme/host e bloqueio fora de `development`.
- `SEC-002` Secrets em repouso (`auth_config`): mitigado com criptografia Fernet em repouso.
- `SEC-003` RBAC não implementado: aberto, não bloqueante para MVP interno.

## Verificações

- Resposta de datasource não expõe `auth_config`; retorna apenas `has_auth_config`.
- Endpoint de query exige autenticação e ownership de datasource.
- Smoke test end-to-end validou criação de datasource e execução real.

## Decisão

Go with constraints

## Restrições para release interna

- Ambiente deve permanecer em `development` apenas para testes locais.
- Definir plano de rotação para `DATASOURCE_ENCRYPTION_KEY` antes de produção.
