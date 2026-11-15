# BTC cent forecast

Forecast Bitcoin's US-dollar price 240 minutes after each checkpoint, from
the last 72 hours of one-minute closes.

## Model

`main.py` (Python 3.13, standard library only) reads each case file from
`$MAKEFUN_INPUT_DIR` (default `/input`) and writes one forecast per case to
`$MAKEFUN_OUTPUT_DIR` (default `/output`) as
`{"forecasts": [{"case": "<id>", "price": <guess>}]}`.

The forecast is the checkpoint's last price times the average of two
log-linear drift factors: each factor extrapolates the OLS slope of log-price
over a trailing window 240 minutes forward (`exp(slope * 240)`), once over
the last 48 hours and once over the full 72 hours. The result is clamped to
the last price +/- 0.5%.

## Practice

On the kit's six practice cases the model scores a mean absolute error of
about 41.2 cents, against the persistence baseline's 47.1 cents (measured
on the five practice cases whose answers are recoverable from the kit data).

## Run locally

```sh
mkdir -p out
MAKEFUN_INPUT_DIR=<kit>/input MAKEFUN_OUTPUT_DIR=out python3 main.py
```
