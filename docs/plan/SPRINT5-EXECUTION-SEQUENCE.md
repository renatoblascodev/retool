# Sprint 5 — Sequência de Execução

> Este documento define a ordem, as dependências e os responsáveis por cada
> bloco de trabalho do Sprint 5.

---

## Visão geral do fluxo

```
Sprint 5A (AI App Generation) — PRIMEIRO (diferencial central)
  ├─► backend: módulo app/ai/ + LiteLLM + endpoints + testes
  └─► frontend: AI Prompt Panel (AIPromptPanel.tsx, useGenerateApp)

Sprint 5B (JS Transform Sandbox) — PARALELO com 5A backend
  ├─► backend: RestrictedPython sandbox + campo transform_js em queries
  └─► frontend: Monaco editor no query panel

Sprint 5C (Email Invites) — APÓS 5A (usa infra de auth já estável)
  ├─► backend: tabela app_invites + Migration 0005 + endpoints SMTP
  └─► frontend: InviteAcceptPage + hooks

Quality — APÓS code-complete de 5A/5B/5C
  ├─► Security Review: AI endpoints + JS sandbox (US-330)
  └─► QA: testes E2E novos fluxos (US-331)
```

**5A** é o item de maior risco técnico e maior impacto — executa primeiro.
**5B** pode rodar em paralelo no backend; frontend de 5B espera 5A estar estável.
**5C** não tem dependência técnica de 5A/5B; pode executar em paralelo.
**Quality** sempre fecha o sprint — roda após code-complete.

---

## Sprint 5A — AI App Generation

### Fase 1 — Backend AI (Python Senior)

**Agente:** `python-integrations-senior`

**Objetivo:** Criar o módulo `app/ai/` com integração LiteLLM e endpoints de
geração de app e sugestão de query.

**Variáveis de ambiente a adicionar ao `.env.example`:**
```
AI_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
LITELLM_LOG=WARNING
```

**Arquivos a criar:**

| Arquivo | Ação |
|---------|------|
| `backend/app/ai/__init__.py` | Criar (vazio) |
| `backend/app/ai/schemas.py` | Criar — `GenerateAppRequest`, `GenerateAppResponse`, `SuggestQueryRequest`, `SuggestQueryResponse` |
| `backend/app/ai/prompts/generate_app.txt` | Criar — prompt de sistema para geração de app |
| `backend/app/ai/prompts/suggest_query.txt` | Criar — prompt de sistema para sugestão de query |
| `backend/app/ai/service.py` | Criar — `generate_app(prompt, datasource_info)`, `suggest_query(datasource_type, goal)` |
| `backend/app/ai/router.py` | Criar — `POST /api/ai/generate-app`, `POST /api/ai/suggest-query` |
| `backend/tests/test_ai_router.py` | Criar — ≥ 10 testes |
| `backend/requirements.txt` | Atualizar — adicionar `litellm>=1.40` |
| `backend/app/main.py` | Atualizar — incluir `ai_router` |

**Arquivos a modificar:**

| Arquivo | Mudança |
|---------|---------|
| `backend/app/main.py` | `app.include_router(ai_router, prefix="/api/ai", tags=["ai"])` |

**Ordem de implementação:**
1. `schemas.py` — define contratos de request/response.
2. `prompts/generate_app.txt` — instrução de sistema que força output JSON.
3. `prompts/suggest_query.txt` — instrução para sugestão por tipo de datasource.
4. `service.py` — chama `litellm.acompletion` com `response_format={"type":"json_object"}`.
5. `router.py` — valida datasource (se fornecido), chama service, retorna response.
6. `main.py` — registra router.
7. `test_ai_router.py` — mock de `litellm.acompletion` via `pytest-mock`.
8. `requirements.txt` — pin de `litellm`.

**Detalhes do prompt de geração de app (`generate_app.txt`):**
```
You are an expert UI builder. Given a user description, generate a JSON layout
for a low-code app builder.

Return ONLY valid JSON matching this schema:
{
  "layout": [
    {
      "i": "<widget_id>",
      "type": "<Table|Chart|Form|Text|Button|Stat>",
      "x": 0, "y": 0, "w": 12, "h": 8,
      "props": { "title": "...", "queryName": "" }
    }
  ],
  "suggested_queries": [
    { "name": "<queryName>", "query": "<sql or rest path>" }
  ],
  "explanation": "One sentence explanation of what was generated."
}

Datasource info: {datasource_info}
User prompt: {user_prompt}
```

---

### Fase 2 — Frontend AI (Frontend React)

**Agente:** `frontend-react-mobile`

**Pré-requisito:** Fase 1 completa (endpoint disponível).

**Arquivos a criar:**

| Arquivo | Ação |
|---------|------|
| `frontend/src/features/ai/useGenerateApp.ts` | Criar — hook TanStack Query mutation |
| `frontend/src/features/ai/AIPromptPanel.tsx` | Criar — drawer lateral |

**Arquivos a modificar:**

| Arquivo | Mudança |
|---------|---------|
| `frontend/src/features/builder/BuilderHeader.tsx` | Adicionar botão "Generate with AI" (ícone Sparkles) |
| `frontend/src/features/builder/BuilderWorkspace.tsx` | Estado `showAIPanel`, renderizar `AIPromptPanel` |
| `frontend/src/app/router.tsx` ou equiv. | (nenhuma mudança de rota necessária) |

