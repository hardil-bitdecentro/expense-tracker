# How this was built

Built with Claude Code, as the task asked. These are the prompts I gave it, in order, and what I checked after each step.

## 1. The brief

> Here is the task PDF: an expense tracker with categories, Next.js frontend, FastAPI backend, SQLite.
> Build it end to end. Keep the rules from the brief in both the API and the database, handle invalid input
> gracefully, write tests for the API, and document the decisions.

Checked:
- every endpoint and response shape matches the PDF (`POST/GET /categories`, `POST/GET /expenses`, `GET /summary`)
- the constraints hold: category must exist, title not empty, amount positive, no duplicate category names
- `pytest` passes (14 tests), including duplicates, missing category, blank title, zero and negative amounts, and an empty summary

## 2. The design

> Make the UI look really good, and it shouldn't look AI generated at all.

Direction I went with: a ledger look. Paper background, a serif heading, numbers in tabular figures so amounts line up,
hairline rules instead of shadows and rounded cards, one dark green accent, and plain-language empty and error states.

Checked in the browser:
- submitting an empty form shows "Pick a category first."
- adding an expense puts it at the top of the list and updates the totals, the count, the average and the category counts
- a duplicate category name shows the API's message instead of failing silently

## 3. Fixes along the way

- The pinned Pydantic version had no build for Python 3.14, so I moved to current releases and pinned those.
- Allowed both `localhost:3000` and `127.0.0.1:3000` for CORS.

## 4. Audit and tests

> Audit it once more against the PDF, add test cases, and run it locally.

What changed:
- the date column now always shows (the brief asks for it), and the table scrolls sideways on small screens instead
- the form checks for at most two decimals before sending, the same rule as the API
- tests went from 14 to 43 on the API, plus 12 unit tests on the frontend and one end-to-end test in Chrome
- ran the API and the production build locally and checked the page with sample data
