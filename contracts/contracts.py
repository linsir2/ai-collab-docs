"""
AI文档锻造平台 — 数据契约 (Contracts)
======================================
项目: ai-collab-docs | MVP: 3-5人团队 | CRDT: Yjs
原则: frozen dataclass + typed enum + 单一写入者
      Yjs同步用官方二进制协议，自定义消息用外层JSON
"""

from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Optional, Any
import uuid

# ============================================================
# 1. 枚举定义
# ============================================================

class DocumentState(StrEnum):
    """文档生命周期状态 — 状态机定义"""
    DRAFT       = "draft"        # 草稿态
    DISCUSSION  = "discussion"   # 讨论态
    REVIEW      = "review"       # 审查态
    FINALIZED   = "finalized"    # 定稿态
    ARCHIVED    = "archived"     # 归档态

class UserRole(StrEnum):
    """五级人类权限"""
    OWNER       = "owner"        # 所有者 — 全部权限
    LEAD_EDITOR = "lead_editor"  # 主编辑 — 编辑+状态推进
    EDITOR      = "editor"       # 编辑者 — 编辑+AI提案审批
    REVIEWER    = "reviewer"     # 审查者 — 审查+审批
    READER      = "reader"       # 只读

class BlockTag(StrEnum):
    """Block 标签体系"""
    LOCKED_BY_HUMAN = "locked-by-human"   # 人类已锁定此Block，AI不可提案
    DUAL_TRACK      = "dual-track"         # 公私双轨对标标记
    CLAIMED         = "claimed"            # 段落已被认领（附claimantId）
    DRIFT_WARNING   = "drift-warning"       # 立意锚漂移预警

class AIMemoryType(StrEnum):
    """AI记忆公私域隔离"""
    PUBLIC  = "public"   # 文档级AI共享记忆
    PRIVATE = "private"  # 个人AI私有记忆

class ProposalStatus(StrEnum):
    """提案状态"""
    PENDING    = "pending"
    ACCEPTED   = "accepted"
    REJECTED   = "rejected"
    CONFLICTED = "conflicted"  # 进入冲突仲裁

class ReviewDimension(StrEnum):
    """审查维度 (MVP仅2维)"""
    EXPRESSION_PRECISION = "expression_precision"  # 表述精准
    POSITION_CONSISTENCY = "position_consistency"  # 立场一致

class ApprovalAction(StrEnum):
    """审批操作"""
    MERGE_ALL       = "merge_all"       # 全盘合并
    REJECT_ANNOTATE = "reject_annotate" # 拒绝批注
    MANUAL_EDIT     = "manual_edit"     # 手动编辑

class ArbitrationResolution(StrEnum):
    """仲裁裁决"""
    PROPOSAL_A = "proposal_a"
    PROPOSAL_B = "proposal_b"
    DECLINED   = "declined"  # 都拒绝

class ConflictType(StrEnum):
    """冲突类型"""
    PURE_PERSONAL   = "pure_personal"     # 纯个人AI冲突（仅本人可见）
    PURE_DOC_AI     = "pure_doc_ai"       # 纯文档级AI冲突
    MIXED           = "mixed"             # 个人AI vs 文档级AI混合冲突

# ============================================================
# 2. 核心数据契约
# ============================================================

@dataclass(frozen=True)
class Anchor:
    """立意锚 — 创建时锚定，不可被AI修改"""
    statement: str                          # 核心声明（一句话）
    target_audience: str                    # 目标读者
    core_argument: str                      # 核心论点
    version: int = 1
    created_by: str = ""                    # userId
    created_at: str = ""                    # ISO timestamp
    history: tuple[str, ...] = ()          # 版本历史快照

    # 不变量: AI零直改。Anchor变更必须经过人类确认。


