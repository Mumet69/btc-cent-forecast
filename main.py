#!/usr/bin/env python3
"""btc-cent-forecast-01 entry: guess BTC's USD price 240 minutes after each
checkpoint, from the 72 hours of 1-minute closes up to the checkpoint.

Model (chosen on the 6 practice cases, verified independently):
  guess = last price * exp(mean of two log-linear trend slopes x 240 min)
  where the slopes are the OLS log-price trends over the last 48h (2880 min)
  and the last 72h (4320 min), averaged. Drifts are small (~$100 on the
  practice window) and the drift is capped at +/-0.5% of the last price.

Practice results (mean absolute error, cents; lower better):
  persistence (house baseline): 47,055 over the 5 exactly-scored cases
  this model:                   41,201 over the same 5 cases (-12.4%)
  per-case MAE cents: p00 21,548 / p01 67,202 / p02 37,840 / p03 67,052 /
  p04 12,361 (p05 scored 40,027 against a Coinbase BTC-USD proxy answer,
  which differs from the Orca recording by $10-50 at the checked minutes,
  so p05 is approximate). The model beats persistence in 4 of the 5 exact
  cases; the one loss is p03 (+$567 actual move against the downtrend).

Why this model and not a sharper one: with only 6 practice cases, the
differences among the top trend variants (41,026-41,781 cents) are noise.
Averaging the 48h and 72h trend slopes removes the arbitrary window choice
without adding a fitted constant. No level is hard-coded, so the model
adapts to whatever price regime the final window is in; the 0.5% drift cap
bounds the damage if the trend reverses.

Stdlib only, deterministic: pure function of the input file, no randomness,
no timestamps, no network. Reads every <id>.in in the input directory and
writes <id>.out per case: {"forecasts": [{"case": "<id>", "price": <n>}]}.
"""
import json
import math
import os

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

MIN_PRICE = 0.00001
MAX_PRICE = 9_999_999.99999
HORIZON_MIN = 240
DRIFT_CAP_FRAC = 0.005  # +/-0.5% of the last price


def price5(x):
    """Keep x on the grid's 5 decimals and inside the scorer's (0, 10M)."""
    return round(min(MAX_PRICE, max(MIN_PRICE, x)) * 1e5) / 1e5


def log_trend_drift(prices, window):
    """Log-linear OLS slope over the last `window` minutes, x 240 min.

    Returns the multiplicative drift factor exp(slope * 240). Uses at most
    the prices available when the window is longer than the history.
    """
    xs = prices[-window:]
    n = len(xs)
    if n < 2:
        return 1.0
    lx = [math.log(v) for v in xs]
    mx = (n - 1) / 2.0
    my = sum(lx) / n
    num = 0.0
    den = 0.0
    for i, v in enumerate(lx):
        d = i - mx
        num += d * (v - my)
        den += d * d
    slope = num / den if den else 0.0
    return math.exp(slope * HORIZON_MIN)


def forecast(prices):
    """One price guess for one case's 1-minute close history."""
    if not prices:
        raise ValueError("empty price history")
    last = prices[-1]
    if not (isinstance(last, (int, float)) and math.isfinite(last)) or last <= 0:
        raise ValueError("last price is not a positive finite number")
    # Average of the 48h and 72h log-trend drift factors.
    drift = (log_trend_drift(prices, 2880) + log_trend_drift(prices, 4320)) / 2.0
    # Cap the drift at +/-0.5% of the last price (bounds reversal damage).
    drift = min(max(drift, 1.0 - DRIFT_CAP_FRAC), 1.0 + DRIFT_CAP_FRAC)
    return price5(last * drift)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for name in sorted(os.listdir(INPUT_DIR)):
        if not name.endswith(".in"):
            continue
        case_id = name[:-3]
        with open(os.path.join(INPUT_DIR, name), "r", encoding="utf-8") as f:
            case = json.load(f)
        markets = case["markets"]
        if len(markets) != 1:
            raise ValueError(f"case {case_id}: expected 1 market, got {len(markets)}")
        guess = forecast(markets[0]["prices"])
        out = {"forecasts": [{"case": case_id, "price": guess}]}
        with open(os.path.join(OUTPUT_DIR, case_id + ".out"), "w", encoding="utf-8") as f:
            json.dump(out, f)
            f.write("\n")


if __name__ == "__main__":
    main()
