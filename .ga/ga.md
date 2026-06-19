# 项目: AI文档锻造平台 (ai-collab-docs)

## What
企业级高严谨度文档人机协作锻造平台。摒弃「AI辅助创作」浅层模式，以**层叠约束+双轨共生+状态锁止+渐进信任+分级执行+场景适配**六层逻辑，实现文档从立意锚定到归档封存的全生命周期工程化管控。

核心价值：人类为唯一决策者，多AI角色为标准化打磨模具（提案/审查/辩论，无直改权限）。服务技术方案、商业BP、合规报告、公文、合同草案等高严谨度场景，同时提供轻量模式覆盖笔记/纪要等轻创作。

## Architecture — 四层层叠约束闭环

```
┌─────────────────────────────────────────┐
│  4. 桌面交互层（场景落地）                │
│  锻造工具UI / 争议仲裁视图 / 审批闭环     │
│  双模式切换 / 进度可视化 / 角色协作视图   │
├─────────────────────────────────────────┤
│  3. AI能力层（约束执行）                  │
│  双轨AI体系 / 多Agent中控调度             │
│  五维审查模型 / 分级执行调度器            │
│  项目级向量记忆 / 成本监控                │
├─────────────────────────────────────────┤
│  2. 业务规则引擎层（约束中枢）            │
│  状态机引擎 / 立意校准引擎 / 审批仲裁     │
│  AI权限安全网关 / 渐进信任引擎 / 预算控制 │
├─────────────────────────────────────────┤
│  1. 底层协同数据层（约束底座）            │
│  Yjs CRDT块级文档 / 立意锚元数据           │
│  全量版本快照 / 操作增量日志 / 权限标签   │
└─────────────────────────────────────────┘
```

自下而上层层赋能、层层校验、层层约束。无例外绕过入口。

## Core Invariants（不可变底线，代码物理锁止）

1. **AI零直改权限**：所有内容变更仅支持提案/批注/争议举证，主干文档修改权归属人类，底层网关硬锁止
2. **人类最高主权**：永久拥有打断、仲裁、权限回收、记忆清空、状态重置的最高操作权
3. **立意唯一锚点**：所有AI能力/协作/修改必须对齐立意锚，语义漂移强制校验，冲突无条件适配立意
4. **状态不可乱序**：草稿→讨论→审查→定稿→归档固化链路，禁止跨状态违规操作，全量日志留存
5. **自动采纳可撤回**：任何自动采纳的AI提案，人类可随时撤销并恢复原内容

## 技术选型（已决策）

| 领域 | 选型 | 原因 |
|------|------|------|
| CRDT协同基座 | **Yjs** | 成熟CRDT实现，含Y.Map/Y.Text/Y.Array，支持离线编辑+冲突自动合并，生态完善 |
| 桌面端框架 | **Tauri v2**（Rust 后端 + React 前端/系统 WebView） | 包体积~5MB，内存~50MB起步，原生文件系统/系统托盘/全局快捷键/多窗口管理 |
| 后端框架 | **FastAPI** | 需支持WebSocket长连接(Yjs sync protocol) |
| LLM提供商 | **DashScope** | 需支持多模型路由(大模型深度审查+小模型快速提案) |
| 向量数据库 | **Qdrant** | 项目级记忆+语义漂移检测 |
| 数据库 | **PostgreSQL** | 存储元数据/权限/日志，CRDT文档数据走Yjs |
| 实时通信 | **WebSocket** (Yjs sync protocol) | Yjs原生支持 |

## 构建/运行

```bash
# 后端服务（Docker）
make up              # docker compose 启动全部后端 (api×3 + yjs + postgres + redis)
make down            # 停止全部服务
make dev-api         # 本地开发: FastAPI hot-reload :8000 (services/api)
make dev-yjs         # 本地开发: y-websocket :1234 (services/yjs)
make dev-backend     # 本地开发: 一键启动 api + yjs

# 桌面客户端（Tauri）
make dev-desktop     # Tauri 开发模式 (services/desktop, hot-reload)
make build-desktop   # Tauri 生产构建 → 安装包 (.dmg/.msi/.deb)
make test            # 运行统一测试 (tests/)
make types           # contracts.py → TypeScript类型生成
make migrate         # alembic数据库迁移 (services/api/alembic)
make logs            # 查看全部后端服务日志 (docker compose logs -f)
```

