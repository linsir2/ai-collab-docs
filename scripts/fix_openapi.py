#!/usr/bin/env python3
"""Fix openapi.yml — remove duplication, extract inline types, fix Error $ref"""
import re
from pathlib import Path

OPENAPI = Path("/home/linsir365/projects/ai-collab-docs/designs/openapi.yml")
txt = OPENAPI.read_text(encoding="utf-8")

# ── Fix 1: BlockMeta — remove block_id/doc_id/order ──
old_bm = """    BlockMeta:
      type: object
      required:
      - block_id
      - doc_id
      - order
      properties:
        block_id:
          type: string
          format: uuid
          description: Block唯一ID
        doc_id:
          type: string
          format: uuid
          description: 所属文档ID
        order:
          type: number
          description: 排序权重（支持拖拽）
        tags:
          type: array
          items:
            $ref: '#/components/schemas/BlockTag'
          description: 标签集合
        claimant_id:
          type: string
          description: 段落认领人userId，有认领人则AI不可对此Block提案
        drift_score:
          type: number
          description: 语义漂移分（余弦相似度），仅审查态触发检测
        version:
          type: integer
          description: Block内容版本号
          default: 1
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
      description: Block元数据 — 存储在PostgreSQL。实际内容(Y.Text)在Yjs中同步。"""
new_bm = """    BlockMeta:
      type: object
      properties:
        tags:
          type: array
          items:
            $ref: '#/components/schemas/BlockTag'
          description: 标签集合（locked-by-human/dual-track/claimed/drift-warning）
        claimant_id:
          type: string
          description: 段落认领人userId，有认领人则AI不可对此Block提案
        drift_score:
          type: number
          description: 语义漂移分（余弦相似度），仅审查态触发检测
        version:
          type: integer
          description: Block内容版本号
          default: 1
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
      description: Block元数据 — 存储在PostgreSQL的外挂结构化标签。block_id/doc_id/order在Block层，不在此重复。"""
assert old_bm in txt, "BlockMeta not found!"
txt = txt.replace(old_bm, new_bm)
print("✅ Fix1: BlockMeta deduplicated")

# ── Fix 2: Error $ref misuse ──
# Pattern: under response status, $ref to Error schema without content wrapper
error_ref_pattern = re.compile(
    r"(('4\d{2}'|'5\d{2}'):\s*\n\s+)\$ref:\s*'#/components/schemas/Error'\s*\n\s+description:\s*([^\n]+)",
    re.MULTILINE
)
repl_count = [0]
def fix_err(m):
    status_line = m.group(1)
    desc_text = m.group(3).strip()
    return f"""{status_line}description: {desc_text}
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'"""
repl_count[0] = 0
def counter(m):
    repl_count[0] += 1
    return fix_err(m)
txt = error_ref_pattern.sub(counter, txt)
print(f"✅ Fix2: Error $ref misuse fixed ({repl_count[0]} instances)")

# ── Fix 3: AnchorVersionRecord ──
old_av = """        version_history:
          type: array
          items:
            type: object
            properties:
              version:
                type: integer
              statement:
                type: string
              updated_at:
                type: string
                format: date-time
              updated_by:
                type: string
          description: 版本历史（仅Owner可修改Anchor）"""
new_av = """        version_history:
          type: array
          items:
            $ref: '#/components/schemas/AnchorVersionRecord'
          description: 版本历史（仅Owner可修改Anchor）"""
assert old_av in txt, "AnchorVersionRecord not found!"
txt = txt.replace(old_av, new_av)
av_schema = """    AnchorVersionRecord:
      type: object
      required:
      - version
      - statement
      properties:
        version:
          type: integer
        statement:
          type: string
        updated_at:
          type: string
          format: date-time
        updated_by:
          type: string
      description: Anchor 版本历史记录"""
txt = txt.replace("    Anchor:", av_schema + "\n" + "    Anchor:", 1)
print("✅ Fix3: AnchorVersionRecord extracted")

# ── Fix 4: AIFeedbackEntry ──
old_fl = """        feedback_log:
          type: array
          items:
            type: object
            properties:
              proposal_id:
                type: string
              action:
                type: string
                enum:
                - accepted
                - rejected
              human_feedback:
                type: string
              timestamp:
                type: string
                format: date-time
          description: 反馈日志（≥3次相同反馈才固化长期记忆）"""
