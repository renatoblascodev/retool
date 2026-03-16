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

- ID: OPS-001
  Área: secrets
  Finding: Rotação da DATASOURCE_ENCRYPTION_KEY não automatizada.
  Severidade: non-blocking
  Exploitabilidade: baixa
  Status: mitigated
  Dono: DevOps + Backend
  Mitigação imediata: variável de ambiente nunca hardcoded; gerada fora do código.
  Remediação estrutural: script CLI `python -m app.tools.rotate_key --old-key=X --new-key=Y` re-encripta todos os registros sem downtime. Suporta --dry-run e --batch. 6 testes em test_datasource_secrets.py::RotateAuthConfigTests.

- ID: OPS-002
  Área: network
  Finding: Sem DNS rebinding protection nem allowlist de hosts no executor REST.
  Severidade: major
  Exploitabilidade: média
  Status: mitigated
  Dono: Backend
  Mitigação imediata: resolução de hostname via socket.getaddrinfo + bloqueio de IPs privados/loopback/link-local em environment != development.
  Configuração: variável SSRF_ALLOW_HOSTS permite lista explícita de hosts autorizados.
  Cobertura: 11 testes em test_query_service.py::ValidateUrlTests.
  Remediação estrutural: configurar allowlist por datasource antes de release externo.

