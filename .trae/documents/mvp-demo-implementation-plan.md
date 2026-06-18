# AI文档锻造平台 — MVP Demo 实施计划

## 概述

从零构建完整的 ai-collab-docs MVP Demo，严格遵循 `.ga/ga.md` 架构约定和 `designs/` 下所有设计文档。实现后可用于演示核心锻造全链路：创建文档 → 草稿态编辑 → 讨论态 → 审查态 → 定稿态 → 归档态。

## 关键约束

1. **单一真相源**：`contracts/contracts.py` 是唯一数据契约源，所有前后端类型由此派生
2. **BC物理隔离**：6个限界上下文不可互相import models，通过main.py路由层编排 + Redis事件总线通信
3. **AI零直改**：所有AI输出仅作为Proposal，需人类审批
4. **双轨AI隔离**：个人AI（private）与文档级AI（public）严格分库/分屏
5. **Mock LLM**：预设返回内容，区分公私AI角色，保证冲突仲裁可触发
6. **Demo数据**：所有界面有预设内容填充，确保每个功能可操作

---

## Phase 1: 基础设施搭建

### 1.1 shared/ 横切层
**文件**: `services/api/src/shared/config.py`
- Pydantic Settings 配置类（DB URL、Redis URL、LLM api_key、JWT secret）
- 读取 .env 环境变量

**文件**: `services/api/src/shared/database.py`
- SQLAlchemy async engine + session factory
- Base 声明基类
- get_db 依赖注入

**文件**: `services/api/src/shared/redis_client.py`
- Redis 异步客户端
- pub/sub 封装（用于BC间事件总线）
- get_redis 依赖注入

**文件**: `services/api/src/shared/__init__.py`
- 导出所有共享模块

### 1.2 state_engine/ 状态机引擎
**文件**: `services/api/src/state_engine/engine.py`
- 从 `contracts.TRANSITION_RULES` 加载状态转换规则
- `guard_transition(from_state, to_state, user_role, doc_id)` → bool
- `get_allowed_transitions(current_state, user_role)` → list
- `check_all_reviewers_approved(doc_id)` → bool
- 守卫规则：REVIEW→FINALIZED 需所有审查者批准

**文件**: `services/api/src/state_engine/__init__.py`
- 导出 StateEngine 类

### 1.3 数据库迁移
**命令**: `cd services/api && alembic init alembic`
- 配置 alembic.ini 指向 shared/database.py
- 创建初始迁移（User, Document, BlockMeta, AIProposal, ReviewSession, Snapshot, Arbitration, OperationLog 等表）
- 注意：Block内容走Yjs，不在PG建表；PG只存元数据

**文件**: `services/api/alembic/env.py`
- 配置 async SQLAlchemy

### 1.4 main.py FastAPI应用组装
**文件**: `services/api/src/main.py`
- 创建 FastAPI app
- lifespan：启动时连接DB/Redis，关闭时释放
- CORS中间件
- 注册所有BC路由
- 健康检查端点 `/health`

---

## Phase 2: 后端 BC 实现

### 2.1 auth/ (BC5) — 权限限界上下文
**文件**: `services/api/src/auth/models.py`
- `User` SQLAlchemy model（user_id, display_name, email, hashed_password, role）
- `DocumentPermission` model（doc_id, user_id, effective_role）
- Pydantic schemas：UserCreate, UserLogin, UserResponse, TokenResponse

**文件**: `services/api/src/auth/service.py`
- `create_user` / `authenticate_user` / `create_jwt_token`
- `get_document_permission` / `set_document_permission`
- `list_document_members`
- JWT encode/decode 用 python-jose，HS256

**文件**: `services/api/src/auth/router.py`
- `POST /api/auth/register` — 注册
- `POST /api/auth/login` — 登录
- `GET /api/auth/me` — 当前用户信息
- `POST /api/docs/{doc_id}/members` — 邀请成员
- `PUT /api/docs/{doc_id}/members/{user_id}/role` — 修改角色

