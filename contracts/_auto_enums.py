"""
AUTO-GENERATED from designs/openapi.yml
DO NOT EDIT MANUALLY.
Run: python contracts/gen_contracts.py
"""
from enum import StrEnum


# AI记忆公私域隔离
class AIMemoryType(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"

# 审批操作：merge_all=全盘合并, reject_annotate=拒绝批注, manual_edit=手动编辑
class ApprovalAction(StrEnum):
    MERGE_ALL = "merge_all"
    REJECT_ANNOTATE = "reject_annotate"
    MANUAL_EDIT = "manual_edit"

# 仲裁裁决
class ArbitrationResolution(StrEnum):
    PROPOSAL_A = "proposal_a"
    PROPOSAL_B = "proposal_b"
    DECLINED = "declined"

# Block标签：locked-by-human=人类锁定AI不可提案, dual-track=公私双轨对标, claimed=段落已认领, drift-warning=立意漂移预警
class BlockTag(StrEnum):
    LOCKED_BY_HUMAN = "locked-by-human"
    DUAL_TRACK = "dual-track"
    CLAIMED = "claimed"
    DRIFT_WARNING = "drift-warning"

# 冲突类型：pure_personal=纯个人AI(仅本人可见), pure_doc_ai=纯文档AI, mixed=混合冲突(全体可见带角色标签)
class ConflictType(StrEnum):
    PURE_PERSONAL = "pure_personal"
    PURE_DOC_AI = "pure_doc_ai"
    MIXED = "mixed"

# 文档生命周期状态：draft=草稿态, discussion=讨论态, review=审查态, finalized=定稿态, archived=归档态
class DocumentState(StrEnum):
    DRAFT = "draft"
    DISCUSSION = "discussion"
    REVIEW = "review"
    FINALIZED = "finalized"
    ARCHIVED = "archived"

# 立意漂移状态。normal=正常, warning=连续3次<0.85(审查态不可定稿), blocked=<0.8(硬拦截，需人类重新锚定)
class DriftStatus(StrEnum):
    NORMAL = "normal"
    WARNING = "warning"
    BLOCKED = "blocked"

# 提案状态
class ProposalStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CONFLICTED = "conflicted"

# 审查维度 (MVP仅2维：表述精准 + 立场一致)
class ReviewDimension(StrEnum):
    EXPRESSION_PRECISION = "expression_precision"
    POSITION_CONSISTENCY = "position_consistency"

# AI触发模式：manual=用户手动触发, auto=文档AI监听变更自动触发
class TriggerMode(StrEnum):
    MANUAL = "manual"
    AUTO = "auto"

# 五级人类权限
class UserRole(StrEnum):
    OWNER = "owner"
    LEAD_EDITOR = "lead_editor"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    READER = "reader"
