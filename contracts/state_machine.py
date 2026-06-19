"""
状态机 Transition 契约
======================
项目: ai-collab-docs | 用于: state_engine BC
注意: TRANSITION_RULES 是唯一真相源。所有状态流转必须经此矩阵校验。
"""
from contracts._auto_enums import DocumentState, UserRole


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

# REVIEW → FINALIZED 守卫: allReviewersApproved AND snapshot.driftScore >= 0.8


def is_transition_allowed(from_state: DocumentState, to_state: DocumentState, user_role: UserRole) -> bool:
    """检查状态流转是否被 TRANSITION_RULES 允许"""
    for f, t, roles in TRANSITION_RULES:
        if f == from_state and t == to_state and user_role in roles:
            return True
    return False


def get_allowed_next_states(current_state: DocumentState, user_role: UserRole) -> list[DocumentState]:
    """返回当前状态下用户可执行的目标状态列表"""
    allowed = []
    for f, t, roles in TRANSITION_RULES:
        if f == current_state and user_role in roles:
            allowed.append(t)
    return allowed


def validate_anchor(statement: str) -> bool:
    """立意锚描述 ≥ 20字"""
    return len(statement) >= 20