**文件**: `services/api/src/auth/deps.py`
- `get_current_user` FastAPI dependency（从JWT解析）
- `require_role(min_role)` 角色守卫

### 2.2 document/ (BC1) — 文档限界上下文
**文件**: `services/api/src/document/models.py`
- `Document` 模型（doc_id, title, state, owner_id, anchor_statement, anchor_audience, anchor_argument, created_at）
- `BlockMeta` 模型（block_id, doc_id, tags, claimant_id, drift_score, locked_by）
- `Anchor` 模型（doc_id, statement, target_audience, core_argument, version, history）
- Pydantic schemas

**文件**: `services/api/src/document/service.py`
- `create_document` — 创建文档 + 锚定立意锚
- `get_document` / `list_documents` / `update_document`
- `create_block_meta` / `get_block_metas` / `update_block_meta`
- `claim_block` / `lock_block` / `get_anchor`

**文件**: `services/api/src/document/router.py`
- `POST /api/documents` — 创建文档
- `GET /api/documents` — 文档列表
- `GET /api/documents/{doc_id}` — 文档详情
- `PUT /api/documents/{doc_id}/blocks/{block_id}/meta` — 更新Block标签
- `POST /api/documents/{doc_id}/blocks/{block_id}/claim` — 段落认领
- `POST /api/documents/{doc_id}/transition` — 状态切换（调用state_engine）

### 2.3 audit/ (BC6) — 审计限界上下文
**文件**: `services/api/src/audit/models.py`
- `OperationLog` SQLAlchemy model

**文件**: `services/api/src/audit/service.py`
- `log_operation` — 写入操作日志
- `query_logs` — 查询日志（按时间/用户/类型筛选）

**文件**: `services/api/src/audit/router.py`
- `GET /api/audit/logs?doc_id=&user_id=&action=` — 查询审计日志
- `GET /api/audit/logs/export` — 导出CSV

### 2.4 ai_forge/ (BC3) — AI锻造限界上下文
**文件**: `services/api/src/ai_forge/models.py`
- `AIProposal` SQLAlchemy model（复用 contracts.AIProposal 字段）
- `AIMemory` model（memory_type: PUBLIC/PRIVATE, user_id, doc_id, rule, solidified, trigger_count）
- Pydantic schemas

**文件**: `services/api/src/ai_forge/llm_client.py`
- `MockLLMClient` 类，实现与 contracts 中 LLMForgeRequest/LLMForgeResponse 等接口一致的签名
- `forge(request: LLMForgeRequest)` → 根据 ai_role 返回预设润色结果
  - TechReviewer(文档AI)：侧重技术安全性、术语规范
  - LegalAgent(文档AI)：侧重合规引用、法律严谨性
  - PersonalAI(个人AI)：侧重用户的个人写作风格偏好
- `review(request: LLMReviewRequest)` → 按审查维度返回审查结果
- `detect_conflict(request: LLMConflictDetectRequest)` → 判断两提案是否对立
- **关键**：公私AI角色有不同的预设文本池，不可混用
- 预设数据：
  - 文档AI预设2个角色：`TechReviewer`(安全审查)、`LegalAgent`(合规审查)
  - 个人AI预设2个角色：`我的技术顾问`、`我的文案助手`
  - 每个角色有3-5条不同场景的预设润色文本
  - 确保有至少1对会产生冲突的预设（同一Block，TechReviewer说"强化安全表述"，LegalAgent说"保持简洁"）
  - 冲突检测逻辑：如果两个提案的rationale互相矛盾（修改方向相反），返回is_opposing=true

**文件**: `services/api/src/ai_forge/service.py`
- `request_forge` — 请求AI提案（根据source区分公私AI，校验提案池上限）
- `request_review` — 请求AI审查
- `get_proposals` / `update_proposal_status`
- `get_memories` / `update_memory`
- `check_proposal_pool_limit` — 公共池800/私有池400/全局1200三级上限
- `resolve_conflict` — 冲突裁决后的双路记忆更新

