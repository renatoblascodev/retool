# Context Management

Este diretório é a fonte oficial de contexto vivo do projeto.

## Estrutura

- `docs/adr/`: decisões arquiteturais (ADRs)
- `docs/plan/`: planejamento de feature e execução
- `docs/status/`: status atual, bloqueios e próximos passos
- `docs/release/`: decisões de release, rollout e rollback
- `docs/security/`: riscos, findings e mitigação

## Regras

1. Um contexto por assunto. Evitar duplicidade entre pastas.
2. Atualizar contexto no mesmo PR da mudança quando houver decisão relevante.
3. Escrever curto e operacional: objetivo, decisão, impacto, próximos passos.
4. Evitar texto longo de histórico em chat; registrar nos templates.

## Cadência Recomendada

- Diário: atualizar `docs/status/current.md`
- Por decisão técnica: criar/atualizar ADR
- Por release: criar nota de release em `docs/release/`
- Por risco de segurança: registrar em `docs/security/risk-register.md`

## Donos

- Product Owner: escopo e prioridade
- Tech Lead: arquitetura e boundaries
- Implementation/Frontend/Python: execução
- QA e Release Manager: qualidade e go/no-go
- Security Reviewer e DevOps: risco e hardening operacional
