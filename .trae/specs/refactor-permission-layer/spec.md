# 全量重构权限分层与界面脱敏规范 Spec

## Why
当前系统只有一套 `UserRole` 权限模型，被同时当作「账号全局身份」和「单文档局部角色」使用，导致三类人群共用同一界面、技术指标裸暴露、运维功能混入写作流。本次重构将完全拆分两套权限域，并据此重构后端授权链、前端视图隔离、技术参数脱敏、菜单分组折叠，确保 MVP 严格对齐 UI v3.0 终版规范。

## What Changes
- **BREAKING**: 用户模型新增 `global_role` 字段（`personal`/`team_admin`/`ops`），原 `role` 字段语义收缩为「仅注册默认值」，不再参与全局视图判断。
- **BREAKING**: JWT payload 同时携带 `global_role` 与 `doc_role`，前端与后端均据此做双层权限校验。
- **BREAKING**: 删除所有将单文档角色误当作全局身份的代码；替换为「账号全局身份 + 单文档局部角色」双轨模型。
- 后端所有敏感端点添加 `require_role` / `require_doc_permission` 依赖，统一由 `authz.py` 真相源裁决。
- 新增 Truth Source 模块：`services/api/src/shared/authz.py`（后端权限判断）、`services/web/src/shared/authz.ts`（前端权限判断）。
- WebSocket 增加消息类型级权限校验，伪造广播被网关拦截。
- 前端新增三级视图切换器（创作/团队管理/运维监控）和顶部双身份标签。
- Tools 菜单按全局身份三级分组折叠。
- 所有技术参数按视图做双层脱敏：业务简化文案 + 悬浮提示。
- 单文档局部角色按规则直接隐藏无权限面板，不再置灰。
- 新增权限说明弹窗组件，点击无权限功能时友好提示边界。
- 种子数据与演示账户按新的全局身份重新分配。
- 更新 Alembic 迁移与 TypeScript 契约自动生成。

## Impact
- Affected specs: PRD 权限体系、UI v3.0 视图隔离规范、双层脱敏规范、五不可变底线。
- Affected code:
  - `services/api/src/auth/models.py`, `auth/router.py`, `auth/service.py`, `auth/deps.py`
  - `services/api/src/document/models.py`, `document/service.py`, `document/router.py`
  - `services/api/src/ai_forge/router.py`, `ai_forge/service.py`
  - `services/api/src/approval/router.py`, `approval/service.py`
  - `services/api/src/audit/router.py`
  - `services/api/src/collab/router.py`, `collab/ws_gateway.py`
  - `services/api/src/shared/authz.py` (new), `shared/config.py`
  - `services/api/src/state_engine/engine.py`
  - `services/api/alembic/versions/`
  - `contracts/contracts.py`
  - `services/web/src/shared/authz.ts` (new), `shared/store/authStore.ts`, `shared/store/documentStore.ts`
  - `services/web/src/layouts/AppLayout.tsx`, `layouts/ForgeLayout.tsx`
  - `services/web/src/features/editor/ForgeEditor.tsx`, `features/editor/StateAirlock.tsx`, `features/editor/LightweightCanvas.tsx`
  - `services/web/src/features/forge/SovereignConsole.tsx`, `features/forge/SurgeryDesk.tsx`, `features/forge/ForgeInitiation.tsx`
  - `services/web/src/features/audit/AuditLog.tsx`, `features/audit/MemoryPanel.tsx`
  - `services/web/src/features/budget/BudgetPanel.tsx`
  - `services/web/src/features/arbitration/ArbitrationArena.tsx`
  - `services/web/src/features/approval/ApprovalDashboard.tsx`
  - `services/web/src/features/collab/DiscussionZone.tsx`
  - `services/web/src/App.tsx`, `shared/types/contracts.ts`
  - `scripts/seed_db.py`

## ADDED Requirements

