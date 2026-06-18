# Checklist

## 架构与真相源
- [ ] `services/api/src/shared/authz.py` 存在且 exported 所有核心权限函数
- [ ] `services/web/src/shared/authz.ts` 存在且 exported 所有前端权限函数
- [ ] 后端所有权限判断均通过 `authz.py`，无分散的 `user.role` 硬编码
- [ ] 前端所有权限判断均通过 `authz.ts`，无分散的角色硬编码

## 数据模型
- [ ] `User` 模型新增 `global_role` 字段（personal/team_admin/ops）
- [ ] `role` 字段被标记为 legacy，新逻辑不再使用
- [ ] `document_permissions.effective_role` 语义明确为单文档局部角色
- [ ] Alembic 迁移可正确应用并回填默认 `global_role = personal`

## 认证与 JWT
- [ ] 注册接口默认 `global_role = personal`
- [ ] 登录返回的 access token payload 包含 `global_role` 与 `doc_role`
- [ ] `get_current_user` 返回 `global_role`
- [ ] `require_role(global_role)` 与 `require_doc_permission(...)` 依赖可用

## 后端端点权限
- [ ] 状态流转端点校验 `doc_role`
- [ ] AI 锻造端点校验文档成员身份与 `doc_role`
- [ ] 审查/仲裁端点按角色开放
- [ ] 审计日志端点按 `global_role` 分层返回
- [ ] WebSocket 消息类型经 `authz.py` 校验后广播

## 契约
- [ ] `contracts/contracts.py` 包含 `GlobalRole` 枚举
- [ ] `services/web/src/shared/types/contracts.ts` 与后端一致
- [ ] `document/schemas.py` 返回当前用户的 `doc_role`

## 前端视图
- [ ] 顶部存在三级视图切换器（创作/团队管理/运维监控）
- [ ] `global_role = personal` 只能看到创作视图
- [ ] `global_role = team_admin` 可切换创作与团队管理视图
- [ ] `global_role = ops` 可切换运维监控视图，进入需二次密码
- [ ] 顶部双身份标签正确显示全局身份与当前文档角色

## 菜单分组
- [ ] Tools 菜单按锻造工具/团队管控/系统运维三级分组
- [ ] 创作视图下团队管控分组对 personal 隐藏
- [ ] 运维监控分组在创作/团队视图下隐藏

## 面板显隐
- [ ] reader 看不到 AI 锻造、提案、状态流转、段落认领、归档、记忆配置、讨论输入
- [ ] reviewer 看不到段落批量分配、文档归档、记忆重置、团队预算调配
- [ ] editor 看不到成员权限分配、归档、清空记忆、状态强制重置
- [ ] lead_editor 看不到团队全局批量规则、团队公共预算总调配面板
- [ ] owner 可见本文档全部功能，但仍受全局身份限制

## 技术脱敏
- [ ] 信任分显示为 谨慎审批 / 适度信任 / 高度信任
- [ ] VU 漂移显示为 贴合 / 轻微跑偏 / 严重偏离
- [ ] 预算面板隐藏 800/400 上限、L1/L2/L3、模型名、P99、WebSocket7d
- [ ] E-STOP 文案为「暂停所有AI建议」
- [ ] 审计日志自然语言翻译，隐藏机器编码
- [ ] Block 标签显示中文（段落区块/锁定/冲突/已认领）
- [ ] hover 悬浮提示存在并为技术项提供业务释义

## 权限弹窗
- [ ] 点击无权限功能弹出 PermissionDeniedModal
- [ ] 弹窗说明当前全局身份与文档角色

## 种子数据
- [ ] `scripts/seed_db.py` 至少包含 personal/team_admin/ops 各一个账户
- [ ] 演示文档权限分配与新模型一致

## 安全加固
- [ ] 后端存在速率限制中间件
- [ ] CORS 生产环境配置被收紧
- [ ] JWT 密钥非默认值且启动时校验

## 测试
- [ ] `pytest` 后端测试通过
- [ ] 前端 `npm run typecheck` 通过
- [ ] `shared/authz.py` 单元测试覆盖核心场景
