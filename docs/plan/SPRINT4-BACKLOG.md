# Sprint 4 Backlog — ToolStack AI (Colaboração, GraphQL e Templates)

> **Objetivo:** Elevar a plataforma de ferramenta individual para produto colaborativo,
> completar a trifeta de conectores (REST ✅ SQL ✅ GraphQL novo), introduzir templates
> para reduzir time-to-value de novos usuários, e estabelecer pipeline de CI/CD auditável.
>
> **Pré-requisito:** Sprint 3 completa ✅ (50 backend / 26 unit / 25 E2E passando).
>
> **KPIs de sucesso:**
> - Usuário consegue compartilhar um app com outro usuário e definir role em < 60s.
> - Usuário consegue criar um app a partir de template em < 30s.
> - Query GraphQL executa e popula widget em < 5 passos (analysis = criar query → executar → vincular).
> - Pipeline CI/CD verde em toda PR nova.
> - Cobertura: ≥ 70 backend / ≥ 30 unit / ≥ 35 E2E.

---

## Sprint 4A — RBAC e Compartilhamento

**Objetivo:** Fechar SEC-003 (risco aberto desde Sprint 2), introduzir papéis por app
(owner / editor / viewer) e permitir que o dono compartilhe o app com colaboradores.

**Responsáveis:** Tech Lead Architect (contrato de API + schema) → Python Senior (backend)
+ Frontend React (UI de compartilhamento).

---

### US-200 Roles por app (RBAC)

> Como dono de um app, quero controlar o que cada colaborador pode fazer,
> para proteger meu trabalho de alterações indesejadas.

**Critérios de aceitação:**

1. Nova tabela `app_members(app_id, user_id, role)` com role `owner | editor | viewer`.
   - Ao criar um app, o criador é automaticamente inserido com `role=owner`.
2. Todos os endpoints de mutação (`PUT`, `DELETE`, `POST` em apps, pages, datasources,
   queries) verificam se o `current_user` é `owner` ou `editor` do app. Retornam
   `403 Forbidden` caso contrário.
3. Endpoints de leitura (`GET`) permitem acesso a `viewer`, `editor` e `owner`.
4. `GET /api/apps` retorna apenas apps onde o usuário é membro (qualquer role).
5. Testes: ≥ 12 pytest com cenários de escalada de privilégio e IDOR.

**Fora de escopo:** Roles a nível de página ou widget. Permissions globais de organização.

---

### US-201 Convidar membro por email

> Como dono de um app, quero convidar um colega por email e atribuir seu role,
> para que ele possa colaborar no meu app.

**Critérios de aceitação:**

