---
name: screen-premarket-stocks
description: Screen and rank A-share premarket candidate pools with the QuantDash Python SDK using current quote snapshots and recent daily liquidity, momentum, gap, and volatility metrics. Use when the user asks for 盘前选股、早盘候选池、开盘前筛选、集合竞价后的候选股、A 股 premarket screening, or a reproducible CSV/JSON/Markdown shortlist before the market opens.
---

# Screen Premarket Stocks

Build a reproducible research shortlist from documented QuantDash `quotes` and
`klines` endpoints. Treat the result as a candidate pool, not a buy list or
return prediction.

## Workflow

1. Confirm the market scope, desired result count, and any user-supplied
   liquidity or risk thresholds. Default to `CN_Stock` and 20 candidates.
2. Check that `QUANTDASH_API_KEY` is available without printing its value.
3. Run the bundled script from the repository root:

   ```bash
   python skills/screen-premarket-stocks/scripts/screen_premarket.py \
     --universe CN_Stock \
     --top 20 \
     --output premarket_candidates.csv
   ```

4. Inspect the reported quote snapshot date and time before interpreting the
   ranking. State clearly when the snapshot is stale, pre-auction, or already
   intraday.
5. Present the top candidates with their factor values and applied thresholds.
   Call out missing history, an empty result, or unusually broad/narrow filters.
6. Add a short risk note: this screen excludes news, fundamentals, suspension
   status, order-book imbalance, transaction costs, and user suitability.

Read [references/screening-methodology.md](references/screening-methodology.md)
when explaining or changing the factors, thresholds, scoring, timing, or known
limitations.

## Common commands

Use stricter liquidity and gap limits:

```bash
python skills/screen-premarket-stocks/scripts/screen_premarket.py \
  --min-average-amount 100000000 \
  --min-gap-pct -1 \
  --max-gap-pct 3 \
  --top 10
```

Use saved data for a reproducible or offline run:

```bash
python skills/screen-premarket-stocks/scripts/screen_premarket.py \
  --quotes-csv quotes.csv \
  --klines-csv daily_klines.csv \
  --format markdown
```

Require `quotes.csv` to contain `symbol`, `last_price`, `prev_close`,
`amount`, and `volume`. Require long-format `daily_klines.csv` to contain
`symbol`, `close`, `amount`, and `volume`, plus `trade_date` or `timestamp`.

## Output contract

- Preserve the numeric factors in CSV or JSON output.
- Include `rank`, `symbol`, `name`, `last_price`, `gap_pct`,
  `avg_amount_20d`, `return_5d_pct`, `volatility_20d_pct`, and `score`.
- Report the quote snapshot separately from the generation time.
- Describe the configured filters instead of implying that defaults are
  universally appropriate.
- Say “candidate”, “screen”, or “research shortlist”; do not say “must buy”,
  “guaranteed”, or claim expected returns.

## Guardrails

- Never expose, log, or write the API key into output files.
- Never place trades or send orders.
- Never silently replace unavailable live data with fabricated values.
- Stop with a clear error when required fields are missing.
- Prefer an empty result over weakening filters without telling the user.
