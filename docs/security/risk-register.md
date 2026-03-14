# Security Risk Register

- ID: SEC-001
  Área: network
  Finding: Endpoint de query REST permitia alvo externo sem validação SSRF.
  Severidade: major
  Exploitabilidade: média
  Status: mitigated
  Dono: Backend
  Mitigação imediata: validação de URL/scheme e bloqueio de host local/privado fora de development.
  Remediação estrutural: allowlist explícita por datasource em ambiente de produção.

- ID: SEC-002
  Área: secrets
  Finding: `auth_config` de datasource é persistido em JSON sem criptografia em repouso.
  Severidade: major
  Exploitabilidade: média
  Status: mitigated
  Dono: Backend
  Mitigação imediata: `auth_config` criptografado em repouso e mascarado nas respostas da API.
  Remediação estrutural: implementar rotação de chave de ambiente sem downtime.

- ID: SEC-003
  Área: auth
  Finding: Ausência de RBAC/escopos finos para colaboração entre usuários.
  Severidade: non-blocking
  Exploitabilidade: baixa
  Status: open
  Dono: Product + Backend
  Mitigação imediata: isolamento estrito por owner_id em todos os recursos.
  Remediação estrutural: introduzir papéis por app (owner/editor/viewer).

