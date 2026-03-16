# ADR-0002 — RBAC por App com tabela `app_members`

**Status:** Accepted  
**Data:** 2026-03-16  
**Autores:** Tech Lead Architect  

---

## Contexto

Na Sprint 3 todos os apps eram acessíveis apenas pelo `owner_id`. Não havia conceito de
compartilhamento ou papéis. O risco SEC-003 (ausência de RBAC) estava aberto. A Sprint 4A
introduz papéis por app para habilitar colaboração e controle de acesso.

---

## Decisão

### 1. Tabela de membros

```sql
CREATE TABLE app_members (
    app_id      VARCHAR(36) NOT NULL REFERENCES apps(id)  ON DELETE CASCADE,
    user_id     VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role        VARCHAR(20) NOT NULL,
    joined_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (app_id, user_id),
    CHECK (role IN ('owner', 'editor', 'viewer'))
);
```

- **PK composta** (`app_id`, `user_id`): garante unicidade e evita duplicação.  
- **Check constraint** no lugar de enum Postgres: mais portável entre ambientes e mais fácil de
  migrar no futuro sem `ALTER TYPE`.  
- `ON DELETE CASCADE`: quando um app ou usuário é removido, os membros são removidos
  automaticamente.

### 2. Roles

| Role | Pode ler | Pode editar | Pode convidar | Pode excluir o app |
|------|----------|------------|--------------|-------------------|
| `owner` | ✅ | ✅ | ✅ | ✅ |
| `editor` | ✅ | ✅ | ❌ | ❌ |
| `viewer` | ✅ | ❌ | ❌ | ❌ |

### 3. Dependency FastAPI `require_role(min_role)`

```python
ROLE_RANK = {"viewer": 0, "editor": 1, "owner": 2}

def require_role(min_role: str):
    async def _dep(app_id: str, current_user: User = Depends(get_current_user), db = Depends(get_db_session)):
        member = await db.scalar(select(AppMember).where(...))
        if member is None or ROLE_RANK[member.role] < ROLE_RANK[min_role]:
            raise HTTPException(403)
        return member
    return _dep
```

Esta factory retorna uma dependência reutilizável. O `owner` do app é automaticamente
inserido como membro `owner` na criação do app (trigger via lógica de aplicação, não DB
trigger).

### 4. Backward compatibility de `GET /api/apps`

O endpoint de listagem continua filtrando por `owner_id` para compatibilidade. Apps
compartilhados com um usuário (como `editor` ou `viewer`) ficam disponíveis via
`GET /api/apps?shared=true` (extensão incremental fora do escopo desta sprint).

### 5. `GET /api/apps/{app_id}` e routers de pages/queries

Ao invés de verificar apenas `owner_id`, esses endpoints verificam se o usuário possui
uma entrada em `app_members` com qualquer role (membership check). Apenas mutations
(PATCH, DELETE) exigem role `editor` ou `owner`.

---

## Alternativas consideradas

| Alternativa | Motivo para rejeitar |
|-------------|----------------------|
| Enum Postgres para `role` | `ALTER TYPE` em produção é complexo; check constraint é suficiente |
| Tabela separada por role | Desnecessário para 3 roles simples |
| Policy de RLS no Postgres | Adiciona complexidade de infra; a lógica de autorização fica no código onde é testável |
| JWT com claims de role | Role pode mudar sem re-emissão de token; melhor consultar DB |

---

## Consequências

- Cada endpoint que acessa um app precisa verificar membership (adicionado via dependency FastAPI).  
- Criação de app agora insere automaticamente uma entrada `app_members(role='owner')`.  
- Routers de `pages`, `queries` e `datasources` recebem o `require_role` mínimo apropriado.  
- Risco SEC-003 fica `mitigated` após deployment desta sprint.  
- Futura extensão multitenancy (workspace) pode adicionar tabela `workspace_members` separada
  sem quebrar esta estrutura.