**服务拓扑**:
```
                    ┌──────────────────────┐
                    │  Tauri 桌面客户端      │
                    │  ┌─────────────────┐ │
                    │  │ React WebView    │ │  用户交互层
                    │  │ (Yjs binding +   │ │
                    │  │  UI组件+ 状态机)  │ │
                    │  ├─────────────────┤ │
                    │  │ Tauri Rust Core  │ │  原生能力层
                    │  │ (文件系统/托盘/   │ │
                    │  │  快捷键/多窗口/   │ │
                    │  │  本地缓存/IPC)    │ │
                    │  └────────┬────────┘ │
                    └───────────┼──────────┘
                                │
              WS通道A (Yjs二进制) │  HTTP/WS通道B (JSON业务)
                                ▼
              ┌─────────────────┴──────────────┐
              │          后端服务集群            │
              │  api(:8000) ×3 (least_conn)     │
              │  yjs(:1234) — Node.js独立进程   │
              │  Redis(:6379) — BC事件总线       │
              │  PostgreSQL(:5432)               │
              └─────────────────────────────────┘
```

**Tauri 桌面端职责详解**:
- **React WebView**: 渲染三栏锻造工作区、块级编辑器、AI面板、仲裁视图——所有UI组件，通过 Tauri IPC `invoke()` 调用原生能力
- **Rust Core**: 系统托盘（同步状态/快速新建/E-STOP）、全局快捷键（`Ctrl+Shift+F` 锻造/`Ctrl+Shift+Esc` E-STOP物理熔断）、原生菜单栏（File/Edit/View/Tools/Help）、文件系统读写（打开/保存 .forge 文件、自动保存到本地缓存）、原生通知（提案就绪/审查完成/漂移预警）、多窗口管理
- **Yjs 集成**: WebView 内 `y-websocket` provider 直连 `yjs(:1234)`，Rust 侧通过 IPC 桥接本地文件缓存和离线编辑队列
- **离线支持**: Rust 侧维护本地 SQLite 缓存，离线编辑先写本地，上线后 Yjs 自动合并冲突
- **安装包**: `make build-desktop` 通过 `tauri-bundler` 生成 macOS(.dmg)、Windows(.msi)、Linux(.deb/.AppImage)

## 架构约定

```
ai-collab-docs/
├── .ga/                              # 项目治理
│
├── services/                         # 所有可运行服务
│   ├── api/                          # FastAPI 后端服务
│   │   ├── pyproject.toml
│   │   ├── alembic/                  # DB迁移
│   │   └── src/
│   │       ├── shared/               # 横切: DB, config, events(Redis), base
│   │       ├── document/             # BC1 文档
│   │       ├── collab/               # BC2 协同
│   │       ├── ai_forge/             # BC3 AI锻造
│   │       ├── approval/             # BC4 审批
│   │       ├── auth/                 # BC5 权限
│   │       ├── audit/                # BC6 审计
│   │       ├── state_engine/         # 领域引擎
│   │       └── main.py
│   │
│   ├── desktop/                      # Tauri 桌面客户端
│   │   ├── src-tauri/                # Rust 后端(Cargo.toml, main.rs, 插件)
│   │   ├── package.json              # React 前端依赖
│   │   ├── vite.config.ts            # Vite 构建配置
│   │   └── src/                      # React 渲染进程
│   │       ├── features/{editor,forge,approval,arbitration,auth,collab}/
│   │       ├── shared/{components,hooks,api,types,utils}/
│   │       └── layouts/
│   │
│   └── yjs/                          # Node.js Yjs同步服务(通道A)
│
├── contracts/                        # 跨服务共享数据契约
│   ├── __init__.py                   # 统一导出 (8模块)
│   ├── _auto_enums.py                # AUTO: 枚举
│   ├── _auto_models.py               # AUTO: frozen dataclass
│   ├── state_machine.py              # HAND: TRANSITION_RULES
│   ├── llm_io.py                     # HAND: LLM内部IO
│   ├── ws_protocol.py                # HAND: WebSocket
│   ├── yjs_schema.py                 # HAND: Yjs文档结构
│   ├── gen_contracts.py              # openapi.yml → _auto_*.py
│   └── gen_ts_types.py               # contracts.py → contracts.ts (供桌面端React使用)
│
├── designs/                          # 所有设计文档
│   ├── openapi.yml                   # ★ 单一真相源
│   ├── prd.md
│   ├── design_report.md
│   ├── model_repo.yaml
│   ├── ui/design.md                  # 桌面端 UI 设计规格书
│   └── test/                         # 测试设计文档
│
├── tests/                            # 统一测试代码
│   ├── api/                          # 后端测试
│   ├── desktop/                      # 桌面端测试 (组件 + Tauri E2E)
│   ├── integration/                  # 跨服务集成测试
│   └── conftest.py
│
├── deploy/                           # 部署与基础设施
│   ├── docker/                       # Dockerfile + compose
│   │   ├── Dockerfile.api
│   │   ├── Dockerfile.yjs
│   │   └── compose.yml
│   └── Makefile
│
└── README.md
```

