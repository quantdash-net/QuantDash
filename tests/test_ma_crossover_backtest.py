from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

import ma_crossover_backtest as mab


def make_frame(closes: list[float]) -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=len(closes), freq="D").strftime("%Y-%m-%d")
    return pd.DataFrame({"trade_date": dates, "close": closes, "open": closes})


class FakeKlines:
    def __init__(self, frame: pd.DataFrame):
        self.frame = frame
        self.calls: list[tuple] = []

    def get(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.frame


class FakeClient:
    def __init__(self, frame: pd.DataFrame):
        self.klines = FakeKlines(frame)


def test_prepare_prices_sorts_and_validates():
    frame = make_frame([1.0, 2.0, 3.0]).iloc[::-1]
    prices = mab.prepare_prices(frame)
    assert list(prices["close"]) == [1.0, 2.0, 3.0]
    with pytest.raises(ValueError):
        mab.prepare_prices(pd.DataFrame({"trade_date": ["2026-01-01"]}))
    with pytest.raises(ValueError):
        mab.prepare_prices(pd.DataFrame(columns=["trade_date", "close"]))


def test_backtest_has_no_lookahead():
    closes = [10.0] * 5 + [11.0, 12.0, 13.0, 14.0, 15.0]
    result = mab.backtest(mab.prepare_prices(make_frame(closes)), fast=2, slow=4, fee_rate=0)
    first_signal = (result["ma_fast"] > result["ma_slow"]).idxmax()
    assert result.loc[first_signal, "position"] == 0
    assert result.loc[first_signal + 1, "position"] == 1


def test_backtest_rejects_bad_params():
    prices = mab.prepare_prices(make_frame([1.0] * 10))
    with pytest.raises(ValueError):
        mab.backtest(prices, fast=5, slow=5)
    with pytest.raises(ValueError):
        mab.backtest(prices, fast=2, slow=20)


def test_summarize_flat_market():
    result = mab.backtest(mab.prepare_prices(make_frame([5.0] * 30)), fast=3, slow=10, fee_rate=0)
    stats = mab.summarize(result)
    assert stats["total_return"] == 0
    assert stats["max_drawdown"] == 0
    assert stats["trades"] == 0


def test_main_requires_api_key(capsys):
    with patch.dict("os.environ", {}, clear=True):
        assert mab.main([]) == 1
    assert "QUANTDASH_API_KEY" in capsys.readouterr().out


def test_main_runs_with_fake_client(capsys):
    closes = [10 + (i % 15) * 0.2 for i in range(60)]
    client = FakeClient(make_frame(closes))
    with (
        patch.dict("os.environ", {"QUANTDASH_API_KEY": "test-key"}, clear=True),
        patch("ma_crossover_backtest.QuantDash", return_value=client),
    ):
        assert mab.main(["510300.SH", "--fast", "3", "--slow", "10", "--count", "60"]) == 0
    args, kwargs = client.klines.calls[0]
    assert args[0] == "510300.SH"
    assert kwargs["count"] == 60
    assert kwargs["adjust"] == "forward"
    assert "策略总收益" in capsys.readouterr().out
