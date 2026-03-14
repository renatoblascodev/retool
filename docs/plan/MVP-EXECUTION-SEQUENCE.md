# MVP Execution Sequence

## Sprint 0: Alinhamento e Base

1. Product Owner fecha escopo do MVP.
2. Tech Lead registra ADR inicial.
3. UX define fluxo principal do builder e preview.
4. DevOps sobe base local mínima.
5. Frontend e Backend fazem bootstrap dos apps.

Entregáveis:

- backlog do MVP aprovado
- ADR-0001 criada
- docs de status iniciados
- ambiente local pronto

## Sprint 1: Fluxo Principal Funcional

1. Backend entrega auth simples, apps, pages e query REST mínima.
2. Frontend entrega login, dashboard, canvas e widget Table.
3. Integração entre query REST e tabela.
4. Preview mode funcional.

Entregáveis:

- criar app
- criar page
- adicionar table
- executar query REST
- visualizar dados

## Sprint 2: Robustez Mínima

1. QA automatiza smoke test principal.
2. Security revisa auth, datasource e executor.
3. DevOps fecha compose e healthchecks.
4. Release Manager consolida readiness do MVP interno.

Entregáveis:

- smoke test
- teste backend essencial
- checklist de risco
- decisão de release interna

## Dependências Críticas

- Query panel depende do endpoint de execução de query.
- Preview depende do binding mínimo do frontend.
- Release depende de QA, Security e DevOps.

## O que pode rodar em paralelo

- UX com Tech Lead após escopo inicial.
- Frontend bootstrap com Backend bootstrap.
- DevOps local setup em paralelo ao bootstrap técnico.
