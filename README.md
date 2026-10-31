# Expense Tracker

A small full-stack expense tracker with categories. Next.js on the front, FastAPI on the back, SQLite underneath.

## Run it

**Backend** (Python 3.11+)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

The API is on http://localhost:8000 and interactive docs are at http://localhost:8000/docs.
The database file `expenses.db` is created on first start.

**Frontend** (Node 20+)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. If the API runs somewhere else, set `NEXT_PUBLIC_API_URL` (see `.env.example`).

**Tests**

```bash
cd backend && pytest                 # 43 API and database tests
cd frontend && npm test              # 12 unit tests for form rules and formatting
cd frontend && npm run typecheck
cd frontend && npm run test:e2e      # full flow in Chrome; starts its own API and app on ports 8011 and 3011 with a throwaway database
```

What the tests cover:
- every endpoint and response shape from the brief, including the example numbers (430.5 total, 215.25 average)
- duplicate categories in any case, blank names and titles, zero, negative, non-numeric and over-precise amounts, unknown categories, malformed JSON
- rejected requests leave no data behind, expenses come back newest first, counts update
- the database rejects bad rows on its own (foreign key, positive amount, non-blank title, unique name)
- money adds up without float drift (ten expenses of 0.10 total exactly 1.00)

## API

| Method | Path | What it does |
|---|---|---|
| POST | `/categories` | Create a category. `409` if the name already exists (case-insensitive). |
| GET | `/categories` | List categories, each with `total_expenses`. |
| POST | `/expenses` | Create an expense. `404` if the category doesn't exist, `422` for a blank title or a non-positive amount. |
| GET | `/expenses` | List expenses with the category name and `created_at`, newest first. |
| GET | `/summary` | `total`, `count` and `average` across all expenses. |

Errors always come back as `{"detail": "readable message"}`, so the UI can show them as they are.

## Design decisions

- **Rules live in the database too, not only in the API.** Category names are `UNIQUE COLLATE NOCASE`, expenses have a real foreign key to categories, and `CHECK` constraints reject a blank title or an amount of zero or less. SQLite ignores foreign keys unless asked, so every connection runs `PRAGMA foreign_keys=ON`.
- **Validation happens first in Pydantic.** Titles and names are trimmed, so `"   "` counts as empty. Amount must be greater than zero with at most two decimals. FastAPI's validation errors are flattened into one sentence for the UI.
- **Duplicate categories are checked twice.** A lookup gives a friendly `409`, and the unique constraint catches two requests racing for the same name.
- **Money is a `Decimal` in Python and `NUMERIC(12,2)` in SQLite**, so totals don't drift with float rounding. It's converted to a number with two decimals only in the response.
- **`created_at` is stored in UTC.** The UI converts it to the viewer's local time.
- **Counts and totals are computed in SQL** (`LEFT JOIN` + `COUNT`, `SUM`), not in Python loops. Categories with no expenses still show with a count of 0.
- **The frontend refreshes everything after each change** (categories, expenses and summary in parallel), so the list, the counts and the totals never disagree.
- **The same rules are checked in the form before sending** (category chosen, title not empty, amount positive) for instant feedback. The API stays the source of truth.

## Project layout

```
backend/
  app/db.py        engine, session dependency, foreign keys on
  app/models.py    Category and Expense tables with constraints
  app/schemas.py   request and response models, validation
  app/main.py      routes, error handling, CORS
  tests/           pytest suite against an in-memory database
frontend/
  app/page.tsx     page: loads data, refreshes after changes
  components/      summary figures, expense form, categories, expense table
  lib/api.ts       typed API client
  lib/format.ts    money and date formatting
```
