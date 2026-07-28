from __future__ import annotations

from unittest.mock import patch

import pandas as pd

import quickstart


class FakeKlines:
    def get(self, *args, **kwargs):
        assert args == ("600519.SH",)
        assert kwargs["adjust"] == "forward"
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


class FakeQuotes:
    def get(self, **kwargs):
        assert kwargs["universes"] == "CN_Stock"
        return pd.DataFrame(
            [
                {
                    "symbol": "600519.SH",
                    "last_price": 1410.0,
                    "ext.change_pct": 0.01,
                    "volume": 100,
                }
            ]
        )


class FakeClient:
    def __init__(self):
        self.klines = FakeKlines()
        self.quotes = FakeQuotes()


def test_main_requires_api_key(capsys):
    with patch.dict("os.environ", {}, clear=True):
        assert quickstart.main() == 1
    assert "QUANTDASH_API_KEY" in capsys.readouterr().out


def test_main_uses_current_sdk_parameters(capsys):
    with (
        patch.dict("os.environ", {"QUANTDASH_API_KEY": "test-key"}, clear=True),
        patch("quickstart.QuantDash", return_value=FakeClient()) as client,
    ):
        assert quickstart.main() == 0

    client.assert_called_once_with(api_key="test-key")
    output = capsys.readouterr().out
    assert "600519.SH" in output
    assert "示例运行成功" in output


def test_preview_rejects_schema_drift():
    frame = pd.DataFrame([{"symbol": "600519.SH"}])
    try:
        quickstart.preview(frame, ["symbol", "last_price"])
    except ValueError as exc:
        assert "last_price" in str(exc)
    else:
        raise AssertionError("preview should reject missing columns")