@dataclass(frozen=True)
class BlockMeta:
    """Block元数据 — 存储在PostgreSQL，非Yjs文档内"""
    block_id: str
    doc_id: str
    tags: tuple[BlockTag, ...] = ()
    claimant_id: str = ""                   # 段落认领人 userId
    drift_score: float = 0.0               # 锚点偏离度 (0=完全一致)
    locked_by: str = ""                     # Locked-by-Human 锁定者

    # 写入者: DocumentService (唯一) — 权限校验后写入PG
    # Yjs中的实际内容由Y.Text管理，Meta是外挂的结构化标签


@dataclass(frozen=True)
class AIProposal:
    """AI提案 — AI产生的修改建议，无直改权限"""
    proposal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    block_id: str                           # 目标Block
    doc_id: str
    ai_source: str                          # "personal_ai:{userId}" 或 "doc_ai:{role}"
    ai_memory_type: AIMemoryType            # 提案基于哪种记忆
    old_content: str                        # 变更前内容（快照）
    new_content: str                        # 变更后建议
    rationale: str                          # 提案理由（AI自解释）
    anchor_alignment_score: float = 0.0     # 与立意锚对齐度
    created_at: str = ""                    # ISO timestamp
    status: ProposalStatus = ProposalStatus.PENDING

    # 不变量: new_content 不直接写入文档，必须经人类审批。
    # 写入者: ForgeService (唯一)


@dataclass(frozen=True)
class ReviewResult:
    """审查结果 — 审查者对文档/Block的评审"""
    review_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str
    snapshot_id: str                        # 基于哪个快照
    reviewer_id: str                        # 审查者 userId (可为AI)
    reviewer_type: str                      # "human" | "doc_ai:{role}"
    dimension: ReviewDimension
    verdict: str                            # "pass" | "fail" | "warning"
    comment: str = ""
    created_at: str = ""

    # 写入者: ReviewService (唯一)


@dataclass(frozen=True)
class ConflictArbitration:
    """冲突仲裁 — 2+AI提案对立时触发"""
    arb_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str
    block_id: str
    conflict_type: ConflictType
    proposals: tuple[str, ...]              # proposal_id列表
    ai_sources: tuple[str, ...]             # 冲突AI角色列表
    claimant_id: str = ""                   # 段落认领人（优先裁决者）
    resolution: Optional[ArbitrationResolution] = None
    decider_id: str = ""                    # 最终裁决者 userId
    decider_reason: str = ""
    resolved_at: str = ""

    # 不变量: 段落认领人(claimant)有优先裁决权。无认领人则沿决策上浮链。
    # 混合冲突(个人AI vs 文档AI)对全体可见（带角色标签）。
    # 纯个人AI冲突仅对当前用户可见。
    # 写入者: ReviewService → ConflictDetector


@dataclass(frozen=True)
class Snapshot:
    """文档快照 — 审查态入口创建，冻结当时的文档状态"""
    snap_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str
    state: DocumentState
    yjs_snapshot: bytes                     # Yjs encodeStateAsUpdate 产生的二进制
    block_metas: tuple[BlockMeta, ...]      # 快照时刻的所有BlockMeta
    anchor: Anchor                          # 快照时刻的Anchor
    created_by: str = ""
    created_at: str = ""

    # 写入者: ReviewService (唯一). 不可修改（不可变快照）


@dataclass(frozen=True)
class OperationLog:
    """操作日志 — 不可删除不可篡改"""
    op_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    action: str                             # "create_doc" | "approve_proposal" | "state_transition" | ...
    target_type: str                        # "document" | "block" | "proposal" | "arbitration" | ...
    target_id: str
    doc_id: str
    before_state: str = ""                  # JSON snapshot of before
    after_state: str = ""                   # JSON snapshot of after
    timestamp: str = ""                     # ISO timestamp

    # 写入者: AuditService (唯一). 不可删除/不可修改


@dataclass(frozen=True)
class User:
    """用户 — Auth限界上下文聚合根"""
    user_id: str
    display_name: str
    role: UserRole                          # 全局默认角色
    created_at: str = ""

    # 写入者: AuthService (唯一)


