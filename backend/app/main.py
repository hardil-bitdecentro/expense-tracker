"""Expense Tracker API (FastAPI + SQLite).

Endpoints
- POST /categories  create a category (409 if the name already exists)
- GET  /categories  list categories with how many expenses each has
- POST /expenses    create an expense (404 if the category does not exist)
- GET  /expenses    list expenses with their category name, newest first
- GET  /summary     total amount, count and average across all expenses
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from decimal import ROUND_HALF_UP, Decimal

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import Base, engine, get_session
from .models import Category, Expense
from .schemas import (
    CategoryCreate,
    CategoryOut,
    CategorySummaryOut,
    ExpenseCreate,
    ExpenseCreatedOut,
    ExpenseOut,
    SummaryOut,
)

CENT = Decimal("0.01")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Expense Tracker API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Turn Pydantic's error list into one readable message the UI can show as is."""
    messages = []
    for error in exc.errors():
        if error.get("type") == "json_invalid":
            messages.append("Request body must be valid JSON")
            continue
        field = ".".join(str(part) for part in error["loc"] if part != "body")
        message = str(error["msg"]).removeprefix("Value error, ")
        messages.append(f"{field}: {message}" if field else message)
    return JSONResponse(status_code=422, content={"detail": "; ".join(messages)})


def money(value: Decimal | None) -> float:
    return float((value or Decimal(0)).quantize(CENT, rounding=ROUND_HALF_UP))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, session: Session = Depends(get_session)) -> Category:
    existing = session.scalar(select(Category).where(Category.name == payload.name))
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f'Category "{existing.name}" already exists')

    category = Category(name=payload.name)
    session.add(category)
    try:
        session.commit()
    except IntegrityError:
        # Two requests racing for the same name: the UNIQUE constraint is the final word.
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f'Category "{payload.name}" already exists')
    return category


@app.get("/categories", response_model=list[CategorySummaryOut])
def list_categories(session: Session = Depends(get_session)) -> list[CategorySummaryOut]:
    rows = session.execute(
        select(Category.id, Category.name, func.count(Expense.id).label("total_expenses"))
        .outerjoin(Expense, Expense.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.name)
    ).all()
    return [CategorySummaryOut(id=r.id, name=r.name, total_expenses=r.total_expenses) for r in rows]


@app.post("/expenses", response_model=ExpenseCreatedOut, status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseCreate, session: Session = Depends(get_session)) -> ExpenseCreatedOut:
    if session.get(Category, payload.category_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Category {payload.category_id} does not exist")

    expense = Expense(title=payload.title, amount=payload.amount, category_id=payload.category_id)
    session.add(expense)
    session.commit()
    return ExpenseCreatedOut(
        id=expense.id,
        title=expense.title,
        amount=money(expense.amount),
        category_id=expense.category_id,
        created_at=expense.created_at,
    )


@app.get("/expenses", response_model=list[ExpenseOut])
def list_expenses(session: Session = Depends(get_session)) -> list[ExpenseOut]:
    rows = session.execute(
        select(Expense.id, Expense.title, Expense.amount, Category.name.label("category"), Expense.created_at)
        .join(Category, Category.id == Expense.category_id)
        .order_by(Expense.created_at.desc(), Expense.id.desc())
    ).all()
    return [
        ExpenseOut(id=r.id, title=r.title, amount=money(r.amount), category=r.category, created_at=r.created_at)
        for r in rows
    ]


@app.get("/summary", response_model=SummaryOut)
def summary(session: Session = Depends(get_session)) -> SummaryOut:
    total, count = session.execute(select(func.sum(Expense.amount), func.count(Expense.id))).one()
    total = Decimal(str(total or 0))
    average = total / count if count else Decimal(0)
    return SummaryOut(total=money(total), count=count, average=money(average))
