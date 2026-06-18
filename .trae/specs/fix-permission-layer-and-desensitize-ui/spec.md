# 修复权限分层与界面脱敏 Spec

## Why
根据 `AUDIT_REPORT.md` 终版审查结论，当前系统存在两大根本性缺陷：
1. **权限域逻辑混淆**：只实现了 `UserRole` 单文档局部角色，完全缺失「账号全局身份」体系，导致无法区分普通用户、团队管理员、运维技术人员；
2. **界面分层缺失**：三类人群共用同一套界面，无权限面板仅置灰不隐藏，底层技术指标（VU相似度、Token池、E-STOP、LLM降级等）直接暴露给业务用户。

本次 Spec 要求全量整改，统一数据契约作为唯一真相源，替换旧有实现。

## What Changes

- **BREAKING**: 在 `contracts.py` 中新增 `GlobalAccountRole` 枚举，与 `UserRole`（单文档局部角色）完全解耦。
- **BREAKING**: 后端 `User` 模型新增 `global_role` 字段；`UserResponse` 同时返回 `global_role` 与 `effective_doc_role`。
- **BREAKING**: JWT payload 加入 `global_role` 与当前文档 `effective_doc_role`。
- **BREAKING**: 后端所有敏感路由接入 `require_role` 或 `require_doc_permission` 依赖，后端不再是仅登录校验。
- 删除旧有的「一套角色走天下」逻辑，替换为两套权限域独立校验。
- 前端新增全局视图切换器：创作视图 / 团队管理视图 / 运维监控视图。
- 前端 ForgeEditor 顶部新增「双身份可视化标签」。
- 前端 AppLayout 导航按三级分组折叠：锻造工具 / 团队管控 / 系统运维。
- 前端所有面板按「当前文档局部角色」显隐，不再置灰而是直接隐藏。
- 前端创作视图全面脱敏：信任分 → 文字标签、VU → 三色文字、预算 → 通俗额度、E-STOP → 「暂停所有AI建议」、审计日志 → 自然语言、Block标签 → 中文。
- 新增工具函数 `canPerform(action, globalRole, docRole)` 与 `desensitizeLabel(view, key, rawValue)`，统一真相源。
- 后端新增 `GET /api/auth/me?doc_id=xxx` 返回当前用户在该文档中的双身份。
- 后端新增 `GET /api/documents/{doc_id}/membership` 返回当前用户的文档局部角色。
- 后端 WebSocket 网关增加消息类型级权限校验，禁止伪造状态/冲突消息。
- 后端 AI Forge、状态流转、审批、仲裁、审计等路由补齐文档级权限校验。
- 配置加固：删除默认弱 JWT 密钥，强制从环境变量读取；CORS 方法/头部收紧；注册 seed 数据使用强密码。

## Impact

- Affected specs: PRD v1.0、UI v3.0 终版规范、AUDIT_REPORT.md
- Affected code:
  - `services/api/src/contracts/contracts.py`
  - `services/api/src/auth/models.py`, `deps.py`, `router.py`, `service.py`
  - `services/api/src/document/models.py`, `router.py`, `service.py`
  - `services/api/src/ai_forge/router.py`, `service.py`
  - `services/api/src/approval/router.py`, `service.py`
  - `services/api/src/audit/router.py`
  - `services/api/src/collab/ws_gateway.py`, `router.py`
  - `services/api/src/state_engine/engine.py`
  - `services/api/src/shared/config.py`
  - `services/web/src/shared/types/contracts.ts`
  - `services/web/src/shared/store/authStore.ts`, `documentStore.ts`
  - `services/web/src/shared/utils/permissions.ts` (NEW)
  - `services/web/src/shared/utils/desensitize.ts` (NEW)
  - `services/web/src/layouts/AppLayout.tsx`
  - `services/web/src/features/editor/ForgeEditor.tsx`, `StateAirlock.tsx`, `LightweightCanvas.tsx`
  - `services/web/src/features/forge/SovereignConsole.tsx`, `SurgeryDesk.tsx`
  - `services/web/src/features/audit/AuditLog.tsx`, `MemoryPanel.tsx`
  - `services/web/src/features/budget/BudgetPanel.tsx`
  - `services/web/src/features/arbitration/ArbitrationArena.tsx`
  - `services/web/src/features/approval/ApprovalDashboard.tsx`
  - `services/web/src/features/pipeline/PipelineDashboard.tsx`
  - `services/web/src/features/team/TeamManagementView.tsx` (NEW)
  - `services/web/src/features/ops/OpsMonitorView.tsx` (NEW)
  - `services/web/src/App.tsx`
  - `scripts/seed_db.py`
  - `alembic` 迁移脚本

## ADDED Requirements

### Requirement: 账号全局身份与单文档局部角色完全解耦

The system SHALL provide two independent permission domains:
1. **Global account role** (`personal`, `