**BC间规则**: 不可互相import models，通过`services/api/src/main.py`路由层编排 + Redis事件总线异步通知。每个BC导出公开Service类(`__init__.py`)。

### contracts与models关系

| 层 | 位置 | 作用 | 依赖 |
|----|------|------|------|
| **contracts** | `contracts/` | 框架无关纯数据契约(frozen dataclass) | 无 |
| **models** | `services/api/src/{bc}/models.py` | SQLAlchemy ORM + Pydantic schema | contracts类型引用 |

`contracts/__init__.py` = 跨模块"通信协议"(桌面端 + 后端共享)。BC内`models.py` = 该BC的"存储+API协议"。同一实体在两个文件中各有职责，不冲突。

### 数据契约优先（Contracts → Core → Business → Integration → Reporting）
在写任何业务逻辑之前，先在 `contracts/` 中定义：
1. Block数据结构（Yjs shared types 映射）
2. Anchor元数据 schema
3. 权限标签枚举
4. 文档状态机 state/transition 定义
5. AI提案/审查结果的标准格式

### 单一写入者原则
- 每个数据只有一个模块能写入，下游只读
- CRDT文档内容：Yjs doc = 唯一真相源
- Anchor：立意锚模块独占写入
- 权限标签：数据层管控，桌面端不可绕过

### 结构保证 > 纪律保证
- 关键不变量写进类型/校验/状态机，不靠调用者"记得"
- 跨模块数据流用 typed dataclass/interface，禁止裸 dict 传参
- AI输出必须经过规则引擎校验后才进入文档

## 工程规范（复用GA标准 + 项目特化）

### 通用
- ruff: E/F/I/UP/B/SIM 规则, 120行宽, double quotes
- commit: feat:/fix:/docs:/refactor: 前缀 + bullet说明
- TDD: 新模块必须配测试
- 文件 ≥ 300行 → 强制拆分
- 大文件操作用 code_run (Python I/O)，不用 file_write/file_patch

### 项目特化
- **禁止 os.chdir() 做请求隔离**（Rule 11）
- **LLM隔离**：AI输出作为候选信号源，须经确定性规则验证；不参与最终决策
- **测试原则**：测试你的逻辑，不测框架承诺（Rule 13）
- **发布门禁**：clean checkout 须可构建，CI引用路径须存在，smoke必验真链路
- **Tauri特化**：Rust侧 `#[tauri::command]` 返回 `Result<T, String>`，禁止 `.unwrap()` 崩溃；IPC消息大小限制 2MB；不依赖浏览器 localStorage，改用 Rust 侧 SQLite 持久化

## "暂时不做"清单（防止范围蔓延）

| 项目 | 原因 | 目标版本 |
|------|------|----------|
| 自研CRDT | 采用Yjs成熟方案 | 不做 |
| 多语言支持(i18n) | MVP聚焦中文企业市场 | v2 |
| Web正式版 | 桌面端优先验证产品力 | 不做 |
| 第三方文档平台导入(飞书/语雀) | 依赖外部API | v1 |
| 离线端侧AI | 算力受限，先云侧 | v2 |
| 自定义模型训练/微调 | 先prompt工程验证 | v2 |
| 全文搜索 | 先聚焦锻造流程 | v1 |
| 文档导出(Word/PDF精美排版) | 非MVP核心 | v1 |
| SSO/企业微信集成 | 先邮箱注册 | v1 |
| 私有化部署 | SaaS先验证 | v2 |

## MVP v0.1 范围定义

> **定位**：多人协作最小可行产品。面向3~5人小型企业团队，主打正式文档多人共创+AI辅助锻造。
> **设计原则**：坚守多人协作主线，架构/协议/规则沿用正式版，仅简化复杂逻辑、删减高阶功能。

### 适用场景
- ✅ 团队多人联合编写：技术方案、项目报告、内部公文、简易商业文档
- ❌ 暂不支持：大型复杂合同、深度合规审查、大规模百人团队、轻量创意文案

### MVP 包含（骨架保留）

