# 阶段 0 验收与回滚

本文件定义阶段0的输入、证据产物、退出条件和回滚边界；“本机命令通过”不等于“全新机器/CI复现通过”。当前复核日期：2026-09-11。

## 范围证据

- 原始基准提交：`37d2c122cee1956c83d99f64996b4f15976053d4`
- 高阶工作区快照：分支 `codex/pre-phase-high-order-snapshot`，提交 `94e22e0`
- 阶段 0 分支：`codex/phase-0`
- ADR：`docs/adr/0001-phase-0-reproducible-baseline.md`

阶段 0 不包含证据三级策略、索引 generation/CAS、管理接口安全、前端协议修复或业务链路重构。

## 本地验收命令

```powershell
uv pip sync requirements-dev.txt --python .venv311\Scripts\python.exe --require-hashes
.\.venv311\Scripts\python.exe -m compileall -q backend config.py evaluation scripts src tests
.\.venv311\Scripts\python.exe -m pytest -q --basetemp .test-temp\pytest-phase0
.\.venv311\Scripts\python.exe -m mypy
.\.venv311\Scripts\python.exe -m ruff check backend/app/config.py scripts/capture_phase0_baseline.py scripts/data_quality.py scripts/snapshot_probe.py scripts/supply_chain.py tests/conftest.py tests/test_settings_contract.py
.\.venv311\Scripts\python.exe scripts\data_quality.py
.\.venv311\Scripts\python.exe scripts\capture_phase0_baseline.py
Push-Location frontend; npm ci --ignore-scripts; npm run typecheck; npm run build; Pop-Location
.\.venv311\Scripts\python.exe scripts\supply_chain.py --fail-on-vulnerability
```

## 验收状态

| 门禁 | 状态 | 证据 |
|---|---|---|
| 运行时及锁文件 | 本机证据通过；新机/CI 未执行 | 本机 Python `3.11.15`、Node `22.17.0`、npm `10.9.2`；前端 `npm ci` 已通过。哈希锁文件保留供 CI/新机器验证 |
| 环境契约 | 通过 | `docs/environment-matrix.md`、3 项配置契约测试 |
| 数据完整性 | 通过 | `docs/baselines/data-integrity.*`，236/235/ID 176/705 待证口径已解释 |
| 原始系统快照 | 通过 | `docs/baselines/original/`，重复运行匹配原始提交 |
| Python 门禁 | 有条件通过 | compileall、`--basetemp .test-temp\pytest-phase0` 下 12 项 pytest、strict mypy 通过；默认 Windows 临时目录曾因权限返回 1 error，不能隐藏该环境限制 |
| 前端门禁 | 通过 | Node 22/npm 10.9 下 `npm ci`、typecheck、Vite build |
| SBOM 与漏洞扫描 | 阻塞 | CycloneDX；Python 剩余 1 个无修复版本的 NLTK 漏洞，前端 high/critical 0；详见 `SEC-001` |

阶段0退出条件是：安装复现、环境复现、数据复现、行为复现和治理复现五项均有证据。当前只有本机证据和已生成报告，CI/新机安装尚未执行，因此阶段0暂不标记为“完全签收”；外部数据来源缺口仍必须阻塞阶段1.5前置条件。

## 2026-09-11 本地复核

- 运行时版本与契约一致：Python `3.11.15`、Node.js `22.17.0`、npm `10.9.2`。
- compileall、12 项离线 Pytest、阶段0 strict Mypy、阶段0限定 Ruff、数据完整性、原始系统快照、前端 `npm ci --ignore-scripts`、typecheck、build 和 `git diff --check` 均通过。
- 全仓 `ruff check backend tests scripts` 仍有 169 项遗留问题；这是阶段1全量质量门禁的真实输入，不计作阶段0限定 Ruff 失败，也不得写成阶段1已通过。
- CI 基线任务已配置完整 Git 历史检出，并在原始快照校验前验证原始提交对象存在；该修复尚未在远程 CI 执行，不能据此关闭“新机/CI 未执行”门禁。
- 供应链扫描已重新联网执行：前端 high/critical 为 0；Python 仍有 1 个无修复版本的 NLTK 漏洞（CVE-2026-81726 / GHSA-8mgp-746c-j5xp，最新 3.10.3 仍受影响）。该项保留为外部阻塞，未使用忽略参数或降低门禁。

## 阶段0交付边界

**输入**：原始提交 `37d2c122cee1956c83d99f64996b4f15976053d4`、当前数据文件、依赖声明、前端 lockfile、离线 Mock Provider 和固定查询集。

**输出**：哈希锁文件、环境矩阵、数据完整性报告、原始 OpenAPI/请求样例/质量快照、SBOM/漏洞报告、缺陷台账、ADR 和 CI 门禁。

**非目标**：不修复原始 API、检索、SSE、索引生命周期或前端协议；不把“705条”当作权威分母；不构建或覆盖真实线上索引，不调用收费 Provider。

## 回滚

阶段0未迁移业务数据且没有不可逆变更。代码回滚目标为原始基线 `main`/提交 `37d2c122cee1956c83d99f64996b4f15976053d4`，高阶原型通过 `codex/pre-phase-high-order-snapshot` 恢复；切换前必须先保存或清理当前未提交工作区，禁止强制覆盖。运行时产生的索引和数据库不属于 Git 回滚范围，删除或迁移前必须另行备份并审批。
