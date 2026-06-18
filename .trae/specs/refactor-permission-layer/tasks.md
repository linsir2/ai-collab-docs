# Tasks

- [ ] Task 1: 建立权限真相源模块
  - [ ] SubTask 1.1: 在 `services/api/src/shared/authz.py` 创建后端权限裁决函数（`can_access_view`, `can_do_in_document`, `allowed_menu_groups`, `is_allowed_ws_message`）
  - [ ] SubTask 1.2: 在 `services/web/src/shared/authz.ts` 创建前端权限裁决函数（同能力）
  - [ ] SubTask 1.3: 定义常量与类型：`GlobalRole`, `DocRole`, `ViewType`, `MenuGroup`

- [ ] Task 2: 重构后端用户与权限数据模型
  - [ ] SubTask 2.1: 在 `auth/models.py` 添加 `global_role` 字段，保留 `role` 作为仅注册默认值
  - [ ] SubTask 2.2: 更新 `document_permissions` 模型，确保 `effective_role` 语义清晰为单文档局部角色
  - [ ] SubTask 2.3: 新增 Alembic 迁移脚本，为现有用户设置默认 `global_role = personal`

- [ ] Task 3: 重构后端认证与 JWT
  - [ ] SubTask 3.1: `auth/service.py` 登录/注册时写入 `global_role`
  - [ ] SubTask 3.2: JWT payload 包含 `global_role` 与 `doc_role`
  - [ ] SubTask 3.3: `auth/deps.py` 的 `get_current_user` 返回 `global_role`；`require_role` 校验 `global_role`
  - [ ] SubTask 3.4: 新增 `require_doc_permission` 依赖工厂

- [ ] Task 4: 为所有后端敏感端点添加权限守卫
  - [ ] SubTask 4.1: `document/router.py` 状态流转、归档、成员管理加 `doc_role` 校验
  - [ ] SubTask 4.2: `ai_forge/router.py` 锻造接口校验文档成员与 `doc_role`
  - [ ] SubTask 4.3: `approval/router.py` 审查/仲裁接口按角色开放
  - [ ] SubTask 4.4: `audit/router.py` 日志接口按 `global_role` 分层返回
  - [ ] SubTask 4.5: `collab/router.py` WebSocket 连接身份校验，并在 `ws_gateway.py` 拦截非法消息类型

- [ ] Task 5: 更新数据契约（唯一真相源）
  - [ ] SubTask 5.1: `contracts/contracts.py` 新增 `GlobalRole` 枚举，调整 `UserResponse`/`TokenPayload`
  - [ ] SubTask 5.2: 运行 `make types` 重新生成 `services/web/src/shared/types/contracts.ts`
  - [ ] SubTask 5.3: 更新 `document/schemas.py` 返回当前用户的 `doc_role`

- [ ] Task 6: 重构前端认证与存储
  - [ ] SubTask 6.1: `authStore.ts` 存储 `global_role` 与 `doc_role`
  - [ ] SubTask 6.2: `documentStore.ts` 获取并缓存当前文档的 `doc_role`
  - [ ] SubTask 6.3: API client 读取新 JWT 字段

- [ ] Task 7: 实现三级全局视图切换
  - [ ] SubTask 7.1: 在 `AppLayout.tsx` 顶部新增视图切换器（创作/团队管理/运维监控）
  - [ ] SubTask 7.2: 创建 `features/team/TeamManagementView.tsx` 骨架
  - [ ] SubTask 7.3: 创建 `features/ops/OpsMonitorView.tsx` 骨架，进入需二次密码弹窗
  - [ ] SubTask 7.4: 在 `App.tsx` 增加 `/team` 与 `/ops` 路由

- [ ] Task 8: 实现 Tools 菜单三级分组折叠
  - [ ] SubTask 8.1: 重写 `AppLayout.tsx` 左侧导航，按 `MenuGroup` 分组渲染
  - [ ] SubTask 8.2: 根据 `global_role` 过滤可见分组
  - [ ] SubTask 8.3: 默认折叠状态按视图自动设定

