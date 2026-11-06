"""Validated, source-traceable expense statement data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class ExpenseKind(str, Enum):
    RECURRING = "recurring"
    EXTRAORDINARY = "extraordinary"
    UNKNOWN = "unknown"


@dataclass(frozen=True, order=True)
class Period:
    year: int
    month: int

    def __post_init__(self) -> None:
        if not 2000 <= self.year <= 2200:
            raise ValueError("year must be between 2000 and 2200")
        if not 1 <= self.month <= 12:
            raise ValueError("month must be between 1 and 12")

    @classmethod
    def from_date(cls, value: date) -> "Period":
        return cls(year=value.year, month=value.month)

    def previous(self) -> "Period":
        if self.month == 1:
            return Period(self.year - 1, 12)
        return Period(self.year, self.month - 1)

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"


@dataclass(frozen=True)
class ExpenseLine:
    description: str
    amount: Decimal
    category: Optional[str] = None
    kind: ExpenseKind = ExpenseKind.UNKNOWN
    source_row: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("expense description cannot be empty")
        if not self.amount.is_finite():
            raise ValueError("expense amount must be finite")


@dataclass(frozen=True)
class MonthlyStatement:
    period: Period
    unit: str
    source_name: str
    source_id: str
    common_amount: Optional[Decimal] = None
    housing_amount: Optional[Decimal] = None
    lines: tuple[ExpenseLine, ...] = field(default_factory=tuple)
    extraction_warnings: tuple[str, ...] = field(default_factory=tuple)
    extraction_confidence: Optional[Decimal] = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.unit.strip():
            raise ValueError("unit cannot be empty")
        if not self.source_name.strip() or not self.source_id.strip():
            raise ValueError("source name and source id are required for traceability")
        if self.extraction_confidence is not None and not (
            Decimal("0") <= self.extraction_confidence <= Decimal("1")
        ):
            raise ValueError("extraction confidence must be between 0 and 1")
        for amount in (self.common_amount, self.housing_amount):
            if amount is not None and not amount.is_finite():
                raise ValueError("statement amounts must be finite")

    @property
    def total_amount(self) -> Optional[Decimal]:
        """Return the statement total when both components are available."""
        if self.common_amount is None and self.housing_amount is None:
            return None
        return (self.common_amount or Decimal("0")) + (
            self.housing_amount or Decimal("0")
        )
