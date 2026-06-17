# 项目目录结构

> 项目: AI文档锻造平台 (ai-collab-docs)
> 更新: 2026-06-17 — 添加 scripts/、AI_SESSION.md、contracts/README.md；补充前端 feature 内部结构
> 原则: 每个父目录有明确的单一基本功，子目录按功能细分

```
ai-collab-docs/
│
├── .ga/                                    # 项目治理中心（Governance）
│   ├── ga.md                               #   项目设计总纲——架构约定、技术选型、MVP范围、ADR
│   ├── directory.md                        #   【本文件】目录结构说明
│   ├── AI_SESSION.md                       #   AI会话交接记录——每次session结束后更新
│   └── memory/                             #   工作记忆存储
│       └── workspace_mem.txt
│
├── services/                               # 所有可运行服务（Runnable Services）
│   │
│   ├── api/                                #   FastAPI 后端服务（API Backend）
│   │   ├── pyproject.toml                  #     Python项目配置与依赖
│   │   ├── alembic/                        #     数据库迁移脚本（PostgreSQL DDL版本管理）
│   │   └── src/
│   │       ├── shared/                     #     横切层：数据库连接、Redis事件总线、配置、基类
│   │       ├── document/                   #     BC1 文档限界上下文——Block内容、标签、立意锚（models/service/router）
│   │       ├── collab/                     #     BC2 协同限界上下文——WebSocket网关（通道B）、Yjs集成
│   │       ├── ai_forge/                   #     BC3 AI锻造限界上下文——双轨AI、提案、LLM客户端、信任分、记忆
│   │       ├── approval/                   #     BC4 审批限界上下文——审查快照、仲裁、提案审批
│   │       ├── auth/                       #     BC5 权限限界上下文——5级角色（Owner/LeadEditor/Editor/Reviewer/Reader）
│   │       ├── audit/                      #     BC6 审计限界上下文——全量操作日志
│   │       ├── state_engine/               #     领域引擎——文档状态机、Transition权限矩阵、规则校验
│   │       └── main.py                     #     FastAPI应用组装、路由注册、中间件
│   │
│   ├── web/                                #   React 前端服务（Web Frontend）
│   │   ├── package.json                    #     Node.js依赖与脚本
│   │   ├── vite.config.ts                  #     Vite构建配置
│   │   └── src/
│   │       ├── features/                   #     功能模块（每个feature独立目录，标准子结构: components/hooks/types/__tests__/index.ts）
│   │       │   ├── editor/                 #       协同编辑器——Yjs绑定、Block渲染、光标同步、虚拟滚动
│   │       │   ├── forge/                  #       锻造工作站——润色台、提案Diff、AI交互面板、双轨切换
│   │       │   ├── approval/               #       审批视图——审查界面、提案审批、漂移检测结果、五维审查分类
│   │       │   ├── arbitration/            #       仲裁视图——三栏对决界面、争议裁决、申诉评分
│   │       │   ├── auth/                   #       认证与权限——登录、五级角色管理、权限矩阵展示、段落认领
│   │       │   ├── collab/                 #       协作功能——在线状态、协作光标、通知、讨论区
│   │       │   ├── team/                   #       企业管理——团队创建、成员邀请、批量权限、进度大盘
│   │       │   ├── budget/                 #       预算控制——三级预算面板、提案计数、Token饱和度、降级/熔断状态
│   │       │   ├── templates/              #       模板中心——预设模板浏览、自定义模板保存与分享、角色模板复用
│   │       │   └── roles/                  #       角色管理——自定义AI角色卡创建、官方预设角色库、活跃度配置
│   │       ├── shared/                     #     共享组件与工具
│   │       │   ├── components/             #       通用UI组件
│   │       │   ├── hooks/                  #       通用React Hooks
│   │       │   ├── api/                    #       REST/WS API客户端封装
│   │       │   ├── types/                  #       TypeScript类型定义（含contracts.ts自动生成）
│   │       │   └── utils/                  #       工具函数
│   │       └── layouts/                    #     布局组件
│   │
│   └── yjs/                                #   Yjs WebSocket 协同服务（Node.js独立进程）
│       ├── package.json
│       └── src/                            #     y-websocket服务端——通道A（Yjs二进制CRDT同步）
│
├── contracts/                              # 跨服务共享数据契约（Shared Data Contracts）
│   ├── README.md                           #   合约使用说明——新增合约流程、TS同步命令、合约vs模型关系
│   ├── contracts.py                        #   框架无关的纯Python数据契约（frozen dataclass）——唯一真相源
│   └── gen_ts_types.py                     #   从contracts.py自动生成TypeScript类型定义的工具
│
├── designs/                                # 所有设计文档（Design Documents）
│   ├── prd.md                              #   产品需求文档——五不可变底线、六层逻辑、核心模块
│   ├── design_report.md                    #   设计报告——6轮结构化设计（Context→StateMachine→DDD→Component→Sequence→Activity）
│   ├── model_repo.yaml                     #   统一模型仓库——概念、流、约束的结构化存储
│   ├── ui/                                 #   UI设计
│   │   └── design.md                       #     Obsidian Luxe 2.0设计语言——重型锻造工作区、仲裁台、三栏布局
│   └── test/                               #   测试设计文档
│       ├── README.md                       #     测试文档体系导航
│       ├── test-plan.md                    #     测试计划——范围、资源、里程碑、风险
│       ├── test-strategy.md                #     测试方案——测试类型、环境规格、通过标准、阈值试探
│       ├── test-matrix.md                  #     详细测试矩阵——T1~T6共70+可测试点
│       └── test-cases.md                   #     测试用例（15条样例，TC-ID格式）
│
├── tests/                                  # 统一测试代码（Unified Test Code）
│   ├── api/                                #   后端API测试（镜像 services/api/src/ 结构）
│   │   ├── document/                       #     BC1 文档测试
│   │   ├── collab/                         #     BC2 协同测试
│   │   ├── ai_forge/                       #     BC3 AI锻造测试
│   │   ├── approval/                       #     BC4 审批测试
│   │   ├── auth/                           #     BC5 权限测试
│   │   ├── audit/                          #     BC6 审计测试
│   │   └── conftest.py                     #     API测试共享fixture
│   ├── web/                                #   前端测试（组件测试 + E2E）
│   ├── integration/                        #   跨服务集成测试（端到端链路验证）
│   └── conftest.py                         #   全局共享fixture
│
├── deploy/                                 # 部署与基础设施（Deployment & Infrastructure）
│   ├── nginx/                              #   Nginx 反向代理与负载均衡
│   │   ├── nginx.conf                      #     主配置——upstream池、SSL、gzip、安全头、限流
│   │   ├── conf.d/
│   │   │   ├── default.conf                #       站点配置——路由规则、静态资源缓存、WS代理
│   │   │   └── rate_limit.conf             #       限流规则——/api/llm/* 30r/m
│   │   └── ssl/                            #     SSL证书（生产用，不提交Git）
│   ├── docker/                             #   Docker镜像构建
│   │   ├── backend.Dockerfile              #     API服务镜像（支持多实例扩展）
│   │   ├── frontend.Dockerfile             #     Web前端镜像（构建产物由Nginx serve）
│   │   ├── yjs-server.Dockerfile           #     Yjs协同服务镜像
│   │   └── nginx.Dockerfile                #     Nginx镜像（Alpine+Nginx+SSL）
│   ├── docker-compose.yml                  #   本地开发容器编排（nginx + web + api×3 + yjs + postgres + redis）
│   └── Makefile                            #   构建/运行/测试/迁移/nginx重载命令入口
│
├── scripts/                                # 开发工具脚本（Dev Scripts）
│   ├── seed_db.py                          #   数据库种子数据初始化
│   ├── dev_setup.sh                        #   开发环境一键初始化
│   └── migrate_data.py                     #   一次性数据迁移工具
│
├── .env                                    # 环境变量（不提交Git，含LLM_API_KEY等敏感信息）
├── .gitignore                              # Git忽略规则
└── README.md                               # 项目说明
```

