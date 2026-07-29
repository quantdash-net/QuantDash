# Screening methodology

## Scope

Use this methodology to rank research candidates before the A-share open. It
does not estimate future returns and does not replace fundamental, news,
compliance, or suitability review.

The script uses only fields documented by the public QuantDash Python SDK:

- `quotes.get(universes="CN_Stock", to_dataframe=True)` for the latest quote
  snapshot;
- `klines.batch(..., period="1d", count=21, adjust="forward",
  to_dataframe=True)` for recent daily history.

QuantDash documentation: <https://docs.quantdash.net/zh-Hans/sdk/python-quickstart>

## Default pipeline

1. Fetch the `CN_Stock` quote universe.
2. Reject invalid prices, excessive gaps, and names containing `ST`, `*ST`, or
   `退`, unless the user explicitly includes risk labels.
3. Prefilter the 300 highest-amount symbols to limit API usage.
4. Fetch 21 forward-adjusted daily bars for the prefiltered symbols.
5. Require at least six usable daily closes.
6. Apply the default filters:

   | Filter | Default |
   | --- | ---: |
   | Minimum price | CNY 2 |
   | Minimum 20-day average amount | CNY 50 million |
   | Gap versus previous close | -3% to 5% |
   | Five-day return | -8% to 15% |
   | Maximum 20-day daily volatility | 6% |

7. Rank the survivors with a 0–100 composite score:

   | Component | Weight | Direction |
   | --- | ---: | --- |
   | 20-day average amount | 40% | Higher is better |
   | Five-day return | 30% | Higher within the filter is better |
   | 20-day daily volatility | 20% | Lower is better |
   | Gap quality | 10% | Closer to the 1% target is better |

The weights and thresholds are transparent defaults for candidate generation,
not universally optimal trading parameters.

## Metric definitions

- `gap_pct = (last_price / prev_close - 1) * 100`
- `avg_amount_20d`: mean daily traded amount over up to 20 recent bars
- `return_5d_pct`: percentage change from the close six bars ago to the latest
  close
- `return_20d_pct`: percentage change from the close 21 bars ago when available
- `volatility_20d_pct`: population standard deviation of up to 20 daily close
  returns, expressed as a percentage
- factor component scores: cross-sectional percentile ranks after filtering

## Timing and data-quality checks

The Shanghai Stock Exchange describes 09:15–09:25 as the opening call auction
and 09:30 as the start of continuous trading:
<https://one.sse.com.cn/onething/gptz/>

Always report the quote snapshot's `trade_date` and `trade_time`.

- Before the auction, `last_price` may still represent the prior session.
- During the auction, a quote snapshot can change quickly.
- After continuous trading begins, describe the output as an intraday screen,
  not a premarket screen.
- A `last_price` gap is not an order-book imbalance signal. The documented
  quote response does not expose virtual matched or unmatched auction volume.
- Zero or stale amount values can distort quote prefiltering. Increase
  `--prefilter` or use offline, audited inputs when necessary.

## Interpretation

Explain why each candidate survived using its displayed factor values. Do not
convert the composite score into a probability, target price, or expected
return. Review corporate actions, suspensions, announcements, liquidity
constraints, and data entitlements separately before any trading decision.