@dataclass(frozen=True)
class DocumentPermission:
    """文档级权限 — 用户在特定文档中的实际角色"""
    doc_id: str
    user_id: str
    effective_role: UserRole                # 可低于全局role（如Owner降为Reviewer，仅Owner可设）
    joined_at: str = ""
    invited_by: str = ""

    # 不变量: effective_role ≤ User.role (只能降权不能升权)
    # 写入者: AuthService (唯一)


# ============================================================
# 3. Yjs 文档结构契约（内存映射，非持久化schema）
# ============================================================

"""
Yjs Y.Doc 顶层共享类型映射:

Y.Doc
├── Y.Map("meta")
│   ├── "docId":       string          — 文档唯一ID
│   ├── "anchor":      JSON string     — Anchor序列化（只读参考副本）
│   └── "state":       string          — DocumentState值
│
├── Y.Array("blocks")
│   └── Y.Map (per block)
│       ├── "blockId":     string      — Block唯一ID
│       ├── "content":     Y.Text      — 实际文档内容（CRDT同步主体）
│       └── "order":       number      — 排序权重（支持拖拽）
│
├── Y.Map("cursorPositions")
│   └── Y.Map(per user)
│       ├── "blockId":     string
│       ├── "offset":      number
│       └── "selection":   JSON string — {anchor, head}
│
└── Y.Map("awareness")
    └── Y.Map(per user)
        ├── "name":        string
        ├── "color":       string
        └── "onlineAt":    string      — ISO timestamp

注意：
- BlockMeta (tags/claimantId/driftScore) 存储在PostgreSQL，不在Yjs中
- Yjs中的 meta.anchor 是只读参考副本，权威源在PostgreSQL
- cursorPositions 和 awareness 也可通过 Yjs Awareness API 管理
"""

# ============================================================
# 4. WebSocket 自定义消息契约（外层JSON）
# ============================================================

class WSMessageType(StrEnum):
    """WebSocket自定义消息类型"""
    # Yjs官方二进制同步 — 不走此JSON通道，直接Yjs Provider处理
    # 以下为自定义业务消息

    # 状态事件
    STATE_CHANGE     = "state_change"       # 文档状态变更通知
    DRIFT_ALERT       = "drift_alert"        # 立意锚漂移预警
    CONFLICT_DETECTED = "conflict_detected"  # 新冲突触发
    ARBITRATION_RESOLVED = "arbitration_resolved"  # 冲突已裁决

    # 提案事件
    PROPOSAL_CREATED  = "proposal_created"   # 新AI提案
    PROPOSAL_UPDATED  = "proposal_updated"   # 提案状态变更

    # 审查事件
    REVIEW_STARTED    = "review_started"     # 进入审查态
    REVIEW_COMPLETED  = "review_completed"   # 审查完成
    APPROVAL_CHANGED  = "approval_changed"   # 审批状态变更

    # 分页/同步指令
    PAGINATION_SYNC   = "pagination_sync"    # 分页同步（大文档）

    # 心跳
    PING = "ping"
    PONG = "pong"


@dataclass(frozen=True)
class WSMessage:
    """WebSocket自定义消息外层信封"""
    type: WSMessageType
    doc_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    sender_id: str = ""
    timestamp: str = ""

    # Yjs同步数据不经过此JSON通道。
    # Yjs Provider 通过独立的二进制通道同步 Y.Doc 的 update 消息。
    # 参见: y-protocols/sync 的 SyncStep1/SyncStep2/Update

"""
WS双通道架构说明:
┌─────────────────────────────────────────────┐
│              WebSocket 连接                   │
├─────────────────────────────────────────────┤
│  通道A: Yjs Sync Protocol (二进制)           │
│  - 由 y-websocket provider 处理             │
│  - 格式: Yjs官方 sync protocol messages     │
│  - 内容: Y.Doc 增量更新 (update),            │
│          awareness state, sync step          │
│  - 开发者不自定义此通道格式                   │
├─────────────────────────────────────────────┤
│  通道B: 自定义业务消息 (JSON)                 │
│  - WSMessage(type + docId + payload)         │
│  - 状态变更、漂移预警、冲突检测、提案通知等    │
│  - 不携带Yjs文档内容                         │
└─────────────────────────────────────────────┘

实现建议:
- 前端: y-websocket 库处理通道A;
        通道B在同一个WebSocket连接上通过自定义事件处理
- 服务端: python-yjs + y-py 处理通道A;
          JSON消息路由处理通道B
- 或者: 使用两个独立的WebSocket连接（简化通道隔离）
"""


