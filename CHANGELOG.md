# Changelog

本项目使用语义化版本，变更按 Added、Changed、Fixed、Security 和 Known Issues 分类。

## Unreleased

### Added

- 阶段 0 的运行时固定、Python 哈希锁和前端 lockfile 门禁。
- dev/test/prod 环境契约与生产启动校验。
- 数据 Schema、来源清单、确定性清洗审计和完整性报告。
- 原始系统 OpenAPI、行为、质量、性能与成本快照。
- CycloneDX SBOM、依赖漏洞扫描、CI、ADR 和缺陷台账。
- NLTK 传递依赖安全约束升级至 3.10.3；当前剩余未修复漏洞已登记为阶段0外部阻塞。
- 阶段1的索引状态、问答、检索和 SSE 领域模型及窄端口。
- 空索引、旧索引加载、top_k、SSE、错误 envelope、CLI 和前端流解析回归测试。

### Changed

- API 启动只加载已有索引；索引缺失时保持 liveness 并返回明确 not-ready。
- 前端流式客户端改为 POST fetch 解析，与后端 SSE 契约一致。
- Mypy strict 扩展至整个 `backend/app`，Ruff 扩展至 `backend tests scripts`。

### Fixed

- 移除公共 `POST /api/v1/index/build`，索引构建只保留受控 CLI。
- 修复 QA/Search 的 `top_k` 透传、累计 chunk 转增量 delta、重复结束事件和流资源释放。
- 验证错误、未就绪和内部异常使用稳定且脱敏的错误 envelope。

### Security

- 配置对象隐藏 Provider 密钥和 JWT 密钥。
- 测试默认使用 Mock Provider、临时目录并禁止网络。

### Known Issues

- 数据来源和“705 条”口径仍待权威证据确认。
- 正式 Provider 的质量、性能和成本基线尚待批准预算。
- NLTK 3.10.3 的 CVE-2026-81726 暂无上游修复版本；扫描保持可见，不使用忽略规则。