**文件**: `services/api/src/ai_forge/router.py`
- `POST /api/forge/refine` — 请求AI润色（指定Block + ai_source）
- `GET /api/forge/proposals?doc_id=&block_id=&status=` — 查询提案列表
- `PUT /api/forge/proposals/{prop_id}` — 更新提案状态
- `GET /api/forge/memories?memory_type=` — 查询AI记忆
- `GET /api/forge/pool-status?doc_id=` — 提案池状态

### 2.5 approval/ (BC4) — 审批限界上下文
**文件**: `services/api/src/approval/models.py`
- `ReviewSession` model（session_id, doc_id, snapshot_id, status, approvals[]）
- `Snapshot` model（snap_id, doc_id, state, yjs_snapshot, block_metas_json, anchor_json, created_at）
- `Arbitration` model（arb_id, doc_id, block_id, conflict_type, proposals, resolution, decider_id, reason）

**文件**: `services/api/src/approval/service.py`
- `start_review` — 进入审查态，创建Snapshot + ReviewSession
- `approve_proposal` / `reject_proposal` — 审批单个提案（3操作：全盘合并/拒绝批注/手动编辑）
- `create_arbitration` — 创建冲突仲裁
- `resolve_arbitration` — 裁决冲突（段落认领人优先）
- `detect_conflicts` — 扫描同一Block的多AI提案，调用LLM冲突检测
- `complete_review` — 完成审查（检查所有审查者批准）

**文件**: `services/api/src/approval/router.py`
- `POST /api/review/{doc_id}/start` — 开始审查
- `GET /api/review/{doc_id}/session` — 获取审查会话
- `PUT /api/review/proposals/{prop_id}/approve` — 审批提案
- `GET /api/review/{doc_id}/arbitrations` — 获取冲突列表
- `POST /api/review/arbitrations/{arb_id}/resolve` — 裁决冲突
- `POST /api/review/{doc_id}/complete` — 完成审查

### 2.6 collab/ (BC2) — 协同限界上下文
**文件**: `services/api/src/collab/ws_gateway.py`
- WebSocket 端点 `/ws/{doc_id}`
- 处理通道B自定义业务消息（WSMessage合约）
- 事件类型：state_change, drift_alert, conflict_detected, proposal_created, proposal_updated
- 广播给同一文档的所有在线用户
- JWT认证 + 权限校验

**文件**: `services/api/src/collab/router.py`
- `GET /api/collab/{doc_id}/presence` — 获取在线用户列表

---

## Phase 3: 前端 React + Vite 项目

### 3.1 项目初始化
**命令**: `cd services && npm create vite@latest web -- --template react-ts`
- 安装依赖：react-router-dom, zustand（状态管理）, yjs, y-websocket（协同）
- 配置 vite.config.ts（代理到后端）
- 配置 tailwindcss（使用设计文档的 CSS 变量主题）
- 生成 TypeScript 类型：`python contracts/gen_ts_types.py contracts/contracts.py services/web/src/shared/types/contracts.ts`

### 3.2 设计系统 (Design Tokens)
**文件**: `services/web/src/styles/tokens.css`
- 全部 CSS 变量（按 UI 设计 §0.2 实现：--bg-page, --bg-surface, --accent, --text-primary 等）
- 暗色主题 Obsidian Luxe 2.0

**文件**: `services/web/src/styles/global.css`
- 全局样式：body 底色、字体、排版铁律（h1-h3, body, small）
- 按钮层级（Primary/Secondary/Tertiary/Danger）
- 标签、模态、输入框基础样式

**目录**: `services/web/src/shared/components/`
- `Button.tsx` — 4级按钮组件
- `Modal.tsx` — 模态框组件
- `Tag.tsx` — 5种Block标签组件
- `Input.tsx` — 输入框组件
- `StatusBadge.tsx` — 状态徽章

### 3.3 共享层
**文件**: `services/web/src/shared/api/client.ts`
- REST API 客户端封装（fetch with JWT）
- WebSocket 客户端封装

