"""authz.py 的完整单元测试 — 权限真值源与脱敏函数全覆盖。

覆盖范围：
- 视图访问权限矩阵（can_access_view / allowed_views）
- 菜单组权限矩阵（allowed_menu_groups）
- 文档内操作权限矩阵（can_do_in_document — 10 actions x 5 roles）
- WebSocket 消息权限矩阵（is_allowed_ws_message）
- 脱敏/标签辅助函数（trust_score_label / drift_label / block_tag_label /
  audit_action_label / format_global_role_label / format_doc_role_label）
- default_doc_permissions 深拷贝语义

纯单元测试，不依赖 client fixture 或数据库。
"""

import pytest

from shared.authz import (
    DocRole,
    GlobalRole,
    MenuGroup,
    ViewType,
    allowed_menu_groups,
    allowed_views,
    audit_action_label,
    block_tag_label,
    can_access_view,
    can_do_in_document,
    default_doc_permissions,
    drift_label,
    format_doc_role_label,
    format_global_role_label,
    is_allowed_ws_message,
    trust_score_label,
)

# ============================================================
# 文档操作权限真值矩阵
# 列顺序: (action, owner, lead_editor, editor, reviewer, reader)
# ============================================================
_DOC_ACTION_MATRIX = [
    ("state_transition", True, True, False, False, False),
    ("archive", True, False, False, False, False),
    ("manage_members", True, False, False, False, False),
    ("assign_paragraphs", True, True, False, False, False),
    ("reset_memory", True, False, False, False, False),
    ("use_forge", True, True, True, False, False),
    ("start_review", True, True, False, True, False),
    ("resolve_arbitration", True, True, False, False, False),
    ("discuss", True, True, True, True, True),
    ("claim_paragraph", True, True, True, True, False),
]

# WebSocket 消息权限真值矩阵
# 列顺序: (msg_type, owner, lead_editor, editor, reviewer, reader)
_WS_MESSAGE_MATRIX = [
    ("STATE_CHANGE", True, True, False, False, False),
    ("PROPOSAL_CREATED", True, True, True, False, False),
    ("CONFLICT_DETECTED", True, True, False, True, False),
    ("AI_BROADCAST", True, True, True, True, False),
]

ALL_DOC_ROLES = [DocRole.OWNER, DocRole.LEAD_EDITOR, DocRole.EDITOR, DocRole.REVIEWER, DocRole.READER]


# ============================================================
# 1. 视图访问权限
# ============================================================
class TestViewAccessFull:
    """完整视图权限矩阵 — 全局角色 vs 顶部视图。"""

    def test_personal_views(self):
        assert can_access_view(GlobalRole.PERSONAL, ViewType.FORGE) is True
        assert allowed_views(GlobalRole.PERSONAL) == [ViewType.FORGE]

    def test_team_admin_views(self):
        assert can_access_view(GlobalRole.TEAM_ADMIN, ViewType.FORGE) is True
        assert can_access_view(GlobalRole.TEAM_ADMIN, ViewType.TEAM) is True
        assert allowed_views(GlobalRole.TEAM_ADMIN) == [ViewType.FORGE, ViewType.TEAM]

    def test_ops_views(self):
        assert can_access_view(GlobalRole.OPS, ViewType.FORGE) is True
        assert can_access_view(GlobalRole.OPS, ViewType.TEAM) is True
        assert can_access_view(GlobalRole.OPS, ViewType.OPS) is True
        assert allowed_views(GlobalRole.OPS) == [ViewType.FORGE, ViewType.TEAM, ViewType.OPS]

    def test_personal_cannot_access_team(self):
        assert can_access_view(GlobalRole.PERSONAL, ViewType.TEAM) is False

    def test_personal_cannot_access_ops(self):
        assert can_access_view(GlobalRole.PERSONAL, ViewType.OPS) is False

    def test_team_admin_cannot_access_ops(self):
        assert can_access_view(GlobalRole.TEAM_ADMIN, ViewType.OPS) is False


