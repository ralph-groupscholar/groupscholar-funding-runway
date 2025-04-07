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
                    depletion_balance NUMERIC(14,2) NOT NULL,
                    depletion_month TEXT NOT NULL,
                    depletion_month_index INTEGER NOT NULL,
                    peak_inflow NUMERIC(14,2) NOT NULL,
                    peak_inflow_month TEXT NOT NULL,
                    peak_outflow NUMERIC(14,2) NOT NULL,
                    peak_outflow_month TEXT NOT NULL,
                    deficit_months INTEGER NOT NULL,
                    best_net_value NUMERIC(14,2) NOT NULL,
                    best_net_month TEXT NOT NULL,
                    worst_net_value NUMERIC(14,2) NOT NULL,
                    worst_net_month TEXT NOT NULL,
                    longest_deficit_streak INTEGER NOT NULL,
                    longest_deficit_start TEXT NOT NULL,
                    longest_deficit_end TEXT NOT NULL,
                    largest_net_swing_abs NUMERIC(14,2) NOT NULL,
                    largest_net_swing_delta NUMERIC(14,2) NOT NULL,
                    largest_net_swing_month TEXT NOT NULL,
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
                    net_trend_delta NUMERIC(14,2) NOT NULL,
                    breakeven_gap NUMERIC(14,2) NOT NULL,
                    breakeven_inflow_pct NUMERIC(14,2) NOT NULL,
                    breakeven_outflow_pct NUMERIC(14,2) NOT NULL,
                    target_runway_months NUMERIC(6,2) NOT NULL,
                    target_cash NUMERIC(14,2) NOT NULL,
                    funding_gap NUMERIC(14,2) NOT NULL,
                    inflow_hhi NUMERIC(8,6) NOT NULL,
                    outflow_hhi NUMERIC(8,6) NOT NULL,
                    top_inflow_share_pct NUMERIC(6,2) NOT NULL,
                    top_outflow_share_pct NUMERIC(6,2) NOT NULL
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
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS depletion_balance NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS depletion_month TEXT NOT NULL DEFAULT ''"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS depletion_month_index INTEGER NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS peak_inflow NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS peak_inflow_month TEXT NOT NULL DEFAULT ''"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS peak_outflow NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS peak_outflow_month TEXT NOT NULL DEFAULT ''"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS deficit_months INTEGER NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS best_net_value NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS best_net_month TEXT NOT NULL DEFAULT ''"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS worst_net_value NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS worst_net_month TEXT NOT NULL DEFAULT ''"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS longest_deficit_streak INTEGER NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS longest_deficit_start TEXT NOT NULL DEFAULT ''"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS longest_deficit_end TEXT NOT NULL DEFAULT ''"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS largest_net_swing_abs NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS largest_net_swing_delta NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS largest_net_swing_month TEXT NOT NULL DEFAULT ''"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS avg_inflow NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS avg_outflow NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS avg_net NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS net_volatility NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS outflow_coverage_months NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS restricted_outflow_total NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS recent_avg_net NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS prior_avg_net NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS net_trend_delta NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS breakeven_gap NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS breakeven_inflow_pct NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS breakeven_outflow_pct NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS target_runway_months NUMERIC(6,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS target_cash NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS funding_gap NUMERIC(14,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS inflow_hhi NUMERIC(8,6) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS outflow_hhi NUMERIC(8,6) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS top_inflow_share_pct NUMERIC(6,2) NOT NULL DEFAULT 0"))
        conn.execute(text(f"ALTER TABLE {schema}.runway_snapshots ADD COLUMN IF NOT EXISTS top_outflow_share_pct NUMERIC(6,2) NOT NULL DEFAULT 0"))
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
        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {schema}.runway_scenarios (
                    snapshot_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    inflow_adj_pct NUMERIC(6,2) NOT NULL,
                    outflow_adj_pct NUMERIC(6,2) NOT NULL,
                    projected_net NUMERIC(14,2) NOT NULL,
                    projected_runway_months NUMERIC(14,2) NOT NULL,
                    risk TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {schema}.runway_top_inflow_categories (
                    snapshot_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    inflow NUMERIC(14,2) NOT NULL,
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
    breakeven = payload.get("breakeven", {})
    targets = payload.get("targets", {})
    concentration = payload.get("concentration", {})

    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                INSERT INTO {schema}.runway_snapshots (
                    id, created_at, as_of, records, months, skipped,
                    total_inflow, total_outflow, net,
                    starting_cash, reserved_cash, available_cash,
                    ending_cash, lowest_cash, lowest_cash_month,
                    depletion_balance, depletion_month, depletion_month_index,
                    peak_inflow, peak_inflow_month, peak_outflow, peak_outflow_month,
                    deficit_months,
                    best_net_value, best_net_month, worst_net_value, worst_net_month,
                    longest_deficit_streak, longest_deficit_start, longest_deficit_end,
                    largest_net_swing_abs, largest_net_swing_delta, largest_net_swing_month,
                    avg_burn, burn_months, runway_months, runway_risk, window_months,
                    avg_inflow, avg_outflow, avg_net, net_volatility,
                    outflow_coverage_months, restricted_outflow_total,
                    recent_avg_net, prior_avg_net, net_trend_delta,
                    breakeven_gap, breakeven_inflow_pct, breakeven_outflow_pct,
                    target_runway_months, target_cash, funding_gap,
                    inflow_hhi, outflow_hhi, top_inflow_share_pct, top_outflow_share_pct
                ) VALUES (
                    :id, :created_at, :as_of, :records, :months, :skipped,
                    :total_inflow, :total_outflow, :net,
                    :starting_cash, :reserved_cash, :available_cash,
                    :ending_cash, :lowest_cash, :lowest_cash_month,
                    :depletion_balance, :depletion_month, :depletion_month_index,
                    :peak_inflow, :peak_inflow_month, :peak_outflow, :peak_outflow_month,
                    :deficit_months,
                    :best_net_value, :best_net_month, :worst_net_value, :worst_net_month,
                    :longest_deficit_streak, :longest_deficit_start, :longest_deficit_end,
                    :largest_net_swing_abs, :largest_net_swing_delta, :largest_net_swing_month,
                    :avg_burn, :burn_months, :runway_months, :runway_risk, :window_months,
                    :avg_inflow, :avg_outflow, :avg_net, :net_volatility,
                    :outflow_coverage_months, :restricted_outflow_total,
                    :recent_avg_net, :prior_avg_net, :net_trend_delta,
                    :breakeven_gap, :breakeven_inflow_pct, :breakeven_outflow_pct,
                    :target_runway_months, :target_cash, :funding_gap,
                    :inflow_hhi, :outflow_hhi, :top_inflow_share_pct, :top_outflow_share_pct
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
                "depletion_balance": cash_flow.get("depletion_balance", 0),
                "depletion_month": cash_flow.get("depletion_month", ""),
                "depletion_month_index": cash_flow.get("depletion_month_index", 0),
                "peak_inflow": cash_flow.get("peak_inflow", 0),
                "peak_inflow_month": cash_flow.get("peak_inflow_month", ""),
                "peak_outflow": cash_flow.get("peak_outflow", 0),
                "peak_outflow_month": cash_flow.get("peak_outflow_month", ""),
                "deficit_months": cash_flow.get("deficit_months", 0),
                "best_net_value": payload.get("net_extremes", {}).get("best_value", 0),
                "best_net_month": payload.get("net_extremes", {}).get("best_month", ""),
                "worst_net_value": payload.get("net_extremes", {}).get("worst_value", 0),
                "worst_net_month": payload.get("net_extremes", {}).get("worst_month", ""),
                "longest_deficit_streak": payload.get("deficit_streak", {}).get("longest_months", 0),
                "longest_deficit_start": payload.get("deficit_streak", {}).get("start_month", ""),
                "longest_deficit_end": payload.get("deficit_streak", {}).get("end_month", ""),
                "largest_net_swing_abs": payload.get("net_swing", {}).get("largest_abs", 0),
                "largest_net_swing_delta": payload.get("net_swing", {}).get("largest_delta", 0),
                "largest_net_swing_month": payload.get("net_swing", {}).get("largest_month", ""),
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
                "breakeven_gap": breakeven.get("gap", 0),
                "breakeven_inflow_pct": breakeven.get("inflow_lift_pct", 0),
                "breakeven_outflow_pct": breakeven.get("outflow_cut_pct", 0),
                "target_runway_months": targets.get("runway_months", 0),
                "target_cash": targets.get("target_cash", 0),
                "funding_gap": targets.get("funding_gap", 0),
                "inflow_hhi": concentration.get("inflow_hhi", 0),
                "outflow_hhi": concentration.get("outflow_hhi", 0),
                "top_inflow_share_pct": concentration.get("top_inflow_share_pct", 0),
                "top_outflow_share_pct": concentration.get("top_outflow_share_pct", 0),
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

        for category in payload.get("top_inflow_categories", []):
            conn.execute(
                text(
                    f"""
                    INSERT INTO {schema}.runway_top_inflow_categories (
                        snapshot_id, category, inflow, count
                    ) VALUES (
                        :snapshot_id, :category, :inflow, :count
                    )
                    """
                ),
                {
                    "snapshot_id": snapshot_id,
                    "category": category.get("category"),
                    "inflow": category.get("inflow", 0),
                    "count": category.get("count", 0),
                },
            )

        for scenario in payload.get("scenarios", []):
            conn.execute(
                text(
                    f"""
                    INSERT INTO {schema}.runway_scenarios (
                        snapshot_id, name, inflow_adj_pct, outflow_adj_pct,
                        projected_net, projected_runway_months, risk
                    ) VALUES (
                        :snapshot_id, :name, :inflow_adj_pct, :outflow_adj_pct,
                        :projected_net, :projected_runway_months, :risk
                    )
                    """
                ),
                {
                    "snapshot_id": snapshot_id,
                    "name": scenario.get("name"),
                    "inflow_adj_pct": scenario.get("inflow_adj_pct", 0),
                    "outflow_adj_pct": scenario.get("outflow_adj_pct", 0),
                    "projected_net": scenario.get("projected_net", 0),
                    "projected_runway_months": scenario.get("projected_runway_months", 0),
                    "risk": scenario.get("risk", "not_at_risk"),
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
