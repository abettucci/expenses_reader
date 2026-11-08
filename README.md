# expenses_reader

This repository started as a script that reads Google Sheets in Drive and appends extracted expense rows to another spreadsheet. The `expenses_reader` package adds a dependency-free domain layer for traceable building statements and month-over-month comparisons.

## Current core

- `BuildingStatement` keeps building expense lines separate from each `UnitSettlement`, including arrears and discounts.
- `Period`, `ExpenseLine`, and `MonthlyStatement` represent statement data and retain the source document ID.
- `compare_building_statements` compares consecutive periods by expense category and unit, reports peso and percentage changes, and flags incomplete extraction, unmatched categories, duplicate units, or totals that differ by more than ARS 1.
- `compare_statements` remains available for unit-to-unit-period comparisons.
- Amounts use `Decimal` so comparisons do not rely on binary floating-point arithmetic.

The package still does not ingest PDFs, Excel files, Drive, or Gmail, and it does not provide shared web access or notifications. The original `consorcio.py` remains the legacy importer. File examples are needed to implement and validate extraction against the actual consorcio format.

## Frontend demo

The `frontend/` directory contains a responsive, static dashboard with illustrative data. Its period selector, navigation, notification panel, and source dialog work locally, but uploads, Gmail, Drive, authentication, and live expense data are not connected. Do not replace the sample data with resident records until the backend access controls are in place.

To deploy it on Vercel, import this repository and set the project root directory to `frontend`. The Vercel configuration runs `npm ci` and `npm run build`, then serves `dist/`. The frontend has no third-party npm dependencies.

## Run the core checks

```sh
python3 -m unittest discover -s tests -v
```
