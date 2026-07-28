"""QuantDash API quick-start example.

Official platform: https://quantdash.net
Documentation: https://docs.quantdash.net
"""

from __future__ import annotations

import os

import pandas as pd
from quantdash import QuantDash

KLINE_COLUMNS = ["trade_date", "open", "high", "low", "close", "volume"]
QUOTE_COLUMNS = ["symbol", "last_price", "ext.change_pct", "volume"]


def preview(frame: pd.DataFrame, columns: list[str], *, rows: int = 5) -> pd.DataFrame:
    """Return a validated, compact preview for terminal output."""
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"响应缺少预期字段：{', '.join(missing)}")
    return frame.loc[:, columns].tail(rows)


def main() -> int:
    """Run two read-only API examples and return a process exit code."""
    api_key = os.getenv("QUANTDASH_API_KEY")
    if not api_key:
        print("[错误] 未检测到环境变量 QUANTDASH_API_KEY。")
        print("请访问 https://quantdash.net 获取 API Key，并参考 README 完成配置。")
        return 1

    print("[+] 正在初始化 QuantDash 客户端...")
    qd = QuantDash(api_key=api_key)
    failures: list[str] = []

    print("\n[+] 1. 获取 600519.SH 前复权日 K 数据...")
    try:
        kline = qd.klines.get(
            "600519.SH",
            period="1d",
            count=5,
            adjust="forward",
            to_dataframe=True,
        )
        if kline is None or kline.empty:
            raise ValueError("接口返回空数据")
        print(f"成功获取 {len(kline)} 条记录：")
        print(preview(kline, KLINE_COLUMNS).to_string(index=False))
    except Exception as exc:
        failures.append("K 线")
        print(f"[错误] K 线请求失败：{exc}")

    print("\n[+] 2. 获取 A 股全市场行情快照...")
    try:
        quotes = qd.quotes.get(universes="CN_Stock", to_dataframe=True)
        if quotes is None or quotes.empty:
            raise ValueError("接口返回空数据")
        print(f"成功获取 {len(quotes)} 只标的，前五行预览：")
        print(preview(quotes.head(5), QUOTE_COLUMNS).to_string(index=False))
    except Exception as exc:
        failures.append("行情快照")
        print(f"[错误] 行情快照请求失败：{exc}")

    print("\n" + "-" * 50)
    if failures:
        print(f"[!] 示例结束，失败接口：{', '.join(failures)}。")
        print("请检查 API Key、接口权限、网络连接和官方文档。")
        return 1

    print("[✓] 示例运行成功。")
    print("更多接口与参数：https://docs.quantdash.net")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
