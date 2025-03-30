#!/usr/bin/env python3
import argparse
import json
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, text


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def ensure_schema(engine, schema: str):
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {schema}.runway_snapshots (
                    id TEXT PRIMARY KEY,
                    created_at TIMESTAMPTZ NOT NULL,
                    as_of TEXT NOT NULL,
                    records INTEGER NOT NULL,
                    months INTEGER NOT NULL,
                    skipped INTEGER NOT NULL,
                    total_inflow NUMERIC(14,2) NOT NULL,
                    total_outflow NUMERIC(14,2) NOT NULL,
                    net NUMERIC(14,2) NOT NULL,
                    starting_cash NUMERIC(14,2) NOT NULL,
                    reserved_cash NUMERIC(14,2) NOT NULL,
                    available_cash NUMERIC(14,2) NOT NULL,
                    ending_cash NUMERIC(14,2) NOT NULL,
                    lowest_cash NUMERIC(14,2) NOT NULL,
                    lowest_cash_month TEXT NOT NULL,
                    deficit_months INTEGER NOT NULL,
                    avg_burn NUMERIC(14,2) NOT NULL,
                    burn_months INTEGER NOT NULL,
                    runway_months NUMERIC(14,2) NOT NULL,
                    runway_risk TEXT NOT NULL,
                    window_months INTEGER NOT NULL,
                    avg_inflow NUMERIC(14,2) NOT NULL,
                    avg_outflow NUMERIC(14,2) NOT NULL,
                    avg_net NUMERIC(14,2) NOT NULL,
                    net_volatility NUMERIC(14,2) NOT NULL,
                    outflow_coverage_months NUMERIC(14,2) NOT NULL,
                    restricted_outflow_total NUMERIC(14,2) NOT NULL,
                    recent_avg_net NUMERIC(14,2) NOT NULL,
                    prior_avg_net NUMERIC(14,2) NOT NULL,
                    net_trend_delta NUMERIC(14,2) NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                f"""
                ALTER TABLE {schema}.runway_snapshots
                ADD COLUMN IF NOT EXISTS runway_risk TEXT NOT NULL DEFAULT 'not_at_risk'
                """
            )
        )
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS ending_cash NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS lowest_cash NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS lowest_cash_month TEXT NOT NULL DEFAULT ''"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS deficit_months INTEGER NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS avg_inflow NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS avg_outflow NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS avg_net NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS net_volatility NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS outflow_coverage_months NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS restricted_outflow_total NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS recent_avg_net NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS prior_avg_net NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS net_trend_delta NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {schema}.runway_recent_months (
                    snapshot_id TEXT NOT NULL,
                    month TEXT NOT NULL,
                    inflow NUMERIC(14,2) NOT NULL,
                    outflow NUMERIC(14,2) NOT NULL,
                    net NUMERIC(14,2) NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {schema}.runway_top_categories (
                    snapshot_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    outflow NUMERIC(14,2) NOT NULL,
                    count INTEGER NOT NULL
                )
                """
            )
        )


def insert_snapshot(engine, schema: str, payload: dict):
    snapshot_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)
    totals = payload.get("totals", {})
    cash = payload.get("cash", {})
    cash_flow = payload.get("cash_flow", {})
    burn = payload.get("burn", {})
    flows = payload.get("flows", {})
    net = payload.get("net", {})
    trend = payload.get("net_trend", {})
    restricted = payload.get("restricted", {})

    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                INSERT INTO {schema}.runway_snapshots (
                    id, created_at, as_of, records, months, skipped,
                    total_inflow, total_outflow, net,
                    starting_cash, reserved_cash, available_cash,
                    ending_cash, lowest_cash, lowest_cash_month, deficit_months,
                    avg_burn, burn_months, runway_months, runway_risk, window_months,
                    avg_inflow, avg_outflow, avg_net, net_volatility,
                    outflow_coverage_months, restricted_outflow_total,
                    recent_avg_net, prior_avg_net, net_trend_delta
                ) VALUES (
                    :id, :created_at, :as_of, :records, :months, :skipped,
                    :total_inflow, :total_outflow, :net,
                    :starting_cash, :reserved_cash, :available_cash,
                    :ending_cash, :lowest_cash, :lowest_cash_month, :deficit_months,
                    :avg_burn, :burn_months, :runway_months, :runway_risk, :window_months,
                    :avg_inflow, :avg_outflow, :avg_net, :net_volatility,
                    :outflow_coverage_months, :restricted_outflow_total,
                    :recent_avg_net, :prior_avg_net, :net_trend_delta
                )
                """
            ),
            {
                "id": snapshot_id,
                "created_at": created_at,
                "as_of": payload.get("as_of", ""),
                "records": payload.get("records", 0),
                "months": payload.get("months", 0),
                "skipped": payload.get("skipped", 0),
                "total_inflow": totals.get("inflow", 0),
                "total_outflow": totals.get("outflow", 0),
                "net": totals.get("net", 0),
                "starting_cash": cash.get("starting", 0),
                "reserved_cash": cash.get("reserved", 0),
                "available_cash": cash.get("available", 0),
                "ending_cash": cash_flow.get("ending_balance", 0),
                "lowest_cash": cash_flow.get("lowest_balance", 0),
                "lowest_cash_month": cash_flow.get("lowest_balance_month", ""),
                "deficit_months": cash_flow.get("deficit_months", 0),
                "avg_burn": burn.get("average_monthly", 0),
                "burn_months": burn.get("months_used", 0),
                "runway_months": burn.get("estimated_runway_months", 0),
                "runway_risk": payload.get("runway_risk", "not_at_risk"),
                "window_months": payload.get("window_months", 0),
                "avg_inflow": flows.get("average_inflow", 0),
                "avg_outflow": flows.get("average_outflow", 0),
                "avg_net": net.get("average_monthly", 0),
                "net_volatility": net.get("volatility", 0),
                "outflow_coverage_months": flows.get("outflow_coverage_months", 0),
                "restricted_outflow_total": restricted.get("outflow_total", 0),
                "recent_avg_net": trend.get("recent_average", 0),
                "prior_avg_net": trend.get("prior_average", 0),
                "net_trend_delta": trend.get("delta", 0),
            },
        )

        for month in payload.get("recent_months", []):
            conn.execute(
                text(
                    f"""
                    INSERT INTO {schema}.runway_recent_months (
                        snapshot_id, month, inflow, outflow, net
                    ) VALUES (
                        :snapshot_id, :month, :inflow, :outflow, :net
                    )
                    """
                ),
                {
                    "snapshot_id": snapshot_id,
                    "month": month.get("month"),
                    "inflow": month.get("inflow", 0),
                    "outflow": month.get("outflow", 0),
                    "net": month.get("net", 0),
                },
            )

        for category in payload.get("top_categories", []):
            conn.execute(
                text(
                    f"""
                    INSERT INTO {schema}.runway_top_categories (
                        snapshot_id, category, outflow, count
                    ) VALUES (
                        :snapshot_id, :category, :outflow, :count
                    )
                    """
                ),
                {
                    "snapshot_id": snapshot_id,
                    "category": category.get("category"),
                    "outflow": category.get("outflow", 0),
                    "count": category.get("count", 0),
                },
            )

    return snapshot_id


def main():
    parser = argparse.ArgumentParser(description="Load a funding runway JSON report into Postgres.")
    parser.add_argument("--json", required=True, help="Path to JSON report from funding-runway")
    parser.add_argument("--schema", default="gs_funding_runway", help="Schema for tables")
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    payload = load_json(args.json)
    engine = create_engine(database_url)

    ensure_schema(engine, args.schema)
    snapshot_id = insert_snapshot(engine, args.schema, payload)
    print(f"Inserted snapshot {snapshot_id} into schema {args.schema}.")


if __name__ == "__main__":
    main()