1. `POST /api/apps/{app_id}/members` body `{ email, role }`.
   - Se o email corresponde a um usuário cadastrado: adiciona diretamente.
   - Se não existe: retorna `404` com mensagem clara ("usuário não encontrado;
     convite por email será adicionado no Sprint 5").
2. Apenas `owner` pode convidar membros.
3. Frontend: botão "Share" no header → drawer lateral com campo de email + select de role
   (Editor / Viewer) + botão "Invite".
4. Feedback visual de sucesso/erro inline no drawer.
5. Testes: 4 pytest (sucesso, usuário não encontrado, sem permissão, email duplicado).

---

### US-202 Listar e revogar membros

> Como dono de um app, quero ver quem tem acesso e remover colaboradores,
> para manter o controle do app.

**Critérios de aceitação:**

1. `GET /api/apps/{app_id}/members` → lista `[{ user_id, email, role, joined_at }]`.
2. `DELETE /api/apps/{app_id}/members/{user_id}` — apenas `owner`; não pode remover a si mesmo.
3. `PATCH /api/apps/{app_id}/members/{user_id}` body `{ role }` — altera role.
4. Frontend: dentro do drawer "Share", lista de membros com avatar/email, badge de role
   e botão de remover.
5. Testes: 5 pytest (listar, revogar, trocar role, auto-remoção bloqueada, não-owner bloqueado).

---

### US-203 Preview/runtime read-only para viewers

> Como viewer de um app, quero acessar o preview sem poder editar nada,
> para consumir a ferramenta com segurança.

**Critérios de aceitação:**

1. Rota `/builder/:appId/:pageId` redireciona `viewer` para `/runtime/:appId/:pageSlug`
   com badge "View only" visível.
2. `viewer` não vê o header do builder (botão Save, botões de widget palette).
3. Backend: `GET /api/apps/{app_id}/me/role` retorna o role do usuário autenticado no app.
4. Testes E2E: 2 testes (viewer redirecionado, editor acessa builder normalmente).

---

## Sprint 4B — GraphQL Datasource

**Objetivo:** Completar a trifeta de conectores — REST ✅ SQL ✅ GraphQL.
Permite que times com APIs GraphQL (Shopify, GitHub, Hasura) usem a plataforma.

**Responsáveis:** Python Senior (executor + introspection + testes)
+ Frontend React (query builder UI).

---

### US-210 GraphQL Datasource — Backend

> Como desenvolvedor, quero conectar minha API GraphQL como datasource para
> executar queries e mutations diretamente no builder.

**Critérios de aceitação:**

1. Tipo `graphql` em datasource com campos: `endpoint` (URL), `headers` (JSON livre).
2. `POST /api/queries/execute` aceita `type=graphql`, `query` (string GQL),
   `variables` (objeto JSON opcional).
3. Executor envia `{ query, variables }` via `httpx.AsyncClient.post` ao endpoint,
   retorna `response.data` normalizado como array (ou objeto se não for lista).
4. Introspection: `POST /api/datasources/{id}/graphql/schema` retorna lista de types
   públicos via query `__schema` padrão. Usado pelo frontend para autocomplete.
5. Auth: suporta `bearer` e `header` customizado (mesma lógica do REST).
6. SSRF guard: mesma proteção DNS rebinding aplicada ao REST (OPS-002).
7. Testes: ≥ 10 pytest (execução básica, variables, mutation, erro GraphQL vs HTTP,
   introspection, SSRF, bearer auth, header customizado, timeout, resposta não-JSON).

---

### US-211 GraphQL Query Builder — Frontend

> Como desenvolvedor, quero editar uma query GraphQL com syntax highlight básico
> e body de variables, para testar e iterar rapidamente.

**Critérios de aceitação:**

1. Datasource panel: novo tipo `graphql` no select de tipo, com campos endpoint + headers.
2. Query panel: quando datasource é `graphql`, exibe:
   - Textarea principal para a query GQL (placeholder com query `{ users { id name } }`).
   - Textarea secundária colapsável "Variables (JSON)".
   - Botão "Fetch Schema" → chama endpoint de introspection e mostra types no dropdown.
3. Execute → chama `/api/queries/execute` e resultado aparece no bottom panel (mesmo flow REST).
4. Selector de operação (Query / Mutation) como radio group.

---

### US-212 Binding de resultado GraphQL em widgets

> Como desenvolvedor, quero vincular o resultado de uma query GraphQL a um widget
> Table ou Chart, da mesma forma que faço com REST.

**Critérios de aceitação:**

1. Runtime resolve `{{queryName.data}}` de resultado GraphQL — nenhuma mudança
   de código necessária se o executor normalizar para array de objetos.
2. Widget Table auto-detecta colunas a partir das chaves do primeiro objeto.
3. `BindingInput` inclui queries GraphQL no autocomplete (já funciona pelo `queryNames`).
4. Teste E2E: 1 teste mock-to-table com datasource GraphQL.

---

## Sprint 4C — App Templates

**Objetivo:** Reduzir drasticamente o time-to-value para novos usuários.
Um template elimina a curva de "blank canvas" e demonstra capabilities.

**Responsáveis:** Product Owner (conteúdo dos templates) + Python Senior (backend)
+ Frontend React (template picker) + UX Specialist (galeria visual).

---

### US-220 Backend de templates

> Como administrador da plataforma, quero um catálogo de templates que pode ser
> clonado para criar apps pré-configurados.

**Critérios de aceitação:**

1. Tabela `templates(id, name, slug, category, description, layout_json, thumbnail_url,
   is_public, created_at)`. Seed com 3 templates iniciais (ver US-221).
2. `GET /api/templates` — lista pública sem autenticação. Suporta `?category=`.
3. `POST /api/apps/from-template` body `{ template_id, app_name }` — cria app + página
   com `layout_json` do template. Retorna o app criado.
4. Testes: 5 pytest (listar, filtrar por categoria, criar a partir de template, template
   inexistente, app_name vazio).

---

### US-221 Template picker na empty state e no header

> Como novo usuário, quero escolher um template para começar meu app rapidamente,
> sem precisar configurar tudo do zero.

**Critérios de aceitação:**

1. Empty state exibe dois caminhos: "Start blank" e "Start from template".
2. "Start from template" abre modal com grid de cards de templates (thumbnail + nome + categoria).
3. Templates iniciais no seed:
   - **CRUD Table** (categoria: dados): tabela + datasource REST de exemplo + query `GET /users`.
   - **KPI Dashboard** (categoria: analytics): 3 widgets Stat + 1 Chart + query de exemplo.
   - **Form + Submit** (categoria: formulários): Input + Select + Button vinculados a `POST`.
4. Seleção de template → input de nome do app → botão "Create" → redireciona para builder com layout pré-populado.
5. Header do builder: botão "+ Template" (para owners) → mesmo modal, adiciona nova página.

---

### US-222 "Save as template" (owner)

> Como criador de um app útil, quero salvá-lo como template para reutilizá-lo
> em outros projetos.

**Critérios de aceitação:**

1. No header do builder (apenas `owner`): menu "…" → "Save as template".
2. Modal: campo nome, select categoria (dados / analytics / formulários / outro),
   upload de thumbnail (opcional).
3. `POST /api/apps/{app_id}/as-template` — captura `layout_json` atual da página,
   cria registro em `templates` com `is_public=false` (visível apenas ao owner).
4. Template aparece no picker do próprio usuário com badge "My templates".

---

## Sprint 4D — CI/CD e Developer Experience

**Objetivo:** Pipeline automatizado que garante que cada PR é verde antes de mergear,
e que releases são reproduzíveis e rastreáveis.

**Responsável:** DevOps.

---

### US-230 GitHub Actions — Pipeline de qualidade (CI)

> Como desenvolvedor, quero que testes rodem automaticamente em cada PR,
> para ter feedback rápido sem depender de rodar tudo localmente.

**Critérios de aceitação:**

1. `.github/workflows/ci.yml` dispara em `push` e `pull_request` para `main`.
2. Jobs paralelos:
   - `backend-tests`: Python 3.10, instala deps, roda `pytest --cov=app --cov-report=xml`.
   - `frontend-unit`: Node 20, `npm ci`, `npm run test`.
   - `frontend-e2e`: Node 20, instala browsers Playwright, `npm run test:e2e`.
3. Artefatos: coverage XML e Playwright HTML report como artifacts do workflow.
4. Badge de CI no `README.md`.
5. Falha em qualquer job → PR bloqueada (branch protection rule documentada).

---

### US-231 GitHub Actions — Pipeline de release (CD)

> Como responsável por releases, quero que uma tag `v*.*.*` dispare build e
> publicação da imagem Docker automaticamente.

**Critérios de aceitação:**

1. `.github/workflows/release.yml` dispara em `push` de tag `v*.*.*`.
2. Faz build do frontend (`npm run build`) e embed no container do backend.
3. Builda imagem Docker com tag `ghcr.io/<org>/toolstack-ai:<tag>`.
4. Push para GitHub Container Registry.
5. Cria GitHub Release com changelog automático (commits desde a última tag).

---

### US-232 Dev Container e onboarding rápido

> Como novo engenheiro no time, quero ter o ambiente de desenvolvimento pronto
> em < 5 minutos sem instalar nada além do VS Code e Docker.

**Critérios de aceitação:**

1. `.devcontainer/devcontainer.json` com:
   - Base image: `mcr.microsoft.com/devcontainers/python:3.10`.
   - `postCreateCommand` instala deps Python + Node + Playwright browsers.
   - Extensões VS Code: Pylance, ESLint, Prettier, Playwright Test.
2. `docker compose up -d` funciona dentro do devcontainer.
3. `README.md` atualizado com seção "Get started" em 5 passos (< 10 linhas).

---

## Épico Transversal — Qualidade Sprint 4

### US-240 Security review — RBAC e novos endpoints

- Security Reviewer audita authorização em todos os endpoints do Sprint 4A e 4B.
- Foco em: privilege escalation nos `/members`, IDOR em `/templates`, injeção via
  headers GraphQL, SSRF no executor GraphQL.
- Output: atualização do risk-register com findings e status.

### US-241 Testes E2E — novos fluxos

- Playwright: compartilhamento de app (convite + role + remoção), template picker,
  query GraphQL mock-to-widget, viewer redirecionado do builder.
- Meta: ≥ 10 novos testes E2E (total ≥ 35).

### US-242 Release note Sprint 4

- Release Manager consolida readiness: qualidade, segurança, operação.
- Cria `docs/release/2026-03-16-release-sprint4-close.md`.

---

## Prioridade e dependências

```
4A (RBAC)
  ├─► Backend schema + API  ────────────────────────────╮
  └─► Frontend share UI                                  │
                                                         ▼
4B (GraphQL)  ──────────────────────────────────► Quality (US-240/241)
4C (Templates) ─────────────────────────────────►
4D (CI/CD) ── totalmente paralelo ──────────────►  US-242 (Release)
```

4A deve ser concluída primeiro (fecha risco de segurança aberto).
4B, 4C e 4D podem rodar em paralelo entre si.

## Fora de escopo do Sprint 4

- Convite por email (link de convite enviado via SMTP) → Sprint 5.
- RBAC a nível de página ou widget → Sprint 5.
- GraphQL subscriptions (WebSocket) → Sprint 5.
- Marketplace público de templates (aprovação, rating) → Sprint 5.
- Geração de app via IA (core diferencial) → Sprint 5.
- Billing e planos → Sprint 5+.