| 模块 | MVP范围 | 说明 |
|------|---------|------|
| **CRDT协同** | 基于Yjs的多人块级编辑器 | 支持3~5人实时协作，Block标签体系；单文档上限**1000 Block（约20万字）**，>100 Block触发Root+SubDoc分片；桌面端原生渲染可视区30-50 Block |
| **状态机** | 草稿→讨论→审查→定稿→归档 | 全链路保留 |
| **立意锚** | 创建必填，余弦漂移检测(阈值**0.8**，`dashscope/text-embedding-v3`) | 审查态触发；漂移速率预警(连续3次<0.85)；单次<0.8硬拦截 |
| **双轨AI** | 个人AI + 文档级AI(1~2个预设角色) | 公私域隔离；提案上限公共800/私有400/全局1200；信任分MVP=50 |
| **权限体系** | 五级权限 + 段落认领 | 权责清晰 |
| **锻造工具** | 外科手术式润色台 + 基础审批闭环 | 框选→提案→Diff→接受/拒绝/手动编辑 |
| **冲突仲裁** | 2+ AI对立提案触发仲裁 | 三栏对决视图(可弹出独立窗口)，人类裁决 |
| **审查体系** | 表述精准 + 立场一致（2维） | 砍掉逻辑结构/读者适配/领域合规 |
| **快照溯源** | 审查态自动快照 + 手动快照 | Block级差异对比、一键回滚 |
| **讨论区** | 公私双讨论区 + 中控调度 | 限AI连续发言，人类可打断/定向提问 |
| **项目记忆** | KV存储，六层隔离，≥3次固化 | PostgreSQL统一存储 |
| **桌面原生** | 菜单栏 + 全局快捷键 + 系统托盘 + 本地文件 + 离线保存 | Tauri IPC调用；E-STOP `Ctrl+Shift+Esc`；SQLite离线缓存 |

### MVP 不包含（延后至v1/v2）

| 项目 | 原因 | 目标版本 |
|------|------|----------|
| 渐进信任与自动采纳 | 需生产数据验证 | v1 |
| 预算控制面板(前端) | 先做后端硬限制 | v1 |
| 五维全量审查 | 高Token消耗，先验证2维 | v1 |
| 向量化项目记忆 + 语义检索 | 高复杂度 | v1 |
| 复杂多轮申诉(论据质量评分) | 先做1轮简单申诉 | v1 |
| 驳回重造/双轨留存审批 | 先做3项基础审批 | v1 |
| 轻量创作模式 | 先验证重型锻造 | v1 |
| 自定义AI角色卡 | 先用预设角色 | v1 |
| 模板中心 + 企业管理面板 | 非核心链路 | v2 |
| 多显示器任意弹出 | 先做仲裁台独立窗口 | v1 |
| 决策上浮链 | 先做手动流转 | v1 |

### MVP 成功标准
1. 3人团队走通全链路，协同流畅（Yjs同步P99<500ms）
2. 公私AI提案互不污染，公私域记忆隔离可验证（≥3次相同反馈固化）
3. 冲突仲裁台正确触发并完成裁决
4. 立意锚拦截漂移（召回率≥80%，余弦阈值0.8）
5. 性能基线：REST P99<300ms，AI提案P99<8s，状态切换P99<200ms
6. 全量日志留存，可逐条追溯
7. **桌面端**：安装包 ≤15MB，冷启动 <3s，1000 Block滚动60fps无掉帧，离线编辑上线自动合并无冲突丢失

## AI治理

- **Session Handoff**：每个session结束后更新 `.ga/AI_SESSION.md`
- **版本化配置**：config_version 字段 + auto-upgrade
- **记忆管理**：项目记忆严格限定项目周期，归档封存

## 架构决策记录 (ADR)

### ADR-005: Yjs服务解耦为独立Node.js进程
- **状态**: accepted | **日期**: 2026-06-09
- **决策**: y-websocket独立部署(Node.js :1234)，不嵌入FastAPI。桌面客户端直连services/yjs做通道A(Yjs二进制同步)，services/api仅处理通道B(JSON业务消息)
- **后果**: 正面—Yjs官方协议零侵入。约束—多一个进程运维

### ADR-006: Redis pub/sub作为BC间事件总线
- **状态**: accepted | **日期**: 2026-06-09
- **决策**: BC间异步通知通过Redis pub/sub传递，AuditService订阅所有事件写入日志
- **后果**: 正面—BC物理解耦。约束—Redis依赖，事件最终一致性