# ============================================================
# 2. 菜单组权限
# ============================================================
class TestMenuGroupsFull:
    """完整菜单组矩阵 — 视图 x 全局角色。"""

    def test_personal_forge_menu(self):
        assert allowed_menu_groups(GlobalRole.PERSONAL, ViewType.FORGE) == [MenuGroup.FORGE_TOOLS]

    def test_team_admin_forge_menu(self):
        assert allowed_menu_groups(GlobalRole.TEAM_ADMIN, ViewType.FORGE) == [
            MenuGroup.FORGE_TOOLS,
            MenuGroup.TEAM_MGMT,
        ]

    def test_ops_forge_menu(self):
        assert allowed_menu_groups(GlobalRole.OPS, ViewType.FORGE) == [
            MenuGroup.FORGE_TOOLS,
            MenuGroup.TEAM_MGMT,
            MenuGroup.OPS_MONITOR,
        ]

    def test_team_admin_team_menu(self):
        assert allowed_menu_groups(GlobalRole.TEAM_ADMIN, ViewType.TEAM) == [MenuGroup.TEAM_MGMT]

    def test_ops_team_menu(self):
        assert allowed_menu_groups(GlobalRole.OPS, ViewType.TEAM) == [
            MenuGroup.TEAM_MGMT,
            MenuGroup.OPS_MONITOR,
        ]

    def test_ops_ops_menu(self):
        assert allowed_menu_groups(GlobalRole.OPS, ViewType.OPS) == [MenuGroup.OPS_MONITOR]

    def test_personal_team_menu_empty(self):
        assert allowed_menu_groups(GlobalRole.PERSONAL, ViewType.TEAM) == []

    def test_personal_ops_menu_empty(self):
        assert allowed_menu_groups(GlobalRole.PERSONAL, ViewType.OPS) == []


# ============================================================
# 3. 文档内操作权限
# ============================================================
class TestDocumentActionsFull:
    """完整文档操作权限矩阵 — 10 actions x 5 roles = 50 个断言。"""

    @pytest.mark.parametrize(
        "action,expected",
        [(row[0], row[1]) for row in _DOC_ACTION_MATRIX],
        ids=[row[0] for row in _DOC_ACTION_MATRIX],
    )
    def test_owner_all_actions_allowed(self, action, expected):
        assert can_do_in_document(DocRole.OWNER, action) is expected

    @pytest.mark.parametrize(
        "action,expected",
        [(row[0], row[2]) for row in _DOC_ACTION_MATRIX],
        ids=[row[0] for row in _DOC_ACTION_MATRIX],
    )
    def test_lead_editor_actions(self, action, expected):
        assert can_do_in_document(DocRole.LEAD_EDITOR, action) is expected

    @pytest.mark.parametrize(
        "action,expected",
        [(row[0], row[3]) for row in _DOC_ACTION_MATRIX],
        ids=[row[0] for row in _DOC_ACTION_MATRIX],
    )
    def test_editor_actions(self, action, expected):
        assert can_do_in_document(DocRole.EDITOR, action) is expected

    @pytest.mark.parametrize(
        "action,expected",
        [(row[0], row[4]) for row in _DOC_ACTION_MATRIX],
        ids=[row[0] for row in _DOC_ACTION_MATRIX],
    )
    def test_reviewer_actions(self, action, expected):
        assert can_do_in_document(DocRole.REVIEWER, action) is expected

    @pytest.mark.parametrize(
        "action,expected",
        [(row[0], row[5]) for row in _DOC_ACTION_MATRIX],
        ids=[row[0] for row in _DOC_ACTION_MATRIX],
    )
    def test_reader_actions(self, action, expected):
        assert can_do_in_document(DocRole.READER, action) is expected

    @pytest.mark.parametrize("role", ALL_DOC_ROLES, ids=[r.value for r in ALL_DOC_ROLES])
    def test_unknown_action_returns_false(self, role):
        assert can_do_in_document(role, "non_existent_action_xyz") is False


