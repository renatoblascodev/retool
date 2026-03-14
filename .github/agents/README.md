# Agents da Equipe

Este diretório contém agentes nativos do GitHub Copilot para o projeto.

Eles foram alinhados aos skills em `.github/skills` e servem como perfis especializados para trabalho recorrente.

## Agentes Disponíveis

- `Team Orchestrator` -> coordena Product, UX, Tech Lead, Frontend, Backend, DevOps e QA
- `Implementation` -> executa tarefas full-stack pequenas entre frontend e backend
- `Release Manager` -> decide go/no-go, rollout, smoke validation e rollback
- `Security Reviewer` -> revisa auth, secrets, SSRF, SQL injection, sandbox e hardening
- `UX Specialist` -> usa o skill `ux-specialist`
- `Frontend React Mobile Specialist` -> usa o skill `frontend-react-mobile`
- `Python Integrations Senior` -> usa o skill `python-integrations-senior`
- `Product Owner` -> usa o skill `product-owner`
- `DevOps` -> usa o skill `devops`
- `Tech Lead Architect` -> usa o skill `tech-lead-architect`
- `QA Test Automation` -> usa o skill `qa-test-automation`

## Uso

- Seleção manual no agent picker
- Invocação por descrições compatíveis no fluxo do Copilot
- Handoffs guiados entre agentes após respostas compatíveis

## Fluxo Guiado Recomendado

- `Team Orchestrator` para tarefas cross-team ou mal definidas
- `Team Orchestrator` -> `Implementation` para tarefas full-stack pequenas e bem delimitadas
- `Team Orchestrator` -> `Release Manager` para revisão de release e rollout
- `Team Orchestrator` -> `Security Reviewer` para revisão de segurança e hardening
- `Product Owner` -> `Tech Lead Architect` ou `UX Specialist`
- `UX Specialist` -> `Frontend React Mobile Specialist`
- `Implementation` -> `Product Owner`, `QA Test Automation` ou `DevOps`
- `Tech Lead Architect` -> `Frontend React Mobile Specialist`, `Python Integrations Senior` ou `DevOps`
- `Frontend React Mobile Specialist` -> `Python Integrations Senior` ou `QA Test Automation`
- `Python Integrations Senior` -> `Frontend React Mobile Specialist`, `QA Test Automation` ou `DevOps`
- `DevOps` -> `QA Test Automation`
- `QA Test Automation` -> `Product Owner` ou `DevOps`
- `Release Manager` -> `QA Test Automation`, `Security Reviewer`, `DevOps`, `Product Owner` ou `Tech Lead Architect`
- `Security Reviewer` -> `Python Integrations Senior`, `DevOps` ou `Tech Lead Architect`

## Convenção

- Um agente por especialidade
- Ferramentas mínimas por papel
- Instruções curtas e objetivas
- Skill correspondente como referência principal