**文件**: `services/web/src/shared/store/`
- `authStore.ts` — Zustand（用户/Token）
- `documentStore.ts` — 当前文档状态
- `forgeStore.ts` — AI提案/锻造状态

### 3.4 布局组件
**文件**: `services/web/src/layouts/AppLayout.tsx`
- 左侧导航栏（56px，无文字图标）
- 顶部 Token 水位条
- 主内容区

**文件**: `services/web/src/layouts/ForgeLayout.tsx`
- 三栏式布局（左280px + 中flex + 右360px）
- 响应式断点

### 3.5 核心页面

#### 3.5.1 Pipeline Dashboard（控制大盘）
**文件**: `services/web/src/features/pipeline/PipelineDashboard.tsx`
- 对应 UI 设计 §1
- 状态管道视图：草稿态/讨论态/审查态/定稿态各列
- 文档卡片列表
- 创建文档入口

#### 3.5.2 Forge Initiation（文档锻造启动页）
**文件**: `services/web/src/features/forge/ForgeInitiation.tsx`
- 对应 UI 设计 §2
- 立意主旨描述输入（最少20字）
- 文档类型选择
- 协作模式选择（重型/轻量）
- 团队成员配置
- 表单校验 + 硬锁止

#### 3.5.3 Three-Column Forge Core（三栏锻造工作区）
**文件**: `services/web/src/features/editor/ForgeEditor.tsx`
- 对应 UI 设计 §3
- **左栏（校准中枢）**：
  - 立意锚卡片（始终可见，可展开历史）
  - VU Meter 语义漂移检测仪（6段跳变条）
  - 文档结构树（章节缩进）
- **中栏（块级编辑器）**：
  - Block 列表渲染（虚拟滚动简化版）
  - Block 状态视觉标识（左边框颜色 + 右上角标签）
  - 框选触发AI润色
- **右栏（双轨AI交互中心）**：
  - Tab切换：`[私域打磨]` | `[公域博弈]`
  - 私域面板：个人AI提案列表 + 私有池计数
  - 公域面板：文档AI提案列表 + 公共池计数
- **底部状态栏**：在线人数、保存时间、字数

#### 3.5.4 Surgery Desk（精准润色台）
**文件**: `services/web/src/features/forge/SurgeryDesk.tsx`
- 对应 UI 设计 §4
- Diff 对比视图（旧轨 vs 新轨）
- `<del>` / `<ins>` 高亮
- 校验报告（立意对齐、表述精准、立场一致）
- 3个操作按钮：全盘合并、拒绝批注、手动编辑

#### 3.5.5 Approval Dashboard（审批闭环视图）
**文件**: `services/web/src/features/approval/ApprovalDashboard.tsx`
- 对应 UI 设计 §5
- 待审批提案列表
- 每条：角色、类型、BlockID、行数变更、对齐度、时间
- 操作：预览Diff / 采纳 / 拒绝
- 已采纳提案可撤销

#### 3.5.6 Arbitration Arena（冲突仲裁台）
**文件**: `services/web/src/features/arbitration/ArbitrationArena.tsx`
- 对应 UI 设计 §6
- 全屏仲裁界面
- 三栏对决：攻方(AI角色A) | 中央对比区(diff) | 辩方(AI角色B)
- 双方核心论点展示 + 论据质量（合理/不合理）
- 最高裁决按钮：采纳A / 采纳B / 均拒绝
- 筛选标签：待解决/已解决
- 裁决同步为项目全局记忆

#### 3.5.7 Discussion Zone（讨论区）
**文件**: `services/web/src/features/collab/DiscussionZone.tsx`
- 对应 UI 设计 §12
- Tab切换：公共讨论/个人讨论
- AI发言卡片（角色头像+内容+时间）
- 人类输入框（支持@角色名）
- AI发言频次限制可视化
- 「一键收束讨论」按钮

