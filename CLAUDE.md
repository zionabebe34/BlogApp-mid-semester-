# BlogApp / HandyHub — RUNI Full Stack final project

A social network (Reddit/Instagram style) for DIY projects. This file is the
project brief: read it before changing anything.

## Working style

The owner (Zion) is being **examined orally on this code**. He is comfortable
with Python/SQL and weaker on React. Therefore:

- **Go slowly, one function at a time.** Do not batch large changes.
- **Show code as text and explain it before writing to files.** Wait for approval.
- Explain *why*, not just *what* — especially new concepts (decorators, hooks,
  SQL joins, security trade-offs).
- Prefer patterns already in the codebase over introducing new ones, so the
  code stays uniform and easy to explain.

## Stack & layout

| Part | Tech | Port |
|---|---|---|
| Frontend | React 19 + Vite + MUI 9 | 5173/5174 |
| Backend | Flask + MySQL (`mysql-connector-python`) | 5001 |

```
backend/
  server.py                 all routes (single file, ~1200 lines)
  seed.py                   fake data from jsonplaceholder + DiceBear
  test_auth.py              unit tests (mocked DB)
  test_auth_integration.py  integration tests (real DB)
  config.env                secrets — gitignored
  config.env.example        template
  schema.sql                CREATE TABLE only, for Docker's MySQL init — start.sh
                             has its own copy with guarded ALTER TABLE migrations
  Dockerfile                backend image
frontend/src/
  api.js                    every backend call; nothing else uses fetch()
  components/SinglePost.jsx post card: likes, comments dialog, report flag
  pages/                    Feed, Login, Signup, ForgotPassword, ResetPassword,
                             Messages, AdminPage, profiles…
  Dockerfile                frontend image (runs `vite --host` dev server)
start.sh                    creates DB + tables, seeds, starts both servers
docker-compose.yml          db + backend + frontend, for containerized run
```

Run locally: `./start.sh` (add `--seed` to reseed, `--seed-only` to just apply schema).
Run with Docker: `docker compose up --build`, then open `http://localhost:5173`.
Tests: `cd backend && .venv/bin/python -m pytest`

## Conventions in this codebase

- **`api.js` is the only place that calls `fetch`.** Pages import named
  functions from it. Every request sends `credentials: 'include'`.
- **Vite proxies `/api` to Flask**, so the frontend uses relative paths and
  there is no CORS in dev. Postman must hit `localhost:5001` directly.
- **Auth**: session cookie → `sessions` table → `current_user_id()`.
  `current_user_role()` returns `user` / `moderator` / `admin`.
  `@roles_required('admin', 'moderator')` guards staff routes — it must sit
  *below* `@app.route`, since decorators apply bottom-up.
- **Frontend route guards are UX only.** Real enforcement is the decorator.
- Constraint violations are caught by errno: `ERR_DUPLICATE_ENTRY` (1062),
  `ERR_FOREIGN_KEY` (1452). 401 = not logged in, 403 = logged in but not allowed.
- Schema changes go in `start.sh`: add to `CREATE TABLE` **and** add a guarded
  `ALTER TABLE` block (checks `information_schema`) so re-running is safe.
- Prefer explicit column lists over `SELECT *`.

## Requirements status

Source: `finalProject.pdf`. Section 1 (mid-semester) is complete.

### Section 2 — Core

| # | Requirement | Status |
|---|---|---|
| 2.a.i | Secure password reset (email) | ✅ done — frontend, backend, tests, real SMTP all verified |
| 2.b.i | Likes / reactions | ✅ done |
| 2.b.ii | Comments (flat) | ✅ done |
| 2.c | Auto-correction, post & comment suggestions | ❌ not started — blocked on `llm_service.py` |
| 2.d.i | 10 autonomous agent accounts, continuous activity | ❌ not started — blocked on `llm_service.py` |
| 2.d.ii | Agent personality stored in user profile | ❌ not started — blocked on `llm_service.py` |
| 2.e.i | Moderators | ✅ done |
| 2.e.ii | Report system + admin dashboard | ✅ done |
| 2.e.iii | Sentiment analysis **before** publishing | ❌ not started — blocked on `llm_service.py` |
| 2.f | 85% code coverage | ✅ done — 89% measured (84 tests: 61 unit + 23 integration) |

### Section 3 — Optional (must deliver 3 of 6). Chosen (finalized 2026-09-24):

1. **Direct Messaging** — private chat between users — ✅ done, verified end-to-end
   (conversations list, thread, send/receive, read receipts, 4s polling, all via
   `/api/conversations` + `/api/messages/<id>` and `pages/Messages.jsx`)
2. **2FA (TOTP)** — not OAuth; Zion picked 2FA only, OAuth is not required — ✅ done,
   verified end-to-end (enable flow on `MyProfilePage`, login gate in `Login.jsx`)
3. **Containerization** — Dockerfile + docker-compose — ✅ done, verified end-to-end
   (signup writes to DB through the container network, feed reads back correctly)

**All three Section 3 requirements are now complete.**

Not chosen (available but dropped): Responsive Design, OAuth (Google) login,
Recommendation Engine / Trending Topics.

## Do this next

1. **Build `llm_service.py`.** One shared abstraction unlocks three
   requirements: 2.c, 2.d and 2.e.iii. Zion has **AWS Bedrock** keys and that
   was the agreed provider, but as of 2026-09-23 he deferred deciding on:
   - How AWS credentials will be supplied (CLI profile / `aws configure` vs.
     explicit `AWS_ACCESS_KEY_ID`+`AWS_SECRET_ACCESS_KEY` in `config.env`).
   - Which Bedrock model to call (no preference chosen yet).
   Don't start this file until Zion revisits both questions. Do this before
   the agents — they depend on it.

2. **2.e.iii sentiment analysis.** Must run *inside* `add_comment`, before the
   `INSERT` — the spec says "before they are even published".

3. **2.d agents.** 10 bot users with a `personality` column on `users`, plus a
   background scheduler (APScheduler was the plan) that posts and replies
   continuously.

4. **AWS deployment**, once the above is done. Section 3 is fully complete,
   so nothing optional is left — only Section 2's LLM-dependent items (2.c,
   2.d, 2.e.iii) and deployment remain.

## Known issues (deliberately deferred)

- **The real MySQL password is in public git history** (`backend/password.py`).
  Rotating it and rewriting history has not been done.
- `debug=True` is still on in `server.py` — must be off before deployment.
- `db.png` (the schema diagram required by section 1f) is **stale**: it lacks
  `likes`, `comments`, `reports`, `password_resets`, and the `role` /
  `is_banned` columns.
- `/api/user-posts/<id>/comments` uses a different prefix from
  `/api/posts/<id>/likes`. Historical inconsistency; harmless but worth knowing.
- **This project used to live at `~/Desktop/BlogApp-mid-semester-`** and moved to
  `~/Projects/BlogApp-mid-semester-` on 2026-09-30 because iCloud Drive's
  "Desktop & Documents" sync was dehydrating `.venv`/`node_modules` files and
  causing multi-minute stalls on ordinary `pip`/`npm`/`pytest` commands. A
  stale copy may still exist on the Desktop — safe to delete, it's not the
  working copy.
