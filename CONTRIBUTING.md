# Contributing

感谢你改进 QuantDash 的公开示例、文档和集成工作流。

## 贡献范围

本仓库接受：

- 可复现的 SDK 使用示例；
- 文档修复；
- 不依赖真实 API Key 的测试；
- 示例代码的可靠性、可读性和跨平台改进。

本仓库不包含也不接受 QuantDash 闭源 SDK 的内部源代码。

## 本地开发

```bash
python -m venv .venv
python -m pip install -r requirements-dev.txt
ruff check .
pytest
```

Windows PowerShell 激活环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux 激活环境：

```bash
source .venv/bin/activate
```

## 提交要求

1. 从 `main` 创建短生命周期分支；
2. 不提交真实 API Key、账户数据或生成的行情数据；
3. 为行为变化增加测试；
4. 确保 `ruff check .` 和 `pytest` 通过；
5. Pull Request 应描述目的、验证方式和兼容性影响。

接口或账户问题请通过 [QuantDash 官方平台](https://quantdash.net)反馈。
