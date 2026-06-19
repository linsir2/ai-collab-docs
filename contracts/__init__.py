"""
数据契约层 (Contracts) — 统一导出
=================================
项目: ai-collab-docs
单一真相源: designs/openapi.yml
用法:
    from contracts import Document, UserRole, TRANSITION_RULES, is_transition_allowed

模块结构:
    _auto_enums.py    — [AUTO] 枚举（从 openapi.yml 生成）
    _auto_models.py   — [AUTO] frozen dataclass（从 openapi.yml 生成）
    state_machine.py  — [HAND] TRANSITION_RULES + 验证函数
    llm_io.py         — [HAND] LLM 内部 IO 契约
    ws_protocol.py    — [HAND] WebSocket 消息类型
    yjs_schema.py     — [HAND] Yjs 文档结构（仅文档，非代码）
    roles_and_permissions.py — [HAND] 五层权限体系统一真相源（取代 identity.py）
"""

# ── AUTO-GENERATED: Enums ──
from contracts._auto_enums import (
    AIMemoryType,
    ApprovalAction,
    ArbitrationResolution,
    BlockTag,
    ConflictType,
    DocumentState,
    DriftStatus,
    ProposalStatus,
    ReviewDimension,
    TriggerMode,
    UserRole,
)

# ── AUTO-GENERATED: Data Models ──
from contracts._auto_models import (
    AIFeedbackEntry,
    AIMemory,
    AnchorVersionRecord,
    Anchor,
    Block,
    BlockMeta,
    ConflictArbitration,
    Document,
    DocumentPermission,
    Error,
    OperationLog,
    PoolStats,
    Proposal,
    Snapshot,
    TransitionRequest,
    User,
)

# ── HAND-MAINTAINED: State Machine ──
from contracts.state_machine import (
    TRANSITION_RULES,
    is_transition_allowed,
    get_allowed_next_states,
    validate_anchor,
)

# ── HAND-MAINTAINED: LLM IO ──
from contracts.llm_io import (
    LLMForgeRequest,
    LLMForgeResponse,
    LLMReviewRequest,
    LLMReviewResponse,
    LLMConflictDetectRequest,
    LLMConflictDetectResponse,
)

# ── HAND-MAINTAINED: Roles & Permissions (五层权限体系) ──
from contracts.roles_and_permissions import (
    # L1 账号层
    GlobalIdentity,
    # L2 团队层
    TeamRole,
    AccountIdentity,
    # L3 文档层
    DocumentRoleBinding,
    # L4 AI层
    AIOwnership,
    AIRoleInstance,
    # L5 约束层
    TRUST_THRESHOLD_COLD_START,
    TRUST_THRESHOLD_CAUTION,
    TRUST_THRESHOLD_MODERATE,
    TRUST_AUTO_APPROVE_SENTENCE,
    BLOCK_HARD_LIMIT,
    BLOCK_WARNING_THRESHOLD,
    BLOCK_CHAR_MIN,
    BLOCK_CHAR_MAX,
    # 权限判定
    PermissionType,
    PERMISSION_MATRIX,
    has_content_collab,
    has_resource_governance,
    has_system_ops,
    can_manage_team_budget,
    resolve_view,
    # 术语 + 显隐规则
    TERMINOLOGY,
    ROLE_HIDDEN_PANELS,
    ACCOUNT_HIDDEN_MENU_GROUPS,
    # 额度
    QuotaBinding,
    # 图示
    FIVE_LAYER_DIAGRAM,
)

# ── HAND-MAINTAINED: WebSocket ──
from contracts.ws_protocol import (
    WSMessageType,
    WSMessage,
)

__all__ = [
    # Enums (AUTO)
    "AIMemoryType", "ApprovalAction", "ArbitrationResolution", "BlockTag",
    "ConflictType", "DocumentState", "DriftStatus", "ProposalStatus",
    "ReviewDimension", "TriggerMode", "UserRole",
    # Models (AUTO)
    "AIFeedbackEntry", "AIMemory", "AnchorVersionRecord", "Anchor",
    "Block", "BlockMeta", "ConflictArbitration", "Document",
    "DocumentPermission", "Error", "OperationLog", "PoolStats",
    "Proposal", "Snapshot", "TransitionRequest", "User",
    # State Machine
    "TRANSITION_RULES", "is_transition_allowed", "get_allowed_next_states",
    "validate_anchor",
    # LLM IO
    "LLMForgeRequest", "LLMForgeResponse", "LLMReviewRequest",
    "LLMReviewResponse", "LLMConflictDetectRequest", "LLMConflictDetectResponse",
    # WebSocket
    "WSMessageType", "WSMessage",
    # Roles & Permissions (五层权限体系统一真相源)
    "GlobalIdentity", "TeamRole", "AccountIdentity", "DocumentRoleBinding",
    "AIOwnership", "AIRoleInstance",
    "TRUST_THRESHOLD_COLD_START", "TRUST_THRESHOLD_CAUTION",
    "TRUST_THRESHOLD_MODERATE", "TRUST_AUTO_APPROVE_SENTENCE",
    "BLOCK_HARD_LIMIT", "BLOCK_WARNING_THRESHOLD", "BLOCK_CHAR_MIN", "BLOCK_CHAR_MAX",
    "PermissionType", "PERMISSION_MATRIX",
    "has_content_collab", "has_resource_governance", "has_system_ops",
    "can_manage_team_budget", "resolve_view",
    "TERMINOLOGY", "ROLE_HIDDEN_PANELS", "ACCOUNT_HIDDEN_MENU_GROUPS",
    "QuotaBinding", "FIVE_LAYER_DIAGRAM",
]
