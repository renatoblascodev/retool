# Sprint 5 Backlog — ToolStack AI (IA, Transform e Convites por Email)

> **Objetivo:** Entregar o diferencial competitivo central da plataforma — geração de apps
> via IA — e completar dois itens diferidos do Sprint 4: sandbox de transformação JS
> para queries e convites por email com SMTP real.
>
> **Pré-requisito:** Sprint 4 completa ✅ (87 backend / 26 unit tests / CI/CD verde).
>
> **KPIs de sucesso:**
> - Usuário digita prompt e obtém layout de app gerado em < 10s (LLM p95).
> - `POST /api/ai/suggest-query` retorna sugestão de query correta para 80% dos cenários
>   de teste com schema simples.
> - Query com transform JS executa em < 500ms com sandbox isolado.
> - Usuário recebe email de convite em < 30s após envio (usando SMTP sandbox).
> - Cobertura: ≥ 100 backend / ≥ 30 unit / ≥ 38 E2E.

---

## Sprint 5A — AI App Generation

**Objetivo:** Implementar o diferencial central do produto — a geração automática de app
a partir de um prompt em linguagem natural, com integração LiteLLM.

**Responsáveis:** Python Senior (backend + LiteLLM) + Frontend React (AI Panel).

---

### US-300 Backend de geração de app via IA

> Como desenvolvedor, quero descrever o app que preciso em linguagem natural
> e receber um layout funcional gerado automaticamente, para reduzir em 80%
> o tempo de configuração inicial.

**Critérios de aceitação:**

1. Novo módulo `backend/app/ai/` com `router.py`, `service.py`, `schemas.py`, `prompts/`.
2. `POST /api/ai/generate-app` — autenticado. Body:
   ```json
   { "prompt": "...", "datasource_id": "uuid-opcional" }
   ```
3. Response `200`:
   ```json
   {
     "layout": [ { "i": "table1", "type": "Table", "x": 0, "y": 0, "w": 12, "h": 8,
                   "props": { "title": "Usuários", "queryName": "" } } ],
     "suggested_queries": [ { "name": "listUsers", "query": "..." } ],
     "explanation": "App gerado com tabela de usuários..."
   }
   ```
4. Integração via **LiteLLM** (`litellm.acompletion`) com `model` configurável por
   variável de ambiente `AI_MODEL` (default: `gpt-4o-mini`).
5. Output JSON estruturado obrigatório: o prompt de sistema instrui o LLM a retornar
   apenas JSON válido conforme schema `GenerateAppResponse`.
6. Timeout de 30s na chamada LLM; retorna `503` se exceder.
7. Se `datasource_id` fornecido: busca tipo e endpoint do datasource e inclui no contexto
   do prompt. Retorna `404` se datasource não encontrado ou não pertence ao usuário.
8. Rota protegida por autenticação JWT (qualquer usuário autenticado pode usar).
9. Testes: ≥ 10 pytest (geração básica, com datasource, sem datasource, prompt vazio,
   timeout simulado, schema inválido retornado pelo LLM rejeita, modelo fallback,
   datasource inexistente, usuário não autenticado, response bem-formada).

**Fora de escopo:** Streaming SSE, histórico de gerações, rate limiting por usuário,
billing por token.

---

### US-301 Sugestão de query via IA

> Como desenvolvedor, quero que a IA sugira uma query adequada com base no datasource
> conectado e no meu objetivo, para economizar tempo de trial and error.

**Critérios de aceitação:**

1. `POST /api/ai/suggest-query` — autenticado. Body:
   ```json
   { "datasource_id": "uuid", "goal": "listar todos os usuários ativos" }
   ```
2. Response `200`:
   ```json
   { "query": "SELECT * FROM users WHERE active = true", "explanation": "..." }
   ```
3. O prompt inclui o `type` do datasource (SQL, REST, GraphQL) e qualifica a sugestão
   por tipo: para SQL retorna query SQL, para REST retorna path + method.
4. Testes: ≥ 6 pytest (SQL, REST, GraphQL, goal vazio, datasource inexistente, não autenticado).

**Fora de escopo:** Introspection automática de schema SQL, execução direta da query sugerida.

---

### US-302 AI Prompt Panel no builder (Frontend)

> Como desenvolvedor, quero um painel lateral no builder para digitar um prompt
> e gerar o layout do meu app automaticamente, sem precisar adicionar widgets manualmente.

**Critérios de aceitação:**

1. Nova aba / botão "Generate with AI" (ícone `Sparkles`) no header do builder — visível
   apenas para `owner` e `editor`.
