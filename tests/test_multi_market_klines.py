from __future__ import annotations

from unittest.mock import patch

import pandas as pd

import multi_market_klines


class FakeKlines:
    def __init__(self):
        self.calls: list[tuple] = []

    def get(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return pd.DataFrame(
            [
                {
                    "trade_date": "2026-07-27",
                    "open": 1400.0,
                    "high": 1420.0,
                    "low": 1390.0,
                    "close": 1410.0,
                    "volume": 100,
                }
            ]
        )


class FakeClient:
    def __init__(self):
        self.klines = FakeKlines()


def test_main_requires_api_key(capsys):
    with patch.dict("os.environ", {}, clear=True):
        assert multi_market_klines.main() == 1
    assert "QUANTDASH_API_KEY" in capsys.readouterr().out


def test_main_uses_same_call_across_markets(capsys):
    client = FakeClient()
    with (
        patch.dict("os.environ", {"QUANTDASH_API_KEY": "test-key"}, clear=True),
        patch("multi_market_klines.QuantDash", return_value=client),
    ):
        assert multi_market_klines.main() == 0
    assert len(client.klines.calls) == 4
    for _args, kwargs in client.klines.calls:
        assert kwargs["period"] == "1d"
        assert kwargs["count"] == 5
        assert kwargs["adjust"] == "forward"
        assert kwargs["to_dataframe"] is True
    assert [args[0] for args, _ in client.klines.calls] == [
        "600519.SH",
        "510300.SH",
        "00700.HK",
        "AAPL.US",
    ]


def test_preview_rejects_missing_columns():
    frame = pd.DataFrame([{"trade_date": "2026-07-27"}])
    try:
        multi_market_klines.preview(frame)
    except ValueError as exc:
        assert "close" in str(exc)
    else:
        raise AssertionError("preview should reject missing columns")
