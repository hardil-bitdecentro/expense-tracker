"""Edge cases from the brief, response formats, and the rules enforced by the database itself."""

import re
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

ISO_SECONDS = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d$")


def category(client: TestClient, name: str) -> int:
    return client.post("/categories", json={"name": name}).json()["id"]


def expense(client: TestClient, title: str, amount: float, category_id: int) -> dict:
    response = client.post("/expenses", json={"title": title, "amount": amount, "category_id": category_id})
    assert response.status_code == 201, response.text
    return response.json()


# --- Categories -----------------------------------------------------------------------------

def test_category_ids_are_unique_and_increasing(client: TestClient) -> None:
    ids = [category(client, name) for name in ("Food", "Travel", "Bills")]
    assert ids == sorted(set(ids))


def test_category_name_is_trimmed(client: TestClient) -> None:
    response = client.post("/categories", json={"name": "  Rent  "})
    assert response.json()["name"] == "Rent"


@pytest.mark.parametrize("payload", [{}, {"name": None}, {"name": 123}, {"name": "x" * 101}])
def test_bad_category_payloads_are_rejected(client: TestClient, payload: dict) -> None:
    response = client.post("/categories", json=payload)
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)


def test_categories_list_is_empty_at_start(client: TestClient) -> None:
    assert client.get("/categories").json() == []


def test_failed_duplicate_does_not_change_anything(client: TestClient) -> None:
    category(client, "Food")
    client.post("/categories", json={"name": "FOOD"})
    assert [c["name"] for c in client.get("/categories").json()] == ["Food"]


# --- Expenses -------------------------------------------------------------------------------

def test_expense_title_is_trimmed(client: TestClient) -> None:
    food = category(client, "Food")
    assert expense(client, "  Lunch  ", 10, food)["title"] == "Lunch"


def test_created_at_is_iso_without_fractions_and_close_to_now(client: TestClient) -> None:
    food = category(client, "Food")
    created = expense(client, "Lunch", 10, food)["created_at"]
    assert ISO_SECONDS.match(created), created
    stored = datetime.fromisoformat(created).replace(tzinfo=timezone.utc)
    assert abs((datetime.now(timezone.utc) - stored).total_seconds()) < 60


@pytest.mark.parametrize(
    "payload, reason",
    [
        ({"title": "Taxi", "amount": 10.555, "category_id": 1}, "more than two decimals"),
        ({"title": "Taxi", "amount": 10, "category_id": "abc"}, "category id not a number"),
        ({"title": "Taxi", "amount": 10, "category_id": 0}, "category id zero"),
        ({"title": "Taxi", "amount": 10}, "category id missing"),
        ({"amount": 10, "category_id": 1}, "title missing"),
        ({"title": "Taxi", "amount": 1e13, "category_id": 1}, "amount too large"),
    ],
)
def test_more_invalid_expenses(client: TestClient, payload: dict, reason: str) -> None:
    category(client, "Travel")
    response = client.post("/expenses", json=payload)
    assert response.status_code == 422, reason


def test_malformed_json_gets_a_readable_error(client: TestClient) -> None:
    response = client.post("/expenses", content="{not json", headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json()["detail"] == "Request body must be valid JSON"


def test_rejected_expense_is_not_saved(client: TestClient) -> None:
    category(client, "Food")
    client.post("/expenses", json={"title": "", "amount": 10, "category_id": 1})
    client.post("/expenses", json={"title": "Taxi", "amount": 10, "category_id": 42})
    assert client.get("/expenses").json() == []
    assert client.get("/summary").json()["count"] == 0


def test_expenses_are_listed_newest_first(client: TestClient) -> None:
    food = category(client, "Food")
    first = expense(client, "Breakfast", 5, food)
    second = expense(client, "Lunch", 7, food)
    assert [e["id"] for e in client.get("/expenses").json()] == [second["id"], first["id"]]


def test_expenses_list_is_empty_at_start(client: TestClient) -> None:
    assert client.get("/expenses").json() == []


def test_expense_shows_the_right_category_name(client: TestClient) -> None:
    food, travel = category(client, "Food"), category(client, "Travel")
    expense(client, "Lunch", 10, food)
    expense(client, "Cab", 20, travel)
    assert {e["title"]: e["category"] for e in client.get("/expenses").json()} == {"Lunch": "Food", "Cab": "Travel"}


# --- Summary --------------------------------------------------------------------------------

def test_summary_matches_the_brief_example(client: TestClient) -> None:
    food = category(client, "Food")
    expense(client, "Lunch", 250.5, food)
    expense(client, "Dinner", 180, food)
    assert client.get("/summary").json() == {"total": 430.5, "count": 2, "average": 215.25}


def test_summary_rounds_average_to_two_decimals(client: TestClient) -> None:
    food = category(client, "Food")
    for amount in (10, 10, 10.01):
        expense(client, "Item", amount, food)
    assert client.get("/summary").json() == {"total": 30.01, "count": 3, "average": 10.0}


def test_summary_has_no_float_drift(client: TestClient) -> None:
    food = category(client, "Food")
    for _ in range(10):
        expense(client, "Tea", 0.1, food)
    assert client.get("/summary").json()["total"] == 1.0


def test_category_counts_follow_new_expenses(client: TestClient) -> None:
    food = category(client, "Food")
    assert client.get("/categories").json()[0]["total_expenses"] == 0
    expense(client, "Lunch", 10, food)
    assert client.get("/categories").json()[0]["total_expenses"] == 1


# --- Database-level rules (a second line of defence behind the API) -------------------------

def test_database_rejects_an_expense_with_unknown_category(engine: Engine) -> None:
    with engine.begin() as conn, pytest.raises(IntegrityError):
        conn.execute(
            text("INSERT INTO expenses (title, amount, category_id, created_at) VALUES ('x', 1, 999, CURRENT_TIMESTAMP)")
        )


def test_database_rejects_non_positive_amount(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO categories (name) VALUES ('Food')"))
    with engine.begin() as conn, pytest.raises(IntegrityError):
        conn.execute(
            text("INSERT INTO expenses (title, amount, category_id, created_at) VALUES ('x', 0, 1, CURRENT_TIMESTAMP)")
        )


def test_database_rejects_blank_title(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO categories (name) VALUES ('Food')"))
    with engine.begin() as conn, pytest.raises(IntegrityError):
        conn.execute(
            text("INSERT INTO expenses (title, amount, category_id, created_at) VALUES ('   ', 5, 1, CURRENT_TIMESTAMP)")
        )


def test_database_rejects_duplicate_names_in_any_case(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO categories (name) VALUES ('Food')"))
    with engine.begin() as conn, pytest.raises(IntegrityError):
        conn.execute(text("INSERT INTO categories (name) VALUES ('fOOd')"))
