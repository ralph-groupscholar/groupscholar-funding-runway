# Group Scholar Funding Runway

A focused CLI to estimate runway, burn, and cash posture from transaction CSVs. It summarizes inflow/outflow by month, highlights top spend categories, and can emit JSON for downstream reporting.

## Features
- Flexible CSV parsing (date/amount/type/category/restricted headers)
- Average burn calculation over a configurable window
- Runway estimate based on available cash
- Runway risk rating for quick escalation signals
- Cash balance timeline with lowest-balance alert
- Peak inflow/outflow month detection
- Cash coverage + net volatility diagnostics
- Category concentration (share of inflow/outflow)
- JSON report output for automation
- Optional database loader script for production snapshots

## Build

```sh
make
```

## Usage

```sh
./funding-runway --file samples/runway_sample.csv --starting-cash 450000 --reserved-cash 60000 --window 6 --json runway_report.json
```

Filter by an "as of" month:

```sh
./funding-runway --file samples/runway_sample.csv --starting-cash 450000 --reserved-cash 60000 --window 6 --as-of 2025-12
```

## Database loader (production use)

The loader reads a JSON report and inserts a snapshot into Postgres. It is designed for production usage only (not local dev).

```sh
python3 scripts/runway_db_load.py --json runway_report.json
```

Environment variables:
- `DATABASE_URL` (required)

Optional flags:
- `--schema` to override the schema name (defaults to `gs_funding_runway`)

## Sample data
`samples/runway_sample.csv` contains 12 months of realistic inflow/outflow to test the CLI and seed a production snapshot.

## Tech
- C (CLI)
- Python + SQLAlchemy (database loader)
