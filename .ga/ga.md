# 项目: AI文档锻造平台 (ai-collab-docs)

## What
企业级高严谨度文档人机协作锻造平台。摒弃「AI辅助创作」浅层模式，以**层叠约束+双轨共生+状态锁止+渐进信任+分级执行+场景适配**六层逻辑，实现文档从立意锚定到归档封存的全生命周期工程化管控。

核心价值：人类为唯一决策者，多AI角色为标准化打磨模具（提案/审查/辩论，无直改权限）。服务技术方案、商业BP、合规报告、公文、合同草案等高严谨度场景，同时提供轻量模式覆盖笔记/纪要等轻创作。

## Architecture — 四层层叠约束闭环

```
┌─────────────────────────────────────────┐
│  4. 前端交互层（场景落地）                │
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
| 前端框架 | React | React/Vue/Svelte 均可，需与Yjs绑定层适配 |
| 后端框架 | fastapi | 需支持WebSocket长连接(Yjs sync protocol) |
| LLM提供商 | dashscope | 需支持多模型路由(大模型深度审查+小模型快速提案) |
| 向量数据库 | qdrant | 项目级记忆+语义漂移检测 |
| 数据库 | postgresql | 存储元数据/权限/日志，CRDT文档数据走Yjs |
| 实时通信 | WebSocket (Yjs sync protocol) | Yjs原生支持 |

## 构建/运行

```bash
make up           # docker compose 启动全部服务 (nginx + web + api×3 + yjs + postgres + redis)
make down         # 停止
make dev-api      # 本地开发: FastAPI hot-reload :8000 (services/api)
make dev-web      # 本地开发: Vite dev :5173 (services/web)
make dev-yjs      # 本地开发: y-websocket :1234 (services/yjs)
make dev          # 本地开发: 一键启动 api + web + yjs (不含nginx, 直连端口)
make test         # 运行统一测试 (tests/)
make types        # contracts.py → TypeScript类型生成
make migrate      # alembic数据库迁移 (services/api/alembic)
make nginx-reload # 热重载nginx配置 (nginx -s reload)
make logs         # 查看全部服务日志 (docker compose logs -f)
```

**服务拓扑**:
```
                    ┌─────────────┐
                    │  Nginx(:443) │  SSL终端 + 反向代理 + 负载均衡
                    └──┬──────┬───┘
                       │      │
             静态资源   │      │  /api/* 负载均衡
             缓存+压缩  │      │  least_conn → api 多实例
                       ▼      ▼
                    web(:5173)  api(:8000) ─ api(:8001) ─ api(:8002)
                       │             │
           WS通道A     │             │  WS通道B (JSON业务)
        (Yjs二进制)    │             │  sticky session绑定
                       ▼             ▼
                    yjs(:1234)   Redis(:6379) 事件总线
                       │             │
                       └──────┬──────┘
                              ▼
                         PostgreSQL(:5432)
                    (元数据 / Y.Doc持久化 / 日志)
```

**Nginx 职责详解**:
- **SSL 终端**: 所有 HTTPS 由 Nginx 卸载，内网服务全 HTTP
- **静态资源**: React/Vite 构建产物由 Nginx 直接 serve（/assets/*），命中后不回源 web
- **API 负载均衡**: `upstream api_backend` 配置 3 个 api worker 实例，least_conn 算法，max_fails=3 自动摘除
- **WebSocket 代理**: `/ws/*` 路径升级 HTTP→WS 协议到 yjs-server，proxy_read_timeout 延长至 7d（保持长连接）
- **API WS 粘性会话**: 业务WebSocket 用 ip_hash 保证同一客户端始终路由到同一 api 实例
- **gzip/brotli**: 对 text/css/js/json 开启压缩，减少传输体积
- **安全头**: X-Frame-Options / X-Content-Type-Options / CSP 统一注入
- **限流**: limit_req_zone 对 /api/llm/* 路径限制 30r/m（防AI调用超量）

## 架构约定

```
ai-collab-docs/
├── .ga/                              # 项目治理: ga.md / directory.md / AI_SESSION.md / memory/
│
├── services/                         # 所有可运行服务
│   ├── api/                          # FastAPI 后端服务
│   │   ├── pyproject.toml
│   │   ├── alembic/                  # DB迁移
│   │   └── src/
│   │       ├── shared/               # 横切: DB, config, events(Redis), base
│   │       ├── document/             # BC1 文档: models, service, router
│   │       ├── collab/               # BC2 协同: gateway(WS通道B), router
│   │       ├── ai_forge/             # BC3 AI锻造: models, service, llm_client, router
│   │       ├── approval/             # BC4 审批: models, service, router
│   │       ├── auth/                 # BC5 权限: models, service, router
│   │       ├── audit/                # BC6 审计: models, service, router
│   │       ├── state_engine/         # 领域引擎: engine, rules
│   │       └── main.py               # FastAPI组装, 路由注册
│   │
│   ├── web/                          # React 前端服务
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   └── src/
│   │       ├── features/{editor,forge,approval,arbitration,auth,collab}/
│   │       ├── shared/{components,hooks,api,types,utils}/
│   │       └── layouts/
│   │
│   └── yjs/                          # Node.js Yjs同步服务(通道A)
│       ├── package.json
│       └── src/
│
├── contracts/                        # 跨服务共享数据契约
│   ├── contracts.py                  # 框架无关纯数据契约(唯一真相源→TS生成)
│   └── gen_ts_types.py               # contracts→TypeScript类型生成
│
├── designs/                          # 所有设计文档
│   ├── prd.md
│   ├── design_report.md
│   ├── model_repo.yaml
│   ├── ui/
│   │   └── design.md
│   └── test/                         # 测试设计文档
│       ├── README.md
│       ├── test-plan.md
│       ├── test-strategy.md
│       ├── test-matrix.md
│       └── test-cases.md
│
├── tests/                            # 统一测试代码（前后端合并）
│   ├── api/                          # 后端测试(镜像 services/api/src/ 结构)
│   │   ├── document/
│   │   ├── collab/
│   │   ├── ai_forge/
│   │   ├── approval/
│   │   ├── auth/
│   │   ├── audit/
│   │   └── conftest.py
│   ├── web/                          # 前端测试
│   ├── integration/                  # 跨服务集成测试
│   └── conftest.py                   # 全局共享 fixture
│
├── deploy/                           # 部署与基础设施
│   ├── docker/                       # Dockerfile + compose
│   │   ├── Dockerfile.api
│   │   ├── Dockerfile.web
│   │   ├── Dockerfile.yjs
│   │   └── compose.yml
│   └── Makefile                      # 构建/运行/测试
│
└── README.md
```

**BC间规则**: 不可互相import models，通过`services/api/src/main.py`路由层编排 + Redis事件总线异步通知。每个BC导出公开Service类(`__init__.py`)。

### contracts与models关系

| 层 | 位置 | 作用 | 依赖 |
|----|------|------|------|
| **contracts** | `contracts/contracts.py` | 框架无关纯数据契约(frozen dataclass) | 无 |
| **models** | `services/api/src/{bc}/models.py` | SQLAlchemy ORM + Pydantic schema | contracts类型引用 |

`contracts.py` = 跨模块"通信协议"(前后端共享，TS生成源头)。BC内`models.py` = 该BC的"存储+API协议"(SQLAlchemy表 + Pydantic请求体)。同一实体在两个文件中各有职责，不冲突。

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
- 权限标签：数据层管控，前端不可写

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

## "暂时不做"清单（防止范围蔓延）

| 项目 | 原因 | 目标版本 |
|------|------|----------|
| 自研CRDT | 采用Yjs成熟方案 | 不做 |
| 多语言支持(i18n) | MVP聚焦中文企业市场 | v2 |
| 移动端原生App | 先Web端验证产品力 | v2 |
| 第三方文档平台导入(飞书/语雀) | 依赖外部API | v1 |
| 离线端侧AI | 算力受限，先云侧 | v2 |
| 自定义模型训练/微调 | 先prompt工程验证 | v2 |
| 全文搜索 | 先聚焦锻造流程 | v1 |
| 文档导出(Word/PDF精美排版) | 非MVP核心 | v1 |
| SSO/企业微信集成 | 先邮箱注册 | v1 |
| 私有化部署 | SaaS先验证 | v2 |

## MVP v0.1 范围定义

> **定位**：多人协作最小可行产品。面向3~5人小型企业团队（技术组/项目组/行政公文组），主打正式文档多人共创+AI辅助锻造。
> **设计原则**：坚守多人协作主线（骨架保留、功能精简、流程完整闭环、梯度迭代），架构/协议/规则沿用正式版，仅简化复杂逻辑、删减高阶功能。

### 适用场景
- ✅ 团队多人联合编写：技术方案、项目报告、内部公文、简易商业文档
- ❌ 暂不支持：大型复杂合同、深度合规审查、大规模百人团队、轻量创意文案

### MVP 包含（骨架保留）

| 模块 | MVP范围 | 说明 |
|------|---------|------|
| **CRDT协同** | 基于Yjs的多人块级编辑器 | 支持3~5人实时协作，Block标签体系；单文档上限**1000 Block（约20万字）**，>100 Block触发Root+SubDoc分片（按需加载）；前端虚拟滚动仅渲染可视区20-30 Block |
| **状态机** | 草稿→讨论→审查→定稿 | 全链路保留，各状态权责与PRD一致 |
| **立意锚** | 创建必填，余弦相似度漂移检测（固定阈值**0.8**，模型`dashscope/text-embedding-v3`） | 仅在审查态触发检测；漂移速率预警（连续3次<0.85）；单次<0.8硬拦截。后续用16对校准样例集精调 |
| **双轨AI** | 个人AI(每用户1个) + 文档级AI(1~2个预设角色) | 公私域隔离；AI提案数上限——公共池800/私有池400/全局1200，80%橙色/95%弹窗/100%阻断；信任分MVP固定50（冷启动，v1启用自动采纳） |
| **权限体系** | 五级权限(所有者/主编辑/编辑者/审查者/只读) + 段落认领 | 权责清晰，区块绑定个人 |
| **锻造工具** | 外科手术式润色台 + 基础审批闭环 | 框选→提案→Diff视图→接受/拒绝/手动编辑（不含双轨留存/驳回重造） |
| **冲突仲裁** | 2+ AI角色对立提案触发仲裁 | 三栏对决视图，人类裁决（无超时自动升级 → v1）；仲裁台提供可解决/待解决筛选标签 |
| **审查体系** | 表述精准 + 立场一致（2维） | 砍掉逻辑结构/读者适配/领域合规 |
| **快照溯源** | 审查态自动快照 + 手动快照 | Block级差异对比、一键回滚、增量日志 |
| **讨论区** | 公私双讨论区 + 中控调度 | 限制AI连续发言，人类可打断/定向提问/收束讨论 |
| **项目记忆** | KV存储（审批结果 + 仲裁结论 + 人类反馈），六层隔离（存储/访问/写入/可见性/生命周期/固化≥3次） | PostgreSQL统一存储，私有记忆脱离Yjs；≥3次相同反馈才固化长期记忆，单次仅影响当前session |

### MVP 不包含（高阶延后至v1/v2）

| 项目 | 原因 | 目标版本 |
|------|------|----------|
| 渐进信任与自动采纳 | 需生产数据验证信任模型 | v1 |
| 预算控制面板(前端) | 先做后端硬限制，用户面暂不暴露 | v1 |
| 五维全量审查(逻辑结构/读者适配/领域合规) | 高Token消耗，先验证2维 | v1 |
| 向量化项目记忆 + 语义检索 | 高复杂度，先KV存储验证 | v1 |
| 复杂多轮申诉(论据质量评分) | 先做1轮简单申诉 | v1 |
| 驳回重造/双轨留存审批选项 | 先做3项基础审批 | v1 |
| 轻量创作模式 | 先验证重型锻造核心价值 | v1 |
| 自定义AI角色卡 | 先用2~3个预设角色 | v1 |
| 模板中心 + 企业管理面板 | 非核心链路 | v2 |
| 离线协同增强UX | Yjs底层已支持冲突合并，仅不做离线专属交互 | v1 |
| 决策上浮链(超时自动升级) | 先做手动流转 | v1 |

### MVP 成功标准
1. 3人团队协作完成一篇技术方案文档，走通 草稿→讨论→审查→定稿 全链路；协同流畅（3人同时编辑100 Block文档无卡顿，Yjs同步P99<500ms）
2. 个人AI与文档级AI各产出提案且互不污染（公私池独立计数），公私域记忆隔离可验证（≥3次相同反馈固化至长期记忆）
3. 2个AI角色对同一Block产生对立提案时，冲突仲裁台正确触发并完成裁决
4. 立意锚在审查态拦截至少1次明显语义漂移（人工标注10个测试用例，召回率≥80%，余弦阈值0.8）
5. 性能基线：REST API读取P99<300ms，AI提案生成P99<8s，状态切换P99<200ms。MVP上线后Locust压测校准
6. 所有操作（提案/审批/仲裁/状态切换）全量日志留存，可逐条追溯

## AI治理

- **Session Handoff**：每个设计/开发session结束后更新 `.ga/AI_SESSION.md`
- **版本化配置**：config_version 字段 + auto-upgrade
- **记忆管理**：项目记忆严格限定项目周期，归档封存

## 架构决策记录 (ADR)

### ADR-005: Yjs服务解耦为独立Node.js进程
- **状态**: accepted | **日期**: 2026-06-09
- **决策**: y-websocket独立部署(Node.js :1234)，不嵌入FastAPI。services/web直连services/yjs做通道A(Yjs二进制同步)，services/api collab/ws_gateway仅处理通道B(JSON业务消息)
- **后果**: 正面—Yjs官方协议零侵入，升级独立。约束—多一个进程运维

### ADR-006: Redis pub/sub作为BC间事件总线
- **状态**: accepted | **日期**: 2026-06-09
- **决策**: BC间异步通知(ProposalCreated/ConflictDetected/StateChanged等)通过Redis pub/sub传递，AuditService订阅所有事件写入日志
- **后果**: 正面—BC物理解耦。约束—Redis依赖，事件最终一致性

### ADR-007: Yjs Document持久化到PostgreSQL
- **状态**: accepted | **日期**: 2026-06-09
- **决策**: services/yjs通过persistence.ts将Y.Doc update增量写入PostgreSQL(与services/api共享DB)
- **后果**: 正面—单一DB运维。约束—Yjs增量较大，需定期压缩

### ADR-008: contracts.py → TypeScript类型自动生成
- **状态**: accepted | **日期**: 2026-06-09
- **决策**: Python contracts.py为单一真相源，contracts/gen_ts_types.py自动生成services/web TypeScript类型定义。执行: `make types`
- **后果**: 正面—消除前后端类型不一致。约束—合约变更必须先跑types同步

### ADR-009: Root+SubDoc 长文档分片架构
- **状态**: accepted | **日期**: 2026-06-16
- **决策**: 超过100 Block的文档启用Yjs SubDoc分片——Root文档存元数据（立意锚/状态/权限），各章节拆为独立SubDoc按需加载/卸载，前端虚拟滚动仅渲染可视区20-30 Block。分片对用户透明。
- **后果**: 正面—单Y.Doc CRDT同步压力可控，大文档编辑流畅。约束—状态机粒度需确认为Root级，审查快照需批次化所有SubDoc，Yjs server需支持SubDoc按需加载
