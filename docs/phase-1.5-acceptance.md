# 阶段 1.5 检索质量专项验收

当前状态：**已进入，前置条件核验中，尚未签收**。阶段1已于2026-09-17按Windows目标环境签收。本文只推进检索质量专项，不提前实现异步 Worker、generation/CAS、PostgreSQL/pgvector或后续治理能力。

## 输入基线

- 数据口径：原始236条、清洗235条；原始 ID 176 因缺少 `category` 被排除。
- 正式索引：`shanghanlun` generation `20260805T062851Z-63195cbd0b8d`，235个文档，`text-embedding-v3`、1536维。
- 黄金集：28条，其中23条可回答、5条 hard-negative。
- 正式 Provider 基线：`Recall@5 = 0.2971`、`MRR@10 = 0.3304`、Top 5重复率 `0`、hard-negative误报率 `0`、检索 P95 `252.575 ms`。
- 证据：`docs/baselines/phase-1/provider-validation.json`。

## 前置条件状态

| ID | 条件 | 当前事实 | 状态 |
|---|---|---|---|
| PRE-001 | 权威数据分母和清洗规则确认 | 只有236/235本地口径；来源、许可、上游版本和采集日期缺证 | 阻塞正式发布口径 |
| PRE-002 | 索引覆盖率100%，排除项有书面原因 | generation覆盖235条；ID 176排除原因已记录，但尚待领域裁决 | 部分满足 |
| PRE-003 | 阶段1行为与架构签收 | Windows验收、Provider兼容性和回滚证据齐备 | 通过 |
| PRE-004 | 黄金集来源和版本可追溯 | 28条集已版本化，但人工标注来源和复核人未记录 | 待补 |

在 PRE-001/PRE-004 补齐前，可以进行可回滚的离线诊断和策略实验，但不得把实验结果宣称为权威质量结论或正式发布验收。

## 工作包

1. 对23条可回答查询逐条记录 Top 10、首个相关排名和失败类型，区分数据缺失、ID语义、切分、查询变体、向量召回、阈值过滤和排序问题。
2. 将黄金集按 exact、paraphrase、formula、symptom、chapter 和 hard-negative 切片，并补齐来源、版本、标注人和复核状态。
3. 在相同235条 generation 和相同查询集上建立 dense 基线；候选 lexical、hybrid、Reranker 必须通过独立 Adapter/Strategy 扩展。
4. 每次实验记录模型、参数、Recall/MRR、重复率、hard-negative误报率、P50/P95、token/费用和失败样本。
5. 保持 QA/Search HTTP 契约不变，并保留回退到阶段1 Retriever 的配置路径。

## 退出标准

- `Recall@5 >= 0.80`。
- `MRR@10 >= 0.65`。
- Top 5重复条文率为0。
- hard-negative误报率达到经批准阈值。
- P95检索延迟和单查询成本满足批准预算。
- 新策略可回退到阶段1 Retriever，API契约测试、完整Windows门禁和真实Provider小规模复核通过。

## 当前差距与非目标

- 当前距离 Recall 目标差 `0.5029`，距离 MRR 目标差 `0.3196`；不得通过删除失败样本、降低门槛或改变分母消除差距。
- `standard_id` 只有9个值且不是唯一条文ID，ID 94/173正文重复，方剂规则准确率未经人工复核；这些问题必须在质量解释中单独统计。
- “705条”没有来源、许可、版本和ID映射，不纳入当前分母。
- 本阶段不实现 Worker、队列、pgvector、active generation/CAS、证据三级策略或自动发布。

## 回滚

阶段1.5策略必须以独立 Adapter/Strategy 和配置选择接入。回滚时切回阶段1 Retriever；不重写现有 generation，不修改 active 指针，不删除旧索引。任何真实索引重建都必须另行说明数据、模型、输出目录、成本、切换方式和失败回滚，并再次获得确认。