# ============================================================
# 5. 状态机Transition契约
# ============================================================

TRANSITION_RULES = [
    # (from_state, to_state, allowed_roles)
    (DocumentState.DRAFT,      DocumentState.DISCUSSION, {UserRole.OWNER, UserRole.LEAD_EDITOR}),
    (DocumentState.DRAFT,      DocumentState.REVIEW,     {UserRole.OWNER}),  # 跳过讨论→直接审查
    (DocumentState.DISCUSSION, DocumentState.REVIEW,     {UserRole.OWNER, UserRole.LEAD_EDITOR}),
    (DocumentState.DISCUSSION, DocumentState.DRAFT,      {UserRole.OWNER, UserRole.LEAD_EDITOR}),
    (DocumentState.REVIEW,     DocumentState.FINALIZED,  {UserRole.OWNER}),  # 需所有审查者批准
    (DocumentState.REVIEW,     DocumentState.DISCUSSION, {UserRole.OWNER, UserRole.LEAD_EDITOR}),
    (DocumentState.REVIEW,     DocumentState.DRAFT,      {UserRole.OWNER}),
    (DocumentState.FINALIZED,  DocumentState.DRAFT,      {UserRole.OWNER}),  # 撤销定稿
    (DocumentState.FINALIZED,  DocumentState.ARCHIVED,   {UserRole.OWNER}),
]

# REVIEW → FINALIZED 守卫: allReviewersApproved AND snapshot.driftScore < threshold


# ============================================================
# 6. LLM输入/输出契约
# ============================================================

@dataclass(frozen=True)
class LLMForgeRequest:
    """向LLM请求提案时的输入格式"""
    anchor: Anchor                          # 全量锚点上下文
    block_content: str                      # 当前Block内容
    block_context: str                      # 前后Block上下文（≥3段，含Diff高亮）
    ai_role: str                            # AI角色（Legal/Editor/Reviewer/Creative...）
    memory_context: str                     # 对应AIMemory的最近反馈摘要
    instruction: str                        # 用户指令（@触发时带上）


@dataclass(frozen=True)
class LLMForgeResponse:
    """LLM返回的提案"""
    proposal_text: str                      # 建议修改后的完整内容
    diff_summary: str                       # 变更摘要（人类可读）
    rationale: str                          # 修改理由
    anchor_alignment_score: float           # 与立意锚的对齐度（LLM自查）


@dataclass(frozen=True)
class LLMReviewRequest:
    """向LLM请求审查时的输入格式"""
    anchor: Anchor
    snapshot_content: str                    # 快照全文
    dimension: ReviewDimension
    ai_role: str
    memory_context: str


@dataclass(frozen=True)
class LLMReviewResponse:
    """LLM返回的审查结果"""
    verdict: str                            # "pass" | "fail" | "warning"
    issues: tuple[str, ...]                 # 问题列表
    suggestions: tuple[str, ...]            # 建议列表


@dataclass(frozen=True)
class LLMConflictDetectRequest:
    """向LLM请求冲突检测时的输入格式"""
    anchor: Anchor
    proposal_a: str                         # 提案A内容
    proposal_a_rationale: str
    proposal_b: str                         # 提案B内容
    proposal_b_rationale: str


@dataclass(frozen=True)
class LLMConflictDetectResponse:
    """LLM返回的冲突检测结果"""
    is_opposing: bool                       # 是否对立
    conflict_description: str               # 冲突描述
    dimension: str                          # 冲突维度（内容/风格/立场）
