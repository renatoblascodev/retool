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

- ID: SEC-004
  Área: ai / prompt-injection
  Finding: Endpoints de IA (/api/ai/generate-app, /api/ai/suggest-query) aceitam `description` e `history` do usuário que são interpolados no prompt sem sanitização formal de injection de instrução.
  Severidade: major
  Exploitabilidade: média
  Status: mitigated
  Dono: Backend
  Mitigação imediata: o LLM é chamado com `role=system` fixo que define o comportamento; output é parseado como JSON estruturado — instrução injetada no conteúdo não pode alterar a função do endpoint.
  Risco residual: modelo pode vazar segredos do sistema prompt se atacado com jailbreak sofisticado.
  Remediação estrutural: (a) jamais inserir credenciais no system prompt; (b) adicionar camada de rate-limiting por user_id nos endpoints AI; (c) considerar output-filtering para detectar vazamento de prompt.

- ID: SEC-005
  Área: ai / privilege-escalation
  Finding: O endpoint POST /api/ai/generate-app cria componentes de UI a partir de descrição em linguagem natural — um atacante poderia tentar gerar componentes que exibam dados de outros usuários.
  Severidade: major
  Exploitabilidade: baixa
  Status: mitigated
  Dono: Backend
  Mitigação imediata: o app gerado é criado com `owner_id = current_user.id`; RBAC por app_member é aplicado em todos os recursos filhos. Nenhum dado cross-tenant é exposto no resultado gerado.
  Remediação estrutural: revisão manual de componentes gerados antes de torná-los públicos; adicionar content-security-policy no runtime.

- ID: SEC-006
  Área: sandbox / js-transform
  Finding: RestrictedPython pode ser bypassado via `__class__.__mro__` e acesso indireto ao `__builtins__` se o código de setup `safe_globals` não cobrir todos os vetores.
  Severidade: major
  Exploitabilidade: média
  Status: mitigated
  Dono: Backend
  Mitigação imediata: safe_globals baseado no padrão RestrictedPython com `__builtins__` restrito; `__import__` bloqueado; execução em thread separada com timeout de 3 s.
  Risco residual: ataques de timing (CPU starvation) ainda possíveis dentro do timeout.
  Remediação estrutural: (a) mover execução JS real para processo isolado (subprocess + seccomp) em vez de thread; (b) adicionar limite de memória via resource.setrlimit.

- ID: SEC-007
  Área: sandbox / resource-exhaustion
  Finding: O executor JS Transform não limita uso de memória — código malicioso pode alocar listas/strings enormes dentro do timeout de 3 s e esgotar RAM do processo.
  Severidade: major
  Exploitabilidade: média
  Status: open
  Dono: Backend
  Mitigação imediata: timeout de 3 s limita dano de CPU; falha de alocação grande faz o processo backend crashar e ser reiniciado pelo Docker.
  Remediação estrutural: aplicar `resource.setrlimit(resource.RLIMIT_AS, ...)` no subprocesso executor antes de release com usuários externos.

- ID: SEC-008
  Área: invite / token-exposure
  Finding: Token de convite é transmitido como query param na URL de aceite — pode ser registrado em logs de servidor, proxy e histórico de browser.
  Severidade: non-blocking
  Exploitabilidade: baixa
  Status: open
  Dono: Backend + Frontend
  Mitigação imediata: token é UUID v4 (128 bits de entropia); convite expira em 7 dias; após aceite o token é invalidado (accepted_at preenchido).
  Remediação estrutural: migrar para token no path ou hash de URL em vez de query param em ambiente de produção; adicionar header `Referrer-Policy: no-referrer` na página de aceite.