**Ordem de implementação:**
1. `useGenerateApp.ts` — mutation que chama `POST /api/ai/generate-app`.
2. `AIPromptPanel.tsx` — drawer com textarea, datasource select, botão Generate.
3. `BuilderHeader.tsx` — botão "Generate" abre panel.
4. `BuilderWorkspace.tsx` — integra panel + substitui layout.

---

## Sprint 5B — JS Transform Sandbox

### Fase 1 — Backend Sandbox (Python Senior)

**Agente:** `python-integrations-senior`

**Arquivos a modificar:**

| Arquivo | Mudança |
|---------|---------|
| `backend/app/queries/schemas.py` | Adicionar `transform_js: str \| None = None` em `QueryRequest` |
| `backend/app/queries/executor.py` | Após execução: se `transform_js` presente, chamar `_run_transform(data, script)` |
| `backend/app/queries/executor.py` | Criar `_run_transform(data, script)` com RestrictedPython + timeout |
| `backend/requirements.txt` | Adicionar `RestrictedPython>=7.0` |
| `backend/tests/test_js_transform.py` | Criar — ≥ 10 testes |

**Ordem de implementação:**
1. Adicionar `RestrictedPython` ao `requirements.txt`.
2. Implementar `_run_transform` no executor (sandbox + timeout 2s).
3. Integrar no fluxo de execução de query (REST, SQL, GraphQL).
4. Escrever testes cobrindo bypasses de segurança.

---

### Fase 2 — Frontend Monaco (Frontend React)

**Agente:** `frontend-react-mobile`

**Pré-requisito:** Fase 1 backend completa.

**Arquivos a modificar:**

| Arquivo | Mudança |
|---------|---------|
| `frontend/src/features/queries/QueryPanel.tsx` | Adicionar seção colapsável "Transform (JS)" |
| `frontend/src/features/queries/QueryPanel.tsx` | Importar Monaco Editor, renderizar quando expandido |
| `frontend/src/features/queries/useQueries.ts` | Incluir `transform_js` no payload de execução e salvamento |

**Nota:** O Monaco Editor já está listado nas dependências da spec (`Monaco Editor`).
Verificar se já instalado (`@monaco-editor/react`); instalar se necessário.

---

## Sprint 5C — Email Invites

### Fase 1 — Backend SMTP (Python Senior)

**Agente:** `python-integrations-senior`

**Arquivos a criar/modificar:**

| Arquivo | Ação |
|---------|------|
| `backend/migrations/versions/0005_app_invites.py` | Criar — tabela `app_invites` |
| `backend/app/models.py` | Adicionar model `AppInvite` |
| `backend/app/invites/__init__.py` | Criar (vazio) |
| `backend/app/invites/schemas.py` | Criar — `InviteRequest`, `InviteInfoResponse`, `AcceptInviteRequest` |
| `backend/app/invites/email.py` | Criar — `send_invite_email(to, app_name, role, link)` |
| `backend/app/invites/router.py` | Criar — 3 endpoints (POST invite, GET token info, POST accept) |
| `backend/app/main.py` | Registrar `invites_router` em `/api` |
| `backend/tests/test_invites_router.py` | Criar — ≥ 10 testes |

---

### Fase 2 — Frontend Invite Accept (Frontend React)

**Agente:** `frontend-react-mobile`

**Arquivos a criar/modificar:**

| Arquivo | Ação |
|---------|------|
| `frontend/src/features/invites/useInvites.ts` | Criar — `useInviteToken(token)` + `useAcceptInvite()` |
| `frontend/src/features/invites/InviteAcceptPage.tsx` | Criar — página `/invites/accept` |
| `frontend/src/app/router.tsx` (ou equiv.) | Adicionar rota `/invites/accept` |

---

## Quality — Sprint 5

### US-330 Security Review (Security Reviewer)

**Agente:** `security-reviewer`

Após code-complete de 5A e 5B:
- SSRF via `datasource_id` no endpoint AI.
- Prompt injection no campo `prompt` da geração de app.
- Bypass do sandbox RestrictedPython (`__class__`, `__mro__`, `__subclasses__`).
- Output: `docs/risk-register.md` atualizado.

### US-331 Testes E2E (QA Test Automation)

**Agente:** `QA Test Automation`

Após aprovação do Security Reviewer:
- `frontend/tests/e2e/ai-generation.spec.ts` — 3 testes.
- `frontend/tests/e2e/js-transform.spec.ts` — 2 testes.
- `frontend/tests/e2e/invite-flow.spec.ts` — 2 testes.

---

## Checklist de Done para Sprint 5

- [ ] `POST /api/ai/generate-app` retorna layout JSON válido (mock LiteLLM em testes).
- [ ] `POST /api/ai/suggest-query` retorna sugestão por tipo de datasource.
- [ ] AI Prompt Panel abre no builder, envia prompt, substitui layout.
- [ ] `transform_js` executado via RestrictedPython com timeout.
- [ ] Monaco editor presente no query panel (colapsável).
- [ ] `POST /api/apps/{id}/invites` cria convite e loga link no console em dev mode.
- [ ] `POST /api/invites/accept` cria membro no app.
- [ ] `InviteAcceptPage` redireciona para builder após aceite.
- [ ] ≥ 100 backend tests passando.
- [ ] TypeScript sem erros.
- [ ] Security review concluído, risk-register atualizado.
- [ ] ≥ 38 E2E specs criados.
- [ ] `docs/status/current.md` atualizado com Sprint 5.
