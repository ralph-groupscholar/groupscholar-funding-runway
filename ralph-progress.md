# groupscholar-funding-runway progress

- 2026-02-08: Added breakeven gap diagnostics (inflow lift/outflow cut) to console + JSON output, extended DB schema for breakeven metrics, and seeded production with a fresh snapshot.
- 2026-02-08: Added runway risk rating to console and JSON output, extended the DB loader schema to store risk, and seeded production with a fresh snapshot.
- 2026-02-08: Added net trend analysis (recent vs prior 3-month average) to console + JSON output, and improved currency parsing/validation for cash inputs.

- 2026-02-08: Added cash balance timeline (ending/lowest balance, deficit months) to console + JSON output; fixed recent-month balance display.

- 2026-02-08: Added outflow category share-of-spend reporting in console/JSON and tightened wording for cash flow diagnostics.
- 2026-02-08: Added peak inflow/outflow month detection plus inflow category concentration to console/JSON, and stored the new fields in production snapshots.
- 2026-02-08: Added average inflow/outflow, net volatility, and outflow coverage metrics to CLI/JSON, and expanded DB loader schema to capture cash-flow + trend diagnostics.
- 2026-02-08: Added cash depletion month detection to CLI/JSON output, extended the DB loader schema for depletion fields, and added a smoke test script.
