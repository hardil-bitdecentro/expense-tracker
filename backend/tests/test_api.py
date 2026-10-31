"""API tests against a fresh in-memory SQLite database per test."""

import pytest
from fastapi.testclient import TestClient


def make_category(client: TestClient, name: str = "Food") -> dict:
    response = client.post("/categories", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def test_create_category_returns_id_and_name(client: TestClient) -> None:
    assert make_category(client, "Food") == {"id": 1, "name": "Food"}


def test_duplicate_category_is_rejected_case_insensitively(client: TestClient) -> None:
    make_category(client, "Food")
    response = client.post("/categories", json={"name": "  food "})
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_blank_category_name_is_rejected(client: TestClient) -> None:
    response = client.post("/categories", json={"name": "   "})
    assert response.status_code == 422


def test_create_expense_and_list_with_category_name(client: TestClient) -> None:
    food = make_category(client, "Food")
    created = client.post("/expenses", json={"title": "Lunch", "amount": 250.5, "category_id": food["id"]})
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "Lunch" and body["amount"] == 250.5 and body["category_id"] == food["id"]
    assert body["created_at"]

    listed = client.get("/expenses").json()
    assert listed == [
        {"id": body["id"], "title": "Lunch", "amount": 250.5, "category": "Food", "created_at": body["created_at"]}
    ]


def test_expense_requires_existing_category(client: TestClient) -> None:
    response = client.post("/expenses", json={"title": "Taxi", "amount": 10, "category_id": 99})
    assert response.status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "", "amount": 10, "category_id": 1},
        {"title": "   ", "amount": 10, "category_id": 1},
        {"title": "Taxi", "amount": 0, "category_id": 1},
        {"title": "Taxi", "amount": -5, "category_id": 1},
        {"title": "Taxi", "amount": "abc", "category_id": 1},
        {"title": "Taxi", "category_id": 1},
    ],
)
def test_invalid_expense_input_is_rejected(client: TestClient, payload: dict) -> None:
    make_category(client, "Travel")
    response = client.post("/expenses", json=payload)
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)


def test_categories_include_expense_counts(client: TestClient) -> None:
    food = make_category(client, "Food")
    make_category(client, "Travel")
    for title in ("Lunch", "Dinner", "Snack"):
        client.post("/expenses", json={"title": title, "amount": 10, "category_id": food["id"]})

    counts = {c["name"]: c["total_expenses"] for c in client.get("/categories").json()}
    assert counts == {"Food": 3, "Travel": 0}


def test_summary_totals_and_average(client: TestClient) -> None:
    food = make_category(client, "Food")
    client.post("/expenses", json={"title": "Lunch", "amount": 250.5, "category_id": food["id"]})
    client.post("/expenses", json={"title": "Dinner", "amount": 180, "category_id": food["id"]})

    assert client.get("/summary").json() == {"total": 430.5, "count": 2, "average": 215.25}


def test_summary_is_zero_when_empty(client: TestClient) -> None:
    assert client.get("/summary").json() == {"total": 0.0, "count": 0, "average": 0.0}
