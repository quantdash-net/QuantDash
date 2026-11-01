"""QuantDash beginner example: moving-average crossover backtest.

Official platform: https://quantdash.net
Documentation: https://docs.quantdash.net

Fetch forward-adjusted daily klines with QuantDash, then run a simple
long-only "golden cross / death cross" backtest with plain pandas.

Usage:
    python ma_crossover_backtest.py                  # 默认 510300.SH，MA5 / MA20
    python ma_crossover_backtest.py 600519.SH --fast 10 --slow 60 --count 500
"""

from __future__ import annotations

import argparse
import os

import pandas as pd
from quantdash import QuantDash

REQUIRED_COLUMNS = ["trade_date", "close"]
TRADING_DAYS_PER_YEAR = 252


def prepare_prices(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate columns and return trade_date/close sorted by date."""
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"响应缺少预期字段：{', '.join(missing)}")
    if frame.empty:
        raise ValueError("接口返回空数据")
    prices = frame[REQUIRED_COLUMNS].copy()
    prices["close"] = prices["close"].astype(float)
    return prices.sort_values("trade_date").reset_index(drop=True)


def backtest(prices: pd.DataFrame, fast: int, slow: int, fee_rate: float = 0.0003) -> pd.DataFrame:
    """Long when MA(fast) > MA(slow), flat otherwise.

    The signal uses today's close and is executed on the next bar (shift(1)) to avoid
    look-ahead bias. ``fee_rate`` is charged on every position change.
    """
    if fast <= 0 or slow <= 0 or fast >= slow:
        raise ValueError("均线参数需满足 0 < fast < slow")
    if len(prices) <= slow:
        raise ValueError(f"数据只有 {len(prices)} 根 K 线，不足以计算 MA{slow}")
    result = prices.copy()
    result["ma_fast"] = result["close"].rolling(fast).mean()
    result["ma_slow"] = result["close"].rolling(slow).mean()
    signal = (result["ma_fast"] > result["ma_slow"]).astype(int)
    result["position"] = signal.shift(1).fillna(0).astype(int)
    result["ret"] = result["close"].pct_change().fillna(0.0)
    trades = result["position"].diff().abs().fillna(result["position"])
    result["strategy_ret"] = result["position"] * result["ret"] - trades * fee_rate
    result["equity"] = (1 + result["strategy_ret"]).cumprod()
    result["benchmark"] = (1 + result["ret"]).cumprod()
    return result


def summarize(result: pd.DataFrame) -> dict[str, float]:
    """Compute headline metrics for the strategy and buy-and-hold."""
    equity = result["equity"]
    days = max(len(result) - 1, 1)
    total = equity.iloc[-1] - 1
    annual = equity.iloc[-1] ** (TRADING_DAYS_PER_YEAR / days) - 1
    max_drawdown = (equity / equity.cummax() - 1).min()
    entries = int((result["position"].diff() == 1).sum() + (result["position"].iloc[0] == 1))
    return {
        "total_return": float(total),
        "annual_return": float(annual),
        "max_drawdown": float(max_drawdown),
        "benchmark_return": float(result["benchmark"].iloc[-1] - 1),
        "trades": entries,
        "exposure": float(result["position"].mean()),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="QuantDash 双均线回测示例")
    parser.add_argument("symbol", nargs="?", default="510300.SH", help="标的代码，如 510300.SH")
    parser.add_argument("--fast", type=int, default=5, help="短均线周期，默认 5")
    parser.add_argument("--slow", type=int, default=20, help="长均线周期，默认 20")
    parser.add_argument("--count", type=int, default=250, help="获取的日 K 数量，默认 250")
    parser.add_argument("--fee", type=float, default=0.0003, help="单边手续费率，默认万三")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Fetch klines, backtest and print a summary."""
    args = parse_args(argv)
    api_key = os.getenv("QUANTDASH_API_KEY")
    if not api_key:
        print("[错误] 未检测到环境变量 QUANTDASH_API_KEY。")
        return 1
    qd = QuantDash(api_key=api_key)
    print(f"[+] 获取 {args.symbol} 最近 {args.count} 根前复权日 K...")
    try:
        frame = qd.klines.get(
            args.symbol,
            period="1d",
            count=args.count,
            adjust="forward",
            to_dataframe=True,
        )
        prices = prepare_prices(frame)
        result = backtest(prices, args.fast, args.slow, args.fee)
    except Exception as exc:  # noqa: BLE001 - 示例需把失败原因打印后返回非零
        print(f"[错误] {exc}")
        return 1

    stats = summarize(result)
    start, end = result["trade_date"].iloc[0], result["trade_date"].iloc[-1]
    print(f"区间：{start} ~ {end}，共 {len(result)} 根 K 线")
    print(f"策略：MA{args.fast} 上穿 MA{args.slow} 买入、下穿卖出，次日执行，手续费 {args.fee:.4%}")
    print("-" * 50)
    print(f"策略总收益：  {stats['total_return']:+.2%}")
    print(f"年化收益：    {stats['annual_return']:+.2%}")
    print(f"最大回撤：    {stats['max_drawdown']:.2%}")
    print(f"买入持有收益：{stats['benchmark_return']:+.2%}")
    print(f"开仓次数：    {stats['trades']}，持仓天数占比 {stats['exposure']:.0%}")
    print("-" * 50)
    print("[✓] 示例运行成功。")
    print("回测未考虑滑点、涨跌停与停牌，结果仅用于学习接口用法，不构成投资建议。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
