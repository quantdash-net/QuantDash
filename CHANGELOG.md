# Changelog

本文件记录 QuantDash 公开示例仓库的重要变化。SDK 自身的版本与接口变化以官方发布说明和文档为准。

## Unreleased

### Changed

- 明确仓库是 MIT 许可的 SDK 示例与集成入口；
- 统一 GitHub 与 PyPI 对 QuantDash Python SDK `0.1.0` 的 MIT 许可表述；
- 明确开源客户端不授予 API 服务、账户权益、市场数据或商标权利；
- 将示例依赖与公开 SDK `0.1.0` 对齐；
- 将 K 线复权参数从旧写法更新为 `forward`；
- 将行情涨跌幅字段更新为 `ext.change_pct`；
- 示例在接口失败或响应字段变化时返回非零退出码。

### Added

- 为本仓库公开示例代码添加 MIT License；
- SDK 开源许可与商业服务、数据和商标之间的边界说明；
- 无需真实 API Key 的单元测试；
- Python 3.9–3.14 CI 和 Ruff 检查；
- 安全策略、贡献指南、Issue 与 Pull Request 模板；
- Windows PowerShell 和 macOS/Linux 上手说明。

## 0.1.0 - 2026-06-30

- 首个公开 QuantDash Python SDK 版本；
- 提供 K 线、实时行情、五档盘口、标的信息和复权因子接口。
