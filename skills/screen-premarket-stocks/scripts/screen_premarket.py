"""Rank A-share premarket research candidates with QuantDash market data."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

REQUIRED_QUOTE_COLUMNS = {
    "symbol",
    "last_price",
    "prev_close",
    "amount",
    "volume",
}
REQUIRED_KLINE_COLUMNS = {"symbol", "close", "amount", "volume"}
RESULT_COLUMNS = [
    "rank",
    "symbol",
    "name",
    "last_price",
    "gap_pct",
    "avg_amount_20d",
    "return_5d_pct",
    "return_20d_pct",
    "volatility_20d_pct",
    "liquidity_score",
    "momentum_score",
    "stability_score",
    "gap_score",
    "score",
    "quote_time",
]


@dataclass(frozen=True)
class ScreenConfig:
    """Transparent thresholds for the candidate screen."""

    top: int = 20
    min_price: float = 2.0
    min_average_amount: float = 50_000_000.0
    min_gap_pct: float = -3.0
    max_gap_pct: float = 5.0
    min_return_5d_pct: float = -8.0
    max_return_5d_pct: float = 15.0
    max_volatility_20d_pct: float = 6.0
    include_risk_labels: bool = False
    gap_target_pct: float = 1.0

    def validate(self) -> None:
        """Reject configurations that would make the screen ambiguous."""
        if self.top < 1:
            raise ValueError("--top must be at least 1")
        if self.min_price < 0:
            raise ValueError("--min-price cannot be negative")
        if self.min_average_amount < 0:
            raise ValueError("--min-average-amount cannot be negative")
        if self.min_gap_pct > self.max_gap_pct:
            raise ValueError("--min-gap-pct cannot exceed --max-gap-pct")
        if self.min_return_5d_pct > self.max_return_5d_pct:
            raise ValueError(
                "--min-return-5d-pct cannot exceed --max-return-5d-pct"
            )
        if self.max_volatility_20d_pct < 0:
            raise ValueError("--max-volatility-20d-pct cannot be negative")


def _require_columns(
    frame: pd.DataFrame,
    required: set[str],
    *,
    source: str,
) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{source} is missing required columns: {', '.join(missing)}")


def normalize_quotes(quotes: pd.DataFrame) -> pd.DataFrame:
    """Validate quote fields and derive comparable snapshot metrics."""
    _require_columns(quotes, REQUIRED_QUOTE_COLUMNS, source="quotes")
    frame = quotes.copy()

    numeric_columns = ["last_price", "prev_close", "amount", "volume"]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame["symbol"] = frame["symbol"].astype(str).str.strip()
    if "ext.name" in frame.columns:
        names = frame["ext.name"].fillna("").astype(str).str.strip()
        frame["name"] = names.where(names.ne(""), frame["symbol"])
    elif "name" in frame.columns:
        names = frame["name"].fillna("").astype(str).str.strip()
        frame["name"] = names.where(names.ne(""), frame["symbol"])
    else:
        frame["name"] = frame["symbol"]

    valid_previous_close = frame["prev_close"].where(frame["prev_close"] > 0)
    frame["gap_pct"] = (
        frame["last_price"].div(valid_previous_close).sub(1.0).mul(100.0)
    )

    if "trade_time" in frame.columns:
        frame["quote_time"] = frame["trade_time"].fillna("").astype(str)
    elif "timestamp" in frame.columns:
        timestamps = pd.to_numeric(frame["timestamp"], errors="coerce")
        frame["quote_time"] = (
            pd.to_datetime(
                timestamps,
                unit="ms",
                utc=True,
                errors="coerce",
            )
            .dt.tz_convert("Asia/Shanghai")
            .astype(str)
        )
    else:
        frame["quote_time"] = ""

    return frame


def _apply_quote_filters(
    quotes: pd.DataFrame,
    config: ScreenConfig,
) -> pd.DataFrame:
    frame = normalize_quotes(quotes)
    mask = (
        frame["symbol"].ne("")
        & frame["last_price"].ge(config.min_price)
        & frame["prev_close"].gt(0)
        & frame["gap_pct"].between(config.min_gap_pct, config.max_gap_pct)
    )
    if not config.include_risk_labels:
        risk_names = frame["name"].str.contains(r"(?i)(?:\*?ST|退)", regex=True)
        mask &= ~risk_names
    return frame.loc[mask].copy()


def select_history_symbols(
    quotes: pd.DataFrame,
    config: ScreenConfig,
    *,
    limit: int,
) -> tuple[pd.DataFrame, list[str]]:
    """Prefilter quotes before requesting daily history."""
    filtered = _apply_quote_filters(quotes, config)
    filtered = filtered.sort_values(
        ["amount", "symbol"],
        ascending=[False, True],
        kind="mergesort",
    )
    if limit > 0:
        filtered = filtered.head(limit)
    return filtered, filtered["symbol"].tolist()


def calculate_history_metrics(
    histories: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Calculate recent liquidity, momentum, and volatility by symbol."""
    rows = []
    for symbol, raw_frame in histories.items():
        if raw_frame is None or raw_frame.empty:
            continue

        frame = raw_frame.copy()
        required = {"close", "amount", "volume"}
        if not required.issubset(frame.columns):
            continue

        if "timestamp" in frame.columns:
            frame = frame.sort_values("timestamp", kind="mergesort")
        elif "trade_date" in frame.columns:
            frame = frame.sort_values("trade_date", kind="mergesort")

        for column in required:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame = frame.dropna(subset=["close", "amount", "volume"])
        frame = frame.loc[frame["close"] > 0].tail(21)
        if len(frame) < 6:
            continue

        closes = frame["close"]
        returns = closes.pct_change().dropna()
        recent = frame.tail(20)
        return_20d = (
            (closes.iloc[-1] / closes.iloc[-21] - 1.0) * 100.0
            if len(closes) >= 21
            else float("nan")
        )
        rows.append(
            {
                "symbol": str(symbol),
                "avg_amount_20d": float(recent["amount"].mean()),
                "avg_volume_20d": float(recent["volume"].mean()),
                "return_5d_pct": float(
                    (closes.iloc[-1] / closes.iloc[-6] - 1.0) * 100.0
                ),
                "return_20d_pct": float(return_20d),
                "volatility_20d_pct": float(
                    returns.tail(20).std(ddof=0) * 100.0
                ),
                "history_bars": int(len(frame)),
            }
        )

    return pd.DataFrame(rows)


