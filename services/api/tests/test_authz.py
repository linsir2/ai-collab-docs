import pytest

from shared.authz import (
    DocRole,
    GlobalRole,
    MenuGroup,
    ViewType,
    allowed_menu_groups,
    allowed_views,
    can_access_view,
    can_do_in_document,
    is_allowed_ws_message,
)


class TestViewAccess:
    """视图入口权限 — 全局角色 vs 顶部视图。"""

    def test_personal_cannot_access_team_or_ops(self):
        assert can_access_view(GlobalRole.PERSONAL, ViewType.FORGE) is True
        assert can_access_view(GlobalRole.PERSONAL, ViewType.TEAM) is False
        assert can_access_view(GlobalRole.PERSONAL, ViewType.OPS) is False
        assert allowed_views(GlobalRole.PERSONAL) == [ViewType.FORGE]

    def test_team_admin_can_access_forge_and_team_but_not_ops(self):
        assert can_access_view(GlobalRole.TEAM_ADMIN, ViewType.FORGE) is True
        assert can_access_view(GlobalRole.TEAM_ADMIN, ViewType.TEAM) is True
        assert can_access_view(GlobalRole.TEAM_ADMIN, ViewType.OPS) is False
        assert allowed_views(GlobalRole.TEAM_ADMIN) == [ViewType.FORGE, ViewType.TEAM]

    def test_ops_can_access_all_views(self):
        assert can_access_view(GlobalRole.OPS, ViewType.FORGE) is True
        assert can_access_view(GlobalRole.OPS, ViewType.TEAM) is True
        assert can_access_view(GlobalRole.OPS, ViewType.OPS) is True
        assert allowed_views(GlobalRole.OPS) == [ViewType.FORGE, ViewType.TEAM, ViewType.OPS]


class TestMenuGroups:
    """菜单分组可见性 — 与视图和角色联动。"""

    def test_personal_forge_menu(self):
        assert allowed_menu_groups(GlobalRole.PERSONAL, ViewType.FORGE) == [MenuGroup.FORGE_TOOLS]

    def test_team_admin_team_menu(self):
        assert allowed_menu_groups(GlobalRole.TEAM_ADMIN, ViewType.TEAM) == [MenuGroup.TEAM_MGMT]

    def test_ops_ops_menu(self):
        assert allowed_menu_groups(GlobalRole.OPS, ViewType.OPS) == [MenuGroup.OPS_MONITOR]


class TestDocumentActions:
    """文档内操作权限 — DocRole vs action。"""

    def test_reader_cannot_state_transition(self):
        assert can_do_in_document(DocRole.READER, "state_transition") is False

    def test_owner_can_perform_all_document_actions(self):
        actions = [
            "state_transition",
            "archive",
            "manage_members",
            "assign_paragraphs",
            "reset_memory",
            "use_forge",
            "start_review",
            "resolve_arbitration",
            "discuss",
            "claim_paragraph",
        ]
        for action in actions:
            assert can_do_in_document(DocRole.OWNER, action) is True, f"owner should be able to {action}"


class TestWebSocketPermissions:
    """WebSocket 业务消息发送权限。"""

    def test_state_change_blocked_for_editor_and_reader(self):
        assert is_allowed_ws_message(DocRole.OWNER, "STATE_CHANGE") is True
        assert is_allowed_ws_message(DocRole.LEAD_EDITOR, "STATE_CHANGE") is True
        assert is_allowed_ws_message(DocRole.EDITOR, "STATE_CHANGE") is False
        assert is_allowed_ws_message(DocRole.REVIEWER, "STATE_CHANGE") is False
        assert is_allowed_ws_message(DocRole.READER, "STATE_CHANGE") is False

    def test_proposal_created_allowed_for_editor_blocked_for_reviewer_reader(self):
        assert is_allowed_ws_message(DocRole.EDITOR, "PROPOSAL_CREATED") is True
        assert is_allowed_ws_message(DocRole.REVIEWER, "PROPOSAL_CREATED") is False
        assert is_allowed_ws_message(DocRole.READER, "PROPOSAL_CREATED") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