new_fl = """        feedback_log:
          type: array
          items:
            $ref: '#/components/schemas/AIFeedbackEntry'
          description: 反馈日志（≥3次相同反馈才固化长期记忆）"""
assert old_fl in txt, "AIFeedbackEntry not found!"
txt = txt.replace(old_fl, new_fl)
fe_schema = """    AIFeedbackEntry:
      type: object
      required:
      - proposal_id
      - action
      properties:
        proposal_id:
          type: string
        action:
          type: string
          enum:
          - accepted
          - rejected
        human_feedback:
          type: string
        timestamp:
          type: string
          format: date-time
      description: AI反馈条目 — 人类对AI提案的采纳/拒绝反馈记录"""
txt = txt.replace("    AIMemory:", fe_schema + "\n" + "    AIMemory:", 1)
print("✅ Fix4: AIFeedbackEntry extracted")

# ── Fix 5: PoolStats ──
old_ps = """                  pool_stats:
                    type: object
                    properties:
                      public_count:
                        type: integer
                        description: 公共池当前计数(上限800)
                      private_count:
                        type: integer
                        description: 私有池当前计数(上限400)
                      public_warning:
                        type: boolean
                        description: ≥80%(640)橙色预警
                      private_warning:
                        type: boolean
                        description: ≥80%(320)橙色预警"""
new_ps = """                  pool_stats:
                    $ref: '#/components/schemas/PoolStats'"""
assert old_ps in txt, "PoolStats not found!"
txt = txt.replace(old_ps, new_ps)
pool_schema = """    PoolStats:
      type: object
      required:
      - public_count
      - private_count
      properties:
        public_count:
          type: integer
          description: 公共池当前计数（文档AI，上限800）
        private_count:
          type: integer
          description: 私有池当前计数（个人AI合计，上限400）
        public_warning:
          type: boolean
          description: 公共池 ≥80%(640) 橙色预警
          default: false
        private_warning:
          type: boolean
          description: 私有池 ≥80%(320) 橙色预警
          default: false
      description: 提案池容量统计 — 双轨AI的公私池计数与预警"""
txt = txt.replace("    Proposal:", pool_schema + "\n" + "    Proposal:", 1)
print("✅ Fix5: PoolStats extracted")

# ── Fix 6: DriftStatus enum ──
old_ds = """        drift_status:
          type: string
          enum:
          - normal
          - warning
          - blocked
          description: 漂移状态"""
new_ds = """        drift_status:
          $ref: '#/components/schemas/DriftStatus'
          description: 漂移状态（连续3次<0.85→warning, <0.8→blocked）"""
assert old_ds in txt, "DriftStatus not found!"
txt = txt.replace(old_ds, new_ds)
drift_schema = """    DriftStatus:
      type: string
      enum:
      - normal
      - warning
      - blocked
      description: 立意漂移状态。normal=正常, warning=连续3次<0.85(审查态不可定稿), blocked=<0.8(硬拦截，需人类重新锚定)"""
txt = txt.replace("    DocumentState:", drift_schema + "\n" + "    DocumentState:", 1)
print("✅ Fix6: DriftStatus extracted")

# ── Fix 7: transition_conditions ──
old_tc = """                  transition_conditions:
                    type: object
                    description: 各可用转换的守卫条件（如review→finalized需allReviewersApproved + driftScore ≥ 0.8）"""
new_tc = """                  transition_conditions:
                    type: object
                    description: 各可用转换的守卫条件
                    properties:
                      all_reviewers_approved:
                        type: boolean
                        description: 所有审查者已批准（review→finalized守卫）
                      drift_score_ok:
                        type: boolean
                        description: 漂移分≥0.8（review→finalized守卫）
                      block_count_ok:
                        type: boolean
                        description: Block数<1000上限"""
assert old_tc in txt, "transition_conditions not found!"
txt = txt.replace(old_tc, new_tc)
print("✅ Fix7: transition_conditions defined")

OPENAPI.write_text(txt, encoding="utf-8")
print(f"\n✅ All done. Final: {len(txt)} chars, {txt.count(chr(10))} lines")
