#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "funding-runway")
SAMPLE = os.path.join(ROOT, "samples", "runway_sample.csv")


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    run(["make", "-C", ROOT])
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "report.json")
        run(
            [
                BIN,
                "--file",
                SAMPLE,
                "--starting-cash",
                "450000",
                "--reserved-cash",
                "60000",
                "--window",
                "6",
                "--json",
                out_path,
            ]
        )
        with open(out_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)

    cash_flow = payload.get("cash_flow", {})
    assert "depletion_month" in cash_flow
    assert "depletion_balance" in cash_flow
    assert "depletion_month_index" in cash_flow
    assert payload.get("net_extremes", {}).get("best_month") is not None
    assert payload.get("deficit_streak", {}).get("longest_months") is not None
    assert payload.get("net_swing", {}).get("largest_abs") is not None
    assert payload.get("totals", {}).get("inflow") is not None
    assert payload.get("runway_risk")
    print("ok")


if __name__ == "__main__":
    main()
