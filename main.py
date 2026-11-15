#!/usr/bin/env python3
"""Forecast Bitcoin's US-dollar price 240 minutes after a checkpoint.

Reads one case at a time: 4,320 one-minute closes of BTC (cbBTC/USDC) covering
the 72 hours up to the checkpoint, and writes a single forecast price.

Model: the last price times the average of two log-linear drift factors.
Each drift factor extrapolates the ordinary-least-squares slope of log-price
over a trailing window 240 minutes forward:

    drift = exp(slope * 240)

The two windows are the last 48 hours (2,880 closes) and the full 72 hours
(4,320 closes). The forecast is clamped to the last price +/- 0.5%, so the
program never guesses a move larger than half a percent in four hours.

Standard library only. Deterministic: the same case always yields the same
forecast, byte for byte.
"""

import json
import math
import os
import sys

HORIZON_MINUTES = 240
WINDOW_48H = 48 * 60
WINDOW_72H = 72 * 60
DRIFT_CAP = 0.005  # +/-0.5% of the last price


def ols_log_slope(prices):
    """OLS slope of log(price) against the minute index, per minute.

    prices is a list of closes in chronological order. Returns the slope of
    the best-fit line through (0, log p0), (1, log p1), ..., (n-1, log pn-1).
    """
    n = len(prices)
    if n < 2:
        return 0.0
    sum_x = n * (n - 1) / 2.0
    sum_xx = (n - 1) * n * (2 * n - 1) / 6.0
    sum_y = 0.0
    sum_xy = 0.0
    for i, price in enumerate(prices):
        y = math.log(price)
        sum_y += y
        sum_xy += i * y
    denom = n * sum_xx - sum_x * sum_x
    if denom == 0.0:
        return 0.0
    return (n * sum_xy - sum_x * sum_y) / denom


def forecast(prices):
    """Forecast the price HORIZON_MINUTES after the last close in prices."""
    last = prices[-1]
    slope_48h = ols_log_slope(prices[-WINDOW_48H:])
    slope_72h = ols_log_slope(prices[-WINDOW_72H:])
    drift_48h = math.exp(slope_48h * HORIZON_MINUTES)
    drift_72h = math.exp(slope_72h * HORIZON_MINUTES)
    guess = last * (drift_48h + drift_72h) / 2.0
    lo = last * (1.0 - DRIFT_CAP)
    hi = last * (1.0 + DRIFT_CAP)
    return min(max(guess, lo), hi)


def main():
    input_dir = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(output_dir, exist_ok=True)
    case_files = sorted(
        name for name in os.listdir(input_dir) if name.endswith(".in")
    )
    if not case_files:
        print("no case files found in %s" % input_dir, file=sys.stderr)
        return 1
    for name in case_files:
        case_id = name[: -len(".in")]
        with open(os.path.join(input_dir, name), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        prices = case["markets"][0]["prices"]
        price = forecast(prices)
        # The price grid itself carries 5 decimals; round the guess to it so
        # the output never claims precision the market data does not have.
        out = {"forecasts": [{"case": case["case"], "price": round(price, 5)}]}
        out_path = os.path.join(output_dir, case_id + ".out")
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(out, fh)
            fh.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
