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
  server.py                 all routes (single file, ~750 lines)
  seed.py                   fake data from jsonplaceholder + DiceBear
  test_auth.py              unit tests (mocked DB)
  test_auth_integration.py  integration tests (real DB)
  config.env                secrets — gitignored
  config.env.example        template
frontend/src/
  api.js                    every backend call; nothing else uses fetch()
  components/SinglePost.jsx post card: likes, comments dialog, report flag
  pages/                    Feed, Login, Signup, AdminPage, profiles…
start.sh                    creates DB + tables, seeds, starts both servers
```

Run: `./start.sh` (add `--seed` to reseed, `--seed-only` to just apply schema).
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
| 2.a.i | Secure password reset (email) | **~90%** — see below |
| 2.b.i | Likes / reactions | ✅ done |
| 2.b.ii | Comments (flat) | ✅ done |
| 2.c | Auto-correction, post & comment suggestions | ❌ not started |
| 2.d.i | 10 autonomous agent accounts, continuous activity | ❌ not started |
| 2.d.ii | Agent personality stored in user profile | ❌ not started |
| 2.e.i | Moderators | ✅ done |
| 2.e.ii | Report system + admin dashboard | ✅ done |
| 2.e.iii | Sentiment analysis **before** publishing | ❌ not started |
| 2.f | 85% code coverage | ⚠️ 61 tests pass; coverage % not measured |

### Section 3 — Optional (must deliver 3 of 6). Chosen:

1. **Secure Login** — both sub-items required: OAuth (Google) **and** 2FA (TOTP)
2. **Responsive Design**
3. **Containerization** — Dockerfile + docker-compose

All three are ❌ not started.

## Do this next

1. **Finish 2.a.i (password reset).** Backend is written: `password_resets`
   table, `hash_reset_token()`, `send_reset_email()`, `/api/forgot-password`,
   `/api/reset-password`. Remaining:
   - Zion must generate a Google App Password and put it in
     `config.env` → `SMTP_PASSWORD` (empty now, so the link prints to the
     console instead of sending).
   - Run `./start.sh --seed-only` to create the table.
   - **Frontend is missing entirely**: a "Forgot password?" link on Login, a
     page to request the email, and `/reset-password` to consume
     `?token=` and set a new password.
   - No tests yet.

2. **Build `llm_service.py`.** One shared abstraction unlocks three
   requirements: 2.c, 2.d and 2.e.iii. Zion has **AWS Bedrock** keys and that
   was the agreed provider. Do this before the agents — they depend on it.

3. **2.e.iii sentiment analysis.** Must run *inside* `add_comment`, before the
   `INSERT` — the spec says "before they are even published".

4. **2.d agents.** 10 bot users with a `personality` column on `users`, plus a
   background scheduler (APScheduler was the plan) that posts and replies
   continuously.

5. **Tests to 85%.** Measure first:
   `.venv/bin/python -m pytest --cov=server --cov-report=term-missing`.
   No tests exist yet for roles, reports, ban, or password reset.

6. **The three optional requirements**, then AWS deployment last.

## Known issues (deliberately deferred)

- **The real MySQL password is in public git history** (`backend/password.py`).
  Rotating it and rewriting history has not been done.
- `debug=True` is still on in `server.py` — must be off before deployment.
- `db.png` (the schema diagram required by section 1f) is **stale**: it lacks
  `likes`, `comments`, `reports`, `password_resets`, and the `role` /
  `is_banned` columns.
- `/api/user-posts/<id>/comments` uses a different prefix from
  `/api/posts/<id>/likes`. Historical inconsistency; harmless but worth knowing.
- `htmlcov/` is generated output and should be gitignored.
