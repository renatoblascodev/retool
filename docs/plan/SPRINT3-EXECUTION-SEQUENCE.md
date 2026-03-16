# Sprint 3 — Sequência de Execução

> Este documento define a ordem, as dependências e os responsáveis por cada
> bloco de trabalho do Sprint 3.

---

## Visão geral do fluxo

```
Sprint 3A (Layout Shell)
  └─► Sprint 3B (Design System)
        ├─► Sprint 3C (Widget Library)
        └─► Sprint 3D (Query UX + SQL)
```

3A e 3B têm dependência sequencial (layout antes de estilo).
3C e 3D podem rodar em paralelo após 3B estar estabilizado.

---

## Sprint 3A — Shell do Builder

**Agente responsável:** `frontend-react-mobile` + `ux-specialist`

### Arquivos a modificar/criar

| Arquivo | Ação |
|---------|------|
| `src/features/builder/BuilderWorkspace.tsx` | Rewrite — novo layout 3 colunas |
| `src/features/builder/LeftSidebar.tsx` | NOVO — sidebar esquerda com abas |
| `src/features/builder/RightPanel.tsx` | NOVO — inspector contextual |
| `src/features/builder/BottomPanel.tsx` | NOVO — painel de queries inferior |
| `src/features/builder/BuilderHeader.tsx` | NOVO — top bar com logo e ações |
| `src/styles.css` | Remover `panel-grid`, adicionar novos tokens |

### Ordem de tasks

1. `BuilderHeader.tsx` — top bar com: Logo | App/Página nome | Preview | Save | UserMenu
2. `LeftSidebar.tsx` — abas: Apps | Pages | Components | Datasources | Queries
3. `RightPanel.tsx` — contextual: sem seleção mostra dicas, com widget mostra WidgetInspector
4. `BottomPanel.tsx` — resize vertical, abas: Query Editor | Response | Logs
5. `BuilderWorkspace.tsx` — orquestra os 4 painéis numa grid CSS profissional
6. CSS: tokens e layout no `styles.css` substituindo `panel-grid`

---

## Sprint 3B — Design System

**Agente responsável:** `frontend-react-mobile`

### Ordem de tasks

1. Verificar e completar CSS variables em `styles.css` (font, spacing, radius, shadow)
2. Substituir todos os `<p>Loading...</p>` por Skeleton shadcn/ui
3. Adicionar toast/sonner para feedback de ações (create, delete)
4. Padronizar Lucide icons em todos os botões e labels
5. Padronizar hover/focus states em todos os list items

---

## Sprint 3C — Widget Library

**Agente responsável:** `frontend-react-mobile`

### Ordem de tasks

1. Definir `WidgetSchema` em `src/lib/layout/schema.ts` por tipo
2. Criar `src/editor/widgets/` — um arquivo por widget type:
   - `ButtonWidget.tsx`
   - `TextInputWidget.tsx`
   - `SelectWidget.tsx`
   - `StatWidget.tsx`
   - `ImageWidget.tsx`
   - `DividerWidget.tsx`
3. `WidgetRenderer.tsx` — dispatcher que renderiza o tipo correto
4. Inspector fields por widget type:
   - `ButtonWidgetFields.tsx`
   - `TextInputWidgetFields.tsx`
   - `SelectWidgetFields.tsx`
5. Widget palette no LeftSidebar aba Components (drag para canvas)

---

## Sprint 3D — Query UX + SQL

**Agente responsável:** `frontend-react-mobile` (frontend) + `python-integrations-senior` (backend)

### Frontend — Ordem de tasks

1. Query list no LeftSidebar com CRUD de queries
2. `QueryBottomPanel.tsx` com Monaco editor (single-line binding) e response viewer
3. `useQueryHistory.ts` — últimas 10 execuções em memória
4. Autocomplete de bindings em campos de propriedades

### Backend — Ordem de tasks

1. `backend/app/datasources/types.py` — adicionar tipo `sql`
2. `backend/app/queries/sql_executor.py` — asyncpg runner (SELECT only por segurança)
3. `backend/app/queries/service.py` — dispatch por tipo de datasource
4. `backend/tests/test_sql_executor.py` — tests com asyncpg mock

---

## Gates de qualidade por sprint

| Sprint | Gate |
|--------|------|
| 3A | Layout renderiza sem erros, sidebars colapsam, canvas visível |
| 3B | Sem warnings de componentes depreciados, toast de sucesso visível |
| 3C | Todos os widgets renderizam no canvas e preview, inspector correto |
| 3D | SQL query executa, retorna dados, exibe no Table widget |

---

## Rastreamento de progresso

| ID | Sprint | Status |
|----|--------|--------|
| 3A-1 | BuilderHeader | ⬜ |
| 3A-2 | LeftSidebar | ⬜ |
| 3A-3 | RightPanel | ⬜ |
| 3A-4 | BottomPanel | ⬜ |
| 3A-5 | BuilderWorkspace refactor | ⬜ |
| 3B-1 | CSS tokens | ⬜ |
| 3B-2 | Skeleton loaders | ⬜ |
| 3B-3 | Toast feedback | ⬜ |
| 3C-1 | Widget schema | ⬜ |
| 3C-2 | Button widget | ⬜ |
| 3C-3 | TextInput widget | ⬜ |
| 3C-4 | Select widget | ⬜ |
| 3C-5 | Stat widget | ⬜ |
| 3D-1 | Query list CRUD | ⬜ |
| 3D-2 | Query bottom panel | ⬜ |
| 3D-3 | SQL executor backend | ⬜ |
