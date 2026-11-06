# expenses_reader

This repository started as a script that reads Google Sheets in Drive and appends extracted expense rows to another spreadsheet. The new `expenses_reader` package adds a small, dependency-free domain layer for traceable monthly statements and month-over-month comparisons.

## Current core

- `Period`, `ExpenseLine`, and `MonthlyStatement` represent validated statement data and retain the source document ID.
- `compare_statements` compares consecutive months for the same unit, reports peso and percentage changes, matches labels without case or accent differences, and flags missing or ambiguous data for review.
- Amounts use `Decimal` so comparisons do not rely on binary floating-point arithmetic.

The core does not yet ingest PDFs, Excel files, Drive, or Gmail, and it does not provide shared web access. Those integrations need a deployment and authentication setup before they can safely be exposed to neighbors. The original `consorcio.py` remains the legacy importer.

## Run the core checks

```sh
python3 -m unittest discover -s tests -v
```
