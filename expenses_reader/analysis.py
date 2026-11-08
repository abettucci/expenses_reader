"""Period-over-period comparisons with explicit uncertainty and provenance."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
import unicodedata
from typing import Optional

from .models import (
    BuildingStatement,
    AUTO_PUBLISH_CONFIDENCE,
    ExpenseKind,
    ExpenseLine,
    MonthlyStatement,
    UnitSettlement,
)


@dataclass(frozen=True)
class Change:
    label: str
    previous_amount: Decimal
    current_amount: Decimal
    difference: Decimal
    percentage: Optional[Decimal]
    kind: ExpenseKind
    previous_source: str
    current_source: str
    status: str = "comparable"


@dataclass(frozen=True)
class StatementComparison:
    previous_period: str
    current_period: str
    unit: str
    total_change: Optional[Change]
    line_changes: tuple[Change, ...]
    unmatched_previous: tuple[str, ...]
    unmatched_current: tuple[str, ...]
    needs_review: bool

    @property
    def largest_increases(self) -> tuple[Change, ...]:
        return tuple(
            sorted(
                (change for change in self.line_changes if change.difference > 0),
                key=lambda change: change.difference,
                reverse=True,
            )
        )


@dataclass(frozen=True)
class UnitSettlementChange:
    unit: str
    previous_amount_due: Decimal
    current_amount_due: Decimal
    difference: Decimal
    percentage: Optional[Decimal]
    previous_arrears: Optional[Decimal]
    current_arrears: Optional[Decimal]


@dataclass(frozen=True)
class BuildingComparison:
    previous_period: str
    current_period: str
    previous_source: str
    current_source: str
    total_change: Optional[Change]
    line_changes: tuple[Change, ...]
    unit_changes: tuple[UnitSettlementChange, ...]
    unmatched_previous_lines: tuple[str, ...]
    unmatched_current_lines: tuple[str, ...]
    unmatched_previous_units: tuple[str, ...]
    unmatched_current_units: tuple[str, ...]
    needs_review: bool

    @property
    def largest_increases(self) -> tuple[Change, ...]:
        return tuple(
            sorted(
                (change for change in self.line_changes if change.difference > 0),
                key=lambda change: change.difference,
                reverse=True,
            )
        )


def _key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


def _percent(previous: Decimal, current: Decimal) -> Optional[Decimal]:
    if previous == 0:
        return None
    return ((current - previous) / abs(previous) * Decimal("100")).quantize(
        Decimal("0.01")
    )


def _change(
    label: str,
    previous: Decimal,
    current: Decimal,
    kind: ExpenseKind,
    previous_source: str,
    current_source: str,
) -> Change:
    return Change(
        label=label,
        previous_amount=previous,
        current_amount=current,
        difference=current - previous,
        percentage=_percent(previous, current),
        kind=kind,
        previous_source=previous_source,
        current_source=current_source,
    )


def _line_map(lines: tuple[ExpenseLine, ...]) -> dict[str, ExpenseLine]:
    """Group identical normalized labels; duplicates remain visible as a review case."""
    grouped: dict[str, list[ExpenseLine]] = {}
    for line in lines:
        label = line.category or line.description
        grouped.setdefault(_key(label), []).append(line)

    # Duplicate labels may represent separate invoices. Aggregate their amounts while
    # retaining the label; callers are warned when a key is duplicated.
    return {
        key: ExpenseLine(
            description=" / ".join(line.description for line in group),
            amount=sum((line.amount for line in group), Decimal("0")),
            category=group[0].category,
            kind=(group[0].kind if all(x.kind == group[0].kind for x in group) else ExpenseKind.UNKNOWN),
            source_row=(";".join(x.source_row for x in group if x.source_row) or None),
        )
        for key, group in grouped.items()
    }


def compare_statements(
    previous: MonthlyStatement, current: MonthlyStatement
) -> StatementComparison:
    """Compare adjacent months for one unit, preserving source references.

    A mismatch, missing headline total, extraction warning, or ambiguous repeated
    label is surfaced as a review requirement instead of being silently treated as
    a reliable increase.
    """
    if previous.unit != current.unit:
        raise ValueError("statements must belong to the same unit")
    if current.period.previous() != previous.period:
        raise ValueError("statements must be from consecutive periods")

    total_change = None
    if previous.total_amount is not None and current.total_amount is not None:
        total_change = _change(
            "Total expensas",
            previous.total_amount,
            current.total_amount,
            ExpenseKind.UNKNOWN,
            previous.source_id,
            current.source_id,
        )

    prev_map = _line_map(previous.lines)
    curr_map = _line_map(current.lines)
    common = prev_map.keys() & curr_map.keys()
    changes = tuple(
        _change(
            curr_map[key].category or curr_map[key].description,
            prev_map[key].amount,
            curr_map[key].amount,
            curr_map[key].kind,
            previous.source_id,
            current.source_id,
        )
        for key in sorted(common)
    )
    unmatched_previous = tuple(prev_map[key].description for key in sorted(prev_map.keys() - curr_map.keys()))
    unmatched_current = tuple(curr_map[key].description for key in sorted(curr_map.keys() - prev_map.keys()))
    duplicate_labels = any(len([line for line in s.lines if _key(line.category or line.description) == key]) > 1
                           for s, mapping in ((previous, prev_map), (current, curr_map))
                           for key in mapping)
    needs_review = bool(
        previous.extraction_warnings
        or current.extraction_warnings
        or previous.extraction_confidence is not None and previous.extraction_confidence < Decimal("0.8")
        or current.extraction_confidence is not None and current.extraction_confidence < Decimal("0.8")
        or total_change is None
        or unmatched_previous
        or unmatched_current
        or duplicate_labels
    )
    return StatementComparison(
        previous_period=str(previous.period),
        current_period=str(current.period),
        unit=current.unit,
        total_change=total_change,
        line_changes=changes,
        unmatched_previous=unmatched_previous,
        unmatched_current=unmatched_current,
        needs_review=needs_review,
    )


def _settlement_map(
    settlements: tuple[UnitSettlement, ...]
) -> dict[str, UnitSettlement]:
    return {_key(settlement.unit): settlement for settlement in settlements}


def _has_duplicate_source_rows(lines: tuple[ExpenseLine, ...]) -> bool:
    row_ids = [line.source_row for line in lines if line.source_row]
    return len(row_ids) != len(set(row_ids))


def compare_building_statements(
    previous: BuildingStatement,
    current: BuildingStatement,
) -> BuildingComparison:
    """Compare building expenses and unit totals between consecutive months."""
    if current.period.previous() != previous.period:
        raise ValueError("statements must be from consecutive periods")

    previous_lines = _line_map(previous.expense_lines)
    current_lines = _line_map(current.expense_lines)
    common_lines = previous_lines.keys() & current_lines.keys()
    line_changes = tuple(
        _change(
            current_lines[key].category or current_lines[key].description,
            previous_lines[key].amount,
            current_lines[key].amount,
            current_lines[key].kind,
            previous.source_id,
            current.source_id,
        )
        for key in sorted(common_lines)
    )
    unmatched_previous_lines = tuple(
        previous_lines[key].description
        for key in sorted(previous_lines.keys() - current_lines.keys())
    )
    unmatched_current_lines = tuple(
        current_lines[key].description
        for key in sorted(current_lines.keys() - previous_lines.keys())
    )

    previous_total = previous.calculated_expense_total
    current_total = current.calculated_expense_total
    total_change = None
    if previous_total is not None and current_total is not None:
        total_change = _change(
            "Gasto total del edificio",
            previous_total,
            current_total,
            ExpenseKind.UNKNOWN,
            previous.source_id,
            current.source_id,
        )

    previous_units = _settlement_map(previous.unit_settlements)
    current_units = _settlement_map(current.unit_settlements)
    common_units = previous_units.keys() & current_units.keys()
    unit_changes = tuple(
        UnitSettlementChange(
            unit=current_units[key].unit,
            previous_amount_due=previous_units[key].amount_due,
            current_amount_due=current_units[key].amount_due,
            difference=current_units[key].amount_due - previous_units[key].amount_due,
            percentage=_percent(
                previous_units[key].amount_due,
                current_units[key].amount_due,
            ),
            previous_arrears=previous_units[key].arrears,
            current_arrears=current_units[key].arrears,
        )
        for key in sorted(common_units)
        if previous_units[key].amount_due is not None
        and current_units[key].amount_due is not None
    )
    unmatched_previous_units = tuple(
        previous_units[key].unit
        for key in sorted(previous_units.keys() - current_units.keys())
    )
    unmatched_current_units = tuple(
        current_units[key].unit
        for key in sorted(current_units.keys() - previous_units.keys())
    )

    duplicate_source_rows = any(
        _has_duplicate_source_rows(statement.expense_lines)
        for statement in (previous, current)
    )
    unit_amounts_missing = any(
        settlement.amount_due is None
        for statement in (previous, current)
        for settlement in statement.unit_settlements
    )
    needs_review = bool(
        previous.extraction_warnings
        or current.extraction_warnings
        or previous.extraction_confidence is None
        or current.extraction_confidence is None
        or previous.extraction_confidence < AUTO_PUBLISH_CONFIDENCE
        or current.extraction_confidence < AUTO_PUBLISH_CONFIDENCE
        or total_change is None
        or previous.expense_total_matches is not True
        or current.expense_total_matches is not True
        or unmatched_previous_lines
        or unmatched_current_lines
        or unmatched_previous_units
        or unmatched_current_units
        or duplicate_source_rows
        or unit_amounts_missing
    )
    return BuildingComparison(
        previous_period=str(previous.period),
        current_period=str(current.period),
        previous_source=previous.source_id,
        current_source=current.source_id,
        total_change=total_change,
        line_changes=line_changes,
        unit_changes=unit_changes,
        unmatched_previous_lines=unmatched_previous_lines,
        unmatched_current_lines=unmatched_current_lines,
        unmatched_previous_units=unmatched_previous_units,
        unmatched_current_units=unmatched_current_units,
        needs_review=needs_review,
    )
