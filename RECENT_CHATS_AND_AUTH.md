# Recent Chats + Backend Auth Scoping — Implementation Summary

## Overview

Two related changes:

1. **Recent chats** — a sidebar on `/ask` listing past chat sessions (subject, preview, time ago) that a student can click to resume, backed by the existing SQLite session-memory store.
2. **Backend auth scoping** — the `/sessions` family of endpoints now verifies the caller's Clerk JWT and only returns/modifies that user's own chats, instead of every session on the server.

---

## 1. Recent Chats

### Backend

- **`backend/services/memory.py`**
  - Added a `collection` column to the `sessions` table (auto-migrated via `ALTER TABLE` for existing DBs).
  - `save_turn(session_id, role, content, collection=None, user_id=None)` now stamps `collection` on each turn (`COALESCE` keeps the existing value if omitted).
  - New `list_sessions(limit=20, user_id=None)` — returns recent non-empty sessions, most recently active first, each with a `preview` (first user message, truncated).

- **`backend/services/rag_qa.py`** — `ask()` passes `collection_name` into `save_turn()` so sessions carry a human-readable label instead of a bare UUID.

- **`backend/routers/session.py`** — new `GET /sessions?limit=20` endpoint.

### Frontend

- **`frontend/lib/api/session.ts`** (new) — `listSessions`, `getSessionHistory`, `deleteSession`.
- **`frontend/hooks/useAsk.ts`** — added `loadSession(sessionId)` to fetch a past session's history and resume it (swaps the active `session_id` so new turns append to the same chat); exposes `sessionId`.
- **`frontend/components/chat/RecentChats.tsx`** (new) — sidebar component: lists recent chats with subject/preview/relative time, per-item delete, highlights the active session.
- **`frontend/app/ask/page.tsx`** — sidebar wired into both the subject-picker and chat screens; selecting a past chat loads it; finishing a Q&A round refreshes the list.

### Known limitation
Sessions created before this feature (or by anyone who chats without signing in) have no `collection`/`user_id` stamped — they still show up for any signed-in user (see auth section below).

---

## 2. Backend Auth Scoping

### Problem
`GET /sessions` initially returned **every** session on the server — there was no backend verification of the Clerk token the frontend already sends, so nothing scoped chats to their owner.

### Fix — `backend/services/auth.py` (new)

Verifies Clerk JWTs without the Clerk SDK — just `PyJWT` + a JWKS lookup:

- `CLERK_PUBLISHABLE_KEY` (added to `config.py`) is the same public value the frontend uses as `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`. Its format is `pk_(test|live)_<base64(domain + "$")>` — decoding it (safe, it's public info shipped to every browser) gives the Clerk Frontend API domain, which is also the JWT issuer and JWKS host.
- `get_optional_user_id(request)` — best-effort: no `Authorization` header → `None` (anonymous). A **present but invalid/expired** token still raises `401` — never silently downgrades to anonymous.
- `require_user_id(request)` — same, but raises `401` if no token was sent at all.

### Wiring

| Endpoint | Dependency | Behavior |
|---|---|---|
| `POST /ask` | `get_optional_user_id` | Works anonymously; if a valid token is sent, stamps the session with that `user_id`. Invalid token → 401. |
| `GET /sessions` | `require_user_id` | 401 without a valid token; otherwise only returns the caller's own sessions. |
| `GET /session/{id}/history` | `require_user_id` | Returns `[]` if the session belongs to a different user (no existence leak). |
| `DELETE /session/{id}` | `require_user_id` | No-op (still 200) if the session belongs to a different user — idempotent, no existence leak. |

`backend/services/memory.py` ownership rule: a session with **no** `user_id` stamped (pre-auth data) stays visible/editable by anyone — the same trust model that existed before this change. Once a `user_id` is stamped, only that user can read/clear it.

### Frontend
- **`frontend/lib/api/session.ts`** — all three calls now take an optional `authToken` and send `Authorization: Bearer <token>`.
- **`frontend/components/chat/RecentChats.tsx`** / **`frontend/hooks/useAsk.ts`** — fetch the Clerk token via `useAuth().getToken()` before calling the session endpoints.

### Verified (via FastAPI `TestClient`, no real Clerk instance needed for this part)
- `GET /sessions`, `GET /session/{id}/history`, `DELETE /session/{id}` → `401` with no token.
- `POST /ask` → `200` with no token (anonymous still works).
- `POST /ask` with a garbage token → `401` (rejected, not silently ignored).
- Publishable-key → issuer/JWKS-URL decoding logic verified against a synthetic key.

### Setup required to actually use this
Add to `backend/.env`:
```
CLERK_PUBLISHABLE_KEY=<same value as frontend's NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY>
```
Restart uvicorn after adding it. Without it, `require_user_id`/`get_optional_user_id` raise a clear `RuntimeError` telling you the key is missing the first time a protected route is hit.

**Not yet tested end-to-end against a real Clerk instance** — this checkout has no `frontend/.env.local`, so Clerk isn't fully configured locally. The JWT verification logic itself (signature check via JWKS, issuer pinning, expiry) is standard and was unit-tested for the issuer-derivation step only.

### Also added
- `PyJWT==2.13.0` to `backend/requirements.txt` (installed in the venv already).
