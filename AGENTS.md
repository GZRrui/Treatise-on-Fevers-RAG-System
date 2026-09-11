# RAGPP 项目协作说明书

本文件是 Codex 在 `D:\ragpp` 项目中协作时必须遵守的工程约定。它描述项目边界、协作流程、修改权限、验证要求和交付标准。

## 1. 项目概况

这是一个面向《伤寒论》的 RAG 智能问答系统，当前以单古籍运行，同时为多古籍资源隔离预留接口。

### 技术栈

- 后端：Python 3.11、FastAPI、Pydantic v2、Uvicorn。
- RAG：LlamaIndex、DashScope Embedding、通义千问 LLM。
- 后端测试与质量：Pytest、pytest-asyncio、HTTPX、Mypy strict。
- 前端：Vue 3、TypeScript、Vite、Axios、Pinia、Marked。
- 当前索引存储：本地文件 Artifact；后续阶段再评估 PostgreSQL/pgvector。
- 当前运行模式：模块化单体；异步索引 Worker 属于后续阶段。

### 当前阶段声明

当前工作区包含部分高阶架构成果，但“阶段一已签收”声明已经撤回。正式顺序是：

1. 阶段0：依赖、环境、数据和原始系统基线。
2. 阶段1：模块化单体与主链路缺陷修复。
3. 阶段1.5：检索质量专项。
4. 阶段2：异步索引 Worker。
5. 阶段3：PostgreSQL/pgvector。
6. 阶段4：评测平台与持续回归。
7. 阶段5：可观测性与 SRE。
8. 阶段6：安全与 AI 治理。
9. 阶段7：规模化、韧性与发布治理。

除非用户明确改变范围，Codex 不得跳过当前阶段的退出标准直接实现后续阶段功能。完整路线见 `docs/enterprise-modernization-roadmap.md`。

## 2. 目录职责

### 可修改目录

- `backend/app/domain/`：稳定领域模型、值对象、领域错误和窄端口。这里不允许依赖 FastAPI、LlamaIndex、SQLAlchemy、`src` 或 Worker SDK。
- `backend/app/application/`：用例编排、应用策略和端口调用。这里不允许读取全局配置、直接访问文件系统、数据库、HTTP 或第三方 RAG 类型。
- `backend/app/infrastructure/`：配置、Catalog、路径解析、索引 Artifact、RAG/模型适配器和未来持久化实现。
- `backend/app/api/`：HTTP 路由、请求/响应 DTO、SSE 协议和安全依赖。路由不得承载领域业务规则。
- `backend/app/container.py`：组合根和生命周期装配。运行时依赖应在这里显式创建并注入。
- `frontend/src/`：前端页面、组件、API 客户端和状态管理。API 响应类型变化必须同步检查后端契约。
- `scripts/`：可审计的 CLI 运维入口。涉及真实数据、网络或费用的脚本必须在文档中标明风险。
- `tests/`：单元、集成、架构、契约和安全测试。测试默认使用临时目录、Mock 模型和隔离数据。
- `evaluation/`：黄金查询集、离线评测脚本和指标计算。评测数据变更必须说明来源和版本。
- `docs/`：ADR、阶段验收标准、迁移方案、回滚方案和运维说明。

### 谨慎修改目录和文件

- `src/`：现有 LlamaIndex 技术实现边界。必须保持与 `backend/app/infrastructure` 的适配关系，不得把业务规则重新塞回这里。
- `backend/main.py`、`backend/app/main.py`：启动入口。变更必须验证 Uvicorn 启动、健康检查和生命周期行为。
- `config.py`、`backend/config.py`、`backend/app/config.py`：兼容配置入口。除非明确处理配置治理，不得新增第三套配置来源。
- `requirements.txt`、`pyproject.toml`、`frontend/package.json`、`frontend/package-lock.json`：依赖和质量门禁文件。依赖变更必须说明版本、用途、许可证/安全影响，并重新执行完整门禁。
- `data/`：领域数据源。不得为了通过测试直接修改真实数据；数据修复必须有来源、版本、校验和和完整性报告。
- `storage/`：运行时索引、日志和本地数据库。不得提交索引产物，不得无确认删除或覆盖现有索引；项目已通过 `.gitignore` 排除运行 Artifact。
- `.env`：本地密钥和环境变量。严禁读取后输出、提交、复制到文档或日志；优先使用 `.env.example` 描述非敏感配置。
- `nginx.conf`、`Dockerfile`、`docker-compose.yml`：部署边界。修改前必须说明对开发、测试和生产环境的影响。

