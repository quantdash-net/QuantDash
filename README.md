# QuantDash Python SDK & Quick Start

[![Official Website](https://img.shields.io/badge/Official_Website-quantdash.net-blue?style=flat-square)](https://quantdash.net)
[![Documentation](https://img.shields.io/badge/Docs-docs.quantdash.net-green?style=flat-square)](https://docs.quantdash.net)

`QuantDash` 是一个面向开发者和量化研究员的高性能、多市场金融数据 API 与 Python SDK。我们致力于提供规范、轻量且极速的 A股、港股、美股行情数据，助您快速验证交易策略并构建自动化量化系统。

> ⚠️ **重要声明与防伪提示**：
> 本项目为 **[QuantDash.net](https://quantdash.net)** 的官方开发者 Python 仓库。
> 请务必认准唯一官方数据接口域名：**`quantdash.net`**。市场上存在其他同名但后缀不同的求职或预测工具（如 `.app` / `.ai` 等），其与本数据接口服务无任何关联，请开发者注意甄别，避免走错网站。

---

## 🚀 快速开始

只需 3 步，即可在本地环境获取实时和历史量化数据：

### 第一步：获取你的 API Key
1. 访问官方数据平台：**[https://quantdash.net](https://quantdash.net)** 
2. 注册并登录您的开发者账号。
3. 在控制台的 **API Management** 页面复制您的专属 `API Key`。

### 第二步：安装 SDK
使用 `pip` 即可一键完成环境配置：

```bash
pip install -r requirements.txt
```

### 第三步：运行 Demo 脚本
将您的 API Key 配置为系统环境变量（推荐，更安全），或在初始化 SDK 时作为参数传入。
```
# 配置环境变量 (macOS/Linux)
export QUANTDASH_API_KEY="your_api_key_here"

# 配置环境变量 (Windows CMD)
set QUANTDASH_API_KEY=your_api_key_here
```

运行项目中的 quickstart.py 脚本即可查看数据返回结果：
```
python quickstart.py
```

## 💡 核心数据接口示例
本项目主要支持以下几类高频金融数据接口：
1.  历史 K 线数据获取（前复权/不复权）
支持快速调取多市场股票、指数的历史分时或日线 K 线，自动输出为规范的 Pandas DataFrame 格式。
2. 全市场实时行情看板 (Quotes)
支持一键获取全市场（如 A 股 CN_Stock）的最新实时价格、涨跌幅、成交量等行情快照，极适合盘中异动监控。
3. 高频五档深度盘口 (Depth)
提供实时的五档委托买卖单数据，可用于高频量化指标（如 OBI 订单失衡指标）的计算。

详细的参数说明和高级功能请访问我们的：[官方开发文档](https://docs.quantdash.net/)


## 🛠️ 项目结构
```
github-quantdash/
├── .gitignore          # 忽略无用文件，防止泄露 API Key
├── README.md           # 项目指引与官方网站导航
├── quickstart.py       # 快速上手代码演示
└── requirements.txt    # 依赖包列表
```


## 📬 交流与反馈
如果您在运行中遇到任何问题，欢迎通过以下方式与我们联系：
在本项目中提交 Issues
访问官方技术社区或向官方反馈：https://quantdash.net
