# Sprint 3 Backlog — ToolStack AI (Paridade Visual com Retool)

> Objetivo: transformar o MVP funcional num produto visualmente profissional,
> com layout de builder real, design system coeso, biblioteca de widgets e
> query UX completa.

---

## Sprint 3A — Shell do Builder (Layout Profissional)

**Objetivo:** Substituir o `panel-grid` CSS por um layout de builder real:
sidebar esquerda, canvas central com grid/snap, sidebar direita de propriedades.

**Responsáveis:** UX Specialist + Frontend

### US-100 Shell de 3 colunas do Builder

- Como desenvolvedor, quero um layout de builder com sidebar esquerda, canvas central
  e painel de propriedades à direita, para ter uma experiência visual próxima do Retool.

Critérios de aceitação:
1. Layout dividido em: left sidebar (240px colapsável) | canvas central (flex-1) | right panel (280px colapsável).
2. Sidebars colapsam com animação suave e ícone de toggle.
3. Header fixo no topo com: logo, nome do app/página, botão Preview, botão Save.
4. Responsivo: em viewport < 900px, sidebars colapsam automaticamente.
5. Estado de colapso persiste em localStorage.

### US-101 Left Sidebar — Navegação estruturada

- Como desenvolvedor, quero uma sidebar esquerda com abas de navegação para acessar
  Apps, Pages, Componentes e Datasources sem poluir o canvas.

Critérios de aceitação:
1. Sidebar tem abas com ícones: Apps | Pages | Components | Datasources.
2. Cada aba renderiza o painel correspondente (AppsPanel, PagesPanel, etc.).
3. Aba ativa tem highlight visual claro.
4. Search/filter dentro de cada aba.

### US-102 Canvas com grid visual e snap

- Como desenvolvedor, quero ver um grid pontilhado no canvas e sentir snap dos
  componentes ao grid ao arrastar.

Critérios de aceitação:
1. Grid de 8px com pontos visíveis no fundo do canvas.
2. Widgets fazem snap ao grid durante drag (múltiplo de 8px).
3. Guideline horizontal/vertical aparece ao alinhar com outros widgets.
4. Resize handles visíveis nos cantos e bordas do widget selecionado.
5. Seleção múltipla com rubber-band (clicar e arrastar no canvas vazio).

### US-103 Right Panel — Inspector de propriedades contextual

- Como desenvolvedor, quero um painel direito que mude de conteúdo conforme o
  widget selecionado, com abas de Propriedades e Estilo.

Critérios de aceitação:
1. Sem seleção: painel mostra atalhos rápidos (Add widget, Run query).
2. Com widget selecionado: mostra propriedades específicas do tipo.
3. Abas: Propriedades | Estilo | Eventos.
4. Campos com labels, tooltips e validação inline.
5. Alterações refletem no canvas em tempo real (sem Save manual).

---

## Sprint 3B — Design System Coeso

**Objetivo:** Aplicar shadcn/ui + Tailwind em 100% da UI, ícones Lucide,
tipografia consistente e tokens de espaçamento.

**Responsáveis:** UX Specialist + Frontend

### US-110 Design tokens e tipografia

- Como usuário, quero uma interface com tipografia e espaçamento consistentes
  em toda a aplicação.

Critérios de aceitação:
1. Fonte: Inter (ou Geist) carregada via Google Fonts / local.
2. Scale tipográfico: xs/sm/base/lg/xl/2xl.
3. Espaçamento baseado em múltiplos de 4px (Tailwind default).
4. Paleta de cores: dark theme com `slate-900` base, `slate-800` surface,
   acentos em `violet-500`.
5. CSS variables para todos os tokens (compatível com shadcn/ui).

### US-111 Ícones Lucide em toda a UI

- Como desenvolvedor, quero ícones consistentes em todos os botões e labels.

Critérios de aceitação:
1. `lucide-react` instalado e usado em 100% dos ícones.
2. Substituir emojis/texto por ícones: ChevronLeft, Plus, Trash2, Play, Save...
3. Tamanho padrão de ícone: 16px inline, 20px em botões de destaque.

### US-112 Componentes shadcn/ui completos

- Como desenvolvedor, quero todos os formulários e painéis usando componentes
  shadcn/ui para consistência visual.

Critérios de aceitação:
1. Input, Select, Button, Label, Badge, Separator, Tooltip aplicados em todos os painéis.
2. Card com header/content nos painéis de forms.
3. Skeleton loader em todos os estados de loading (substituir `<p>Loading...</p>`).
4. Toast/sonner para feedback de sucesso/erro em ações de create/delete.

### US-113 Empty states e micro-interações

- Como usuário, quero feedback visual claro em estados vazios e ações.

