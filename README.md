# 《伤寒论》RAG 智能问答系统

基于 LlamaIndex、FastAPI 和 Vue 3 的《伤寒论》检索增强问答系统。当前分支只交付企业现代化阶段 0：可复现的原始系统基线，不包含后续阶段功能扩展。阶段0尚未完成全新机器/CI复现，阶段1尚未签收。

## 运行时

- Python `3.11.15`
- Node.js `22.17.0`
- npm `10.9.2`

Python 直接依赖维护在 `requirements.in`，开发依赖维护在 `requirements-dev.in`；安装只使用带哈希的锁文件。前端只使用 `npm ci`。

## 安装

```powershell
py -3.11 -m venv .venv311
uv pip sync requirements-dev.txt --python .venv311\Scripts\python.exe --require-hashes
Push-Location frontend
npm ci --ignore-scripts
Pop-Location
```

运行环境只需要 `requirements.txt`：

```powershell
uv pip sync requirements.txt --python .venv311\Scripts\python.exe --require-hashes
```

## 配置与启动

开发环境复制 `.env.example` 为 `.env`。默认使用 Mock Provider，不需要 API Key；切换线上 Provider 时必须显式关闭 `RAG_OFFLINE_MODE` 并设置 `DASHSCOPE_API_KEY`。

```powershell
.\.venv311\Scripts\python.exe scripts\build_index.py
.\.venv311\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

前端：

```powershell
Push-Location frontend
npm run dev
Pop-Location
```

环境矩阵见 `docs/environment-matrix.md`。生产环境拒绝 DEBUG、Mock Provider、默认或缺失密钥、缺失数据库连接以及宽泛、本地或非 HTTPS CORS 源。

## 阶段 0 验证

```powershell
.\.venv311\Scripts\python.exe -m compileall -q backend config.py evaluation scripts src tests
.\.venv311\Scripts\python.exe -m pytest -q --basetemp .test-temp\pytest-phase0
.\.venv311\Scripts\python.exe -m mypy
.\.venv311\Scripts\python.exe scripts\data_quality.py
.\.venv311\Scripts\python.exe scripts\capture_phase0_baseline.py
.\.venv311\Scripts\python.exe scripts\supply_chain.py --fail-on-vulnerability
Push-Location frontend; npm run typecheck; npm run build; Pop-Location
```

完整命令、验收状态和回滚步骤见 `docs/phase-0-acceptance.md`。阶段1实施前的输入、非目标和退出门槛见 `docs/phase-1-acceptance.md`。

## 基线事实

- 原始数据 236 条，清洗数据 235 条；ID 176 因 `category` 缺失被显式排除。
- “705 条”缺少来源、许可、版本和 ID 映射，不作为权威分母。
- 原始系统快照固定在提交 `37d2c122cee1956c83d99f64996b4f15976053d4`。
- 高阶工作区保存在 `codex/pre-phase-high-order-snapshot` 的提交 `94e22e0`，不得整体合并到阶段 0。

路线图见 `docs/enterprise-modernization-roadmap.md`，数据报告见 `docs/baselines/data-integrity.md`，缺陷归属见 `docs/phase-0-defects.md`，阶段1验收见 `docs/phase-1-acceptance.md`。

## License

MIT
