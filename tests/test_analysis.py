import unittest
from decimal import Decimal

from expenses_reader.analysis import compare_building_statements, compare_statements
from expenses_reader.models import (
    BuildingStatement,
    ExpenseKind,
    ExpenseLine,
    MonthlyStatement,
    Period,
    UnitSettlement,
)


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


def building_statement(year, month, lines, units, reported_total, confidence="0.95"):
    return BuildingStatement(
        period=Period(year, month),
        source_name=f"expensas-{year}-{month:02}.xlsx",
        source_id=f"doc-{year}-{month:02}",
        expense_lines=tuple(lines),
        unit_settlements=tuple(units),
        reported_expense_total=Decimal(reported_total),
        extraction_confidence=Decimal(confidence),
    )


class BuildingComparisonTests(unittest.TestCase):
    def test_auto_publication_requires_confidence_and_reconciled_totals(self):
        accepted = building_statement(
            2026,
            1,
            [ExpenseLine("Agua", Decimal("5000"))],
            [UnitSettlement("UF 1", Decimal("10000"))],
            "5000",
        )
        low_confidence = building_statement(
            2026,
            2,
            [ExpenseLine("Agua", Decimal("5000"))],
            [UnitSettlement("UF 1", Decimal("10000"))],
            "5000",
            confidence="0.89",
        )
        mismatch = building_statement(
            2026,
            3,
            [ExpenseLine("Agua", Decimal("5000"))],
            [UnitSettlement("UF 1", Decimal("10000"))],
            "5002",
        )
        self.assertTrue(accepted.ready_for_auto_publication)
        self.assertFalse(low_confidence.ready_for_auto_publication)
        self.assertFalse(mismatch.ready_for_auto_publication)

    def test_repeated_category_rows_aggregate_but_duplicate_source_rows_flag_review(self):
        previous = building_statement(
            2026,
            1,
            [
                ExpenseLine("Electricidad", Decimal("5000"), category="Servicios", source_row="Hoja1!A1"),
                ExpenseLine("Gas", Decimal("10000"), category="Servicios", source_row="Hoja1!A2"),
            ],
            [UnitSettlement("UF 1", Decimal("15000"))],
            "15000",
        )
        current = building_statement(
            2026,
            2,
            [
                ExpenseLine("Electricidad", Decimal("6000"), category="Servicios", source_row="Hoja1!A1"),
                ExpenseLine("Gas", Decimal("10000"), category="Servicios", source_row="Hoja1!A2"),
            ],
            [UnitSettlement("UF 1", Decimal("16000"))],
            "16000",
        )
        result = compare_building_statements(previous, current)
        self.assertEqual(len(result.line_changes), 1)
        self.assertEqual(result.line_changes[0].difference, Decimal("1000"))
        self.assertFalse(result.needs_review)

        duplicate_row = building_statement(
            2026,
            2,
            [
                ExpenseLine("Electricidad", Decimal("6000"), category="Servicios", source_row="Hoja1!A1"),
                ExpenseLine("Gas", Decimal("10000"), category="Servicios", source_row="Hoja1!A1"),
            ],
            [UnitSettlement("UF 1", Decimal("16000"))],
            "16000",
        )
        self.assertTrue(compare_building_statements(previous, duplicate_row).needs_review)

    def test_compares_expense_categories_and_unit_amounts_separately(self):
        previous = building_statement(
            2026,
            1,
            [
                ExpenseLine("Limpieza", Decimal("10000"), category="Limpieza", kind=ExpenseKind.RECURRING),
                ExpenseLine("Ascensor", Decimal("5000"), category="Mantenimiento", kind=ExpenseKind.RECURRING),
            ],
            [UnitSettlement("UF 4B", Decimal("40000"), arrears=Decimal("2000"))],
            "15000",
        )
        current = building_statement(
            2026,
            2,
            [
                ExpenseLine("LIMPIEZA", Decimal("12500"), category="limpieza", kind=ExpenseKind.RECURRING),
                ExpenseLine("Ascensor", Decimal("7000"), category="Mantenimiento", kind=ExpenseKind.RECURRING),
            ],
            [UnitSettlement("uf 4b", Decimal("47000"), arrears=Decimal("8000"))],
            "19500",
        )
        result = compare_building_statements(previous, current)
        self.assertEqual(result.total_change.difference, Decimal("4500"))
        self.assertEqual(result.unit_changes[0].difference, Decimal("7000"))
        self.assertEqual(result.unit_changes[0].current_arrears, Decimal("8000"))
        self.assertEqual(result.largest_increases[0].difference, Decimal("2500"))
        self.assertFalse(result.needs_review)

    def test_unmatched_categories_and_total_mismatch_require_review(self):
        previous = building_statement(
            2026,
            1,
            [ExpenseLine("Agua", Decimal("5000"))],
            [UnitSettlement("UF 1", Decimal("10000"))],
            "5000",
        )
        current = building_statement(
            2026,
            2,
            [ExpenseLine("Gas", Decimal("6000"))],
            [UnitSettlement("UF 1", Decimal("12000"))],
            "9000",
        )
        result = compare_building_statements(previous, current)
        self.assertTrue(result.needs_review)
        self.assertEqual(result.unmatched_previous_lines, ("Agua",))
        self.assertEqual(result.unmatched_current_lines, ("Gas",))

    def test_rejects_duplicate_unit_rows_and_nonconsecutive_periods(self):
        with self.assertRaises(ValueError):
            building_statement(
                2026,
                1,
                [],
                [UnitSettlement("UF 1", Decimal("100")), UnitSettlement("uf 1", Decimal("200"))],
                "0",
            )
        january = building_statement(2026, 1, [], [], "0")
        march = building_statement(2026, 3, [], [], "0")
        with self.assertRaises(ValueError):
            compare_building_statements(january, march)
