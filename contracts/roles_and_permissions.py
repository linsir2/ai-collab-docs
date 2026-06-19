"""
五层权限体系 — 统一真相源 (Roles & Permissions)
=================================================
项目: ai-collab-docs | 取代: contracts/identity.py
原则: 本文件是项目所有"角色/身份/权限/标签"的唯一定义索引。
      所有其他文件通过 contracts/__init__.py 引用，不直接 import 本文件。

五层架构:
  L1 账号层   — 你是谁登录的？（1人1身份，登录时固定）
  L2 团队层   — 你在团队里管什么？（v1隐式单团队，v2多团队）
  L3 文档层   — 你在这个文档里能做什么？（每文档不同）
  L4 AI角色层  — 哪个AI在说话？（多AI实例，各有立场和记忆）
  L5 操作约束层 — 这个操作允不允许？（Block/状态粒度）
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional, Literal
from uuid import uuid4

from contracts._auto_enums import AIMemoryType, BlockTag, ConflictType, DocumentState, TriggerMode, UserRole


# ═══════════════════════════════════════════════════════════════
# L1 — 账号层: 全局身份
# ═══════════════════════════════════════════════════════════════

class GlobalIdentity(StrEnum):
    """账号全局身份 — 登录时由企业后台分配，不随文档创建/分享改变"""
    REGULAR_USER = "regular_user"       # 标准用户（默认）
    TEAM_ADMIN = "team_admin"           # 团队管理员（企业后台手动授予）
    OPS_TECH = "ops_tech"               # 运维技术账号（独立业务体系）


# ═══════════════════════════════════════════════════════════════
# L2 — 团队层: 团队角色
# ═══════════════════════════════════════════════════════════════

class TeamRole(StrEnum):
    """团队内角色 — v1隐式单团队，v2多团队"""
    MEMBER = "member"
    ADMIN = "admin"


@dataclass(frozen=True)
class AccountIdentity:
    """请求上下文中的账号身份 — L1 ∩ L2"""
    global_id: GlobalIdentity = GlobalIdentity.REGULAR_USER
    team_id: str = "default"
    team_role: TeamRole = TeamRole.MEMBER


# ═══════════════════════════════════════════════════════════════
# L3 — 文档层: 文档局部角色（由 _auto_enums.UserRole 定义）
# ═══════════════════════════════════════════════════════════════
# UserRole: OWNER / LEAD_EDITOR / EDITOR / REVIEWER / READER
# —— 定义在 _auto_enums.py（auto-generated from openapi.yml）

@dataclass(frozen=True)
class DocumentRoleBinding:
    """用户在特定文档中的角色绑定"""
    doc_id: str
    user_id: str
    effective_role: str  # UserRole 枚举值
    bound_at: Optional[str] = None
    bound_by: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# L4 — AI角色层: AI身份与记忆
# ═══════════════════════════════════════════════════════════════

class AIOwnership(StrEnum):
    """AI归属方 — 该AI实例属于谁、对谁可见"""
    PERSONAL = "personal"        # 私域AI: 仅创建者可见
    DOC_PUBLIC = "doc_public"    # 公域AI: 全文档共享


@dataclass(frozen=True)
class AIRoleInstance:
    """一个具体的AI角色实例 — 每个文档中每个AI角色有独立的信任分和记忆"""
    role_name: str                     # "TechReviewer" / "LegalAgent" / 自定义名称
    ownership: AIOwnership
    doc_id: str
    owner_user_id: str = ""            # personal AI: 所属用户ID; doc_public: 空
    trust_score: int = 50              # 该实例在此文档中的信任分 [0,100]
    trigger_mode: TriggerMode = TriggerMode.MANUAL
    trust_score_decay: float = 0.95    # 月度衰减系数 (v1启用)


@dataclass(frozen=True)
class AIMemory:
    """AI记忆条目 — 存储隔离，AIMemoryType 区隔公私"""
    ai_source: str                     # AI角色名称
    memory_type: AIMemoryType          # PUBLIC / PRIVATE
    memory_id: str = field(default_factory=lambda: str(uuid4()))
    doc_id: str = ""
    feedback_log: Optional[list["AIFeedbackEntry"]] = None
    trust_score: int = 50
    solidified: bool = False           # ≥3次相同反馈才固化
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass(frozen=True)
class AIFeedbackEntry:
    """人类对AI提案的反馈记录"""
    proposal_id: str
    action: str                        # accepted / rejected
    human_feedback: Optional[str] = None
    timestamp: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# L5 — 操作约束层: Block标签 + 状态流转权限 + 信任分阈值
# ═══════════════════════════════════════════════════════════════
# BlockTag: locked-by-human / dual-track / claimed / drift-warning
# DocumentState: draft / discussion / review / finalized / archived
# —— 均在 _auto_enums.py 定义
#
# 信任分阈值:
TRUST_THRESHOLD_COLD_START = 50    # 新AI实例初始信任分
TRUST_THRESHOLD_CAUTION = 39       # ≤39: 谨慎审批
TRUST_THRESHOLD_MODERATE = 69      # 40-69: 适度信任, 70+: 高度信任
TRUST_AUTO_APPROVE_SENTENCE = 80   # v1: ≥80可自动采纳单句修改
TRUST_AUTO_APPROVE_PARAGRAPH = 90  # v1: ≥90可自动采纳段落修改
TRUST_ADOPT_BONUS = 3              # 采纳 +3
TRUST_REJECT_PENALTY = 2           # 拒绝 -2
TRUST_ARBITRATION_WIN = 10         # 仲裁胜出 +10
TRUST_ARBITRATION_LOSE = 15        # 仲裁失败 -15

# Block 内容约束:
BLOCK_HARD_LIMIT = 1000            # 单文档Block硬上限
BLOCK_WARNING_THRESHOLD = 900      # 黄色预警阈值
BLOCK_CHAR_MIN = 500               # Block最小字符
BLOCK_CHAR_MAX = 2000              # Block最大字符


# ═══════════════════════════════════════════════════════════════
# 跨层权限类型定义（三种独立权限）
# ═══════════════════════════════════════════════════════════════

PermissionType = Literal["content_collab", "resource_governance", "system_ops"]

# 权限判定矩阵: (GlobalIdentity, UserRole) → 允许的PermissionType
# 解释:
#   content_collab    — 编辑/审查/提案/仲裁（由 UserRole 决定）
#   resource_governance — 查看/熔断团队预算（由 GlobalIdentity.TEAM_ADMIN 决定）
#   system_ops         — 监控/修复/底层日志（由 GlobalIdentity.OPS_TECH 决定）

PERMISSION_MATRIX: dict[tuple[GlobalIdentity, str | None], set[PermissionType]] = {
    # 标准用户 + 任意文档角色
    (GlobalIdentity.REGULAR_USER, "any"):    {"content_collab"},
    # 团队管理员 + 任意文档角色（额外拥有资源治理权）
    (GlobalIdentity.TEAM_ADMIN, "any"):      {"content_collab", "resource_governance"},
    # 运维账号（仅系统运维权，不参与文档协作）
    (GlobalIdentity.OPS_TECH, "any"):        {"system_ops"},
}


# ═══════════════════════════════════════════════════════════════
# 权限判定辅助函数
# ═══════════════════════════════════════════════════════════════

def has_content_collab(identity: AccountIdentity) -> bool:
    """是否有内容协作权（所有登录用户都有）"""
    return identity.global_id != GlobalIdentity.OPS_TECH

def has_resource_governance(identity: AccountIdentity) -> bool:
    """是否有资源治理权（团队预算/成员/模板/规则管理）"""
    return identity.global_id == GlobalIdentity.TEAM_ADMIN

def has_system_ops(identity: AccountIdentity) -> bool:
    """是否有系统运维权"""
    return identity.global_id == GlobalIdentity.OPS_TECH

def can_manage_team_budget(identity: AccountIdentity) -> bool:
    """团队管理员对团队公共预算的治理权"""
    return (identity.global_id == GlobalIdentity.TEAM_ADMIN and
            identity.team_role == TeamRole.ADMIN)

def resolve_view(identity: AccountIdentity) -> Literal["创作视图", "团队管理视图", "运维监控视图"]:
    """根据账号身份解析默认视图"""
    if identity.global_id == GlobalIdentity.OPS_TECH:
        return "运维监控视图"
    if identity.global_id == GlobalIdentity.TEAM_ADMIN:
        return "团队管理视图"
    return "创作视图"


# ═══════════════════════════════════════════════════════════════
# 术语对照表 (中文 → 英文 → 代码enum)
# ═══════════════════════════════════════════════════════════════

TERMINOLOGY = {
    # L1 账号层
    "标准用户":       {"en": "Regular User",     "code": "GlobalIdentity.REGULAR_USER"},
    "团队管理员":     {"en": "Team Admin",        "code": "GlobalIdentity.TEAM_ADMIN"},
    "运维技术账号":   {"en": "Ops Tech",           "code": "GlobalIdentity.OPS_TECH"},
    # L2 团队层
    "团队成员":       {"en": "Team Member",       "code": "TeamRole.MEMBER"},
    "团队管理":       {"en": "Team Admin",        "code": "TeamRole.ADMIN"},
    # L3 文档层
    "文档所有者":     {"en": "Document Owner",    "code": "UserRole.OWNER"},
    "主编辑":         {"en": "Lead Editor",       "code": "UserRole.LEAD_EDITOR"},
    "编辑者":         {"en": "Editor",            "code": "UserRole.EDITOR"},
    "审查者":         {"en": "Reviewer",          "code": "UserRole.REVIEWER"},
    "只读用户":       {"en": "Reader",            "code": "UserRole.READER"},
    "段落负责人":     {"en": "Block Claimant",    "code": "BlockTag.CLAIMED"},
    # L4 AI层
    "私域AI":         {"en": "Personal AI",       "code": "AIOwnership.PERSONAL"},
    "公域AI":         {"en": "Doc Public AI",     "code": "AIOwnership.DOC_PUBLIC"},
    "私有记忆":       {"en": "Private Memory",    "code": "AIMemoryType.PRIVATE"},
    "公共记忆":       {"en": "Public Memory",     "code": "AIMemoryType.PUBLIC"},
    # L5 额度
    "个人额度":       {"en": "Personal Quota",    "code": "quota_source='personal'"},
    "团队额度":       {"en": "Team Quota",        "code": "quota_source='team'"},
}

# ═══════════════════════════════════════════════════════════════
# 显隐规则优先级链 (UI面板可见性判定顺序)
# ═══════════════════════════════════════════════════════════════
# 1. 角色显隐规则（L3 文档层）  — 无权限则直接隐藏面板
# 2. 账号视图规则（L1 账号层）  — 普通用户隐藏团队管理分组
# 3. 简易模式规则（UI偏好层）   — 额外隐藏高级面板
# 4. 脱敏规则（UI偏好层）       — 替代数值为文字标签
# 判定: 任何一层返回"隐藏"，则面板不渲染。
#       脱敏规则不隐藏面板，仅改变面板内展示内容。

# 角色面板显隐矩阵 (UserRole → 永久隐藏的面板)
ROLE_HIDDEN_PANELS: dict[UserRole, set[str]] = {
    UserRole.READER:       {"forge", "proposal", "state_transition", "claim", "archive", "memory_config", "discussion"},
    UserRole.REVIEWER:     {"claim_batch", "archive", "memory_reset", "team_budget"},
    UserRole.EDITOR:       {"member_permission", "archive", "memory_reset", "state_force_reset"},
    UserRole.LEAD_EDITOR:  {"team_bulk_rules", "team_budget_total"},
    UserRole.OWNER:        set(),  # 无隐藏（团队管理面板按账号身份隐藏）
}

# 账号视图分组显隐 (GlobalIdentity → 永久隐藏的Tools菜单分组)
ACCOUNT_HIDDEN_MENU_GROUPS: dict[GlobalIdentity, set[str]] = {
    GlobalIdentity.REGULAR_USER:  {"team_governance", "system_ops"},
    GlobalIdentity.TEAM_ADMIN:    {"system_ops"},
    GlobalIdentity.OPS_TECH:      {"forge_tools", "team_governance"},
}


# ═══════════════════════════════════════════════════════════════
# 额度治理规则 (problem.md §二审查意见#2-3)
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class QuotaBinding:
    """文档额度绑定 — 文档创建时确定，创建后不可切换"""
    doc_id: str
    quota_source: Literal["personal", "team"]  # 创建时绑定
    bound_by: str                              # 创建者ID
    bound_at: Optional[str] = None

# 规则:
# 1. 文档创建时绑定 quota_source，创建后不可切换（v2支持切换，需审计+管理员审批）
# 2. 协作者发起的AI提案消耗文档绑定的quota_source
# 3. 团队管理员对"消耗团队预算的文档"保留查看/熔断权限（不动内容/角色）


# ═══════════════════════════════════════════════════════════════
# 五层架构 ASCII 图 (供文档引用)
# ═══════════════════════════════════════════════════════════════

FIVE_LAYER_DIAGRAM = r"""
┌─────────────────────────────────────────────────────────────┐
│  L1 — 账号层: 你是谁登录的？（1人1身份，登录时固定）         │
│  GlobalIdentity: regular_user | team_admin | ops_tech       │
├─────────────────────────────────────────────────────────────┤
│  L2 — 团队层: 你在团队里管什么？（v1隐式单团队，v2多团队）    │
│  TeamRole: member | admin                                   │
├─────────────────────────────────────────────────────────────┤
│  L3 — 文档层: 你在这个文档里能做什么？（每文档不同）          │
│  UserRole: owner | lead_editor | editor | reviewer | reader │
├─────────────────────────────────────────────────────────────┤
│  L4 — AI角色层: 哪个AI在说话？（多AI实例，各有立场和记忆）    │
│  归属: personal(私域AI) | doc_public(公域AI)                │
│  角色: TechReviewer | LegalAgent | [用户自定义]...           │
│  记忆: public_memory(公共) | private_memory(私有)            │
├─────────────────────────────────────────────────────────────┤
│  L5 — 操作约束层: 这个操作允不允许？（Block/状态粒度）        │
│  Block标签: locked-by-human | claimed | dual-track | drift  │
│  文档状态: draft | discussion | review | finalized | archived│
│  AI信任分: 0-100（每个AI角色实例独立维护, 冷启动=50）        │
│  三种权限: 内容协作权 | 资源治理权 | 系统运维权               │
└─────────────────────────────────────────────────────────────┘
"""
