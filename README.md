# QuantDash Python Examples

[![PyPI](https://img.shields.io/pypi/v/quantdash?style=flat-square)](https://pypi.org/project/quantdash/)
[![Python](https://img.shields.io/pypi/pyversions/quantdash?style=flat-square)](https://pypi.org/project/quantdash/)
[![CI](https://github.com/quantdash-net/QuantDash/actions/workflows/ci.yml/badge.svg)](https://github.com/quantdash-net/QuantDash/actions/workflows/ci.yml)
[![Official Website](https://img.shields.io/badge/website-quantdash.net-blue?style=flat-square)](https://quantdash.net)
[![Documentation](https://img.shields.io/badge/docs-docs.quantdash.net-green?style=flat-square)](https://docs.quantdash.net)

QuantDash 是面向开发者和量化研究员的多市场金融数据服务，提供 A 股、ETF、港股和美股行情数据。

本仓库是 QuantDash 官方 Python 示例与集成仓库，包含可运行示例、测试和后续开放的工作流；**不包含闭源 QuantDash SDK 的源代码**。SDK 通过 [PyPI](https://pypi.org/project/quantdash/) 分发，完整接口说明以[官方文档](https://docs.quantdash.net)为准。

> 请认准官方域名 `quantdash.net`、API 域名 `api.quantdash.net` 和 GitHub 账号 `quantdash-net`。

## 快速开始

### 1. 获取 API Key

访问 [QuantDash](https://quantdash.net)，注册并在控制台的 API Management 页面创建 API Key。

### 2. 创建环境并安装

本仓库当前示例与公开 SDK `0.1.0` 对齐，支持 Python 3.9 及以上版本。

Windows PowerShell：

```powershell
git clone https://github.com/quantdash-net/QuantDash.git
cd QuantDash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

macOS / Linux：

```bash
git clone https://github.com/quantdash-net/QuantDash.git
cd QuantDash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

如果只需要 SDK：

```bash
pip install quantdash==0.1.0
```

### 3. 配置 API Key

不要把 API Key 写入代码或提交到 Git。

Windows PowerShell：

```powershell
$env:QUANTDASH_API_KEY = "your_api_key_here"
```

macOS / Linux：

```bash
export QUANTDASH_API_KEY="your_api_key_here"
```

### 4. 运行示例

```bash
python quickstart.py
```

示例将依次获取：

1. `600519.SH` 的前复权日 K 数据；
2. A 股全市场实时行情快照；
3. 关键字段的前五行预览。

## 最小代码示例

```python
from quantdash import QuantDash

qd = QuantDash()  # 自动读取 QUANTDASH_API_KEY

kline = qd.klines.get(
    "600519.SH",
    period="1d",
    count=5,
    adjust="forward",
    to_dataframe=True,
)

quotes = qd.quotes.get(
    universes="CN_Stock",
    to_dataframe=True,
)
```

复权参数支持：

- `forward`：前复权；
- `backward`：后复权；
- `none`：不复权；
- `forward_additive` / `backward_additive`：加法复权。

## 市场与代码格式

| 市场 | 标的池 | 示例 |
| --- | --- | --- |
| A 股 | `CN_Stock` | `600519.SH`、`000001.SZ` |
| ETF | `CN_ETF` | `510300.SH` |
| 港股 | `HK_Stock` | `00700.HK` |
| 美股 | `US_Stock` | `AAPL.US` |

## 项目结构

```text
QuantDash/
├── .github/              # CI、Issue 与 PR 模板
├── tests/                # 无需真实 API 的自动化测试
├── .env.example          # 环境变量示例
├── CHANGELOG.md          # 示例仓库变更记录
├── CONTRIBUTING.md       # 贡献指南
├── SECURITY.md           # 安全问题报告方式
├── pyproject.toml        # 测试与代码质量配置
├── quickstart.py         # 快速上手示例
└── requirements.txt      # 可复现的运行依赖
```

## 常见问题

### 未检测到 API Key

确认变量设置在当前终端会话中：

```powershell
Get-ChildItem Env:QUANTDASH_API_KEY
```

### 返回 401 或 403

检查 API Key 是否有效，以及当前套餐是否包含目标接口或市场权限。

### 返回 429

请求频率超过限制。降低调用频率，并按照服务端返回的等待时间重试。

### 返回空 DataFrame

检查标的代码后缀、交易时段、市场权限和查询周期。完整排查方式请参考[官方文档](https://docs.quantdash.net)。

## 安全与免责声明

- 不要在 Issue、日志、截图或示例中提交真实 API Key。
- 行情数据和示例仅用于开发、研究与接口演示，不构成投资建议。
- 安全问题请按照 [SECURITY.md](SECURITY.md) 私下报告。

## 反馈与贡献

- 使用问题或功能建议：提交 [Issue](https://github.com/quantdash-net/QuantDash/issues)；
- 贡献示例与修复：阅读 [CONTRIBUTING.md](CONTRIBUTING.md)；
- SDK 接口文档：[docs.quantdash.net](https://docs.quantdash.net)；
- 官方平台：[quantdash.net](https://quantdash.net)。
