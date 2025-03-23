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
                    avg_burn NUMERIC(14,2) NOT NULL,
                    burn_months INTEGER NOT NULL,
                    runway_months NUMERIC(14,2) NOT NULL,
                    window_months INTEGER NOT NULL
                )
                """
            )
        )
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
    burn = payload.get("burn", {})

    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                INSERT INTO {schema}.runway_snapshots (
                    id, created_at, as_of, records, months, skipped,
                    total_inflow, total_outflow, net,
                    starting_cash, reserved_cash, available_cash,
                    avg_burn, burn_months, runway_months, window_months
                ) VALUES (
                    :id, :created_at, :as_of, :records, :months, :skipped,
                    :total_inflow, :total_outflow, :net,
                    :starting_cash, :reserved_cash, :available_cash,
                    :avg_burn, :burn_months, :runway_months, :window_months
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
                "avg_burn": burn.get("average_monthly", 0),
                "burn_months": burn.get("months_used", 0),
                "runway_months": burn.get("estimated_runway_months", 0),
                "window_months": payload.get("window_months", 0),
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
