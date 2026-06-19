# AI 会话交接记录 (AI Session Handoff)

> 项目: AI文档锻造平台 (ai-collab-docs)
> 用途: 每个设计/开发 session 结束后更新，确保下一个 session 的 AI 能快速理解上下文
> 触发: session 结束前，由当前 AI 追加最新条目

---

## 会话记录

| # | 日期 | 类型 | 关键决策/产出 | 遗留问题 | 下一步 |
|---|------|------|-------------|---------|--------|
| 1 | 2026-06-16 | 设计 | 完成 PRD v1.0、ga.md 架构约定、6父目录解耦重构、test文档体系、UI设计初稿 | P-001~P-009 阈值待决议 | 阈值圆桌讨论 |
| 2 | 2026-06-17 | 设计审计 | P-001~P-009 全部决议（见 test-strategy.md §5）；UI 设计大幅补全（模板中心、企业管理、预算面板、角色管理、五维审查视图等）；目录增加 scripts/ 和 contracts/README.md；更新 test 文档引用 | — | 进入 MVP 开发阶段 |
| 3 | 2026-06-17 | 基础设施 | Nginx 反向代理+负载均衡方案落地（SSL终端/least_conn/WS代理/限流/安全头）；API多实例(3 worker)；UI可拓展性声明(四层解耦+v2扩展演练)；PRD §四 新增基础设施条目；directory.md 新增 deploy/nginx/ | — | MVP 开发 |
| 4 | 2026-06-17 | 契约基建 | **openapi.yml 确立为单一真相源**(1689行/25REST+1WS/14schema)；反转旧链路改为 openapi→gen_contracts→contracts.py + gen_ts_types→contracts.ts；**contracts.py 解耦为8模块**(_auto_enums/_auto_models/state_machine/llm_io/ws_protocol/yjs_schema/__init__)；修复7处openapi内部问题(BlockMeta去重/Error $ref语法/内联对象提升为schema/PoolStats三级阈值/Anchor补created_by+created_at)；ga.md合规审计全部33条通过；同步更新directory.md/ga.md/README.md | TDD测试待写；nginx限流配置未实现；gen_contracts可能还需要 `_sort_key` 作用域优化 | 进入MVP后端开发：FastAPI路由骨架 + Pydantic models + 各BC service 实现 |
| 6 | 2026-06-19 | 设计审计+清理 | **MVP审计**: 对temp/ai-collab-docs MVP做全量代码审查，发现11项致命/严重/重要缺陷（假Yjs/假LLM/零Tauri/Block无存储/API路径不匹配/BC隔离失效/前端Mock不可控等），沉淀为 experience.md (12条教训+10额外漏洞+4阶段路线图)。**problem.md全量对照**: 8项外部审查意见全部采纳并融入设计文档。**角色分层重构**: 识别5层17+角色，发现8个混淆点，创建 contracts/roles_and_permissions.py 统一真相源（五层架构/三种独立权限/术语表/显隐规则/PERMISSION_MATRIX），废弃 contracts/identity.py。新增ADR-021(两域拆分)+ADR-022(三轴预留)，prd.md新增术语表，ui/design.md新增§29-36，test-matrix.md新增T7(14条权限测试)，model_repo.yaml更新c2描述 | contracts/roles_and_permissions.py 中 L4(AIRoleInstance) 与 _auto_models.py 中 AIMemory 可能存在字段重叠，gen_contracts.py 尚未适配新模块 | 桌面端MVP开发：Tauri+Rust骨架

---

## 当前状态快照

- **阶段**: 设计审查+权限重构完成，全部设计文档一致性验证通过，待进入MVP桌面端开发
- **新文件**: contracts/roles_and_permissions.py (五层权限真相源), .ga/experience.md (MVP实施教训)
- **弃用**: contracts/identity.py (内容已迁移至 roles_and_permissions.py)
- **真相源**: designs/openapi.yml (1689行) → contracts/_auto_*.py (自动生成) + contracts.ts (自动生成)
- **ABC 范围**: 3~5人团队，重型锻造模式全链路，Yjs协同，双轨AI，5级权限，冲突仲裁
- **技术选型**: Tauri v2 (Rust 8模块分层 + React/系统WebView) + FastAPI + Yjs(Node.js) + PostgreSQL + Redis
- **Rust 8模块（ADR-011）**: ipc / collab / rule_gateway / fs / offline / ai_scheduler / tray / menu+shortcuts
- **关键阈值**: 余弦0.8/0.85(dashscope/text-embedding-v3)，信任分MVP=50，提案池80%/95%/100%三级预警
- **模式**: 无自动采纳(MVP)，审查仅2维(MVP)，轻量模式延后至v1
- **contracts 结构**: 8模块解耦（_auto_enums/_auto_models/state_machine/llm_io/ws_protocol/yjs_schema/__init__/gen_contracts+gen_ts_types）
- **新增ADR**: ADR-011(Rust分层)/ADR-012(导入导出)/ADR-013(E-STOP三级兜底)/ADR-014(跨设备同步)
- **新增UI能力**: 原生菜单(§21)、快捷键(§22)、系统托盘(§23)、多窗口(§24)、本地文件+离线(§25)、导入导出(§26)、跨设备同步(§27)
- **桌面包体积目标**: <15MB (Tauri release)
