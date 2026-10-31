"""Request and response models.

Validation happens here first, so bad input gets a clear 422 before it reaches the database.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def strip_and_require(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Category name cannot be empty")
        return value


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CategorySummaryOut(CategoryOut):
    total_expenses: int


class ExpenseCreate(BaseModel):
    title: str = Field(max_length=200)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category_id: int = Field(gt=0)

    @field_validator("title")
    @classmethod
    def strip_and_require(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title cannot be empty")
        return value


class ExpenseCreatedOut(BaseModel):
    id: int
    title: str
    amount: float
    category_id: int
    created_at: datetime


class ExpenseOut(BaseModel):
    id: int
    title: str
    amount: float
    category: str
    created_at: datetime


class SummaryOut(BaseModel):
    total: float
    count: int
    average: float
