# Sprint 6 Backlog — ToolStack AI (Templates, Runtime Engine e Publish)

> **Objetivo:** Fechar as três lacunas críticas que separam o MVP do produto publicável:
> (1) runtime client-side com data binding real, (2) templates para acelerar time-to-value
> de novos usuários, e (3) publicação de apps com URL pública.
>
> **Pré-requisito:** Sprint 5 completa ✅ (125 backend / 12 unit invites / E2E specs).
>
> **Data de início:** 2026-03-17
> **Data-alvo:** 2026-03-31 (2 semanas)
>
> **KPIs de sucesso:**
> - Usuário abre um template, personaliza e publica em < 5 minutos.
> - Data binding `{{query.data}}` funciona no runtime para os 5 tipos de widget (Table,
>   Text, Button, TextInput, Stat).
> - App publicado abre em URL pública `/r/{app_slug}` sem necessidade de login.
> - `POST /api/apps/{id}/publish` retorna `public_url` em < 2s.
> - Cobertura: ≥ 145 backend / ≥ 42 E2E.

---

## Sprint 6A — Runtime Engine (Data Binding Real)

**Objetivo:** Substituir o binding estático do runtime atual por um engine que avalia
expressões `{{query.data}}` em tempo real, sincronizado com o estado das queries.

**Responsáveis:** Frontend React.

---

### US-400 Runtime engine com data binding reativo

> Como usuário final, quero que os widgets exibam os dados das queries automaticamente,
> para que a tabela se atualize quando a query retornar novos resultados.

**Critérios de aceitação:**

1. `frontend/src/runtime/` contém o engine de avaliação de expressões:
   - `engine.ts` — função `evaluate(expr: string, context: RuntimeContext): unknown`
     avalia expressões `{{...}}` usando `new Function()` em sandbox (sem acesso a `window`,
     `document`, `fetch`).
   - `context.ts` — `RuntimeContext` agrega o estado de todas as queries da página:
     `{ [queryName]: { data, loading, error } }`.
   - `useRuntimeContext.ts` — hook que executa todas as queries `run_on_load=true` ao
     montar a página e mantém o contexto atualizado.

2. `WidgetRenderer` usa `evaluate()` para resolver props dinâmicas:
   - `TableWidget`: `columns` e `data` resolvidos via expression.
   - `TextWidget`: `content` resolvido.
   - `StatWidget`: `value` e `label` resolvidos.
   - `ButtonWidget`: `label` e `disabled` resolvidos.
   - `TextInputWidget`: `defaultValue` resolvido.

3. Se a expressão lança erro (sintaxe inválida, propriedade undefined): widget renderiza
   em estado de erro com bordas vermelhas e tooltip com a mensagem — **não quebra o app**.

4. `run_on_load=true` em queries: executadas automaticamente ao abrir o runtime.

5. Testes unitários (Vitest):
   - `engine.test.ts`: ≥ 8 casos (literal, objeto, array, nested, undefined, syntax error,
     injection attempt com `window.fetch`, circular reference).

6. Testes E2E (Playwright) — arquivo `tests/e2e/runtime-binding.spec.ts`:
   - Abre runtime de app, mock de query retorna dados, tabela exibe dados.
   - Widget de texto exibe `{{query.data[0].name}}` resolvido corretamente.
   - Erro de expressão não quebra a página.

**Fora de escopo:** Eventos de widget (onClick), edição de binding no builder visual,
streaming de dados, WebSocket.

---

### US-401 Execução de queries no runtime

> Como usuário final, quero que as queries sejam executadas automaticamente ao abrir
> o app, para que os dados apareçam sem precisar clicar em nada.

**Critérios de aceitação:**

1. Hook `useRuntimeQueries(appId, pageId)`:
   - Busca as queries da página via `GET /api/apps/{appId}/queries`.
   - Executa em paralelo as queries com `run_on_load=true` via `POST /api/queries/execute`.
   - Armazena estado de cada query: `{ data, loading, error, lastRunAt }`.
   - Re-executa manualmente quando `refetch()` é chamado.

2. Backend: `GET /api/apps/{appId}/queries` — novo endpoint que lista todas as queries
   salvas de um app. Retorna lista com `{ id, name, datasource_id, type, config, transform_js, run_on_load }`.

3. Queries com erro não bloqueiam outras queries — falhas são isoladas.

4. Testes backend: ≥ 6 pytest para o novo endpoint de listagem.

5. Testes E2E: ≥ 4 cenários no `runtime-binding.spec.ts`.

**Fora de escopo:** Refresh automático por intervalo, dependência entre queries,
parâmetros dinâmicos de query passados pelo usuário.

---

## Sprint 6B — Templates de App

**Objetivo:** Permitir que usuários criem apps a partir de templates pré-definidos,
acelerando o time-to-value para novos usuários.

**Responsáveis:** Python Senior (backend) + Frontend React (UI de templates).

---

### US-410 Backend de templates

> Como desenvolvedor, quero escolher um template ao criar um app, para começar com
> um layout funcional em vez de uma página em branco.