def _gap_quality(gaps: pd.Series, config: ScreenConfig) -> pd.Series:
    span = max(
        abs(config.min_gap_pct - config.gap_target_pct),
        abs(config.max_gap_pct - config.gap_target_pct),
        1.0,
    )
    return (1.0 - gaps.sub(config.gap_target_pct).abs().div(span)).clip(0.0, 1.0)


def screen_candidates(
    quotes: pd.DataFrame,
    histories: Mapping[str, pd.DataFrame],
    config=None,
) -> pd.DataFrame:
    """Filter and rank candidates without making network requests."""
    config = config or ScreenConfig()
    config.validate()

    filtered_quotes = _apply_quote_filters(quotes, config)
    metrics = calculate_history_metrics(histories)
    if filtered_quotes.empty or metrics.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    candidates = filtered_quotes.merge(metrics, on="symbol", how="inner")
    candidates = candidates.loc[
        candidates["avg_amount_20d"].ge(config.min_average_amount)
        & candidates["return_5d_pct"].between(
            config.min_return_5d_pct,
            config.max_return_5d_pct,
        )
        & candidates["volatility_20d_pct"].le(
            config.max_volatility_20d_pct
        )
    ].copy()
    if candidates.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    candidates["liquidity_score"] = (
        candidates["avg_amount_20d"].rank(method="average", pct=True).mul(100.0)
    )
    candidates["momentum_score"] = (
        candidates["return_5d_pct"].rank(method="average", pct=True).mul(100.0)
    )
    candidates["stability_score"] = (
        candidates["volatility_20d_pct"]
        .rank(method="average", pct=True, ascending=False)
        .mul(100.0)
    )
    candidates["gap_score"] = _gap_quality(candidates["gap_pct"], config).mul(
        100.0
    )
    candidates["score"] = (
        candidates["liquidity_score"].mul(0.40)
        + candidates["momentum_score"].mul(0.30)
        + candidates["stability_score"].mul(0.20)
        + candidates["gap_score"].mul(0.10)
    )

    candidates = candidates.sort_values(
        ["score", "avg_amount_20d", "symbol"],
        ascending=[False, False, True],
        kind="mergesort",
    ).head(config.top)
    candidates.insert(0, "rank", range(1, len(candidates) + 1))

    for column in RESULT_COLUMNS:
        if column not in candidates.columns:
            candidates[column] = ""
    return candidates.loc[:, RESULT_COLUMNS].reset_index(drop=True)


