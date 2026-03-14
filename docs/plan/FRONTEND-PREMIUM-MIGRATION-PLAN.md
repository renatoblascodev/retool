# Frontend Premium Migration Plan

## Data

2026-03-13

## Objetivo

Evoluir o frontend atual (monolito em `frontend/src/App.tsx`) para uma arquitetura premium de builder usando:

- `shadcn/ui` para design system e consistencia de UI.
- `dnd-kit` para drag and drop robusto no canvas.
- `React Flow` para editor de grafo de queries/bindings.
- `Recharts` para widgets de chart no builder/runtime.

## Diagnostico Atual

- Frontend concentrado em `frontend/src/App.tsx` (~2300 linhas).
- Sem sistema de componentes reutilizavel (estilos custom em `styles.css`).
- Sem libs especializadas para drag, grafo e charts.
- Fluxo funcional MVP, mas com alto custo de evolucao e risco de regressao.

## Arquitetura Alvo

```text
frontend/src/
  app/
    AppShell.tsx
    routes.tsx
    providers/
  lib/
    api/
    layout/
      schema.ts
      binding.ts
  features/
    auth/
    apps/
    pages/
    queries/
      graph/QueryGraphPanel.tsx
  editor/
    store/useEditorStore.ts
    canvas/
    inspector/
  runtime/
    RuntimePage.tsx
    widgets/
  components/ui/   # shadcn/ui
```

## Dependencias Recomendadas

- Base: `react-router-dom`, `@tanstack/react-query`, `zustand`, `immer`, `zod`.
- UI: `shadcn/ui` + `class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react`.
- Canvas DnD: `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/modifiers`, `@dnd-kit/utilities`.
- Query Graph: `@xyflow/react`.
- Charts: `recharts`.
- Testes: `vitest`, `@testing-library/*`, `@playwright/test`, `msw`.

## Fases de Implementacao

### M0 - Foundation

- Introduzir `react-router-dom` e `react-query`.
- Extrair utilitarios de layout/binding de `App.tsx` para `lib/layout`.
- Inicializar `shadcn/ui` e migrar componentes base (Button/Input/Select/Dialog/Tabs/Toast).
- Quebrar `App.tsx` em modulos por dominio (auth/apps/pages/runtime/queries).

Criterio de aceite:

1. `App.tsx` com menos de 200 linhas.
2. Fluxo atual (login + apps/pages + runtime) sem regressao.
3. UI base unificada via componentes compartilhados.

### M1 - Builder Canvas V2

- Implementar `dnd-kit` no canvas com snap em grid 12 colunas.
- Suporte a multi-select, drag por teclado, reorder/layers e resize robusto.
- Painel inspector modular para tipos de widget.
- Melhorar empty/error/loading states.

Criterio de aceite:

1. Drag/resize com mouse e teclado.
2. Save/autosave sem corrida de estado.
3. Testes de interacao do canvas cobrindo casos criticos.

### M2 - Query Graph + Charts

- Integrar `React Flow` para visualizar datasource -> query -> widget binding.
- Persistir posicoes do grafo em `layout_json.meta.graphPositions`.
- Migrar renderer de chart para `Recharts` no builder/runtime.
- Sincronizar selecao entre grafo e inspector.

Criterio de aceite:

1. Grafo renderiza e permite navegacao/edicao de bindings.
2. Charts renderizam com dados bindados e fallback elegante.
3. E2E do fluxo query->binding->runtime aprovado.

## Plano da Equipe

- Product Owner: escopo por fase e acceptance criteria semanais.
- UX Specialist: fluxo Builder + Runtime + Query Graph, acessibilidade e microinteracoes.
- Frontend React: implementacao tecnica por fase e refatoracao incremental.
- Backend: contratos estaveis para layout/queries/datasources.
- QA: smoke + integracao + E2E por risco.
- Security: revisao de dependencias e fluxos de dados.
- DevOps: gates de build/test/performance e preview envs.
- Release Manager: go/no-go e rollback por feature flag.

## Riscos e Mitigacoes

- Acoplamento do App monolitico.
  - Mitigacao: strangler pattern por modulos.
- Regressao no editor durante migracao.
  - Mitigacao: feature flags por fase + testes E2E.
- Crescimento de bundle/perf.
  - Mitigacao: lazy loading de modulos pesados, metricas em CI.

## Go/No-Go por Fase

- M0: arquitetura modular ativa + regressao zero no fluxo principal.
- M1: canvas v2 estavel com teclado e autosave confiavel.
- M2: query graph e charts integrados com testes verdes.

## Proximo Passo Pratico

1. Executar M0 em PR inicial de fundacao:
   - adicionar dependencias,
   - criar shell/rotas/providers,
   - extrair `App.tsx` em modulos,
   - configurar primeiros componentes `shadcn/ui`.
