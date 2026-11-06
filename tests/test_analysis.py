import unittest
from decimal import Decimal

from expenses_reader.analysis import compare_statements
from expenses_reader.models import ExpenseKind, ExpenseLine, MonthlyStatement, Period


def statement(year, month, common, lines, warnings=(), confidence=Decimal("1")):
    return MonthlyStatement(
        period=Period(year, month),
        unit="UF 4B",
        source_name=f"expensas-{year}-{month:02}.pdf",
        source_id=f"doc-{year}-{month:02}",
        common_amount=Decimal(common),
        lines=tuple(lines),
        extraction_warnings=tuple(warnings),
        extraction_confidence=confidence,
    )


class ComparisonTests(unittest.TestCase):
    def test_reports_amount_and_percentage_for_adjacent_months(self):
        previous = statement(2026, 1, "100000", [ExpenseLine("Limpieza", Decimal("10000"), kind=ExpenseKind.RECURRING)])
        current = statement(2026, 2, "125000", [ExpenseLine("LIMPIEZA", Decimal("12000"), kind=ExpenseKind.RECURRING)])
        result = compare_statements(previous, current)
        self.assertEqual(result.total_change.difference, Decimal("25000"))
        self.assertEqual(result.total_change.percentage, Decimal("25.00"))
        self.assertEqual(result.line_changes[0].difference, Decimal("2000"))
        self.assertFalse(result.needs_review)
        self.assertEqual(result.total_change.current_source, "doc-2026-02")

    def test_unmatched_or_low_confidence_data_requires_review(self):
        previous = statement(2026, 1, "100000", [ExpenseLine("Agua", Decimal("5000"))])
        current = statement(2026, 2, "105000", [ExpenseLine("Gas", Decimal("6000"))], confidence=Decimal("0.5"))
        result = compare_statements(previous, current)
        self.assertTrue(result.needs_review)
        self.assertEqual(result.unmatched_previous, ("Agua",))
        self.assertEqual(result.unmatched_current, ("Gas",))

    def test_rejects_nonconsecutive_periods_and_different_units(self):
        january = statement(2026, 1, "1", [])
        march = statement(2026, 3, "1", [])
        with self.assertRaises(ValueError):
            compare_statements(january, march)
        february_other_unit = MonthlyStatement(
            period=Period(2026, 2), unit="UF 9", source_name="x", source_id="y"
        )
        with self.assertRaises(ValueError):
            compare_statements(january, february_other_unit)

    def test_zero_baseline_has_no_percentage(self):
        previous = statement(2026, 1, "0", [])
        current = statement(2026, 2, "500", [])
        result = compare_statements(previous, current)
        self.assertIsNone(result.total_change.percentage)
