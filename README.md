# ToolStack AI

[![CI](https://github.com/codigovalor/retool/actions/workflows/ci.yml/badge.svg)](https://github.com/codigovalor/retool/actions/workflows/ci.yml)

ToolStack AI e um builder de ferramentas internas com foco em apps administrativos, queries e automacoes assistidas por IA.

## Get started

O caminho mais rapido para ter o ambiente pronto e pelo Dev Container (requer VS Code + Docker):

1. Instale [VS Code](https://code.visualstudio.com) e a extensao **Dev Containers**.
2. Clone o repositorio: `git clone https://github.com/codigovalor/retool && cd retool`
3. Abra no VS Code e aceite **"Reopen in Container"** — o ambiente sera configurado automaticamente.
4. Dentro do container, inicie os servicos: `docker compose -f infra/docker-compose.yml up -d`
5. Acesse o builder em `http://localhost:5173` e a API em `http://localhost:8000/docs`.


## Estrutura

- `frontend/`: app React + Vite do builder
- `backend/`: API FastAPI do produto
- `packages/`: pacotes compartilhados
- `infra/`: ambiente local e infraestrutura
- `docs/`: contexto vivo do projeto
- `.github/skills` e `.github/agents`: automacao operacional do time

## Bootstrap Atual

- backend com `GET /health`
- backend com CRUD de datasources REST em `GET/POST/PATCH/DELETE /api/datasources`
- backend com `POST /api/queries/execute` com execucao REST real
- frontend React consumindo o endpoint mock
- docs de contexto e backlog do MVP preparados

## Como rodar localmente

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker Compose

```bash
docker compose -f infra/docker-compose.yml up --build
```

## Smoke test da API

Com o backend em execucao, rode:

```bash
cd backend
python tests/smoke_api.py
```

Saida esperada: `SMOKE_TEST_OK`.