### ADR-007: Yjs Document持久化到PostgreSQL
- **状态**: accepted | **日期**: 2026-06-09
- **决策**: services/yjs通过persistence.ts将Y.Doc update增量写入PostgreSQL
- **后果**: 正面—单一DB运维。约束—Yjs增量较大，需定期压缩

### ADR-008: contracts.py → TypeScript类型自动生成
- **状态**: accepted | **日期**: 2026-06-09
- **决策**: contracts.py为单一真相源，gen_ts_types.py自动生成TypeScript类型供桌面端React使用。执行: `make types`
- **后果**: 正面—消除桌面端与后端类型不一致。约束—合约变更必须先跑types同步

### ADR-009: Root+SubDoc 长文档分片架构
- **状态**: accepted | **日期**: 2026-06-16
- **决策**: >100 Block启用Yjs SubDoc分片，Root存元数据，各章节拆为独立SubDoc按需加载。桌面端原生渲染可视区30-50 Block
- **后果**: 正面—大文档编辑流畅。约束—状态机需确认Root级粒度

### ADR-010: Tauri v2 作为桌面端框架
- **状态**: accepted | **日期**: 2026-06-18
- **背景**: 平台从Web端转向桌面客户端。原因：(1) 长文档场景下浏览器内存限制(~2-4GB Tab)无法满足1000 Block需求；(2) 原生文件系统、系统托盘、全局快捷键、多窗口是刚需；(3) 离线编辑需本地持久化
- **决策**: 使用 **Tauri v2**（Rust 后端 + React 前端/系统 WebView）
- **备选方案**:
  | 方案 | 优点 | 缺点 | 为何未选 |
  |------|------|------|---------|
  | Electron | React零摩擦，VSCode验证 | 包体积~150MB，内存~200MB起步 | 资源占用不适合长文档 |
  | 原生Qt/GTK | 最佳性能 | 开发成本极高 | MVP速度优先 |
- **架构**: React渲染进程 → Tauri IPC `invoke()` → Rust Core → 系统API。Yjs在WebView内通过y-websocket直连后端；Rust侧负责文件系统(tauri-plugin-fs)、托盘(tauri-plugin-tray)、快捷键(tauri-plugin-global-shortcut)、通知(tauri-plugin-notification)、本地SQLite离线缓存
- **后果**: 正面—包体积~5MB、内存~50MB起步，原生能力完整，跨平台一致。约束—系统WebView在不同OS有微小差异，需跨平台CI验证

### ADR-011: Rust 后端模块分层
- **状态**: accepted | **日期**: 2026-06-18
- **背景**: ADR-010只说明Tauri Rust承载底层能力，未拆分内部模块，多人开发易出现耦合
- **决策**: `services/desktop/src-tauri/src/` 强制拆分为8个顶层模块，每个模块单一职责，通过 IPC 层统一对外暴露，模块间通信必须经过明确的内部 trait 接口：
  - `ipc/` — IPC 通信层：#[tauri::command] 命令路由、前端事件发射、`invoke()` 请求分发
  - `collab/` — 协同数据模块：Yjs sync protocol bridge、用户 awareness 状态管理
  - `rule_gateway/` — 规则网关模块：状态 transition 预校验（与 contracts/state_machine.py 逻辑镜像）、权限标签验证、立意锚漂移预拦截
  - `fs/` — 本地文件系统模块：`.forge` 文件读写（protobuf/JSON）、文件变更 watcher（自动保存）、导入/导出插件调度器
  - `offline/` — 离线缓存模块：SQLite 本地缓存、离线操作队列（CRUD/AI 请求）、断网重连合并逻辑
  - `ai_scheduler/` — AI 限流调度模块：Token 预算桶/限速、AI 任务优先级队列、E-STOP 电路中断控制
  - `tray/` — 系统托盘模块：托盘菜单构建、原生通知发射
  - `menu/` — 原生菜单模块：菜单栏构建、快捷键注册表
- **约束**: 每个模块仅依赖下层抽象（如 `ai_scheduler` 依赖 `ipc` 发射事件，不依赖前端具体组件）。模块间禁止直接交叉调用，必须通过 `ipc/` 层或内部事件总线传递