# ============================================================
# 4. WebSocket 消息权限
# ============================================================
class TestWebSocketPermissionsFull:
    """完整 WebSocket 权限矩阵。"""

    @pytest.mark.parametrize(
        "role,expected",
        [
            (DocRole.OWNER, True),
            (DocRole.LEAD_EDITOR, True),
            (DocRole.EDITOR, False),
            (DocRole.REVIEWER, False),
            (DocRole.READER, False),
        ],
        ids=[r.value for r in ALL_DOC_ROLES],
    )
    def test_state_change_permissions_all_roles(self, role, expected):
        assert is_allowed_ws_message(role, "STATE_CHANGE") is expected

    @pytest.mark.parametrize(
        "role,expected",
        [
            (DocRole.OWNER, True),
            (DocRole.LEAD_EDITOR, True),
            (DocRole.EDITOR, True),
            (DocRole.REVIEWER, False),
            (DocRole.READER, False),
        ],
        ids=[r.value for r in ALL_DOC_ROLES],
    )
    def test_proposal_created_permissions_all_roles(self, role, expected):
        assert is_allowed_ws_message(role, "PROPOSAL_CREATED") is expected

    @pytest.mark.parametrize(
        "role,expected",
        [
            (DocRole.OWNER, True),
            (DocRole.LEAD_EDITOR, True),
            (DocRole.EDITOR, False),
            (DocRole.REVIEWER, True),
            (DocRole.READER, False),
        ],
        ids=[r.value for r in ALL_DOC_ROLES],
    )
    def test_conflict_detected_permissions_all_roles(self, role, expected):
        assert is_allowed_ws_message(role, "CONFLICT_DETECTED") is expected

    @pytest.mark.parametrize(
        "role,expected",
        [
            (DocRole.OWNER, True),
            (DocRole.LEAD_EDITOR, True),
            (DocRole.EDITOR, True),
            (DocRole.REVIEWER, True),
            (DocRole.READER, False),
        ],
        ids=[r.value for r in ALL_DOC_ROLES],
    )
    def test_ai_broadcast_permissions_all_roles(self, role, expected):
        assert is_allowed_ws_message(role, "AI_BROADCAST") is expected

    @pytest.mark.parametrize("role", ALL_DOC_ROLES, ids=[r.value for r in ALL_DOC_ROLES])
    def test_unknown_message_type_allows_all_roles(self, role):
        assert is_allowed_ws_message(role, "SOME_UNKNOWN_MSG_TYPE") is True

    @pytest.mark.parametrize(
        "msg_type",
        ["state_change", "State_Change", "Proposal_Created", "conflict_detected", "ai_broadcast"],
    )
    def test_message_type_case_insensitive(self, msg_type):
        # 大小写不敏感：小写/混合大小写应与全大写行为一致
        upper_result = is_allowed_ws_message(DocRole.OWNER, msg_type.upper())
        assert is_allowed_ws_message(DocRole.OWNER, msg_type) is upper_result
        # editor 对 STATE_CHANGE 应被拒绝（验证大小写不改变判定结果）
        assert is_allowed_ws_message(DocRole.EDITOR, msg_type) is is_allowed_ws_message(
            DocRole.EDITOR, msg_type.upper()
        )


