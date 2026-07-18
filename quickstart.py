"""
QuantDash API - Quick Start Demo
--------------------------------------------------
官方开发者平台: https://quantdash.net
官方文档中心: https://docs.quantdash.net

注意：运行本脚本前，请确保您已前往官方网站 https://quantdash.net 免费注册并获取您的 API Key。
"""

import os
import sys
from quantdash import QuantDash

def main():
    # 1. 初始化客户端
    # 推荐做法：从系统环境变量中读取 API Key
    # 备用做法：如果您未配置环境变量，可以手动替换下方字符串
    api_key = os.getenv("QUANTDASH_API_KEY")
    
    if not api_key:
        print("[!] 提示: 未检测到系统环境变量 QUANTDASH_API_KEY。")
        print("    请前往官方网站申请 API Key: https://quantdash.net")
        print("    并运行命令配置环境，或将下方 your_api_key_here 替换为您的 Key 再次尝试。")
        
        # 允许用户临时硬编码替换测试
        api_key = "your_api_key_here"
        
        if api_key == "your_api_key_here":
            print("\n[错误] 请输入有效的 API Key 以运行此 demo。")
            sys.exit(1)

    print("[+] 正在初始化 QuantDash 客户端 (API Host: quantdash.net)...")
    qd = QuantDash(api_key=api_key)

    # 2. 演示接口一：获取历史 K 线数据 (以 A股 贵州茅台 为例)
    # 接口细节可参考：https://docs.quantdash.net/klines
    try:
        print("\n[+] 1. 正在调取历史K线接口 (K-Line Data)...")
        df_kline = qd.klines.get(
            symbol="600519.SH", 
            period="1d", 
            adjust="qfq", 
            to_dataframe=True
        )
        if not df_kline.empty:
            print(f"成功获取 600519.SH 日K线数据，共 {len(df_kline)} 条记录。")
            print(df_kline[["trade_date", "open", "high", "low", "close", "volume"]].tail(5))
        else:
            print("未获取到有效数据，请检查网络或标的代码。")
    except Exception as e:
        print(f"调取K线数据失败，请确认 API 权限是否正常: {e}")

    # 3. 演示接口二：获取全市场实时行情看板 (Quotes)
    # 接口细节可参考：https://docs.quantdash.net/quotes
    try:
        print("\n[+] 2. 正在调取全市场行情快照接口 (Quotes)...")
        # 传入 universes 参数（支持 A 股市场 'CN_Stock'）获取实时行情快照
        quotes_df = qd.quotes.get(universes=["CN_Stock"], to_dataframe=True)
        if not quotes_df.empty:
            print("A 股全市场实时行情数据样本预览 (前5行)：")
            print(quotes_df[["symbol", "last_price", "change_percent", "volume"]].head(5))
        else:
            print("未获取到实时行情快照。")
    except Exception as e:
        print(f"调取行情快照失败: {e}")

    print("\n--------------------------------------------------")
    print("[✓] Demo 运行演示结束。")
    print("想要了解更多关于高频五档盘口、历史 Tick 数据的细节？")
    print("请访问唯一官方网站: https://quantdash.net 获取最新更新。")

if __name__ == "__main__":
    main()
