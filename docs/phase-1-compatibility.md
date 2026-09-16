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

## 尚未关闭

- 前端 UI 当前仍默认使用非流式 QA；`askStream` 已改为 POST fetch 流解析并完成独立解析测试，后续启用 UI 流式交互时无需改变后端契约。
- 未调用真实 DashScope Provider，因此没有新的线上质量、P50/P95 或费用数据；在获得明确预算前不能将该项写为通过。
