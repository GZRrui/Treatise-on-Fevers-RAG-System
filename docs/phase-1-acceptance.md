# 阶段 1 验收与回滚

本文件把路线图中的“模块化单体与主链路缺陷修复”落实为可执行的阶段契约。阶段1不是检索质量专项；未满足阶段0退出条件时，不得把阶段1候选代码标记为已签收。

当前状态：**验收中，尚未签收**。阶段0已按 Windows 目标环境签收；公共索引构建路由、空索引隐式构建、主要 HTTP/SSE 契约缺陷和前端流解析已完成本地修复，仍待远程 Windows CI 与线上模型质量/性能预算。

## 范围

阶段1只处理以下缺陷及其必要的分层改造：

- `API-001`：`top_k`、SSE delta 和错误 envelope 契约。
- `API-002`：公共索引构建 HTTP 接口的边界。
- `INDEX-001`：空索引启动时 API 进程内同步重建。

任何涉及检索算法、阈值、Prompt、数据分母、索引 generation/CAS、Worker、队列、pgvector、证据策略或完整管理安全的变更，必须移到后续阶段并单独建账。

## 输入与输出

**输入**

- 阶段0的锁文件、环境矩阵、数据完整性报告、原始 OpenAPI/请求样例/质量快照和缺陷台账。
- 已批准的 `domain/application/infrastructure/api` 分层方案、窄端口契约和离线 Mock Provider。

**输出**

- 唯一组合根、显式依赖注入和无框架核心层的模块化单体。
- QA/Search 的 `top_k`、SSE、错误、健康检查和空索引启动回归测试。
- 只读索引状态 HTTP 接口与受控 CLI 构建入口；公共索引构建路由移除。
- OpenAPI diff、行为兼容性报告、测试输出、迁移说明和本文件对应的状态更新。

## 验收矩阵

| ID | 退出条件 | 必须证据 | 当前状态 |
|---|---|---|---|
| ARCH-001 | Domain/Application 不导入 FastAPI、LlamaIndex、SQLAlchemy、`src` 或文件系统；依赖只从组合根注入 | 架构依赖测试、组合根代码审查 | 本地通过 |
| API-001A | QA/Search 的 `top_k` 经 HTTP 校验后原值到达 Retriever，返回数不超过请求值 | 端到端请求与 Fake Adapter 断言 | 本地通过 |
| API-001B | 正常 SSE 的内容事件是增量 delta；来源、内容、结束顺序稳定，正常流恰好一个结束事件 | 累计 chunk、空流和多 chunk 测试 | 本地通过 |
| API-001C | 客户端断开或 Provider 异常时关闭/释放迭代器；错误流不追加成功结束事件 | 断开、异常和资源释放测试 | 本地通过 |
| API-002 | 公共 `/api/v1/index/build` 不再出现在 OpenAPI；构建仅由受控 CLI 触发，状态接口只读 | OpenAPI diff、HTTP 回归、CLI smoke test | 本地通过 |
| API-003 | 验证错误、未就绪、冲突和内部异常使用稳定错误码、批准 HTTP 状态和统一 envelope，不泄露密钥/堆栈 | HTTP 契约测试、脱敏断言 | 本地通过；无公共构建冲突面 |
| INDEX-001 | 空索引不会在 API 启动路径同步构建；服务返回明确 not-ready，已有旧索引仍可查询 | 空 storage 启动测试、旧索引回归 | 本地通过 |
| HEALTH-001 | `/health` 只表示进程存活；`/health/ready` 反映依赖和索引可用性，状态码/字段稳定 | liveness/readiness 契约测试 | 本地通过 |
| COMPAT-001 | 除批准修复和移除公共构建路由外，OpenAPI、字段和同一输入的检索/问答结果在允许误差内兼容 | 阶段0样例对比、OpenAPI diff、质量/性能报告 | 部分通过；线上质量/性能/费用未验证 |

所有矩阵项必须有可追溯测试输出；仅代码审查或单元测试通过不能关闭端到端契约项。

## 验证命令

在阶段1实现完成后，至少执行以下命令，并把实际输出链接到变更记录：

```powershell
.\.venv311\Scripts\python.exe -m compileall -q backend config.py evaluation scripts src tests
.\.venv311\Scripts\python.exe -m pytest -q --basetemp .test-temp\pytest-phase1
.\.venv311\Scripts\python.exe -m mypy
.\.venv311\Scripts\python.exe -m ruff check backend tests scripts
git diff --check
```

还必须执行 API 集成/契约、架构依赖、SSE 断开与空索引启动测试；如果测试依赖临时目录，必须显式指定仓库内可写目录，不能把 Windows 权限错误当作通过。

## 2026-09-16 Windows 本地证据

- compileall 通过。
- Pytest 26 项通过，覆盖旧索引重新加载、CLI smoke、兼容 facade 和核心契约。
- Mypy strict 已从阶段0的 5 个文件扩展到整个 `backend/app`，34 个源文件通过。
- `ruff check backend tests scripts` 从阶段0的 169 项遗留问题清零并通过；中文全角标点通过 `allowed-confusables` 明确列举，不关闭 Ruff 规则。
- OpenAPI 仅移除批准的 `POST /api/v1/index/build`；详见 `docs/phase-1-compatibility.md`。
- 前端 3 项 SSE 解析测试、TypeScript typecheck 和 Vite build 通过。
- 测试夹具和 Pytest basetemp 均固定在仓库内 `.test-temp`，不依赖 Windows 系统临时目录权限。
- 未调用真实模型、未覆盖真实索引、未产生 Provider 费用。

## 退出与回滚

阶段1只有在验收矩阵全部通过、阶段0质量和性能指标没有无解释退化、且 OpenAPI diff 获得批准后才能签收，并将 `API-001`、`API-002`、`INDEX-001` 台账状态更新为已关闭。否则保持“未关闭”，不得进入阶段1.5。

阶段1不迁移或覆盖真实数据，不切换 active 索引，不引入不可逆数据库变更。回滚时保留阶段0基线和快照，将阶段1变更作为独立提交撤回或切回阶段0分支；切换前必须保存未提交工作区，禁止强制重置。运行时索引和数据库不属于代码回滚范围，任何删除或迁移都需要单独备份和审批。
