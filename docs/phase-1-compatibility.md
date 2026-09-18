# 阶段 1 兼容性与 OpenAPI 差异

复核日期：2026-09-16。目标环境：Windows、Python 3.11（本机 3.11.15，GitHub Windows runner 3.11.9）、Node.js 22.17.0、npm 10.9.2。

## 已批准的行为差异

- 移除 `POST /api/v1/index/build` 及其 `BuildIndexRequest`、`IndexBuildData`、`IndexBuildResponse` schema。索引构建只保留 `python -m scripts.build_index` 受控 CLI。
- 空索引启动不再同步构建向量；进程继续存活，`/health` 返回 200，`/health/ready` 返回 503，QA/Search 返回稳定的 `APPLICATION_NOT_READY` envelope。
- SSE 内容统一为增量 delta，成功流只有一个 `end`，失败流只有 `error` 且不追加成功结束事件。
- 参数验证、未就绪和内部异常使用稳定错误码与统一 envelope；非 debug 环境不返回内部异常文本。

## 未变化的公共操作

- `GET /health`
- `GET /health/ready`
- `GET /api/v1/index/status`
- `POST /api/v1/qa`
- `POST /api/v1/qa/stream`
- `POST /api/v1/search`

QA/Search 的请求字段和成功响应字段保持兼容，`top_k` 现在有端到端端口断言；检索算法、阈值、Prompt、数据分母和索引文件格式均未改变。

## 验证证据

- `tests/test_phase1_api_contract.py`：top_k、SSE 顺序、累计转增量、单结束、异常、脱敏、资源关闭。
- `tests/test_phase1_index_contract.py`：空索引未就绪、只读 HTTP、CLI smoke、旧索引重新加载。
- `tests/test_application_architecture.py`：组合根注入与核心层依赖方向。
- `frontend/tests/sse.test.mjs`：POST SSE 分帧、跨 chunk 拼接、CRLF、单结束事件和非法 payload。
- OpenAPI 操作差异：仅移除 `POST /api/v1/index/build`，无新增公共操作。

## 正式 Provider 兼容性

- 2026-09-17 在 Windows、Python 3.11.15 上使用 `text-embedding-v3`、`qwen-plus` 和现有235文档 generation 完成真实调用。
- 28条检索全部返回成功，P50/P95 为 `227.715/252.575 ms`；3条 QA 全部返回成功，P50/P95 为 `12050.421/13782.495 ms`。
- QA/Search 公共字段、`top_k` 和成功 envelope 与阶段1契约一致；没有发现因分层改造引入的线上错误。
- 检索质量为 `Recall@5 = 0.2971`、`MRR@10 = 0.3304`。该结果高于阶段0正式离线 Mock 基线的 `0/0`，但低于阶段1.5门槛，已作为下一阶段基线保留。
- 证据和调用用量见 `docs/baselines/phase-1/provider-validation.json`。

## 已知限制

- 前端 UI 当前仍默认使用非流式 QA；`askStream` 已改为 POST fetch 流解析并完成独立解析测试，后续启用 UI 流式交互时无需改变后端契约。
- 默认根 Artifact 并非本次正式 Provider 兼容性证据使用的索引；在线运行必须显式配置已验证 generation 路径。阶段1不提前实现阶段2的 active generation/CAS 解析。
- DashScope 响应只返回 token 用量，不返回最终账单金额；本轮在已批准的人民币1元以内调用预算中执行，不声称已读取账单中心。