def load_offline_data(
    quotes_path: Path,
    klines_path: Path,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """Load reproducible CSV inputs."""
    quotes = pd.read_csv(quotes_path)
    klines = pd.read_csv(klines_path)
    _require_columns(klines, REQUIRED_KLINE_COLUMNS, source="daily klines")
    if "trade_date" not in klines.columns and "timestamp" not in klines.columns:
        raise ValueError("daily klines require trade_date or timestamp")
    histories = {
        str(symbol): frame.copy()
        for symbol, frame in klines.groupby("symbol", sort=False)
    }
    return quotes, histories


def fetch_live_data(
    *,
    universe: str,
    prefilter: int,
    history_count: int,
    config: ScreenConfig,
    show_progress: bool,
) -> tuple[pd.DataFrame, Mapping[str, pd.DataFrame]]:
    """Fetch documented quote and daily K-line data from QuantDash."""
    if not os.getenv("QUANTDASH_API_KEY"):
        raise ValueError(
            "QUANTDASH_API_KEY is not set; configure it or use both CSV inputs"
        )

    from quantdash import QuantDash

    with QuantDash() as client:
        quotes = client.quotes.get(
            universes=universe,
            to_dataframe=True,
        )
        if quotes is None or quotes.empty:
            raise ValueError(f"quote universe {universe} returned no data")

        _, symbols = select_history_symbols(quotes, config, limit=prefilter)
        if not symbols:
            return quotes, {}

        histories = client.klines.batch(
            symbols,
            period="1d",
            count=history_count,
            adjust="forward",
            to_dataframe=True,
            show_progress=show_progress,
        )
    if not isinstance(histories, Mapping):
        raise ValueError("QuantDash kline batch returned an unexpected result")
    return quotes, histories


def quote_snapshot(quotes: pd.DataFrame) -> str:
    """Return the latest visible quote date/time without inventing one."""
    if quotes.empty:
        return "unknown"
    normalized = normalize_quotes(quotes)
    values = normalized["quote_time"].dropna().astype(str)
    values = values.loc[values.ne("")]
    return values.max() if not values.empty else "unknown"


def _format_markdown_value(column: str, value: object) -> str:
    if pd.isna(value):
        return ""
    if column == "avg_amount_20d":
        return f"{float(value) / 1_000_000:.1f}m"
    if column in {
        "last_price",
        "gap_pct",
        "return_5d_pct",
        "return_20d_pct",
        "volatility_20d_pct",
        "score",
    }:
        return f"{float(value):.2f}"
    return str(value).replace("|", "\\|")


def render_markdown(result: pd.DataFrame) -> str:
    """Render a dependency-free Markdown table."""
    columns = [
        "rank",
        "symbol",
        "name",
        "last_price",
        "gap_pct",
        "avg_amount_20d",
        "return_5d_pct",
        "volatility_20d_pct",
        "score",
        "quote_time",
    ]
    labels = {
        "rank": "Rank",
        "symbol": "Symbol",
        "name": "Name",
        "last_price": "Last",
        "gap_pct": "Gap %",
        "avg_amount_20d": "Avg amount 20d",
        "return_5d_pct": "Return 5d %",
        "volatility_20d_pct": "Volatility 20d %",
        "score": "Score",
        "quote_time": "Quote time",
    }
    header = "| " + " | ".join(labels[column] for column in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = [header, separator]
    for _, row in result.iterrows():
        values = [_format_markdown_value(column, row[column]) for column in columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def serialize_result(result: pd.DataFrame, output_format: str) -> str:
    """Serialize results without losing numeric CSV/JSON fields."""
    if output_format == "csv":
        return result.to_csv(index=False)
    if output_format == "json":
        return result.to_json(orient="records", force_ascii=False, indent=2)
    return render_markdown(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rank A-share premarket research candidates.",
    )
    parser.add_argument("--universe", default="CN_Stock")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument(
        "--prefilter",
        type=int,
        default=300,
        help="Maximum quote symbols to request daily history for; 0 means all.",
    )
    parser.add_argument("--history-count", type=int, default=21)
    parser.add_argument("--min-price", type=float, default=2.0)
    parser.add_argument(
        "--min-average-amount",
        type=float,
        default=50_000_000.0,
    )
    parser.add_argument("--min-gap-pct", type=float, default=-3.0)
    parser.add_argument("--max-gap-pct", type=float, default=5.0)
    parser.add_argument("--min-return-5d-pct", type=float, default=-8.0)
    parser.add_argument("--max-return-5d-pct", type=float, default=15.0)
    parser.add_argument(
        "--max-volatility-20d-pct",
        type=float,
        default=6.0,
    )
    parser.add_argument("--include-risk-labels", action="store_true")
    parser.add_argument("--show-progress", action="store_true")
    parser.add_argument("--quotes-csv", type=Path)
    parser.add_argument("--klines-csv", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--format",
        choices=("csv", "json", "markdown"),
        default="markdown",
    )
    return parser


def _format_from_output(path, fallback: str) -> str:
    if path is None:
        return fallback
    suffixes = {".csv": "csv", ".json": "json", ".md": "markdown"}
    return suffixes.get(path.suffix.lower(), fallback)


def main(argv: Sequence[str] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.prefilter < 0:
            raise ValueError("--prefilter cannot be negative")
        if args.history_count < 6:
            raise ValueError("--history-count must be at least 6")

        config = ScreenConfig(
            top=args.top,
            min_price=args.min_price,
            min_average_amount=args.min_average_amount,
            min_gap_pct=args.min_gap_pct,
            max_gap_pct=args.max_gap_pct,
            min_return_5d_pct=args.min_return_5d_pct,
            max_return_5d_pct=args.max_return_5d_pct,
            max_volatility_20d_pct=args.max_volatility_20d_pct,
            include_risk_labels=args.include_risk_labels,
        )
        config.validate()

        offline_flags = (args.quotes_csv is not None, args.klines_csv is not None)
        if any(offline_flags) and not all(offline_flags):
            raise ValueError("--quotes-csv and --klines-csv must be used together")

        if all(offline_flags):
            quotes, histories = load_offline_data(
                args.quotes_csv,
                args.klines_csv,
            )
        else:
            quotes, histories = fetch_live_data(
                universe=args.universe,
                prefilter=args.prefilter,
                history_count=args.history_count,
                config=config,
                show_progress=args.show_progress,
            )

        result = screen_candidates(quotes, histories, config)
        snapshot = quote_snapshot(quotes)
        generated = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(
            timespec="seconds"
        )
        print(
            f"Quote snapshot: {snapshot}; generated: {generated}; "
            f"candidates: {len(result)}",
            file=sys.stderr,
        )
        if result.empty:
            print(
                "No candidates matched. Review data freshness and thresholds.",
                file=sys.stderr,
            )
            return 2

        output_format = _format_from_output(args.output, args.format)
        serialized = serialize_result(result, output_format)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized, encoding="utf-8")
            print(f"Wrote {args.output}", file=sys.stderr)
        else:
            print(serialized)
        return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
