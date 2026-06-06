# 因果记忆系统（Causal Memory）

## 背景

2026-06-06，用户 L 提出核心洞察："向量匹配不是逻辑匹配，它做不到和人一样思考。"

这导致 Second Self 的 Phase 4 从"向量记忆（sqlite-vec）"彻底转向"因果记忆系统"。

## 核心区别

| | 向量记忆 | 因果记忆 |
|--|---------|---------|
| 原理 | 数学相似度（cosine distance） | 逻辑因果关系（因为/导致/从而） |
| 查询"网站慢" | 找到含"网站"、"慢"的记忆 | 找到"React → 慢 → SSR → 解决" |
| 可解释性 | 黑盒（两个向量近） | 白盒（展示因果链） |
| 学习成长 | 被动存储 | 主动归纳模式 |

## 借鉴项目

### Hindsight（15.8k stars）
- 核心：memory_links 表（causes/caused_by/enables/prevents）
- 检索：4路并行（semantic + BM25 + graph + temporal）
- 融合：RRF + Cross-Encoder 重排序

### Graphiti（Zep 平台）
- 核心：时序知识图谱（Episode → Entity → Edge）
- 节点：EpisodicNode / EntityNode / CommunityNode
- 边：EpisodicEdge / EntityEdge / HasEpisodeEdge

## 实现

### 文件
- `study-hub/second-self/memory_causal.py` — 因果记忆系统核心
- `study-hub/second-self/memory_store.py` — 集成因果表和自动提取

### 数据模型

```sql
-- 实体表
entities(id, name, entity_type, first_seen, last_seen, mention_count)

-- 记忆-实体关联
entry_entities(entry_id, entity_id)

-- 因果链接（核心）
causal_links(from_entry_id, to_entry_id, link_type, confidence, extracted_from)
-- link_type: causes | caused_by | enables | prevents | leads_to | results_in

-- 时序链接
temporal_links(from_entry_id, to_entry_id, relation, confidence)
-- relation: before | after | during | simultaneous
```

### 因果提取器

从记忆文本自动提取：
- **因果关系**：因为/导致/引起/使/让/从而/结果是...
- **时序关系**：之前/之后/同时
- **实体识别**：人/项目/技术/地点/概念

### 检索策略

```
用户提问 → 关键词种子 → 因果链扩展（前因后果）→ 时序扩展 → 实体扩展 → 融合排序 → 返回
```

融合权重：
- 种子结果：1.0
- 因果扩展：0.9 × confidence
- 时序扩展：0.7 × confidence
- 实体扩展：0.6 × confidence

## 关键修复

### 递归问题
`search_memory()` 调用 `causal_search()`，`causal_search()` 又调用 `search_memory()`，导致无限递归。

**修复**：`causal_search()` 内部调用 `search_memory(query, use_causal=False)` 避免递归。

### 子串匹配问题
"为" 是 "因为" 的子串，导致一句话被匹配两次。

**修复**：按标记词长度降序排序，长词优先匹配，匹配后跳过短词。

## 性能

- 因果检索：~0.35 秒/查询
- 零外部依赖（纯 SQLite + Python）

## 当前统计（2026-06-06）

- 总记忆：103 条
- 因果链接：17 条
- 时序链接：4 条
- 实体节点：11 个

## 待优化

1. 更多因果模式（条件句、假设句）
2. 因果链的可视化展示
3. 基于因果的预测（"如果做 X，可能会导致 Y"）