### ADR-012: 文档导入/导出插件体系
- **状态**: accepted | **日期**: 2026-06-18
- **背景**: 企业现有合同/技术方案等存量文件（docx/PDF/Markdown）无法进入锻造流程，产品封闭在 `.forge` 私有格式内
- **决策**: `fs/` 模块内置 `ImportPlugin` / `ExportPlugin` trait 接口，每种格式实现为独立插件。MVP 阶段支持 Markdown 导入/导出（零外部依赖）；v1 引入 docx 导入（`mammoth.js` 前端解析 + Rust 侧文件读取）；v2 引入 PDF 导出（headless WebView 打印）。插件接口定义：`parse(bytes: Vec<u8>) -> Result<Vec<Block>>` / `serialize(blocks: Vec<Block>) -> Result<Vec<u8>>`
- **后果**: 正面—存量业务无缝接入。约束—格式解析不是100%保真，复杂排版可能丢失；导入时自动生成"导入来源"审计标记

### ADR-013: E-STOP 物理熔断兜底逻辑
- **状态**: accepted | **日期**: 2026-06-18
- **背景**: E-STOP 仅定义快捷键触发，但未说明熔断后数据如何保障，极端操作存在内容丢失风险
- **决策**: `ai_scheduler::circuit_breaker` 模块在 E-STOP 触发时执行 **三级兜底**：
  1. **正在执行的 AI 任务**：向 `ai_scheduler` 发送中断信号，所有未完成 LLM 请求标记为 `INTERRUPTED`，已生成的部分提案保留为 `DRAFT`（带 E-STOP 时间戳标签），不进入文档
  2. **未保存提案 + 离线缓存数据**：`offline` 模块立即 flush SQLite 所有 pending writes，包括：当前文档 Yjs update 快照、未提交提案池、离线操作队列、冲突仲裁草稿。写入后校验 checksum
  3. **未归档冲突**：当前所有处于仲裁态的冲突条目强制标记为 `E_STOPPED`，冻结等待人类裁决，不自动丢弃
- **恢复流程**：应用重启后，若检测到 E-STOP 标记存在，弹出「熔断恢复」对话框，列出所有被保留的数据项（AI草稿/离线写入/冲突），用户逐条选择恢复/丢弃。恢复时自动校验 checksum，失败则提示"数据可能损坏，建议从云端最新版本恢复"
- **后果**: 正面—极端场景下内容零丢失。约束—E-STOP 时短暂卡顿（SQLite flush 可能需 100-300ms），UI 显示 "正在安全保存..." 遮罩

### ADR-014: 跨设备云端同步数据流
- **状态**: accepted | **日期**: 2026-06-18
- **背景**: 当前仅覆盖「离线本地编辑，联网后单端同步」，多台电脑登录同一账号、跨设备打开同一文档的机制空白
- **决策**: 
  - **身份层**: JWT 令牌 + 设备指纹（device_id），用户账户跨设备绑定。登录时获取设备列表
  - **文档元数据**: 标题/权限/成员/状态等通过 REST API 读写，PostgreSQL 为唯一真相源。桌面端启动时拉取文档列表，变更时推送到后端
  - **文档内容**: Yjs CRDT 跨设备自动合并。当设备B上线时，Yjs 自动将本地 update 与服务器端 update 合并。冲突由 CRDT 语义解决（last-write-wins for text），无需人工干预
  - **离线队列**: 每台设备有独立的 SQLite 离线队列（`offline` 模块）。上线后按 FIFO 顺序上传队列条目，服务端接收后广播到其他在线设备
  - **冲突降级**: 若 CRDT 合并产生语义异常（如同一段落被两台设备同时大幅修改），触发「软冲突」：标记段落为 `MERGE_WARNING`，UI 显示黄色警示边框，提示用户手动检查
- **后果**: 正面—换设备无缝接续工作。约束—首次打开大文档时需全量加载（可能慢于本地文件打开）；多设备同时编辑时网络带宽消耗翻倍

### ADR-015: 长文档拆分辅助工具
- **状态**: accepted | **日期**: 2026-06-18
- **背景**: Yjs SubDoc 长文档分片(ADR-009) 规定 >100 Block 启用分片，但用户手中有超长文档需要主动拆分为独立子文档进行管理，当前缺乏拆分工具
- **决策**: 达到 900 Block 时顶栏黄色预警「接近上限——建议拆分」。拆分向导按 H1/H2 标题边界建议拆分点。拆分后创建子文档并建立兄弟关系引用，立意锚继承+子文档独白，权限/成员默认复制。Rust `fs` 模块扩展 `split_document()` 命令。独立窗口 680×520px
- **后果**: 正面—超长文档可被拆分为逻辑独立的子文档。约束—子文档各自独立 Yjs 状态，跨文档引用需前端超链接实现(MVP不做联动编辑)