#### 3.5.8 State Airlock（状态流转条）
**文件**: `services/web/src/features/editor/StateAirlock.tsx`
- 对应 UI 设计 §13
- 五状态卡片横向排列
- 当前态高亮、可流转态可点击、禁止态灰色
- 状态切换确认模态

#### 3.5.9 Lightweight Canvas（轻量创作模式）
**文件**: `services/web/src/features/editor/LightweightCanvas.tsx`
- 对应 UI 设计 §14
- 简化三栏（仅编辑器 + 右下角悬浮AI面板）
- 状态条精简：创作中 → 已定稿

#### 3.5.10 Memory & Audit（项目记忆与审计日志）
**文件**: `services/web/src/features/audit/MemoryPanel.tsx`
- 对应 UI 设计 §16.1
- 立场法则列表（已固化/待固化）
- 当前编辑触发记忆提示

**文件**: `services/web/src/features/audit/AuditLog.tsx`
- 对应 UI 设计 §16.2
- 等宽字体日志表格
- 按时间/类型/成员筛选

#### 3.5.11 Sovereign Console（AI控制台）
**文件**: `services/web/src/features/forge/SovereignConsole.tsx`
- 对应 UI 设计 §17
- 各AI角色活跃度滑块
- 全局触发模式（仅@/阶段/全程）
- E-STOP 冻结全域AI按钮

#### 3.5.12 Budget Panel（预算面板）
**文件**: `services/web/src/features/budget/BudgetPanel.tsx`
- 对应 UI 设计 §10
- 团队月度Token：进度条 + 预估耗尽日
- 提案池容量：公共池/私有池/全局私有
- 单文档排名表
- 降级/熔断状态

### 3.6 路由配置
**文件**: `services/web/src/App.tsx`
```
/login                          → 登录页
/dashboard                      → Pipeline Dashboard
/documents/new                  → Forge Initiation
/documents/:docId/forge         → 三栏锻造工作区（重型）
/documents/:docId/forge/light   → 轻量创作模式
/documents/:docId/arbitration   → 全屏仲裁台
/documents/:docId/audit         → 审计日志
/budget                         → 预算面板
```

---

## Phase 4: Yjs 协同服务

### 4.1 Yjs Server
**文件**: `services/yjs/package.json`
- 依赖：yjs, y-websocket, y-leveldb（或直接PostgreSQL持久化）

**文件**: `services/yjs/src/server.ts`
- 基于 y-websocket 的 WebSocket 服务端（端口1234）
- 配置 Y.Doc 持久化到 PostgreSQL（或文件系统简化版）
- 支持 Awareness 协议（光标位置同步）

### 4.2 前端 Yjs 集成
**文件**: `services/web/src/features/editor/YjsProvider.tsx`
- y-websocket provider 连接 yjs-server
- Y.Doc + Y.Text 绑定到 Block 编辑器
- 光标位置 awareness 同步

**文件**: `services/web/src/features/editor/CollaborativeBlock.tsx`
- 单个 Block 的 Y.Text 绑定编辑组件
- 协作光标渲染（不同颜色区分用户/AI）

---

## Phase 5: Demo 种子数据

### 5.1 种子脚本
**文件**: `scripts/seed_db.py`
- 创建 Demo 用户：
  - `owner@demo.com` (张三, Owner)
  - `editor@demo.com` (李四, Editor)
  - `reviewer@demo.com` (王五, Reviewer)
  - `reader@demo.com` (赵六, Reader)
- 创建一个 Demo 文档：
  - 标题：「Q3技术架构升级方案」
  - 立意锚：statement="构建面向企业法务团队的合同审查自动化平台，输出符合ISO 27001认证要求的技术架构方案"
  - 状态：草稿态（方便演示流转）
  - 5个Block填充示例内容（技术方案相关的真实文本）
  - 预设Block标签（1个LOCK、1个Claimed-by-张三）
