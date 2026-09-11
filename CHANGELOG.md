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

### Security

- 配置对象隐藏 Provider 密钥和 JWT 密钥。
- 测试默认使用 Mock Provider、临时目录并禁止网络。

### Known Issues

- 数据来源和“705 条”口径仍待权威证据确认。
- 正式 Provider 的质量、性能和成本基线尚待批准预算。
