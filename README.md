# expenses_reader

This repository started as a script that reads Google Sheets in Drive and appends extracted expense rows to another spreadsheet. The `expenses_reader` package adds a dependency-free domain layer for traceable building statements and month-over-month comparisons.

## Current core

- `BuildingStatement` keeps building expense lines separate from each `UnitSettlement`, including arrears and discounts.
- `Period`, `ExpenseLine`, and `MonthlyStatement` represent statement data and retain the source document ID.
- `compare_building_statements` compares consecutive periods by expense category and unit, reports peso and percentage changes, and flags incomplete extraction, unmatched categories, duplicate units, or totals that differ by more than ARS 1.
- `compare_statements` remains available for unit-to-unit-period comparisons.
- Amounts use `Decimal` so comparisons do not rely on binary floating-point arithmetic.

The package still does not ingest files in Python or provide shared web access. The original `consorcio.py` remains the legacy importer. File examples are needed to validate extraction against the actual consorcio format.

## Frontend

The `frontend/` directory contains a responsive dashboard. It can read text PDFs and `.xlsx` workbooks in the browser, show extracted rows for review, and compare consecutive periods. Files are not sent to a server; imported data is kept only in memory and is cleared when the page is refreshed or closed. The parser accepts files up to 15 MB, PDFs up to 80 pages, and workbooks up to 20,000 expense rows. Scanned PDFs need OCR and legacy `.xls` files must be saved as `.xlsx` first.

Google Drive and Gmail are not connected yet because they need OAuth and a backend. “Compartir resumen” opens the device's share sheet when available; it does not send notifications automatically to other residents. The dashboard starts with illustrative sample data and switches to imported periods after a file is analyzed.

The root `vercel.json` builds and publishes `frontend/dist`, so Vercel can use the repository root as its project directory. The parser bundles and matching PDF worker are committed to keep the Vercel build independent of a package registry. See `frontend/VENDOR-NOTICES.md` for included library licenses.

## Run the core checks

```sh
python3 -m unittest discover -s tests -v
```