### ADR-016: 记忆文件损坏修复
- **状态**: accepted | **日期**: 2026-06-18
- **背景**: 项目记忆(SQLite/PG/向量)是AI上下文根基，文件系统崩溃或进程异常终止可能导致记忆损坏，当前缺乏检测和修复机制
- **决策**: 每条记忆写入时附加 SHA256 checksum。启动时全量扫描，损坏条目隔离到 `quarantine/` 并标记 CORRUPTED。SQLite WAL checkpoint 回滚到最近有效位点；每日自动 `.tar.gz` 备份到 `~/.forge-docs/backups/`。设置面板「记忆管理 → 扫描并修复」。Y.Doc 损坏时导出可恢复部分，不可恢复 Block 标记为 IRRECOVERABLE 占位符并通知 Owner
- **后果**: 正面—记忆零丢失。约束—每日备份额外占用 ~10-50MB 磁盘

### ADR-017: 云端 LLM 服务宕机三级降级
- **状态**: accepted | **日期**: 2026-06-18
- **背景**: DashScope LLM 是AI提案/审查/讨论的唯一在线服务方，宕机或网络中断时用户无法使用锻造功能
- **决策**: 
  - **L1 静默重试**(0~60s): 自动重试3次指数退避(5s/15s/40s)，前端仅旋转图标
  - **L2 队列化**(60s~30min): 黄色横幅「LLM暂不可用——请求已保存」。Rust `ai_scheduler` 写 SQLite 离线队列，定时重试(1/3/10/30min)
  - **L3 纯文本模式**(>30min): AI面板变灰「✕ AI不可用」。用户正常编辑/查找替换。已保存提案仍可查看决策。托盘变灰
  - **恢复**: 首次成功请求后 FIFO 处理队列，绿色横幅「正在处理之前 N 条请求...」
  - **心跳**: `ai_scheduler` 每分钟 `GET /health`，纳入API预算
- **后果**: 正面—LLM宕机不影响基本编辑。约束—心跳探测额外60次/天 API调用

### ADR-018: 预算耗尽未合并提案缓存策略 (更新: 2026-06-19 — 补充额度治理权)