Critérios de aceitação:
1. Empty state com ícone + título + CTA em: apps, pages, widgets, datasources, queries.
2. Hover state em todos os list items (background sutil).
3. Focus ring acessível em todos os elementos interativos.
4. Transition suave (150ms ease) em abrir/fechar painéis.

---

## Sprint 3C — Widget Library

**Objetivo:** Expandir de 3 para 10+ tipos de widget, cada um com propriedades
ricas no inspector e renderização fiel no preview.

**Responsáveis:** Frontend + UX Specialist + Backend (schema)

### US-120 Widget Button

- Critérios: label, variant (primary/secondary/danger), disabled, onClick (expressão JS),
  renderizado no canvas e no preview.

### US-121 Widget Text Input

- Critérios: placeholder, label, value binding, onChange, validação inline.

### US-122 Widget Select

- Critérios: options (static list ou `{{query.data}}`), value binding, onChange.

### US-123 Widget Form Container

- Critérios: agrupa campos filhos, botão Submit, `onSubmit` executa query.

### US-124 Widget Modal

- Critérios: trigger via evento de outro widget, conteúdo configurável, fechar via botão.

### US-125 Widget Stat (KPI Card)

- Critérios: título, valor (binding), subtítulo, ícone, cor de destaque.

### US-126 Widget Chart — Bar, Line, Pie

- Critérios: dataSource binding, configuração de eixos, cores, labels. Usa Recharts.

### US-127 Widget Image

- Critérios: src (URL ou binding), alt text, fit (cover/contain/fill).

### US-128 Widget Divider / Spacer

- Critérios: separador horizontal com altura configurável.

### US-129 Inspector de propriedades por tipo

- Cada widget tem seu próprio schema de propriedades no inspector.
- Critérios: campos dinâmicos por tipo, sem campos irrelevantes, agrupados por categoria.

---

## Sprint 3D — Query UX Profissional

**Objetivo:** Query panel com UX completa: múltiplas queries por página,
autocomplete de binding, abas, histórico de execução e SQL datasource.

**Responsáveis:** Frontend + Backend (Python) + UX Specialist

### US-130 Múltiplas queries por página

- Critérios:
  1. Lista de queries na sidebar esquerda (aba Queries).
  2. Criar/renomear/deletar query.
  3. Query ativa abre no painel inferior.
  4. Queries persistidas no `layout_json`.

### US-131 Autocomplete de binding no inspector

- Critérios:
  1. Campos de propriedade que aceitam `{{...}}` mostram autocomplete.
  2. Sugestões: `query1.data`, `query2.data`, `currentUser.email`.
  3. Monaco Editor inline (single-line) nos campos de binding.

### US-132 Painel inferior de query (Query Bottom Panel)

- Critérios:
  1. Painel no rodapé do canvas (colapsável, 300px).
  2. Abas: Editor | Response | Headers | Logs.
  3. Response renderizada como JSON pretty-print com syntax highlighting.
  4. Timestamp e duração da última execução.

### US-133 Histórico de execução

- Critérios:
  1. Últimas 10 execuções de cada query em memória.
  2. Clicar numa execução mostra request + response.
  3. Badge de status (200, 4xx, 5xx) com cor.

### US-134 SQL Datasource (PostgreSQL)

- Critérios:
  1. Tipo `sql` em datasource com host, port, database, user, password.
  2. Backend executa query SQL via asyncpg (não via httpx).
  3. Resultado normalizado como array de objetos (igual ao REST).
  4. Credenciais criptografadas com Fernet (mesmo padrão atual).

---

## Épico Transversal — Qualidade Sprint 3

### US-140 Testes E2E para novos fluxos

- Playwright: sidebar toggle, widget drag-and-drop, inspector update em tempo real.

### US-141 Testes de acessibilidade

- axe-playwright: sem violações críticas de a11y no layout principal.

### US-142 Performance baseline

- Lighthouse CI: FCP < 2s, TTI < 4s no builder em dev.

---

## Prioridade e sequência

| Sprint | Duração estimada | Pré-requisito |
|--------|-----------------|---------------|
| 3A — Shell Layout | 1–2 semanas | MVP completo ✅ |
| 3B — Design System | 1 semana | Sprint 3A |
| 3C — Widget Library | 2–3 semanas | Sprint 3B |
| 3D — Query UX + SQL | 2–3 semanas | Sprint 3B |

**Ordem de entrega:** 3A → 3B (paralelo com início 3C/3D) → 3C + 3D conjuntos.

## KPIs de sucesso do Sprint 3

- Builder parece um produto profissional (avaliação subjetiva do PO).
- Novo usuário consegue criar um dashboard em < 5 minutos sem tutorial.
- Cobertura de testes mantida: ≥ 34 backend / ≥ 21 unit / ≥ 11 E2E.
- Lighthouse score ≥ 80 performance em dev build.