**Critérios de aceitação:**

1. Nova tabela `app_templates`:
   ```sql
   CREATE TABLE app_templates (
     id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     name        VARCHAR(255) NOT NULL,
     description TEXT,
     category    VARCHAR(100) NOT NULL,  -- 'crud' | 'dashboard' | 'form' | 'report'
     thumbnail   TEXT,                   -- URL de imagem de preview
     layout_json JSONB NOT NULL,         -- snapshot do layout a ser clonado
     is_active   BOOLEAN DEFAULT TRUE,
     created_at  TIMESTAMPTZ DEFAULT NOW()
   );
   ```

2. Migration `0006_app_templates.py` cria a tabela e insere **3 templates seed**:
   - `"User Management"` (categoria: crud) — tabela de usuários + form de criação.
   - `"KPI Dashboard"` (categoria: dashboard) — 3 StatWidgets + 1 tabela.
   - `"Feedback Form"` (categoria: form) — 2 TextInputWidgets + Button submit.

3. Endpoints:
   - `GET /api/templates` — lista templates ativos. Público (sem auth).
   - `POST /api/apps` — aceita campo opcional `template_id: str | None`. Se fornecido,
     cria a página Home do app com o `layout_json` do template clonado (deep copy).

4. Testes: ≥ 8 pytest (listar templates, criar app sem template, criar app com template,
   template inexistente retorna 400, template inativo não aparece na listagem,
   layout clonado não referencia o original, listagem paginada, sem auth em GET /templates).

**Fora de escopo:** Templates criados por usuários, marketplace pago, edição de templates
pela interface, versionamento de templates.

---

### US-411 Template picker no frontend

> Como novo usuário, quero ver os templates disponíveis ao criar um app, para escolher
> o ponto de partida mais adequado ao meu caso de uso.

**Critérios de aceitação:**

1. Ao clicar em "New App" (ou no CTA do empty state), abre modal/drawer `TemplatePickerModal`:
   - Exibe os templates retornados por `GET /api/templates`.
   - Cards com thumbnail, nome e descrição.
   - Filtro por categoria (All / CRUD / Dashboard / Form / Report).
   - Opção "Blank App" (sem template).

2. Ao selecionar e confirmar: `POST /api/apps` com `{ name, template_id }`.

3. Após criação: navega para o builder do novo app.

4. Estado de loading e erro tratados com skeleton e mensagem.

5. Testes E2E — arquivo `tests/e2e/template-picker.spec.ts` (arquivo existente a ser
   expandido ou substituído):
   - Abre modal ao clicar em "New App".
   - Filtra templates por categoria.
   - Seleciona template e verifica criação do app.
   - Cria app em branco (sem template).

**Fora de escopo:** Preview ao vivo do template, favoritar templates, busca por texto.

---

## Sprint 6C — Publish de Apps

**Objetivo:** Permitir que o dono de um app o publique com uma URL pública, tornando-o
acessível a usuários finais sem login.

**Responsáveis:** Python Senior (backend) + Frontend React (botão de publish).

---

### US-420 Backend de publish

> Como dono de um app, quero publicar meu app para que usuários finais possam acessá-lo
> via URL pública, sem precisar de conta na plataforma.

**Critérios de aceitação:**

1. Novo campo na tabela `apps`:
   ```sql
   ALTER TABLE apps ADD COLUMN IF NOT EXISTS is_published BOOLEAN DEFAULT FALSE;
   ALTER TABLE apps ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ;
   ALTER TABLE apps ADD COLUMN IF NOT EXISTS slug VARCHAR(100);
   ```
   Migration `0007_app_publish.py`.

2. `POST /api/apps/{app_id}/publish` — owner only.
   - Marca `is_published=true`, `published_at=now()`.
   - Gera `slug` único se ainda não existir (baseado no nome do app, slugified).
   - Response: `{ public_url: "https://toolstack.dev/r/{slug}" }`.

3. `DELETE /api/apps/{app_id}/publish` — owner only.
   - Marca `is_published=false`.

4. `GET /api/r/{slug}` — **público** (sem auth). Retorna o snapshot completo do app:
   pages + queries + layout_json. Usado pelo runtime público.

5. Testes: ≥ 10 pytest (publish, unpublish, slug único, slug colisão gera sufixo,
   app não publicado retorna 404 em /r/{slug}, não-owner não pode publicar,
   publicar app já publicado é idempotente, resposta inclui public_url, não autenticado retorna 401).

**Fora de escopo:** Custom domains, CDN, versionamento de publicação, analytics de acesso.

---

### US-421 Botão de publish no builder

> Como dono de um app, quero um botão "Publish" no builder para tornar o app público
> com um clique.

**Critérios de aceitação:**

1. Botão "Publish" no `BuilderHeader` — visível apenas para owners.
   - Estado: "Publish" (não publicado) / "Published ✓" (já publicado, com badge verde).

2. Ao clicar "Publish":
   - Chama `POST /api/apps/{id}/publish`.
   - Toast de sucesso com a `public_url` e botão "Copy link".
   - Header muda para estado "Published ✓".

