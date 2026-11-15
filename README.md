# BTC cent forecast — 4-hour-ahead Bitcoin price forecast

Entry for make.fun competition `btc-cent-forecast-01`: read BTC's last 72 hours
of 1-minute closes up to a checkpoint and forecast the close 240 minutes later.

## Model

Damped mean reversion toward the 24-hour EMA of log prices (see the header
comment in `main.ts` for the full reasoning and the local test numbers):

- deviation `d = last log close − 24h EMA`
- deadband 0.2% (smaller deviations are noise)
- 45% of the excess deviation reverts over 4 hours
- forecast move capped at ±2%

If the price sits at its 24h mean the guess is the checkpoint close
(persistence). Momentum and trend extrapolation were tested on the practice
data and made the score worse, so they are not used.

## Local results (practice data)

- 66 pseudo-checkpoints cut from the kit's practice series: mean absolute
  error ~38,300 cents vs ~40,950 for pure persistence.
- 5 scorable real practice cases (p00–p04, a downtrend day): ~48,500 cents
  vs ~47,100 for persistence — a small cost in a trending regime for a
  larger gain in a ranging one.

## Run

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out node main.ts
```

Node 22, standard library only, no network, deterministic.
