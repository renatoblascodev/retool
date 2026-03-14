# Skills da Equipe

Este diretório contém os skills nativos do GitHub Copilot para o projeto.

Cada skill fica em uma pasta própria com `SKILL.md`, seguindo o formato suportado pelo VS Code/Copilot.

## Skills Disponíveis

### UX

- Pasta: `ux-specialist`
- Uso: fluxos, design system, acessibilidade, estados de UI, experiência do builder
- Comando: `/ux-specialist`

### Frontend React + Mobile

- Pasta: `frontend-react-mobile`
- Uso: React 19, TypeScript, React Native, builder visual, runtime client-side, performance
- Comando: `/frontend-react-mobile`

### Python Integrações Sênior

- Pasta: `python-integrations-senior`
- Uso: FastAPI, integrações REST/SQL/GraphQL, segurança, query engine, workers
- Comando: `/python-integrations-senior`

### Product Owner

- Pasta: `product-owner`
- Uso: backlog, user stories, critérios de aceitação, roadmap, priorização
- Comando: `/product-owner`

### DevOps

- Pasta: `devops`
- Uso: Docker, CI/CD, Kubernetes, observabilidade, deploy, rollback
- Comando: `/devops`

### Security Reviewer

- Pasta: `security-reviewer`
- Uso: autenticação, autorização, secrets, SSRF, SQL injection, sandbox, hardening e risco de release
- Comando: `/security-reviewer`

### Tech Lead / Arquitetura

- Pasta: `tech-lead-architect`
- Uso: ADRs, boundaries, revisão arquitetural, ownership, decisões técnicas transversais
- Comando: `/tech-lead-architect`

### QA / Test Automation

- Pasta: `qa-test-automation`
- Uso: estratégia de testes, automação E2E, integração, critérios de release, severidade de bugs
- Comando: `/qa-test-automation`

## Regras de Uso

- Use o skill mais específico para a tarefa, não o mais genérico.
- O Product Owner define escopo e prioridade, não implementação.
- O Tech Lead decide padrões e boundaries, não microdetalhes locais.
- QA cobre risco e regressão, não burocratiza entrega sem ganho real.
- DevOps automatiza ambiente e operação, não redesenha produto.

## Origem

Os arquivos em `.ai/skills/*.md` permanecem como material-base mais extenso.
Os arquivos em `.github/skills/**/SKILL.md` são a versão convertida para o formato nativo do Copilot.
