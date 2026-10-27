"""QuantDash multi-market klines example.

Official platform: https://quantdash.net
Documentation: https://docs.quantdash.net

Same klines.get call, only the symbol changes:
A-share, ETF, Hong Kong and US markets.
"""

from __future__ import annotations

import os

import pandas as pd
from quantdash import QuantDash

SYMBOLS = {
    "A 股": "600519.SH",
    "ETF": "510300.SH",
    "港股": "00700.HK",
    "美股": "AAPL.US",
}

KLINE_COLUMNS = ["trade_date", "open", "high", "low", "close", "volume"]


def preview(frame: pd.DataFrame) -> pd.Series:
    """Return the latest row after validating expected columns."""
    missing = [column for column in KLINE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"响应缺少预期字段：{', '.join(missing)}")
    if frame.empty:
        raise ValueError("接口返回空数据")
    return frame.iloc[-1]


def main() -> int:
    """Run the same klines call across four markets."""
    api_key = os.getenv("QUANTDASH_API_KEY")
    if not api_key:
        print("[错误] 未检测到环境变量 QUANTDASH_API_KEY。")
        return 1
    qd = QuantDash(api_key=api_key)
    failures: list[str] = []
    for market, symbol in SYMBOLS.items():
        print(f"\n[+] {market} {symbol} 前复权日 K 数据...")
        try:
            frame = qd.klines.get(
                symbol,
                period="1d",
                count=5,
                adjust="forward",
                to_dataframe=True,
            )
            row = preview(frame)
            print(f"最新日期：{row['trade_date']}，收盘价：{row['close']}")
        except Exception as exc:  # noqa: BLE001 - 示例需把各市场失败汇总后返回
            failures.append(market)
            print(f"[错误] {market} 请求失败：{exc}")
    print("\n" + "-" * 50)
    if failures:
        print(f"[!] 示例结束，失败市场：{', '.join(failures)}。")
        return 1
    print("[✓] 示例运行成功。")
    print("行情数据和示例仅用于开发、研究与接口演示，不构成投资建议。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