2. Ao clicar, abre `AIPromptPanel` (drawer lateral ou modal):
   - Textarea: "Describe the app you want to build..."
   - Select: datasource opcional (lista os datasources do app)
   - Botão "Generate" — desabilitado quando prompt vazio ou loading
   - Estado loading com spinner e mensagem "Generating..."
3. Ao receber resposta: exibe `explanation` em toast; substitui o layout da página atual
   com os widgets gerados (confirmação se houver widgets existentes).
4. Em caso de erro da API: exibe mensagem de erro amigável no painel.
5. Hook `useGenerateApp(appId)` — mutation TanStack Query para `POST /api/ai/generate-app`.
6. TypeScript sem erros, sem `any` nas interfaces do response.

**Fora de escopo:** Streaming visual widget-a-widget, undo/redo da geração, histórico
de prompts no painel.

---

## Sprint 5B — JS Transform Sandbox

**Objetivo:** Permitir que o usuário escreva JavaScript inline para transformar
o resultado de uma query antes de vincular a um widget. Completa o query engine.

**Responsáveis:** Python Senior (sandbox backend) + Frontend React (Monaco editor).

---

### US-310 Backend — Execução de JS transform com RestrictedPython

> Como desenvolvedor, quero adicionar um script de transformação à minha query
> para formatar/filtrar dados antes de exibi-los no widget, sem riscos de segurança.

**Critérios de aceitação:**

1. Campo opcional `transform_js: str | None` em `QueryRequest` (schemas de queries).
2. Após executar a query original, se `transform_js` presente: executa o script via
   `RestrictedPython` sandbox com `data` como variável de entrada. O script deve
   retornar (última expressão ou `result =`) o valor transformado.
3. Sandbox tem:
   - Sem acesso a `import`, `os`, `sys`, `open`, `exec`, `eval`.
   - Timeout de 2s (thread com `signal.alarm` ou `concurrent.futures`).
   - Acesso a builtins seguros: `len`, `list`, `dict`, `str`, `int`, `float`,
     `sorted`, `filter`, `map`, `sum`, `min`, `max`, `enumerate`, `zip`.
4. Se o script lançar exceção: retorna `400` com `{ "error": "transform_error",
   "detail": "<mensagem>" }` sem expor stack trace completo.
5. Se timeout: retorna `408` com `{ "error": "transform_timeout" }`.
6. Testes: ≥ 10 pytest (transform básico, filtro, sort, import proibido, exec proibido,
   timeout, exceção no script, data=lista, data=dict, script vazio passa sem transformar).

**Fora de escopo:** Múltiplos scripts por query, persistência do script, acesso a
outros datasources dentro do script.

---

### US-311 Frontend — Monaco editor para JS transform

> Como desenvolvedor, quero escrever meu script de transformação diretamente
> no query panel, com syntax highlight de JavaScript.

**Critérios de aceitação:**

1. No query panel: seção colapsável "Transform (JS)" abaixo do query body.
2. Quando expandida: editor Monaco com `language="javascript"`, altura mínima 80px.
3. Placeholder: `// data is your query result (array or object)\n// return the transformed value\ndata.filter(row => row.active)`.
4. `transform_js` incluído no payload de `executeQuery` e salvo junto com a query.
5. Se a resposta retornar `transform_error` ou `transform_timeout`: exibe mensagem
   de erro no painel de resultado com destaque em vermelho.
6. TypeScript sem erros.

**Fora de escopo:** Autocomplete de colunas do datasource, testes unitários do script
antes da execução, linting JS inline.

---

## Sprint 5C — Email Invites com SMTP

**Objetivo:** Completar o fluxo de convite do Sprint 4 — atualmente o backend cria o
membro direto sem enviar email. Este sprint adiciona link de convite e envio SMTP real.

**Responsáveis:** Python Senior (backend SMTP + token) + Frontend React (UI de convite).

---

### US-320 Backend — Link de convite e envio de email

> Como dono de um app, quero convidar um colega por email com um link temporário,
> para que ele possa aceitar e entrar no app sem precisar de conta pré-existente.

**Critérios de aceitação:**

1. Nova tabela `app_invites(id UUID, app_id FK, email, role, token UUID, expires_at,
   accepted_at nullable, created_by FK users)`.