## 父目录基本功速查

| 父目录 | 基本功 | 不做什么 |
|--------|--------|---------|
| `.ga/` | 项目治理——设计决策、问题跟踪、目录说明 | 不含代码 |
| `services/` | 所有可运行服务——api+web+yjs | 不存文档、不存测试 |
| `contracts/` | 跨服务共享数据契约——唯一真相源 | 不依赖任何框架 |
| `designs/` | 所有设计文档——PRD+设计报告+UI+测试设计 | 不含可执行代码 |
| `tests/` | 统一测试代码——api+web+integration | 不存业务代码 |
| `deploy/` | 部署与基础设施——Docker+Compose+Makefile | 不存源码 |

## 路径迁移对照（旧 → 新）

| 旧路径 | 新路径 |
|--------|--------|
| `backend/` | `services/api/` |
| `frontend/` | `services/web/` |
| `yjs-server/` | `services/yjs/` |
| `backend/tests/` | `tests/api/` |
| `docs/` | `designs/` |
| `docs/designs/` | `designs/`（合并） |
| `docs/test/` | `designs/test/` |
| `docker/` | `deploy/docker/` |
| `docker-compose.yml` | `deploy/docker-compose.yml` |
| `Makefile` | `deploy/Makefile` |
| `tools/gen_ts_types.py` | `contracts/gen_ts_types.py` |