# ============================================================
# 5. 脱敏/标签辅助函数
# ============================================================
class TestDesensitizationFunctions:
    """脱敏与标签辅助函数。"""

    # --- trust_score_label ---
    @pytest.mark.parametrize(
        "score,expected",
        [
            (0, "谨慎审批"),
            (10, "谨慎审批"),
            (39, "谨慎审批"),
            (40, "适度信任"),
            (50, "适度信任"),
            (75, "适度信任"),
            (76, "高度信任"),
            (100, "高度信任"),
        ],
        ids=["0", "10", "39", "40", "50", "75", "76", "100"],
    )
    def test_trust_score_labels(self, score, expected):
        assert trust_score_label(score) == expected

    def test_trust_score_boundary_40(self):
        assert trust_score_label(40) == "适度信任"

    def test_trust_score_boundary_75(self):
        assert trust_score_label(75) == "适度信任"

    # --- drift_label ---
    def test_drift_label_high(self):
        assert drift_label(0.90) == ("贴合", "text-success")
        assert drift_label(1.0) == ("贴合", "text-success")

    def test_drift_label_medium(self):
        assert drift_label(0.70) == ("轻微跑偏", "text-warning")

    def test_drift_label_low(self):
        assert drift_label(0.30) == ("严重偏离", "text-danger")
        assert drift_label(0.0) == ("严重偏离", "text-danger")

    def test_drift_label_boundary_085(self):
        assert drift_label(0.85) == ("贴合", "text-success")

    def test_drift_label_boundary_060(self):
        assert drift_label(0.60) == ("轻微跑偏", "text-warning")

    # --- block_tag_label ---
    @pytest.mark.parametrize(
        "tag,expected",
        [
            ("locked-by-human", "锁定"),
            ("locked", "锁定"),
            ("lock", "锁定"),
            ("LOCKED-BY-HUMAN", "锁定"),
            ("Locked", "锁定"),
            ("drift-warning", "冲突"),
            ("drift", "冲突"),
            ("warn", "冲突"),
            ("warning", "冲突"),
            ("Drift-Warning", "冲突"),
            ("claimed", "已认领"),
            ("claim", "已认领"),
            ("CLAIMED", "已认领"),
        ],
        ids=[
            "locked-by-human",
            "locked",
            "lock",
            "LOCKED-BY-HUMAN",
            "Locked",
            "drift-warning",
            "drift",
            "warn",
            "warning",
            "Drift-Warning",
            "claimed",
            "claim",
            "CLAIMED",
        ],
    )
    def test_block_tag_labels_all_variants(self, tag, expected):
        assert block_tag_label(tag) == expected

    @pytest.mark.parametrize(
        "tag",
        ["custom-tag", "review", "ai-proposal", "dual-track", "unknown_tag"],
    )
    def test_block_tag_label_unknown(self, tag):
        assert block_tag_label(tag) == tag

    # --- audit_action_label ---
    @pytest.mark.parametrize(
        "action,expected",
        [
            ("create_document", "创建文档"),
            ("create_doc", "创建文档"),
            ("state_transition", "状态流转"),
            ("proposal_accepted", "采纳提案"),
            ("proposal_rejected", "拒绝提案"),
            ("ai_interrupted", "中断 AI"),
            ("manage_members", "成员管理"),
            ("archive", "归档文档"),
            ("reset_memory", "重置记忆"),
            ("start_review", "启动审查"),
            ("resolve_arbitration", "仲裁裁决"),
            ("assign_paragraphs", "分配段落"),
            ("claim_paragraph", "认领段落"),
            ("discuss", "参与讨论"),
            ("CREATE_DOCUMENT", "创建文档"),
            ("State_Transition", "状态流转"),
        ],
        ids=[
            "create_document",
            "create_doc",
            "state_transition",
            "proposal_accepted",
            "proposal_rejected",
            "ai_interrupted",
            "manage_members",
            "archive",
            "reset_memory",
            "start_review",
            "resolve_arbitration",
            "assign_paragraphs",
            "claim_paragraph",
            "discuss",
            "CREATE_DOCUMENT-upper",
            "State_Transition-mixed",
        ],
    )
    def test_audit_action_labels_all(self, action, expected):
        assert audit_action_label(action) == expected

    @pytest.mark.parametrize(
        "action",
        ["unknown_action", "custom_event", "foo_bar"],
    )
    def test_audit_action_label_unknown(self, action):
        assert audit_action_label(action) == action

    # --- format_global_role_label ---
    @pytest.mark.parametrize(
        "role,expected",
        [
            (GlobalRole.PERSONAL, "个人用户"),
            (GlobalRole.TEAM_ADMIN, "团队管理员"),
            (GlobalRole.OPS, "运维管理员"),
        ],
    )
    def test_format_global_role_labels(self, role, expected):
        assert format_global_role_label(role) == expected

    # --- format_doc_role_label ---
    @pytest.mark.parametrize(
        "role,expected",
        [
            (DocRole.OWNER, "所有者"),
            (DocRole.LEAD_EDITOR, "主编辑"),
            (DocRole.EDITOR, "编辑者"),
            (DocRole.REVIEWER, "审查者"),
            (DocRole.READER, "只读成员"),
        ],
    )
    def test_format_doc_role_labels(self, role, expected):
        assert format_doc_role_label(role) == expected


# ============================================================
# 6. default_doc_permissions
# ============================================================
class TestDefaultDocPermissions:
    """default_doc_permissions 深拷贝语义验证。"""

    def test_default_doc_permissions_returns_copy(self):
        perms = default_doc_permissions()
        # 应包含全部 10 个操作
        assert set(perms.keys()) == {row[0] for row in _DOC_ACTION_MATRIX}
        # 每个操作的值应为 set[DocRole]
        for action, roles in perms.items():
            assert isinstance(roles, set)
            # 与真值矩阵一致
            expected_roles = {
                DocRole.OWNER,
            }
            # 重建期望集合
            for row in _DOC_ACTION_MATRIX:
                if row[0] == action:
                    expected_roles = set()
                    for role_idx, role in enumerate(ALL_DOC_ROLES):
                        if row[role_idx + 1]:
                            expected_roles.add(role)
                    break
            assert roles == expected_roles
        # 两次调用返回不同对象（深拷贝）
        perms2 = default_doc_permissions()
        assert perms is not perms2
        for action in perms:
            assert perms[action] is not perms2[action]

    def test_default_doc_permissions_modification_does_not_affect_original(self):
        perms = default_doc_permissions()
        # 修改返回的副本
        perms["archive"].add(DocRole.EDITOR)
        perms["discuss"].discard(DocRole.READER)
        perms["state_transition"] = set()
        # 再次获取应不受影响
        fresh = default_doc_permissions()
        assert DocRole.EDITOR not in fresh["archive"]
        assert DocRole.READER in fresh["discuss"]
        assert fresh["state_transition"] == {DocRole.OWNER, DocRole.LEAD_EDITOR}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