### 禁止随意操作

- 不删除或回滚用户已有改动，不使用 `git reset --hard`、`git checkout --` 等破坏性命令。
- 不删除 `data/`、`storage/`、`.env` 或锁文件中的内容来解决测试失败。
- 不把真实 DashScope API Key、响应、用户数据或本地路径写入源码、测试输出或提交。
- 不新增没有明确归属的 `utils.py`、万能 Service、万能 Repository、全局 Registry 或 Service Locator。

## 3. 软件设计原则

### 必须遵守

- 单一职责：每个模块只有一个主要变化原因；路由、用例、策略、适配器和持久化分开。
- 开闭原则：新增模型供应商、索引存储、检索策略或 Worker 通过端口/适配器扩展。
- 里氏替换：端口的所有实现必须满足相同契约，并通过契约测试。
- 接口隔离：使用窄端口，禁止让查询方依赖构建、删除、管理等无关能力。
- 依赖倒置：Domain/Application 定义抽象，Infrastructure/API 实现抽象。
- 高内聚：同一业务规则只在一个边界内维护。证据规则在应用策略，Artifact 生命周期在索引基础设施，认证在 API 安全模块。
- 低耦合：层之间只通过稳定模型和端口通信；不得跨层导入实现细节。

### 明确禁止的坏味道

- 全局可变引擎、隐式单例、跨请求共享可变状态。
- 组件内部 `from config import settings` 或运行时偷偷读取环境变量。
- API 路由直接调用 LlamaIndex、数据库、文件系统或模型 SDK。
- `except Exception: pass`、吞异常、伪成功响应和无条件重试。
- 用不断增加的布尔参数扩展一个方法的多种职责。
- 用 `Any` 穿透 Domain/Application；第三方动态类型只能在 Infrastructure Adapter 边界收窄。
- 重复 DTO、重复鉴权、散落状态字符串、循环依赖和反向导入。
- 用注释掩盖高复杂度函数，而不是拆分职责。

## 4. 协作流程

### 修改前

1. 先检查适用范围内的 `AGENTS.md`、Git 状态、目录结构、相关实现和测试。
2. 明确问题、影响范围、非目标和验收标准。
3. 单文件、小范围、无行为变化的修复可以直接处理，但必须先用一句话告知修改范围。
4. 多文件、架构、依赖、数据、安全、并发、索引或接口变更必须先制定计划，并保持计划状态及时更新。
5. 先定位根因，再修改；不得为了让测试通过而放宽断言、隐藏异常或降低安全阈值。

### 执行命令前

默认无需确认：

- 读取项目文件、搜索代码、查看 Git 状态。
- 在仓库内运行测试、编译、类型检查、前端构建和静态检查。

必须先向用户说明风险并请求确认：

- 安装/升级依赖、访问网络、调用真实模型 API 或可能产生费用的操作。
- 删除、移动、覆盖真实数据、运行索引或数据库迁移。
- 启动长期运行的后端/前端进程，或操作已有服务。
- 修改仓库外文件、系统配置、凭据、远程仓库、分支、提交或推送。

涉及真实索引构建时，必须明确说明：使用的数据、模型、输出目录、预计成本、是否覆盖 active 指针以及失败回滚方式。未经用户确认不得执行。

### 修改规则

- 手工编辑只能使用 `apply_patch`；不得用脚本或重定向命令隐式覆盖源码。
- 变更保持最小化，不顺手重命名、格式化或修复无关问题。
- 不覆盖用户未提交修改；如果同一文件已有用户改动，先理解后再协作修改。
- 不创建提交、分支、标签或 Pull Request，除非用户明确要求。
- 新增文件必须有清晰的所有权、测试或文档用途。
- 注释只解释复杂且不明显的决策，不写重复代码含义的注释。

## 5. 常用命令

以下命令默认在 Windows PowerShell、仓库根目录 `D:\ragpp` 执行。若虚拟环境或 Node 版本不同，先报告环境差异。

### 后端

