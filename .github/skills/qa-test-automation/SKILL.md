---
name: qa-test-automation
description: 'Especialista em QA e automação de testes para SaaS com builder visual. Use para estratégia de testes, cobertura por risco, Playwright, pytest, testes de integração, smoke tests, critérios de release, regressão e classificação de bugs.'
argument-hint: 'Descreva a feature, fluxo crítico, bug ou nível de cobertura desejado.'
user-invocable: true
---

# QA / Test Automation

## Quando Usar

- Definir estratégia de testes por feature ou sprint
- Criar cenários E2E, integração e unitários
- Cobrir fluxos críticos do builder, query engine e preview
- Classificar bugs por severidade e risco de release
- Montar smoke tests e gate de qualidade para staging/produção

## Objetivo

Reduzir regressões e tornar o comportamento do produto verificável sem transformar o processo em burocracia pesada.

## Procedimento

1. Identifique o fluxo principal e o risco associado.
2. Decida o menor nível de teste que cobre o comportamento com confiança.
3. Defina cenários felizes, negativos e de borda.
4. Automatize o que protege melhor o fluxo crítico.
5. Classifique bugs por impacto real.
6. Estabeleça critérios de release claros e observáveis.

## Cobertura Prioritária

- criar app
- adicionar componente ao canvas
- executar query REST/SQL
- data binding em tabela
- preview com `run_on_load`
- bloqueios básicos de segurança funcional

## Regras

- E2E poucos e críticos
- Integração para maior parte do valor
- Unitários para lógica isolada e utilitários
- Flaky test deve ser tratado, não ignorado indefinidamente

## Guardrails

- Não perseguir 100% de cobertura sem critério
- Não automatizar tudo no primeiro momento
- Não usar E2E para provar casos que integração cobre melhor

## Saídas Típicas

- plano de testes
- matriz de casos críticos
- smoke tests
- classificação de bug
- recomendação de release/no-release