// btc-cent-forecast-01 entry: 4-hour-ahead BTC price forecast (Node 22, stdlib only).
//
// Model: damped mean reversion toward the 24-hour EMA of log prices.
//   - Work in log space. Let `last` be the checkpoint close and `ema` the
//     24-hour (1440-minute) exponential moving average of log closes.
//   - Deviation d = last - ema. Small deviations (|d| <= 0.2%) are noise, so
//     a deadband removes them; only the excess reverts, at 45% over 4 hours:
//         move = -0.45 * sign(d) * max(0, |d| - 0.002)
//   - The move is capped at +/-2% so one wild deviation never produces a
//     wild guess. Guess = exp(last + move), rounded to the grid's 5 decimals.
//   - If the price sits at its 24h mean, the guess is the checkpoint close
//     (persistence), which is the safe fallback.
//
// Why this shape: on 66 pseudo-checkpoints cut from the kit's practice
// series (every 4h inside the 72h windows), this scores ~38,300 cents mean
// absolute error vs ~40,950 for pure persistence (-6%); on the 5 scorable
// real practice cases (a one-day downtrend) it scores ~48,500 vs ~47,100
// for persistence (+3%) — a small cost in a trending regime for a larger
// gain in a ranging one. Momentum and trend extrapolation were tested and
// made both sets worse, so they are not used.
//
// Tuning (measured on the kit's practice data, 2026-11-15):
//   - 66 pseudo-checkpoints cut every 4h inside the practice series:
//     this model ~38,300 cents mean absolute error vs ~40,950 persistence.
//   - 5 scorable real practice cases p00-p04 (a downtrend day):
//     ~48,500 vs ~47,100 persistence — the cost of reverting in a trend.
//   - EMA spans 720/1080/2160/2880 and momentum/trend terms were all tried
//     and scored worse on the pseudo set; the 24h EMA won.
//   - The deadband matters: without it the real-practice cost was ~52,300.

import { mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const INPUT_DIR = process.env.MAKEFUN_INPUT_DIR ?? '/input';
const OUTPUT_DIR = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

/** The smallest positive price on the grid: one unit of its 5 decimals. */
const MIN_PRICE = 0.00001;
/** The largest grid price below the scorer's exclusive 10,000,000-dollar cap. */
const MAX_PRICE = 9_999_999.99999;

/** EMA span in minutes: 1440 = 24 hours. */
const EMA_SPAN = 1440;
/** Fraction of the (deadbanded) deviation expected to revert in 4 hours. */
const REVERT = 0.45;
/** Deviations smaller than this (in log points) are treated as noise. */
const DEADBAND = 0.002;
/** Largest log move the forecast is allowed to make, either way. */
const MAX_MOVE = 0.02;

interface CaseMarket {
  id: string;
  prices: number[];
}

interface Case {
  markets: CaseMarket[];
}

/** x kept on the grid's 5 decimals and inside the scorer's (0, 10,000,000). */
const price5 = (x: number): number => Math.round(Math.min(MAX_PRICE, Math.max(MIN_PRICE, x)) * 1e5) / 1e5;

/** EMA of a log-price series, seeded with its first value. */
function emaLast(logPrices: number[], span: number): number {
  const a = 2 / (span + 1);
  let e = logPrices[0] as number;
  for (let i = 1; i < logPrices.length; i++) {
    e = a * (logPrices[i] as number) + (1 - a) * e;
  }
  return e;
}

/** The 4-hour-ahead forecast for one market, in dollars. */
function forecast(m: CaseMarket): number {
  if (!Array.isArray(m.prices) || m.prices.length === 0) throw new Error(`market ${m.id} has no prices`);
  const logPrices = m.prices.map((p) => {
    if (typeof p !== 'number' || !Number.isFinite(p) || p <= 0) throw new Error(`market ${m.id} has a bad price`);
    return Math.log(p);
  });
  const last = logPrices[logPrices.length - 1] as number;
  const mean = emaLast(logPrices, EMA_SPAN);
  let d = last - mean;
  if (Math.abs(d) <= DEADBAND) d = 0;
  else d = Math.sign(d) * (Math.abs(d) - DEADBAND);
  let move = -REVERT * d;
  if (move > MAX_MOVE) move = MAX_MOVE;
  if (move < -MAX_MOVE) move = -MAX_MOVE;
  return price5(Math.exp(last + move));
}

mkdirSync(OUTPUT_DIR, { recursive: true });
// Every case file, in name order, so two runs write the same bytes.
const inputs = readdirSync(INPUT_DIR).filter((f) => f.endsWith('.in')).sort();
for (const file of inputs) {
  const id = file.slice(0, -'.in'.length);
  const c = JSON.parse(readFileSync(join(INPUT_DIR, file), 'utf8')) as Case;
  if (!Array.isArray(c.markets) || c.markets.length !== 1) throw new Error(`${file} does not hold exactly one market`);
  writeFileSync(join(OUTPUT_DIR, `${id}.out`), `${JSON.stringify({ forecasts: [{ case: id, price: forecast(c.markets[0] as CaseMarket) }] })}\n`);
}