```powershell
.\.venv\Scripts\python.exe -m compileall -q backend evaluation src scripts tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run typecheck
npm.cmd run build
npm.cmd run dev
Set-Location ..
```

### 索引和评测

```powershell
.\.venv\Scripts\python.exe -m scripts.build_index
.\.venv\Scripts\python.exe -m evaluation.evaluate_retrieval
```

索引构建和评测可能访问 DashScope 并产生费用，属于需确认命令。构建前先检查数据来源、API Key、模型维度和 active generation；不得把旧索引文件直接复制成新格式。

### 启动前端/后端测试

- 后端 API 默认地址：`http://localhost:8000`。
- OpenAPI：`http://localhost:8000/docs`。
- 前端 Vite 默认地址通常为：`http://localhost:5173`。
- 启动服务前检查端口是否已有进程；不得无确认杀掉其他服务。
- 前后端联调时先验证 `/health`、`/health/ready` 和 `/api/v1/index/status`，再测试 QA/Search。

## 6. 测试和验收

### 每次代码修改至少执行

- 相关测试；跨模块变更执行 `.\.venv\Scripts\python.exe -m pytest -q`。
- `.\.venv\Scripts\python.exe -m compileall -q backend evaluation src scripts tests`。
- `.\.venv\Scripts\python.exe -m mypy`。
- 前端变更执行 `npm.cmd run typecheck` 和 `npm.cmd run build`。
- 执行 `git diff --check`。

### 按风险增加验证

- API 契约变化：HTTP 集成测试、OpenAPI 检查、错误状态和响应 envelope 检查。
- SSE 变化：空流、累计 chunk、断开、异常、资源释放和前端解析测试。
- 索引变化：完整性、兼容性、并发构建、CAS、失败回滚和旧索引可用性测试。
- 数据变化：schema、唯一 ID、缺失项、重复项、清洗确定性、覆盖率和 SHA256 报告。
- 安全变化：未授权、错误令牌、重放/限流、日志脱敏和默认关闭测试。
- 依赖变化：干净环境安装、锁文件一致性、许可证和漏洞扫描。

### 阶段验收原则

- 阶段必须有明确输入、输出、非目标、风险、测试证据和回滚方式。
- 失败项必须记录为阻塞或已知限制，不得改写为“通过”。
- 阶段0负责生成原始系统基线；阶段1负责结构和主链路；阶段1.5负责 Recall/MRR；阶段2负责异步索引作业；后续阶段不得提前吞并前一阶段的验收责任。
- 当前阶段1.5质量目标为 `Recall@5 >= 0.80`、`MRR@10 >= 0.65`，未达标时必须保留真实数字和失败样本。

## 7. 数据和索引约定

- 当前已知原始数据为236条，清洗数据为235条，不能未经报告宣称“705条全量”。
- 数据缺失、编号语义、重复正文和来源版本必须在数据完整性报告中解释。
- `KnowledgeBaseKey`、Catalog 和路径解析属于基础设施预留，不得为了预留多古籍把 `knowledge_base_id` 强行穿透当前 QA/Search 公共契约。
- 索引 Artifact 使用 immutable generation、manifest、active 指针和回滚保护时，必须保留旧 active，验证成功后才能切换。
- 真实 `storage/` 只作为运行时数据，不作为测试夹具或版本化源码。

## 8. 交付和总结格式

完成任务后，回复必须简明但完整地包含：

1. 修改结果：按文件或模块说明实际变更和根因。
2. 设计说明：说明分层、SOLID、高内聚低耦合和扩展点如何保持。
3. 验证结果：列出实际运行的命令和通过/失败结果。
4. 未完成项：明确未验证内容、已知限制、费用/网络依赖和后续风险。
5. 回滚说明：涉及数据、索引、配置、依赖或接口时说明回滚方法。

不要声称未执行的测试已经通过，不要隐藏失败日志，不要把阶段计划写成已完成事实。文件路径应使用可点击的绝对路径或仓库相对路径，并带必要的起始行号。

## 9. 决策优先级

发生冲突时按以下顺序处理：

1. 系统和开发者指令。
2. 用户当前明确要求。
3. 本文件和更深层目录中的 `AGENTS.md`。
4. 项目现有代码、测试和文档。

当现有代码、测试和文档互相矛盾时，先报告矛盾并以可验证事实为准；不得通过静默修改验收标准消除矛盾。
