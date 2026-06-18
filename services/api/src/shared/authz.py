"""授权真值源 — 后端权限/视图/菜单/WebSocket 的权威判定。

所有视图入口、文档内操作、WebSocket 消息发送权限均由此模块集中定义，
避免在路由/服务/gateway 中散落权限常量。
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from contracts.contracts import GlobalRole

# re-export 全局角色，保持 contracts 为唯一枚举源
__all__ = [
    "GlobalRole",
    "DocRole",
    "ViewType",
    "MenuGroup",
    "can_access_view",
    "allowed_views",
    "allowed_menu_groups",
    "can_do_in_document",
    "default_doc_permissions",
    "is_allowed_ws_message",
    "format_global_role_label",
    "format_doc_role_label",
    "trust_score_label",
    "drift_label",
    "block_tag_label",
    "audit_action_label",
]


class DocRole(StrEnum):
    """文档内人类角色 — 与 contracts.UserRole 值保持一致。"""

    OWNER = "owner"
    LEAD_EDITOR = "lead_editor"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    READER = "reader"


class ViewType(StrEnum):
    """顶部视图入口。"""

    FORGE = "forge"
    TEAM = "team"
    OPS = "ops"


class MenuGroup(StrEnum):
    """侧边栏菜单分组。"""

    FORGE_TOOLS = "forge_tools"
    TEAM_MGMT = "team_mgmt"
    OPS_MONITOR = "ops_monitor"


# ============================================================
# 1. 视图与菜单权限
# ============================================================

_VIEW_ACCESS: dict[GlobalRole, set[ViewType]] = {
    GlobalRole.PERSONAL: {ViewType.FORGE},
    GlobalRole.TEAM_ADMIN: {ViewType.FORGE, ViewType.TEAM},
    GlobalRole.OPS: {ViewType.FORGE, ViewType.TEAM, ViewType.OPS},
}

_MENU_GROUPS_BY_VIEW: dict[ViewType, dict[GlobalRole, list[MenuGroup]]] = {
    ViewType.FORGE: {
        GlobalRole.PERSONAL: [MenuGroup.FORGE_TOOLS],
        GlobalRole.TEAM_ADMIN: [MenuGroup.FORGE_TOOLS, MenuGroup.TEAM_MGMT],
        GlobalRole.OPS: [MenuGroup.FORGE_TOOLS, MenuGroup.TEAM_MGMT, MenuGroup.OPS_MONITOR],
    },
    ViewType.TEAM: {
        GlobalRole.TEAM_ADMIN: [MenuGroup.TEAM_MGMT],
        GlobalRole.OPS: [MenuGroup.TEAM_MGMT, MenuGroup.OPS_MONITOR],
    },
    ViewType.OPS: {
        GlobalRole.OPS: [MenuGroup.OPS_MONITOR],
    },
}


def can_access_view(global_role: GlobalRole, view: ViewType) -> bool:
    """判定某全局角色是否可进入指定顶部视图。"""
    return view in _VIEW_ACCESS.get(global_role, set())


def allowed_views(global_role: GlobalRole) -> list[ViewType]:
    """返回某全局角色可进入的全部视图（固定顺序）。"""
    return [view for view in ViewType if view in _VIEW_ACCESS.get(global_role, set())]


def allowed_menu_groups(global_role: GlobalRole, view: ViewType) -> list[MenuGroup]:
    """返回某角色在指定视图下可见的菜单分组。"""
    view_map = _MENU_GROUPS_BY_VIEW.get(view, {})
    return list(view_map.get(global_role, []))


# ============================================================
# 2. 文档内操作权限
# ============================================================

_DOC_ACTIONS: dict[str, set[DocRole]] = {
    "state_transition": {DocRole.OWNER, DocRole.LEAD_EDITOR},
    "archive": {DocRole.OWNER},
    "manage_members": {DocRole.OWNER},
    "assign_paragraphs": {DocRole.OWNER, DocRole.LEAD_EDITOR},
    "reset_memory": {DocRole.OWNER},
    "use_forge": {DocRole.OWNER, DocRole.LEAD_EDITOR, DocRole.EDITOR},
    "start_review": {DocRole.OWNER, DocRole.LEAD_EDITOR, DocRole.REVIEWER},
    "resolve_arbitration": {DocRole.OWNER, DocRole.LEAD_EDITOR},
    "discuss": {DocRole.OWNER, DocRole.LEAD_EDITOR, DocRole.EDITOR, DocRole.REVIEWER, DocRole.READER},
    "claim_paragraph": {DocRole.OWNER, DocRole.LEAD_EDITOR, DocRole.EDITOR, DocRole.REVIEWER},
}


def _str(value: Any) -> str:
    """统一把字符串或枚举转成字符串值。"""
    return value.value if isinstance(value, StrEnum) else str(value)


def can_do_in_document(doc_role: DocRole, action: str) -> bool:
    """判定某文档角色是否有权执行指定操作。"""
    allowed = _DOC_ACTIONS.get(action)
    if allowed is None:
        return False
    return doc_role in allowed


def default_doc_permissions() -> dict[str, set[DocRole]]:
    """返回所有文档操作的默认允许角色集合（深拷贝，防止外部修改）。"""
    return {action: set(roles) for action, roles in _DOC_ACTIONS.items()}


# ============================================================
# 3. WebSocket 消息发送权限
# ============================================================

_WS_MESSAGE_PERMISSIONS: dict[str, set[DocRole]] = {
    "STATE_CHANGE": {DocRole.OWNER, DocRole.LEAD_EDITOR},
    "PROPOSAL_CREATED": {DocRole.OWNER, DocRole.LEAD_EDITOR, DocRole.EDITOR},
    "CONFLICT_DETECTED": {DocRole.OWNER, DocRole.LEAD_EDITOR, DocRole.REVIEWER},
    "AI_BROADCAST": {DocRole.OWNER, DocRole.LEAD_EDITOR, DocRole.EDITOR, DocRole.REVIEWER},
}


def is_allowed_ws_message(doc_role: DocRole, msg_type: str) -> bool:
    """判定某文档角色是否有权发送指定类型的 WebSocket 业务消息。

    注意：AI_BROADCAST 等只读类消息可被读者接收，但本函数只判定"发送"权限。
    默认规则：只要具备 reader 及以上文档成员身份即可发送其他未列明消息。
    """
    allowed = _WS_MESSAGE_PERMISSIONS.get(msg_type.upper())
    if allowed is None:
        return doc_role in set(DocRole)
    return doc_role in allowed


# ============================================================
# 4. 标签/展示文案辅助函数
# ============================================================

_GLOBAL_ROLE_LABELS: dict[GlobalRole, str] = {
    GlobalRole.PERSONAL: "个人用户",
    GlobalRole.TEAM_ADMIN: "团队管理员",
    GlobalRole.OPS: "运维管理员",
}

_DOC_ROLE_LABELS: dict[DocRole, str] = {
    DocRole.OWNER: "所有者",
    DocRole.LEAD_EDITOR: "主编辑",
    DocRole.EDITOR: "编辑者",
    DocRole.REVIEWER: "审查者",
    DocRole.READER: "只读成员",
}


def format_global_role_label(role: GlobalRole) -> str:
    return _GLOBAL_ROLE_LABELS.get(role, role.value)


def format_doc_role_label(role: DocRole) -> str:
    return _DOC_ROLE_LABELS.get(role, role.value)


def trust_score_label(score: int) -> str:
    """根据信任分返回中文等级（0-100）。"""
    if score < 40:
        return "谨慎审批"
    if score <= 75:
        return "适度信任"
    return "高度信任"


def drift_label(similarity: float) -> tuple[str, str]:
    """根据立意锚相似度返回 (label, color_class)。

    similarity 范围建议 0.0~1.0，越接近 1 表示越贴合。
    """
    if similarity >= 0.85:
        return ("贴合", "text-success")
    if similarity >= 0.60:
        return ("轻微跑偏", "text-warning")
    return ("严重偏离", "text-danger")


def block_tag_label(tag: str) -> str:
    """把 Block 标签编码映射为展示文案。"""
    normalized = tag.lower().replace("-", "_")
    mapping = {
        "locked_by_human": "锁定",
        "locked": "锁定",
        "lock": "锁定",
        "drift_warning": "冲突",
        "drift": "冲突",
        "warn": "冲突",
        "warning": "冲突",
        "claimed": "已认领",
        "claim": "已认领",
    }
    return mapping.get(normalized, tag)


def audit_action_label(action: str) -> str:
    """把审计动作编码映射为中文展示文案。"""
    mapping = {
        "create_document": "创建文档",
        "create_doc": "创建文档",
        "state_transition": "状态流转",
        "proposal_accepted": "采纳提案",
        "proposal_rejected": "拒绝提案",
        "ai_interrupted": "中断 AI",
        "manage_members": "成员管理",
        "archive": "归档文档",
        "reset_memory": "重置记忆",
        "start_review": "启动审查",
        "resolve_arbitration": "仲裁裁决",
        "assign_paragraphs": "分配段落",
        "claim_paragraph": "认领段落",
        "discuss": "参与讨论",
    }
    return mapping.get(action.lower(), action)