### Requirement: 双域权限真相源
The system SHALL provide a single source of truth for authorization decisions in both backend and frontend.

#### Scenario: 后端权限裁决
- **WHEN** any API endpoint or WebSocket message needs to authorize an action
- **THEN** it SHALL call `shared/authz.py` functions rather than inline role checks
- **AND** `shared/authz.py` SHALL distinguish `global_role` (account tier) from `doc_role` (document permission)

#### Scenario: 前端权限裁决
- **WHEN** a component decides whether to render a panel, button, or route
- **THEN** it SHALL import helpers from `shared/authz.ts`
- **AND** those helpers SHALL read `global_role` and `doc_role` from auth/document stores

### Requirement: 账号全局身份
The system SHALL support three account global roles that never change based on document creation or sharing.

#### Scenario: 注册与登录
- **WHEN** a new account is registered via `POST /api/auth/register`
- **THEN** the default `global_role` SHALL be `personal`
- **AND** only an existing `team_admin` or `ops` user (or seeded admin) can create other `team_admin`/`ops` accounts

#### Scenario: JWT 携带全局身份
- **WHEN** a user logs in
- **THEN** the access token SHALL include `global_role` and `doc_role` for the active document context
- **AND** the refresh token SHALL include at least `user_id` and `global_role`

### Requirement: 单文档局部角色
The system SHALL enforce five document-local roles that apply only within the current document.

#### Scenario: 文档创建
- **WHEN** a `personal` user creates a document
- **THEN** they receive `doc_role = owner` for that document only
- **AND** their account `global_role` remains `personal`

#### Scenario: 团队管理员打开他人文档
- **WHEN** a `team_admin` user opens a document they do not own
- **THEN** their effective `doc_role` is determined by `document_permissions`
- **AND** they do NOT automatically receive owner permissions

### Requirement: 后端端点权限守卫
The system SHALL enforce role and permission checks on every sensitive endpoint.

#### Scenario: 状态流转
- **WHEN** `POST /api/documents/{doc_id}/transition` is called
- **THEN** the user must be authenticated
- **AND** have `doc_role` in {owner, lead_editor} or a state-machine-defined permitted role
- **AND** state machine rules SHALL be evaluated by `shared/authz.py`

#### Scenario: AI 锻造
- **WHEN** `POST /api/forge/refine` is called
- **THEN** the user must be a member of the document
- **AND** have `doc_role` in {owner, lead_editor, editor}

#### Scenario: 审查与仲裁
- **WHEN** `POST /api/review/{doc_id}/start` or `/api/review/arbitrations/{arb_id}/resolve` is called
- **THEN** the user must have `doc_role` in {owner, lead_editor, reviewer} depending on the action

#### Scenario: 审计日志
- **WHEN** `GET /api/audit/logs` is called
- **THEN** `global_role = ops` SHALL be required for full raw logs
- **AND** `team_admin` SHALL see simplified team logs
- **AND** `personal` SHALL only see logs for documents they participate in

### Requirement: WebSocket 消息权限
The system SHALL validate every inbound WebSocket message type before broadcasting.

#### Scenario: 伪造状态变更
- **WHEN** a client sends `STATE_CHANGE` over `/api/collab/ws/{doc_id}`
- **THEN** the gateway SHALL verify the sender has `doc_role` in {owner, lead_editor}
- **AND** reject and close the connection if unauthorized

### Requirement: 三级全局视图切换
The system SHALL provide three top-level client views controlled by `global_role`.

#### Scenario: 创作视图
- **WHEN** `global_role` is `personal` or `team_admin`
- **THEN** the default view is the forge editor
- **AND** only document-level tools are visible

#### Scenario: 团队管理视图
- **WHEN** `global_role` is `team_admin`
- **THEN** a "团队管理" tab is available in the top-level switcher
- **AND** it shows members, shared budget, templates, global rules

