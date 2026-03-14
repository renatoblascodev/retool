# ADR-0001: Modular Monolith First

## Status

Accepted

## Contexto

- O projeto precisa sair rapidamente do estado de planejamento para um MVP funcional.
- O time ainda está pequeno e o acoplamento entre builder, query engine, auth, preview e gestão de apps é alto.
- Uma arquitetura distribuída cedo demais aumentaria custo operacional, dificuldade de debugging e latência de entrega.
- Ainda precisamos validar produto, fluxo principal e limites reais de escala.

## Decisão

- Adotar **monólito modular** no backend com FastAPI.
- Adotar estrutura de repositório com `frontend/`, `backend/`, `packages/` e `infra/`.
- Separar responsabilidades por domínio no backend (`auth`, `apps`, `pages`, `components`, `datasources`, `queries`, `ai`, `permissions`, `workers`).
- Manter integração entre módulos por contratos explícitos e boundaries simples.
- Postergar microserviços reais até existir necessidade comprovada de isolamento de deploy, escala ou segurança.

## Consequências

### Ganhos

- Menor complexidade operacional no início.
- Maior velocidade para entregar o fluxo principal do MVP.
- Debugging, testes e refactors mais simples.
- Menor custo de infraestrutura local e de staging.

### Custos

- Menor isolamento de falhas no backend.
- Escala horizontal menos granular no começo.
- Risco de acoplamento excessivo se boundaries não forem respeitados.

### Riscos

- Módulos podem virar acoplamento implícito se não houver disciplina de arquitetura.
- Crescimento rápido do query engine pode exigir extração futura.

## Plano de Ação

1. Bootstrap do backend FastAPI como monólito modular.
2. Criar fronteiras de diretórios e contratos mínimos entre frontend e backend.
3. Validar o MVP completo antes de discutir extração de serviços.
4. Reavaliar esta decisão após o primeiro ciclo funcional do MVP.

## Métrica de Sucesso

- O time consegue entregar o fluxo principal do MVP com backend e frontend executando localmente.
- O backend mantém módulos separados por domínio sem imports cruzados arbitrários.

## Responsáveis

- Owner: Tech Lead Architect
- Revisores: Product Owner, Python Integrations Senior, DevOps

## Data

- 2026-03-13
