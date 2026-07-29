from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

SCRIPT_PATH = (
    Path(__file__).parents[1]
    / "skills"
    / "screen-premarket-stocks"
    / "scripts"
    / "screen_premarket.py"
)
SPEC = importlib.util.spec_from_file_location("screen_premarket", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
screen_premarket = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = screen_premarket
SPEC.loader.exec_module(screen_premarket)


def make_history(
    symbol: str,
    *,
    start: float,
    step: float,
    amount: float,
) -> pd.DataFrame:
    closes = [start + step * index for index in range(21)]
    return pd.DataFrame(
        {
            "symbol": symbol,
            "trade_date": pd.date_range("2026-06-29", periods=21).astype(str),
            "close": closes,
            "amount": [amount] * 21,
            "volume": [1_000_000] * 21,
        }
    )


def test_screen_filters_risk_labels_gap_and_liquidity():
    quotes = pd.DataFrame(
        [
            {
                "symbol": "600001.SH",
                "ext.name": "候选一",
                "last_price": 10.2,
                "prev_close": 10.0,
                "amount": 90_000_000,
                "volume": 1_000_000,
            },
            {
                "symbol": "600002.SH",
                "ext.name": "*ST风险",
                "last_price": 10.1,
                "prev_close": 10.0,
                "amount": 100_000_000,
                "volume": 1_000_000,
            },
            {
                "symbol": "600003.SH",
                "ext.name": "低流动性",
                "last_price": 10.1,
                "prev_close": 10.0,
                "amount": 10_000_000,
                "volume": 1_000_000,
            },
            {
                "symbol": "600004.SH",
                "ext.name": "跳空过高",
                "last_price": 11.0,
                "prev_close": 10.0,
                "amount": 100_000_000,
                "volume": 1_000_000,
            },
        ]
    )
    histories = {
        "600001.SH": make_history(
            "600001.SH",
            start=9.0,
            step=0.05,
            amount=90_000_000,
        ),
        "600002.SH": make_history(
            "600002.SH",
            start=9.0,
            step=0.05,
            amount=100_000_000,
        ),
        "600003.SH": make_history(
            "600003.SH",
            start=9.0,
            step=0.05,
            amount=10_000_000,
        ),
        "600004.SH": make_history(
            "600004.SH",
            start=9.0,
            step=0.05,
            amount=100_000_000,
        ),
    }

    result = screen_premarket.screen_candidates(quotes, histories)

    assert result["symbol"].tolist() == ["600001.SH"]
    assert result.iloc[0]["rank"] == 1
    assert 0 <= result.iloc[0]["score"] <= 100


def test_ranking_is_deterministic_and_prefers_combined_factors():
    quotes = pd.DataFrame(
        [
            {
                "symbol": "600010.SH",
                "ext.name": "高流动性",
                "last_price": 10.1,
                "prev_close": 10.0,
                "amount": 200_000_000,
                "volume": 1_000_000,
            },
            {
                "symbol": "600011.SH",
                "ext.name": "普通流动性",
                "last_price": 10.1,
                "prev_close": 10.0,
                "amount": 80_000_000,
                "volume": 1_000_000,
            },
        ]
    )
    histories = {
        "600010.SH": make_history(
            "600010.SH",
            start=9.0,
            step=0.04,
            amount=200_000_000,
        ),
        "600011.SH": make_history(
            "600011.SH",
            start=9.0,
            step=0.03,
            amount=80_000_000,
        ),
    }

    result = screen_premarket.screen_candidates(quotes, histories)

    assert result["symbol"].tolist() == ["600010.SH", "600011.SH"]
    assert result["score"].is_monotonic_decreasing


def test_offline_cli_writes_csv(tmp_path, capsys):
    quotes_path = tmp_path / "quotes.csv"
    klines_path = tmp_path / "klines.csv"
    output_path = tmp_path / "candidates.csv"
    pd.DataFrame(
        [
            {
                "symbol": "600020.SH",
                "name": "离线样本",
                "last_price": 10.1,
                "prev_close": 10.0,
                "amount": 90_000_000,
                "volume": 1_000_000,
                "trade_time": "2026-07-28 09:25:00",
            }
        ]
    ).to_csv(quotes_path, index=False)
    make_history(
        "600020.SH",
        start=9.0,
        step=0.04,
        amount=90_000_000,
    ).to_csv(klines_path, index=False)

    exit_code = screen_premarket.main(
        [
            "--quotes-csv",
            str(quotes_path),
            "--klines-csv",
            str(klines_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert pd.read_csv(output_path)["symbol"].tolist() == ["600020.SH"]
    stderr = capsys.readouterr().err
    assert "Quote snapshot: 2026-07-28 09:25:00" in stderr