- 预设AI提案：
  - 文档AI `TechReviewer`：3条润色提案（安全表述补充、术语规范化、架构描述优化）
  - 文档AI `LegalAgent`：3条审查提案（GDPR合规引用、免责声明补充、数据保留条款）
  - 个人AI `我的技术顾问`（张三）：2条私密提案
  - 个人AI `我的文案助手`（李四）：2条私密提案
  - 1条故意冲突：TechReviewer提案"扩充安全架构描述"，LegalAgent提案"精简技术细节保持可读性" → 触发冲突仲裁
- 预设讨论发言（公私讨论区各有2-3条）
- 预设审查结果（表述精准8/10，立场一致9/10）

### 5.2 预设 Mock LLM 文本池
**文件**: `services/api/src/ai_forge/mock_data.py`
- `TECH_REVIEWER_FORGES`: 5条预设润色文本
- `LEGAL_AGENT_FORGES`: 5条预设审查文本
- `PERSONAL_AI_FORGES`: 4条预设个人AI文本
- `CONFLICT_PAIRS`: 2对预设冲突提案
- `REVIEW_RESULTS`: 审查结果预设文本
- `DISCUSSION_MESSAGES`: 讨论区预设对话

---

## Phase 6: 测试骨架

### 6.1 后端测试
- `tests/api/conftest.py` — 共享 fixture（测试数据库、测试客户端、认证头）
- `tests/api/test_state_engine/test_transitions.py` — 状态机40格权限矩阵测试
- `tests/api/test_document/test_document_crud.py` — 文档CRUD
- `tests/api/test_auth/test_auth.py` — 认证注册
- `tests/api/test_ai_forge/test_forge.py` — AI提案流程
- `tests/api/test_approval/test_arbitration.py` — 冲突仲裁

### 6.2 前端测试（骨架）
- `tests/web/` — 组件渲染测试骨架

---

## 文件创建清单汇总

### services/api/src/ (后端)
| # | 文件 | 阶段 |
|---|------|------|
| 1 | `shared/config.py` | P1 |
| 2 | `shared/database.py` | P1 |
| 3 | `shared/redis_client.py` | P1 |
| 4 | `shared/__init__.py` | P1 |
| 5 | `state_engine/engine.py` | P1 |
| 6 | `state_engine/__init__.py` | P1 |
| 7 | `main.py` | P1 |
| 8 | `auth/models.py` | P2 |
| 9 | `auth/service.py` | P2 |
| 10 | `auth/router.py` | P2 |
| 11 | `auth/deps.py` | P2 |
| 12 | `document/models.py` | P2 |
| 13 | `document/service.py` | P2 |
| 14 | `document/router.py` | P2 |
| 15 | `audit/models.py` | P2 |
| 16 | `audit/service.py` | P2 |
| 17 | `audit/router.py` | P2 |
| 18 | `ai_forge/models.py` | P2 |
| 19 | `ai_forge/llm_client.py` | P2 |
| 20 | `ai_forge/mock_data.py` | P2 |
| 21 | `ai_forge/service.py` | P2 |
| 22 | `ai_forge/router.py` | P2 |
| 23 | `approval/models.py` | P2 |
| 24 | `approval/service.py` | P2 |
| 25 | `approval/router.py` | P2 |
| 26 | `collab/ws_gateway.py` | P2 |
| 27 | `collab/router.py` | P2 |

