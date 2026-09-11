# 阶段 1 验收与回滚

本文件把路线图中的“模块化单体与主链路缺陷修复”落实为可执行的阶段契约。阶段1不是检索质量专项；未满足阶段0退出条件时，不得把阶段1候选代码标记为已签收。

当前状态：**未开始验收**。阶段0的全新机器/CI安装证据尚未取得，且当前工作区仍保留公共 `/api/v1/index/build` 路由和空索引启动时的隐式构建行为；这些是阶段1的待关闭事项，不是已通过的功能。

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
| ARCH-001 | Domain/Application 不导入 FastAPI、LlamaIndex、SQLAlchemy、`src` 或文件系统；依赖只从组合根注入 | 架构依赖测试、组合根代码审查 | 未开始 |
| API-001A | QA/Search 的 `top_k` 经 HTTP 校验后原值到达 Retriever，返回数不超过请求值 | 端到端请求与 Fake Adapter 断言 | 未开始 |
| API-001B | 正常 SSE 的内容事件是增量 delta；来源、内容、结束顺序稳定，正常流恰好一个结束事件 | 累计 chunk、空流和多 chunk 测试 | 未开始 |
| API-001C | 客户端断开或 Provider 异常时关闭/释放迭代器；错误流不追加成功结束事件 | 断开、异常和资源释放测试 | 未开始 |
| API-002 | 公共 `/api/v1/index/build` 不再出现在 OpenAPI；构建仅由受控 CLI 触发，状态接口只读 | OpenAPI diff、未授权 HTTP 回归、CLI smoke test | 未开始 |
| API-003 | 验证错误、未就绪、冲突和内部异常使用稳定错误码、批准 HTTP 状态和统一 envelope，不泄露密钥/堆栈 | HTTP 契约测试、脱敏断言 | 未开始 |
| INDEX-001 | 空索引不会在 API 启动路径同步构建；服务返回明确 not-ready，已有旧索引仍可查询 | 空 storage 启动测试、旧索引回归 | 未开始 |
| HEALTH-001 | `/health` 只表示进程存活；`/health/ready` 反映依赖和索引可用性，状态码/字段稳定 | liveness/readiness 契约测试 | 未开始 |
| COMPAT-001 | 除批准修复和移除公共构建路由外，OpenAPI、字段和同一输入的检索/问答结果在允许误差内兼容 | 阶段0样例对比、OpenAPI diff、质量/性能报告 | 未开始 |

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

## 退出与回滚

阶段1只有在验收矩阵全部通过、阶段0质量和性能指标没有无解释退化、且 OpenAPI diff 获得批准后才能签收，并将 `API-001`、`API-002`、`INDEX-001` 台账状态更新为已关闭。否则保持“未关闭”，不得进入阶段1.5。

阶段1不迁移或覆盖真实数据，不切换 active 索引，不引入不可逆数据库变更。回滚时保留阶段0基线和快照，将阶段1变更作为独立提交撤回或切回阶段0分支；切换前必须保存未提交工作区，禁止强制重置。运行时索引和数据库不属于代码回滚范围，任何删除或迁移都需要单独备份和审批。
