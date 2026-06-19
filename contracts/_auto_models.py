"""
AUTO-GENERATED from designs/openapi.yml
DO NOT EDIT MANUALLY.
Run: python contracts/gen_contracts.py
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from uuid import uuid4

from contracts._auto_enums import *  # noqa: F403


@dataclass(frozen=True)
class AIFeedbackEntry:
    """AI反馈条目 — 人类对AI提案的采纳/拒绝反馈记录"""
    proposal_id: str
    action: str
    human_feedback: Optional[str] = None
    timestamp: Optional[str] = None

@dataclass(frozen=True)
class AnchorVersionRecord:
    """Anchor 版本历史记录"""
    version: int
    statement: str
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None

@dataclass(frozen=True)
class BlockMeta:
    """Block元数据 — 存储在PostgreSQL的外挂结构化标签。block_id/doc_id/order在Block层，不在此重复。"""
    tags: Optional[list[BlockTag]] = None
    claimant_id: Optional[str] = None
    drift_score: Optional[float] = 0
    version: Optional[int] = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass(frozen=True)
class ConflictArbitration:
    """冲突仲裁 — 2+AI提案对立时触发。段落认领人有优先裁决权，无人认领沿决策上浮链。"""
    conflict_type: ConflictType
    proposals: list[str]
    arb_id: str = field(default_factory=lambda: str(uuid4()))
    doc_id: str = field(default_factory=lambda: str(uuid4()))
    block_id: str = field(default_factory=lambda: str(uuid4()))
    ai_sources: Optional[list[str]] = None
    claimant_id: Optional[str] = None
    resolution: Optional[ArbitrationResolution] = None
    decider_id: Optional[str] = None
    decider_reason: Optional[str] = None
    resolved_at: Optional[str] = None

@dataclass(frozen=True)
class DocumentPermission:
    """文档级权限 — 用户在特定文档中的实际角色。不变量：effective_role ≤ User.role。"""
    user_id: str
    effective_role: UserRole
    doc_id: str = field(default_factory=lambda: str(uuid4()))
    joined_at: Optional[str] = None
    invited_by: Optional[str] = None

@dataclass(frozen=True)
class Error:
    code: str
    message: str
    detail: Optional[str] = None

@dataclass(frozen=True)
class OperationLog:
    """操作日志 — 不可删除不可篡改。AuditService唯一写入者。"""
    user_id: str
    action: str
    target_type: str
    target_id: str
    timestamp: str
    op_id: str = field(default_factory=lambda: str(uuid4()))
    doc_id: str = field(default_factory=lambda: str(uuid4()))
    before_state: Optional[str] = None
    after_state: Optional[str] = None

@dataclass(frozen=True)
class PoolStats:
    """提案池容量统计 — 双轨AI的公私池计数与三级预警（80%橙/95%弹窗/100%阻断）"""
    public_count: int
    private_count: int
    public_limit: int
    private_limit: int
    global_count: Optional[int] = 0
    public_warning: Optional[bool] = False
    private_warning: Optional[bool] = False
    public_popup: Optional[bool] = False
    private_popup: Optional[bool] = False
    public_blocked: Optional[bool] = False
    private_blocked: Optional[bool] = False
    global_blocked: Optional[bool] = False

@dataclass(frozen=True)
class Proposal:
    """AI提案 — AI零直改权限：仅提案/批注/争议举证，无直接修改权。"""
    ai_source: str
    content_before: str
    content_after: str
    rationale: str
    status: ProposalStatus
    prop_id: str = field(default_factory=lambda: str(uuid4()))
    doc_id: str = field(default_factory=lambda: str(uuid4()))
    block_id: str = field(default_factory=lambda: str(uuid4()))
    ai_role: Optional[str] = None
    anchor_alignment_score: Optional[float] = 0
    memory_type: Optional[AIMemoryType] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None

@dataclass(frozen=True)
class TransitionRequest:
    """状态流转请求 — 受TRANSITION_MATRIX权限约束"""
    target_state: DocumentState
    reason: Optional[str] = None

@dataclass(frozen=True)
class User:
    """用户 — Auth BC聚合根。文档级权限见DocumentPermission。"""
    display_name: str
    role: UserRole
    user_id: str = field(default_factory=lambda: str(uuid4()))
    email: Optional[str] = None
    created_at: Optional[str] = None

@dataclass(frozen=True)
class AIMemory:
    """AI记忆 — 公私域隔离。六层隔离：存储/访问/写入/可见性/生命周期/固化≥3次。"""
    ai_source: str
    memory_type: AIMemoryType
    memory_id: str = field(default_factory=lambda: str(uuid4()))
    doc_id: str = field(default_factory=lambda: str(uuid4()))
    feedback_log: Optional[list[AIFeedbackEntry]] = None
    approval_history: Optional[list[str]] = None
    rejection_history: Optional[list[str]] = None
    long_term_patterns: Optional[list[str]] = None
    trust_score: Optional[int] = 50
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass(frozen=True)
class Anchor:
    """立意锚 — 文档唯一锚点。创建时必填，所有AI能力/修改必须对齐此锚。仅Owner可修改。"""
    statement: str
    target_audience: str
    core_argument: str
    version: int
    version_history: Optional[list[AnchorVersionRecord]] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None

@dataclass(frozen=True)
class Block:
    """Block视图 — 聚合BlockMeta + 内容预览。实际内容通过Yjs同步。"""
    order: float
    block_id: str = field(default_factory=lambda: str(uuid4()))
    doc_id: str = field(default_factory=lambda: str(uuid4()))
    content_preview: Optional[str] = None
    meta: Optional[BlockMeta] = None

@dataclass(frozen=True)
class Document:
    """文档聚合根 — BC1核心实体。状态流转受StateEngine约束，Block内容走Yjs同步。"""
    anchor: Anchor
    state: DocumentState
    owner_id: str
    doc_id: str = field(default_factory=lambda: str(uuid4()))
    title: Optional[str] = None
    mode: Optional[str] = "heavy_forge"
    block_count: Optional[int] = 0
    proposal_count_public: Optional[int] = 0
    proposal_count_private: Optional[int] = 0
    drift_status: Optional[DriftStatus] = None
    tags: Optional[list[BlockTag]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    archived_at: Optional[str] = None

@dataclass(frozen=True)
class Snapshot:
    """文档快照 — 审查态入口创建，冻结当时文档状态。不可修改。"""
    state: DocumentState
    created_by: str
    snap_id: str = field(default_factory=lambda: str(uuid4()))
    doc_id: str = field(default_factory=lambda: str(uuid4()))
    yjs_snapshot: Optional[str] = None
    block_metas: Optional[list[BlockMeta]] = None
    anchor: Optional[Anchor] = None
    created_at: Optional[str] = None