### services/web/src/ (前端)
| # | 文件 | 阶段 |
|---|------|------|
| 28 | package.json, vite.config.ts, tsconfig.json, index.html | P3 |
| 29 | `styles/tokens.css` | P3 |
| 30 | `styles/global.css` | P3 |
| 31 | `shared/types/contracts.ts` (make types生成) | P3 |
| 32 | `shared/components/Button.tsx` | P3 |
| 33 | `shared/components/Modal.tsx` | P3 |
| 34 | `shared/components/Tag.tsx` | P3 |
| 35 | `shared/components/Input.tsx` | P3 |
| 36 | `shared/components/StatusBadge.tsx` | P3 |
| 37 | `shared/api/client.ts` | P3 |
| 38 | `shared/store/authStore.ts` | P3 |
| 39 | `shared/store/documentStore.ts` | P3 |
| 40 | `shared/store/forgeStore.ts` | P3 |
| 41 | `layouts/AppLayout.tsx` | P3 |
| 42 | `layouts/ForgeLayout.tsx` | P3 |
| 43 | `features/pipeline/PipelineDashboard.tsx` | P3 |
| 44 | `features/forge/ForgeInitiation.tsx` | P3 |
| 45 | `features/editor/ForgeEditor.tsx` | P3 |
| 46 | `features/forge/SurgeryDesk.tsx` | P3 |
| 47 | `features/approval/ApprovalDashboard.tsx` | P3 |
| 48 | `features/arbitration/ArbitrationArena.tsx` | P3 |
| 49 | `features/collab/DiscussionZone.tsx` | P3 |
| 50 | `features/editor/StateAirlock.tsx` | P3 |
| 51 | `features/editor/LightweightCanvas.tsx` | P3 |
| 52 | `features/audit/MemoryPanel.tsx` | P3 |
| 53 | `features/audit/AuditLog.tsx` | P3 |
| 54 | `features/forge/SovereignConsole.tsx` | P3 |
| 55 | `features/budget/BudgetPanel.tsx` | P3 |
| 56 | `features/editor/YjsProvider.tsx` | P4 |
| 57 | `features/editor/CollaborativeBlock.tsx` | P4 |
| 58 | `App.tsx` (路由) | P3 |
| 59 | `main.tsx` (入口) | P3 |

### services/yjs/ (Yjs服务)
| # | 文件 | 阶段 |
|---|------|------|
| 60 | `package.json` | P4 |
| 61 | `src/server.ts` | P4 |

### scripts/ (工具脚本)
| # | 文件 | 阶段 |
|---|------|------|
| 62 | `seed_db.py` | P5 |

### tests/ (测试)
| # | 文件 | 阶段 |
|---|------|------|
| 63 | `api/conftest.py` | P6 |
| 64 | `api/test_state_engine/test_transitions.py` | P6 |
| 65 | `api/test_document/test_document_crud.py` | P6 |
| 66 | `api/test_auth/test_auth.py` | P6 |
| 67 | `api/test_ai_forge/test_forge.py` | P6 |
| 68 | `api/test_approval/test_arbitration.py` | P6 |

### alembic/ (数据库迁移)
| # | 项 | 阶段 |
|---|------|------|
| 69 | `alembic.ini` + `alembic/env.py` + 初始迁移 | P1 |

---

## 实施顺序（依赖关系）

```
P1: shared/ + state_engine/ + main.py + alembic    ← 底座
     ↓
P2: auth/ → document/ → audit/ → ai_forge/ → approval/ → collab/    ← 后端BC（auth先做因为有JWT依赖）
     ↓
P3: 前端项目 + 所有页面/组件    ← 可大部分并行
     ↓
P4: Yjs服务 + 前端Yjs集成
     ↓
P5: seed_db.py 种子数据
     ↓
P6: 测试骨架
```

## 验证步骤

1. `make migrate` — 数据库迁移成功
2. `make dev-api` — 后端启动，`/health` 返回200
3. `python scripts/seed_db.py` — 种子数据写入成功
4. `curl POST /api/auth/login` — 认证通过获取Token
5. `curl GET /api/documents` — 返回预填充的Demo文档
6. `make dev-web` — 前端启动，页面可访问
7. 走通全链路：Dashboard → 创建文档 → 编辑 → AI提案 → Diff → 审批 → 状态切换 → 审查 → 冲突仲裁 → 定稿
8. `make test` — 所有测试通过

## 待确认项（实施时需注意）

1. `.env` 文件需要手动创建（含 JWT_SECRET, DATABASE_URL 等）
2. PostgreSQL 需提前运行（Docker或本地）
3. 前端依赖安装需网络环境
4. Yjs 简化版暂不做 SubDoc 分片（>100 Block 的长文档分片 v1再做）