2. Migration Alembic `0005_app_invites.py`.
3. `POST /api/apps/{app_id}/invites` — owner only. Body: `{ "email": "...", "role": "editor|viewer" }`.
   - Cria registro em `app_invites` com `token = uuid4()`, `expires_at = now + 7 dias`.
   - Envia email via `smtplib` com conteúdo HTML simples: nome do app, role, link de aceite.
   - Link: `{FRONTEND_URL}/invites/accept?token={token}`.
   - Configuração SMTP via env vars: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`,
     `SMTP_FROM`. Se `SMTP_HOST` não configurado: loga o link no console (dev mode).
4. `GET /api/invites/accept?token=...` — público (sem auth). Sem criar sessão ainda.
   - Valida token: não expirado, não aceito. Retorna `{ "app_id", "app_name", "role",
     "email", "inviter_name" }` para o frontend exibir confirmação.
   - Retorna `404` se token inválido/expirado.
5. `POST /api/invites/accept` — autenticado. Body: `{ "token": "..." }`.
   - Valida token. Confere que `current_user.email == invite.email`.
   - Cria `AppMember(app_id, user_id=current_user.id, role=invite.role)`.
   - Marca `invite.accepted_at = now`.
   - Retorna `{ "app_id" }` para redirecionar o frontend.
6. Testes: ≥ 10 pytest (enviar convite, aceitar convite, token expirado, email errado,
   token já aceito, SMTP dev-mode loga console, role inválido, não owner, convite duplicado
   (idempotente), buscar info do token).

**Fora de escopo:** Reenvio de convite, revogação antecipada, convites sem conta
(signup via invite), limite de convites por app.

---

### US-321 Frontend — Fluxo de aceite de convite

> Como convidado, quero clicar no link do email, ver os detalhes do convite
> e confirmar minha entrada no app com um clique.

**Critérios de aceitação:**

1. Nova rota `/invites/accept` — página `InviteAcceptPage.tsx`.
2. Ao carregar: lê `?token=` da URL, chama `GET /api/invites/accept?token=...`.
3. Exibe card com: nome do app, role atribuído, quem convidou.
4. Se usuário não autenticado: botão "Login to accept" → redireciona para `/login?next=...`.
5. Se autenticado: botão "Accept and open app" → chama `POST /api/invites/accept`
   → redireciona para `/builder/:appId`.
6. Se token expirado/inválido: exibe estado de erro com link para home.
7. Hook `useInviteToken(token)` + `useAcceptInvite()` em `useInvites.ts`.
8. TypeScript sem erros.

---

## Épico Transversal — Qualidade Sprint 5

### US-330 Security Review — AI endpoints e JS Sandbox

**Agente:** Security Reviewer

- Revisar `POST /api/ai/generate-app` para: SSRF via `datasource_id`, prompt injection,
  vazamento de dados de outros usuários no contexto do LLM.
- Revisar sandbox RestrictedPython: bypass de `import`, escapes via `__class__`,
  consumo de CPU/memória descontrolado.
- Output: atualização do `docs/risk-register.md`.

### US-331 Testes E2E — AI generation e JS transform

**Agente:** QA Test Automation

1. E2E `ai-generation.spec.ts`:
   - Usuário abre AI Panel, digita prompt, clica Generate (mock da API), verifica
     que widgets aparecem no canvas.
   - Prompt vazio: botão Generate desabilitado.
2. E2E `js-transform.spec.ts`:
   - Usuário expande seção Transform, digita script `data.slice(0, 3)`, executa
     query (mock), verifica resultado limitado a 3 itens.
   - Script com erro: exibe mensagem de erro no painel.
3. E2E `invite-flow.spec.ts`:
   - Owner envia convite (mock email), copia link, aceita como outro usuário.

---

## Resumo de Escopo

| Item | US | Agente | Prioridade | Esforço |
|------|-----|--------|-----------|---------|
| AI App Generation backend | US-300 | Python Senior | P0 — diferencial | Alto |
| AI Query Suggestion | US-301 | Python Senior | P1 | Médio |
| AI Prompt Panel frontend | US-302 | Frontend React | P0 | Médio |
| JS Transform backend | US-310 | Python Senior | P1 | Alto |
| JS Transform frontend | US-311 | Frontend React | P1 | Médio |
| Email Invites backend | US-320 | Python Senior | P2 — deferred Sprint 4 | Alto |
| Invite Accept frontend | US-321 | Frontend React | P2 | Médio |
| Security Review AI+Sandbox | US-330 | Security | P0 | Médio |
| E2E testes novos fluxos | US-331 | QA | P1 | Médio |

**Fora do escopo Sprint 5:** Billing e planos, rate limiting por usuário/org, template
marketplace com aprovação e rating, page-level RBAC, GraphQL subscriptions WebSocket,
pgvector para busca semântica de templates, org/team model.