- [ ] Task 9: 实现顶部双身份可视化标签
  - [ ] SubTask 9.1: 在 `ForgeEditor.tsx`/`ForgeLayout.tsx` 顶部渲染双身份标签
  - [ ] SubTask 9.2: Hover 悬浮提示说明两类权限定义

- [ ] Task 10: 按单文档角色裁剪前端面板
  - [ ] SubTask 10.1: `ForgeEditor.tsx` 右侧面板按 `doc_role` 显隐
  - [ ] SubTask 10.2: `StateAirlock.tsx` 仅 owner/lead_editor 可见
  - [ ] SubTask 10.3: `SovereignConsole.tsx` 仅 owner 可见完整功能，reviewer/editor 可见受限版本
  - [ ] SubTask 10.4: `ApprovalDashboard.tsx` 按角色显隐审批按钮
  - [ ] SubTask 10.5: `ArbitrationArena.tsx` 按角色显隐裁决按钮
  - [ ] SubTask 10.6: `DiscussionZone.tsx` 输入框仅 editor 及以上可见
  - [ ] SubTask 10.7: `MemoryPanel.tsx` 仅 owner 可见记忆重置

- [ ] Task 11: 全量技术参数脱敏
  - [ ] SubTask 11.1: `SurgeryDesk.tsx` 信任分转业务标签
  - [ ] SubTask 11.2: `ForgeEditor.tsx` VU 漂移数字转三色文字
  - [ ] SubTask 11.3: `BudgetPanel.tsx` 按视图分层展示，隐藏 L1/L2/L3、模型名、P99
  - [ ] SubTask 11.4: `SovereignConsole.tsx` E-STOP 改为「暂停所有AI建议」，隐藏三级日志
  - [ ] SubTask 11.5: `AuditLog.tsx` 自然语言翻译，隐藏机器编码
  - [ ] SubTask 11.6: Block 标签中文翻译（段落区块/锁定/冲突/已认领）
  - [ ] SubTask 11.7: 新增通用 `HoverTooltip` 组件，为保留的技术项提供业务释义

- [ ] Task 12: 实现权限说明弹窗
  - [ ] SubTask 12.1: 创建 `shared/components/PermissionDeniedModal.tsx`
  - [ ] SubTask 12.2: 在需要权限但当前角色不足的操作上绑定弹窗

- [ ] Task 13: 更新种子数据与演示账户
  - [ ] SubTask 13.1: `scripts/seed_db.py` 为用户分配新 `global_role`
  - [ ] SubTask 13.2: 至少包含一个 `team_admin`、一个 `ops`、两个 `personal` 账户
  - [ ] SubTask 13.3: 调整演示文档的权限分配

- [ ] Task 14: 安全加固
  - [ ] SubTask 14.1: 后端添加基于慢速 LRU 的速率限制中间件（端点级 + WebSocket 级）
  - [ ] SubTask 14.2: 收紧 CORS，生产环境只允许配置来源
  - [ ] SubTask 14.3: JWT 密钥禁止默认弱值，启动时校验

- [ ] Task 15: 测试与验证
  - [ ] SubTask 15.1: 为 `shared/authz.py` 编写单元测试
  - [ ] SubTask 15.2: 为关键端点编写角色权限集成测试
  - [ ] SubTask 15.3: 前端 TypeScript 类型检查通过
  - [ ] SubTask 15.4: 后端 pytest 全部通过

# Task Dependencies
- Task 1 must complete before Task 2, 3, 6, 10, 11, 12
- Task 2 must complete before Task 4, 5, 13
- Task 3 must complete before Task 4
- Task 5 must complete before Task 6, 7, 9, 10, 11
- Task 6 must complete before Task 7, 8, 9, 10, 12
- Task 7, 8, 9 can run in parallel after Task 6
- Task 10, 11, 12 can run in parallel after Task 5 and Task 6
- Task 14 can run in parallel with Task 7-12
- Task 15 depends on all other tasks