#### Scenario: 运维监控视图
- **WHEN** `global_role` is `ops`
- **THEN** a "运维监控" tab is available
- **AND** entering it requires a secondary password prompt
- **AND** it shows LLM health, memory repair, performance SLO, raw logs

### Requirement: 顶部双身份可视化标签
The system SHALL display the user's global identity and current document role at the top of the editor.

#### Scenario: 普通用户是文档Owner
- **WHEN** a `personal` user with `doc_role = owner` opens a document
- **THEN** the top bar shows: `全局身份：个人普通用户 | 当前文档身份：文档所有者`

### Requirement: Tools 菜单三级分组折叠
The system SHALL group the left/global tools menu into three collapsible sections.

#### Scenario: 创作视图菜单
- **WHEN** the active view is "创作"
- **THEN** Group 1 (锻造工具) is expanded
- **AND** Group 2 (团队管控) is collapsed and hidden for `global_role = personal`
- **AND** Group 3 (运维监控) is completely hidden

### Requirement: 单文档角色前端显隐
The system SHALL hide panels and buttons based on `doc_role`, not disable them.

#### Scenario: 只读用户
- **WHEN** `doc_role = reader`
- **THEN** AI forge tools, proposal panels, state transition, paragraph claim, archive, memory config, and discussion input are HIDDEN
- **AND** only reading, snapshot history, and export remain visible

### Requirement: 双层技术参数脱敏
The system SHALL translate technical metrics into business language in the forge view and expose raw values only in ops view.

#### Scenario: 信任分
- **WHEN** in forge view
- **THEN** scores map to labels: 谨慎审批 / 适度信任 / 高度信任
- **AND** the raw 0-100 number is hidden

#### Scenario: VU 漂移检测
- **WHEN** in forge view
- **THEN** similarity maps to colors/labels: 贴合 / 轻微跑偏 / 严重偏离
- **AND** cosine values and embedding model names are hidden

#### Scenario: 预算面板
- **WHEN** in forge view
- **THEN** show通俗额度提示
- **AND** hide raw pool caps (800/400), L1/L2/L3 naming, model names, P99 latency

#### Scenario: E-STOP
- **WHEN** in forge view
- **THEN** label is "暂停所有AI建议"
- **AND** L1/L2/L3 interrupt logs are hidden

#### Scenario: 审计日志
- **WHEN** in forge view
- **THEN** actions are translated to natural language
- **AND** machine IDs (blk-003, op_001) are hidden

#### Scenario: Block 标签
- **WHEN** in forge view
- **THEN** tags show as "段落区块" or Chinese states
- **AND** LOCK/WARN/CLAIMED English labels are hidden

### Requirement: 权限说明弹窗
The system SHALL explain permission boundaries when a user attempts an unavailable action.

#### Scenario: 无权限点击
- **WHEN** a user without permission clicks a visible but restricted action
- **THEN** a modal explains why the action is unavailable
- **AND** it states the user's current `global_role` and `doc_role`

## MODIFIED Requirements

### Requirement: User Model
The User model SHALL keep `role` as a legacy/default field for backward compatibility but SHALL add `global_role` as the source of truth for account-level permissions.

- `role` SHALL NOT be used to determine global view access.
- New code SHALL reference `global_role` only.

### Requirement: JWT Payload
The JWT payload SHALL include `global_role` and, when applicable, `doc_role`.

- Existing tokens with only `sub` and `exp` SHALL be treated as legacy and rejected or refreshed.

### Requirement: Document Creation
Creating a document SHALL grant `doc_role = owner` on that document only.

- It SHALL NOT change `global_role`.

## REMOVED Requirements

### Requirement: 单域 UserRole 作为全局权限
**Reason**: The original design incorrectly used document roles (`owner`, `lead_editor`, etc.) as account-level roles, causing the "creating a document makes you a global admin" confusion.
**Migration**: Replace all `current_user.role` checks with `current_user.global_role` for global decisions and `doc_role` for document decisions via `shared/authz.py`.
