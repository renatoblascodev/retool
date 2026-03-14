# MVP Tasks by Agent

## Product Owner

1. Priorizar os épicos do MVP.
2. Congelar fora de escopo inicial.
3. Refinar critérios de aceitação das user stories US-001 a US-051.

## Tech Lead Architect

1. Registrar ADR-0001 para monólito modular + monorepo.
2. Confirmar boundaries entre `frontend`, `backend`, `packages` e `infra`.
3. Definir contratos mínimos entre builder, query engine e preview.

## UX Specialist

1. Definir fluxo de login, dashboard vazio e criação de app.
2. Definir UX do canvas, sidebar de widgets e painel de propriedades.
3. Definir UX do query panel e do preview.

## Frontend React Mobile Specialist

1. Bootstrap do app React com layout do builder.
2. Criar canvas básico e widget Table.
3. Implementar query panel e binding mínimo da tabela.
4. Implementar preview mode.

## Python Integrations Senior

1. Bootstrap do backend FastAPI com healthcheck.
2. Criar módulos iniciais de auth, apps, pages, datasources e queries.
3. Implementar executor REST mínimo.
4. Implementar endpoint de execução de query.

## DevOps

1. Criar infraestrutura local com Docker Compose.
2. Definir variáveis de ambiente base.
3. Garantir startup de frontend, backend, postgres e redis.

## QA Test Automation

1. Definir smoke tests do fluxo MVP.
2. Cobrir ao menos um teste de integração backend e um teste de frontend.
3. Preparar checklist de regressão do MVP.

## Security Reviewer

1. Revisar auth básico, credenciais de datasource e executor REST.
2. Validar proteção inicial contra SSRF e exposição de segredos.
3. Classificar riscos bloqueantes antes do primeiro release interno.

## Release Manager

1. Definir critério de go/no-go do MVP interno.
2. Consolidar sinais de QA, Security e DevOps.
3. Preparar rollout interno e rollback simples.
