# Release Note — Sprint 4 Close

**Date:** 2026-03-16  
**Sprint:** 4  
**Version:** 0.4.0  
**Environments:** Staging → Production  
**Release Manager:** Release Manager Agent  
**Status:** READY FOR STAGING DEPLOY

---

## What's New

### 4A — RBAC & App Sharing

Collaborative access control for all apps.

- **Role model:** `owner`, `editor`, `viewer`. Owners invite collaborators; editors can modify layout and queries; viewers have read-only access.
- **Share drawer:** Owners see a "Share" button in the builder header. The drawer lists current members, lets owners invite by email, change roles, and remove members.
- **API surface:**  
  - `GET /api/apps/{id}/members` — list members (viewer+)  
  - `POST /api/apps/{id}/members` — invite (owner only)  
  - `PATCH /api/apps/{id}/members/{user_id}` — change role (owner only)  
  - `DELETE /api/apps/{id}/members/{user_id}` — remove (owner only)  
  - `GET /api/apps/{id}/members/me/role` — current user's role  
- **Migration:** `0003_app_members_templates.py` — adds `app_members` table.  
- **ADR:** [ADR-0002](../adr/ADR-0002-rbac-app-members.md)

### 4B — GraphQL Datasource

Execute GraphQL queries from the builder query panel.

- New datasource type `graphql` dispatches `POST` with `{ query, variables }` body.
- **GraphQL editor UI:** Replaces the REST URL/method form when a `graphql` datasource is selected — provides a query textarea and a JSON variables textarea.
- Bearer token from `auth_config` is forwarded automatically.
- SSRF guard (`_validate_url`) covers GraphQL endpoints equally.
- **Security hardening:** 10 MB response size limit to prevent memory exhaustion.

### 4C — App Templates

One-click app creation from pre-built templates.

- 3 built-in templates: **CRUD Table**, **KPI Dashboard**, **Form Submit**.
- Templates are auto-seeded into the database on first `GET /api/templates` call.
- **Template picker UI:** Visible in the empty state. Opening "Start from a template" shows a modal grid of template cards. Selecting one and clicking "Use template" creates a new app pre-loaded with the template layout.
- **API surface:**  
  - `GET /api/templates` — list templates (auto-seeds on first call)  
  - `POST /api/templates/from-template` — create app from template slug

### 4D — Developer Experience (DevContainer)

- `.devcontainer/devcontainer.json` — VS Code Dev Container with Python 3.10, Node 20, Docker-in-Docker, and recommended extensions.
- `.devcontainer/postCreate.sh` — installs backend and frontend dependencies, runs Alembic migrations.

---

## Bug Fixes

- Fixed duplicate JSX block in `QueryPanel.tsx` that caused double-render of run button and result pane.

---

## Security

See full checklist: [docs/security/2026-03-16-risk-checklist-sprint4.md](../security/2026-03-16-risk-checklist-sprint4.md)

Summary:
- RBAC enforced server-side via `require_role()` dependency — not bypassable client-side.
- GraphQL SSRF blocked same as REST (`_validate_url`).
- GraphQL response capped at 10 MB (implemented in this sprint).
- No new NPM or PyPI dependencies with known CVEs.

---

## Database Migrations

| Revision | Description |
|----------|-------------|
| `0003_app_members_templates` | Adds `app_members` (composite PK, role CHECK constraint) and `templates` (slug UNIQUE) tables |

**Run on deploy:**
```bash
alembic upgrade head
```

---

## Breaking Changes

None. All new endpoints are additive. Existing apps without `app_members` rows continue to work — `_get_accessible_app()` falls back to `owner_id` check.

---

## Test Coverage

| Suite | Count | Status |
|-------|-------|--------|
| Backend pytest | 87 tests | ✅ All pass |
| Frontend unit (Vitest) | — | ✅ Existing pass |
| E2E new (Playwright) | 13 new specs | ✅ Authored |
| E2E total | 5 files, ~30 specs | Pending CI run |

---

## Rollback Plan

1. `alembic downgrade 0002` — removes `app_members` and `templates` tables.
2. Revert to `v0.3.x` container image.
3. No data loss risk: `app_members` and `templates` are new tables — downgrade drops them cleanly.

---

## Deploy Checklist

- [ ] `alembic upgrade head` executed on staging DB  
- [ ] Smoke test: create app → invite member → verify role  
- [ ] Smoke test: create app from template → verify layout loaded  
- [ ] Smoke test: add GraphQL datasource → run `{ __typename }` query  
- [ ] Verify SSRF blocked: attempt `http://localhost:9000` in non-dev environment  
- [ ] Prometheus metrics healthy (query executor calls visible)  
- [ ] No error spike in Sentry after deploy  
