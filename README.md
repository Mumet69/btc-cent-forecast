# btc-cent-forecast-01

Guess BTC's USD price 240 minutes after each checkpoint, from the 72 hours
of 1-minute closes up to the checkpoint.

Model: last price x the mean of the 48h and 72h log-linear trend drift
factors (OLS slope on log prices, extrapolated 240 minutes), drift capped
at +/-0.5% of the last price. Stdlib only, deterministic, no network.

Practice (mean absolute error, cents): persistence baseline 47,055 vs this
model 41,201 over the 5 exactly-scored cases (-12.4%); beats persistence
in 4 of 5 cases. See `main.py` docstring for the full practice table.

Run: `MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py`
