# 数据结构规范

本文定义两类数据契约：岗位配置（`references/role-configs/<role_id>.json`）与本地经验库（fact store）。两套契约分别由 `scripts/validate_role_configs.py` 与 `scripts/validate_fact_store.py` 确定性校验。

## 1. 岗位配置（role config）

每个文件一个岗位。文件名为 `<role_id>.json`，`role_id` 与文件内字段一致。

```json
{
  "schema_version": "1.0",
  "role_id": "overseas_growth",
  "name_zh": "海外用户/增长运营",
  "tier": "primary",
  "expression_focus": "基于区域用户与市场差异制定本地化增长策略，体现获客、留存及合作成效",
  "clusters": [
    {
      "cluster_id": "overseas_growth.localization_ops",
      "name_zh": "本地化运营",
      "scope": "distinctive",
      "keywords": ["本地化内容", "本土渠道", "区域策略", "文化适配", "本地合规"]
    }
  ],
  "action_verbs": ["制定", "策划", "拓展", "落地", "运营", "协同", "验证"],
  "typical_responsibilities": ["制定区域增长策略", "拓展本地渠道", "策划本地化内容与活动"],
  "typical_deliverables": ["本地化运营方案", "区域增长策略", "渠道合作清单"],
  "metric_examples": ["获客成本", "新增用户", "留存率", "区域 ROI", "渠道转化率"],
  "confusable_roles": {
    "product_operations": "产品运营偏产品功能驱动增长；海外增长偏区域市场与本地化渠道"
  }
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schema_version` | string | 是 | 契约版本；当前支持 `1.x` |
| `role_id` | string | 是 | 全局唯一，小写字母/数字/下划线，≤64 字符 |
| `name_zh` | string | 是 | 中文名称 |
| `tier` | string | 是 | `primary`（重点）/ `secondary`（辅助） |
| `expression_focus` | string | 是 | 表达重点（一至两句） |
| `clusters` | array | 是 | 能力簇列表，至少 1 个 |
| `action_verbs` | array<string> | 是 | 岗位常用动词 |
| `typical_responsibilities` | array<string> | 是 | 典型职责 |
| `typical_deliverables` | array<string> | 是 | 典型交付物 |
| `metric_examples` | array<string> | 是 | 指标口径示例 |
| `confusable_roles` | object | 是 | 键为易混淆 `role_id`，值为区分线索 |

簇（cluster）字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `cluster_id` | string | 是 | 全局唯一，格式 `role_id.cluster_slug` |
| `name_zh` | string | 是 | 能力簇中文名 |
| `scope` | string | 是 | `distinctive`（区分性）/ `generic`（通用，仅辅助证据） |
| `keywords` | array<string> | 是 | 非空关键词列表，无空串、无簇内重复 |

关键词的「同义 / 上下位」语义关系由通用匹配流程处理（见 `scoring.md` 的经历匹配），JSON 中只维护规范词表，不在每个关键词上重复存关系。通用能力（数据分析、沟通、协作、执行）不作为岗位簇写入，只在角色判定时作为辅助证据（见 `scoring.md`）。

### 校验规则（validate_role_configs.py）

- 必填字段存在、类型正确；
- `schema_version` 主版本兼容（当前仅 `1`）；
- `tier ∈ {primary, secondary}`，`scope ∈ {distinctive, generic}`；
- `role_id`、`cluster_id` 格式合法，`cluster_id` 前缀等于所属 `role_id`；
- 全部配置中 `role_id` 不重复、`cluster_id` 全局不冲突；
- `keywords` 非空、无空串、无簇内重复；
- 未知字段默认保留但不参与计算，未知 schema 主版本不静默解释；
- 单个配置无效时隔离该配置并报告原因，不使整批校验失败。

## 2. 本地经验库（fact store）

经验库不放在 Skill 安装目录，保存位置由运行环境决定并取得用户同意（见 `safety-and-privacy.md`）。一个 JSON 文件可包含多位候选人；实际使用中通常按候选人隔离。

```json
{
  "schema_version": "1.0",
  "candidates": [
    {
      "candidate_id": "cand_001",
      "facts": [
        {
          "fact_id": "fact_001",
          "candidate_id": "cand_001",
          "source_id": "src_001",
          "source_hash": "sha256:...",
          "source_version": "1",
          "fact_value": "在 XX 公司任产品运营，负责拉新活动，3 个月新增用户 10 万",
          "fact_status": "user_confirmed",
          "source_location": "page 2",
          "confirmed_at": "2026-09-18T10:05:00+08:00",
          "supersedes_fact_id": null,
          "scope": "reusable"
        }
      ]
    }
  ]
}
```

### 事实字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `fact_id` | string | 是 | 事实 ID，同一候选内唯一 |
| `candidate_id` | string | 是 | 必须等于所属 `candidate_id` |
| `source_id` | string | 是 | 源文件标识 |
| `source_hash` | string | 是 | 源文件哈希（版本判定用） |
| `source_version` | string | 是 | 源文件版本 |
| `fact_value` | string | 是 | 经历事实内容 |
| `fact_status` | string | 是 | 见下方枚举 |
| `source_location` | string | 是 | 来源位置（页码 / 章节 / 表格 / 段落） |
| `confirmed_at` | string \| null | 否 | 确认时间（ISO 8601） |
| `supersedes_fact_id` | string \| null | 否 | 指向被本事实取代的旧 `fact_id` |
| `scope` | string | 是 | 见下方枚举 |

### 事实状态 `fact_status`

| 值 | 含义 |
| --- | --- |
| `extracted` | 从材料直接提取 |
| `inferred` | 基于已有经历推断 |
| `user_confirmed` | 用户明确陈述或确认 |
| `conflicted` | 来源冲突 |
| `rejected` | 用户否认 |
| `superseded` | 被更新事实取代 |

### 复用范围 `scope`

| 值 | 含义 |
| --- | --- |
| `reusable` | 跨岗位可复用 |
| `role_specific` | 仅特定岗位适用 |
| `jd_specific` | 仅当前 JD 使用 |
| `writing_preference` | 写作偏好 |

### 校验规则（validate_fact_store.py）

- `schema_version` 主版本兼容；
- `candidate_id` 非空且全局唯一；
- 事实必填字段存在、类型正确；`candidate_id` 与所属候选一致；
- `fact_status`、`scope` 在枚举内；
- `supersedes_fact_id` 非空时须指向同一候选内已存在的 `fact_id`；
- `confirmed_at` 非空时须为可解析的 ISO 8601 时间。
