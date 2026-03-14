# MVP Backlog

## Objetivo do MVP

Permitir que um usuário autenticado crie um app simples, adicione uma página com um componente de tabela, conecte uma REST API, execute uma query e visualize os dados no preview.

## Fora de Escopo do MVP

- Billing
- SSO
- Mobile app nativo
- Marketplace de templates
- SQL datasource
- GraphQL datasource
- Plugin SDK aberto para terceiros
- Audit logs completos

## Épico 1: Auth e Onboarding

### US-001 Registro e login

- Como desenvolvedor, quero entrar na plataforma para começar a criar ferramentas.

Critérios de aceitação:

1. Usuário consegue fazer login com email e senha.
2. Sessão autenticada permite acessar o dashboard.
3. Usuário não autenticado é redirecionado para login.

### US-002 Empty state inicial

- Como novo usuário, quero ver uma tela clara para começar meu primeiro app.

Critérios de aceitação:

1. Dashboard vazio mostra CTA para criar app.
2. Empty state não depende de dados prévios.

## Épico 2: Gestão de Apps e Pages

### US-010 Criar app

- Como desenvolvedor, quero criar um app com nome e slug.

Critérios de aceitação:

1. App pode ser criado com nome válido.
2. Slug é gerado ou validado.
3. App criado aparece na listagem.

### US-011 Criar página

- Como desenvolvedor, quero criar uma página dentro do app.

Critérios de aceitação:

1. Página é criada e associada ao app.
2. Página abre no builder após criação.

## Épico 3: Builder Visual Base

### US-020 Adicionar componente Table

- Como desenvolvedor, quero adicionar uma tabela ao canvas.

Critérios de aceitação:

1. Widget Table pode ser inserido no canvas.
2. Tabela aparece selecionada após inserção.
3. Layout mínimo do componente é persistido.

### US-021 Editar propriedades básicas

- Como desenvolvedor, quero editar propriedades básicas do componente Table.

Critérios de aceitação:

1. Painel lateral permite editar nome e binding de dados.
2. Mudanças refletem no preview local.

## Épico 4: Datasource REST e Query Builder

### US-030 Criar datasource REST

- Como desenvolvedor, quero cadastrar uma REST API para consumir dados.

Critérios de aceitação:

1. Datasource aceita nome, base URL e autenticação básica do MVP.
2. Credenciais não são expostas ao frontend.

### US-031 Criar e executar query REST

- Como desenvolvedor, quero executar uma query REST e ver o resultado.

Critérios de aceitação:

1. Query aceita método, endpoint e headers básicos.
2. Botão Run executa a chamada com resposta visível.
3. Erro de API aparece de forma legível.

## Épico 5: Data Binding e Preview

### US-040 Bindar query na tabela

- Como desenvolvedor, quero conectar o resultado da query à tabela.

Critérios de aceitação:

1. Campo de binding aceita `{{query_name.data}}`.
2. Tabela renderiza as linhas retornadas.

### US-041 Abrir preview

- Como desenvolvedor, quero visualizar meu app sem as ferramentas de edição.

Critérios de aceitação:

1. Preview oculta controles do builder.
2. Query marcada como `run_on_load` executa ao abrir preview.

## Épico 6: Qualidade e Operação Mínima

### US-050 Ambiente local completo

- Como time de engenharia, queremos subir frontend, backend, postgres e redis localmente.

Critérios de aceitação:

1. Ambiente local sobe com um comando principal.
2. Backend expõe healthcheck.
3. Frontend consegue chamar backend local.

### US-051 Smoke test do fluxo MVP

- Como time, queremos validar o fluxo principal sem regressão óbvia.

Critérios de aceitação:

1. Existe ao menos um smoke test do fluxo principal.
2. Existe ao menos um teste backend do executor de query.