- **状态**: accepted | **日期**: 2026-06-18 | **更新**: 2026-06-19
- **背景**: Token预算耗尽时传入的AI提案若直接丢弃将丢失内容和讨论
- **决策**: 预算70%/90%预警通知。耗尽时「锻造」按钮禁用+灰底提示，新请求可「保存草稿」。未合并提案存 SQLite `pending_proposals` 表（含完整Block引用+AI建议+时间戳）。前端队列面板「📋 N条提案等待预算重置」。下月1日按优先级(审查>润色>讨论)自动处理。Owner可申请紧急预算(1000额外Token/月，需二次确认)
- **后果**: 正面—预算耗尽不丢提案。约束—队列内提案引用可能因文档编辑而过时，处理时需重新diff校验
- **补充规则 (problem.md §二审查意见#2-3)**: 
  - **额度来源绑定**: 文档创建时选择 `quota_source: personal | team`，创建后不可切换（v2支持切换，需审计+管理员审批）
  - **协作者消耗**: 协作编辑时发起的AI提案消耗文档绑定的quota_source（而非协作者个人池）
  - **团队管理员治理权**: 团队管理员对「消耗团队预算的文档」保留查看/熔断权限（不动文档内容/角色，仅管理团队额度使用）——这是独立于文档局部角色的第三种权限类型（资源治理权≠内容协作权）

### ADR-019: Yjs 极端冲突完整合并流程
- **状态**: accepted | **日期**: 2026-06-18
- **背景**: ADR-014仅定义 MERGE_WARNING 标记，Yjs CRDT 语义合并失败时缺少完整用户导向流程
- **决策**: 六步流程:
  - **检测**: 块级 Hash 对比，离线修改文本相似度 <40% 触发
  - **冻结**: 红色边框⬛标记 SEVERE_CONFLICT，暂停该Block所有编辑和AI提案
  - **并排呈现**: 独立窗口 1000×600px，左右分栏+内联Diff(+绿/-红)
  - **合并选项**: [保留A][保留B][AI辅助合并][手动编辑合并]。AI合并调用LLM生成融合版本
  - **审计记录**: 两个原始版本+最终选择存入 audit_log
  - **解除冻结**: 合并后清除标记。7天未处理自动保留最新版本+记录「自动解决」
- **后果**: 正面—冲突有完整SOP。约束—极端冲突弹窗打断工作流；AI合并额外耗Token

### ADR-020: 新手简易模式与引导体系
- **状态**: accepted | **日期**: 2026-06-18
- **背景**: 六层记忆/信任分/漂移阈值/仲裁评分/多级预算/状态锁止等规则体系门槛极高，新用户易被功能密度劝退
- **决策**: 三层渐进式暴露:
  - **L0 简易模式(默认新用户)**: 顶部开关 `🔰简易/⚙专业`。隐藏: 信任分面板/仲裁评分/预算面板/五维审查/AI角色管理/Block历史/记忆面板/企业面板/状态机流转条(仅显示状态标签)。保留: 三栏编辑器/框选→AI润色→接受拒绝/讨论区(简化版)/保存导出。自动: 信任分≥50时提案自动显示绿色「建议接受」; 预算静默; 锚点漂移仅≥0.15时弹一次警告
  - **L1 引导教程**: 首次启动4步引导(欢迎→写文档→AI帮你→你与AI边界)，全程可跳过/重新打开(菜单Help→新手教程)
  - **L2 模板初始化**: 📄公文模板(立意锚+权限Owner+2Editor+4Reader+预置AI角色「公文格式审查Agent」)、📄合同模板(立意锚+权限Owner+1Editor+2Reviewer+预置「合同条款校验Agent」「合规审查Agent」)。一键套用→5秒进入编辑。模板JSON格式可扩展
- **后果**: 正面—非专业用户10秒上手，专业用户无损失。约束—简易模式隐藏规则仍在后台运行；模板维护需持续投入

### ADR-021: 两域权限拆分 — 账号全局身份 vs 单文档局部角色 (problem.md §一)

- **状态**: accepted | **日期**: 2026-06-19
- **背景**: 原设计未区分「账号全局身份」和「单文档局部角色」两套独立权限域，导致"创建文档=成为全局管理员"的逻辑混淆。团队管理员自动获得所有文档最高管控权，普通用户可见团队管理面板（仅置灰）。
- **决策**: 
  - **两域永久解耦**: 
    - 域1: 账号全局身份（`GlobalIdentity`: `REGULAR_USER`/`TEAM_ADMIN`/`OPS_TECH`）— 登录时由企业后台分配，决定顶级视图、团队资源额度、后台管理功能，不随文档创建/分享改变
    - 域2: 单文档局部角色（`UserRole`: `OWNER`/`LEAD_EDITOR`/`EDITOR`/`REVIEWER`/`READER`）— 仅管控单文档内操作，不解锁团队全局资源
  - **全局普通用户**: 新建文档自动获得该文档局部Owner权限，但账号全局身份不变。仅消耗个人私有月度额度。团队管理视图/分组永久隐藏。
  - **全局团队管理员**: 打开他人文档时仅拥有被分配的文档局部角色（不能直接归档、清空记忆）。拥有独立团队管理视图，可调配团队预算/成员/模板/规则。
  - **编辑器双身份标签**: 顶部状态流转条左侧永久展示两行 `全局身份：XXX | 当前文档身份：XXX`，hover悬浮提示权限边界
  - **前端无权限功能直接隐藏**（不做置灰），仅保留当前角色可用功能
- **后果**: 正面—消除权限混淆，三类用户界面互不干扰。约束—权限判断需同时在API层和前端做双向校验；双身份标签需额外UI空间
- **相关**: contracts/roles_and_permissions.py — 五层权限体系: `GlobalIdentity` / `AccountIdentity` / `DocumentRoleBinding`

### ADR-022: 三轴权限模型预留 — Account × Team × Document (problem.md §二审查意见#1)

- **状态**: accepted | **日期**: 2026-06-19
- **背景**: problem.md外部审查指出两轴模型（账号×文档）在多团队场景下失效——用户可能在团队A是管理员、团队B是普通成员。当前"全局团队管理员"是账号级单一标签。
- **决策**: MVP采用两轴（`GlobalIdentity` × `UserRole`），预留第三轴Team为v2。当前以"单团队隐式上下文"（team_id="default"）运行，API层携带team_id占位。v2扩展：
  - 账号身份(普通用户/运维) 
  - 团队角色(在某个team_id下的MEMBER/ADMIN) 
  - 文档局部角色(在某个doc_id下的五级角色)
- **后果**: 正面—MVP不增加复杂度，v2扩展路径清晰。约束—需在Auth BC的JWT payload中携带team_id占位；DB schema预留team_id字段
- **相关**: contracts/roles_and_permissions.py — 五层权限体系: `TeamRole` / `AccountIdentity(team_id, team_role)`