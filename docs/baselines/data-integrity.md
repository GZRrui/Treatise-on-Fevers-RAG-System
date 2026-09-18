# 阶段 0 数据完整性基线

## 结论

审计状态：**通过**。本地原始快照为 236 条，清洗及索引口径为 235 条。清洗结果可由版本化策略逐字节重建。

## 口径与来源

- 原始记录/唯一 ID：236 / 236
- 清洗记录/唯一 ID：235 / 235
- 排除 ID：[176]，原因是原始 `category=null`
- 本地 236 口径覆盖率：99.58%
- 外部 705 口径：`unverified-no-source-or-id-map`，无来源、许可、版本和 ID 映射，不作为权威分母
- 来源、许可、上游版本和采集日期仍未得到证据，详见 `data/dataset-manifest.json`

## 已知质量问题

- 原始重复正文：ID 94 与 173。
- `standard_id` 仅 9 个值；其现有语义是篇章区间起点，不是唯一条文编号。唯一性应使用 `id`。
- 方剂启发式候选 105 个，现有提取唯一值 77 个，候选检测率 68.57%。
- 候选但未提取：一名复脉汤, 不可与猪苓汤, 不可与白虎汤, 与五苓散, 与承气汤, 与禹余粮丸, 与调胃承气汤, 与麻黄汤, 乌梅丸, 五苓散, 可与调胃承气汤, 可与麻黄杏仁甘草石膏汤, 四逆散, 宜四逆汤, 宜大承气汤, 宜当归四逆加吴茱萸生姜汤, 宜桂枝二越婢一汤, 宜桂枝二麻黄一汤, 宜桂枝汤, 宜桂枝麻黄各半汤, 宜桃核承气汤, 宜理中丸, 宜瓜蒂散, 宜麻黄汤, 恐不为大柴胡汤, 攻表宜桂枝汤, 救表宜桂枝汤, 烧裈散, 然不及汤, 牡蛎泽泻散, 理中丸, 稍加至二十丸, 麻子仁丸。
- 方剂准确率仍需中医领域专家建立标注集后确认；当前数字仅是规则覆盖代理，不冒充人工准确率。

## 自动门禁

- PASS: `manifest_hashes_match`
- PASS: `manifest_counts_match`
- PASS: `raw_ids_unique`
- PASS: `clean_ids_unique`
- PASS: `clean_schema_valid`
- PASS: `only_known_raw_schema_error`
- PASS: `exclusions_match_policy`
- PASS: `clean_rebuild_matches_bytes`

## 重现

```shell
python scripts/data_quality.py
python scripts/data_quality.py --write-clean --update-reports
```