3. Ao clicar "Published ✓":
   - Opções: "Copy link" e "Unpublish".
   - "Unpublish" chama `DELETE /api/apps/{id}/publish` e reverte o estado.

4. Permissão: viewers e editors não veem o botão Publish.

5. Testes E2E — `tests/e2e/publish-flow.spec.ts`:
   - Owner publica app, vê toast com URL.
   - Owner despublica.
   - Editor não vê botão.
   - App publicado abre em `/r/{slug}` sem auth.

**Fora de escopo:** Preview de publicação, agendamento de publish.

---

## Sprint 6D — Qualidade e Segurança

**Objetivo:** Fechar os riscos abertos SEC-007 e SEC-008, ampliar cobertura de testes
e garantir que o CI/CD está verde.

**Responsáveis:** Security Reviewer + QA Test Automation.

---

### US-430 Rate limiting nos endpoints AI (SEC-004 remediação estrutural)

> Como operador da plataforma, quero limitar chamadas ao LLM por usuário, para evitar
> abuso e custos não controlados.

**Critérios de aceitação:**

1. Middleware de rate limiting usando `slowapi` (wrapper de `limits` para FastAPI):
   - `POST /api/ai/generate-app`: limite de **10 req/min por user_id**.
   - `POST /api/ai/suggest-query`: limite de **20 req/min por user_id**.
   - Retorna `429 Too Many Requests` com header `Retry-After`.

2. Configurável por variável de ambiente:
   - `AI_RATE_LIMIT_GENERATE=10/minute`
   - `AI_RATE_LIMIT_SUGGEST=20/minute`

3. Testes: ≥ 4 pytest (dentro do limite, excede limite, reset após janela, header Retry-After presente).

4. Atualizar `docs/security/risk-register.md`: SEC-004 status → `remediated`.

**Fora de escopo:** Rate limiting global por IP, billing por token.

---

### US-431 Remediação SEC-007 (resource exhaustion no sandbox)

> Como operador, quero que o sandbox de transform não possa esgotar a memória do servidor.

**Critérios de aceitação:**

1. O executor de transform (`app/queries/transform.py`) passa a executar o script em
   **subprocesso isolado** com `resource.setrlimit(RLIMIT_AS, 256MB)`.
2. Timeout de 3s mantido via `subprocess.run(..., timeout=3)`.
3. Fallback gracioso: se subprocesso falha por OOM ou timeout, retorna `{"error": "Transform limit exceeded"}`.
4. Testes: ≥ 3 pytest (execução normal, timeout, OOM simulado via `bytearray(300_000_000)`).
5. Atualizar `docs/security/risk-register.md`: SEC-007 status → `remediated`.

**Fora de escopo:** cgroups, namespaces Linux, container por execução.

---

### US-432 Cobertura de testes e CI verde

> Como time, queremos garantir que toda PR passa na suite completa sem falhas.

**Critérios de aceitação:**

1. `backend/tests/` atinge ≥ 145 testes passando.
2. `frontend/tests/e2e/` atinge ≥ 42 specs E2E.
3. `frontend/tests/unit/` mantém ≥ 30 testes unitários Vitest.
4. GitHub Actions (`.github/workflows/ci.yml`) roda `pytest` + `tsc --noEmit` + `playwright` em toda PR.
5. Badge de CI no README.

**Fora de escopo:** Testes de carga, testes de mutação, relatório de cobertura detalhado.

---

## Resumo de User Stories

| ID     | Descrição                              | Agente Principal          | Complexidade |
|--------|----------------------------------------|---------------------------|-------------|
| US-400 | Runtime engine com data binding        | frontend-react-mobile     | Alta        |
| US-401 | Execução de queries no runtime         | frontend-react-mobile + python | Média  |
| US-410 | Backend de templates                   | python-integrations-senior | Média      |
| US-411 | Template picker no frontend            | frontend-react-mobile     | Média       |
| US-420 | Backend de publish                     | python-integrations-senior | Média      |
| US-421 | Botão de publish no builder            | frontend-react-mobile     | Baixa       |
| US-430 | Rate limiting endpoints AI             | python-integrations-senior | Baixa      |
| US-431 | Remediação SEC-007 sandbox             | python-integrations-senior | Média      |
| US-432 | Cobertura de testes e CI verde        | qa-test-automation        | Média       |

---

## Critérios de Saída do Sprint 6

- [ ] `GET /api/templates` retorna 3 templates seed
- [ ] Criar app com template copia layout corretamente
- [ ] Template picker abre ao clicar em "New App"
- [ ] `POST /api/apps/{id}/publish` gera slug e retorna `public_url`
- [ ] `GET /api/r/{slug}` serve app sem auth
- [ ] Botão Publish visível apenas para owners
- [ ] Runtime avalia `{{query.data}}` e popula tabela
- [ ] Rate limiting 429 em AI endpoints
- [ ] SEC-007 marcado como remediated
- [ ] ≥ 145 testes backend passando
- [ ] ≥ 42 testes E2E passando
- [ ] CI GitHub Actions verde em toda PR
