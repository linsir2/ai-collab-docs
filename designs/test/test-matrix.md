# 详细测试矩阵

> 从 PRD / ga.md / design_report / model_repo.yaml / UI design 逐一提取可测试点
> 每个测试点标注：来源文档、测试断言、所需数据/条件、优先级

---

## T1. 不可变底线测试（5项）

> 来源: PRD 二 | 这些是代码级物理锁止，非"约定"

| ID | 测试项 | 来源 | 测试断言 | 怎么测 | 优先级 |
|----|--------|------|---------|--------|--------|
| T1.1 | AI零直改文档Block | PRD二 | AI角色调用的所有写入路径返回Proposal对象，不存在直接修改Block.content的API | 审计所有AI能力层函数返回值类型 | P0 |
| T1.2 | 任何时刻Owner可中断AI | PRD二 | AI长任务有abort入口，abort后状态正确回滚，不残留孤儿Proposal | 模拟AI润色中途Owner abort | P0 |
| T1.3 | 立意锚不可被AI修改 | PRD二 | Anchor.write() 权限仅限人类角色，AI调用返回PermissionDenied | ACL测试：以AI身份调用Anchor.write | P0 |
| T1.4 | 状态不可跳级 | PRD二 | 从草稿直接请求定稿被拒绝（必须经过讨论→审查） | Transition API输入不合法状态对 | P0 |
| T1.5 | 自动采纳可撤回 | PRD二 | 信任分触发的自动采纳有undo记录，撤回后恢复到采纳前状态 | 信任分≥80触发采纳→Owner撤回 | P1(v1) |

---

## T2. 状态机测试（5状态 × 8transition × 5角色）

> 来源: PRD六、design_report Round2 StateMachine

### T2.1 状态存在性

| ID | 测试项 | 预期 |
|----|--------|------|
| T2.1.1 | 5状态完整性 | 草稿态、讨论态、审查态、定稿态、归档态 全部在代码中可枚举 |
| T2.1.2 | 状态不可变 | 状态枚举不可运行时添加/删除 |

### T2.2 Transition权限矩阵

> 来源: design_report Round2。预期矩阵：

| Transition | Owner | LeadEdit | Editor | Reviewer | Reader |
|-----------|-------|----------|--------|----------|--------|
| 创建→草稿 | ✅ | ✅ | ✅ | ❌ | ❌ |
| 草稿→讨论 | ✅ | ✅ | ✅ | ❌ | ❌ |
| 讨论→审查 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 讨论→草稿 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 审查→定稿 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 审查→讨论 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 定稿→草稿(撤销定稿) | ✅ | ❌ | ❌ | ❌ | ❌ |
| 定稿→归档 | ✅ | ❌ | ❌ | ❌ | ❌ |

> 每个格子需要一项参数化测试

| ID | 测试项 | 预期 |
|----|--------|------|
| T2.2.1 | 8条transition × 5角色 = 40格权限测试 | 与上表完全一致 |
| T2.2.2 | 定稿态逆向操作仅Owner | 定稿→草稿、定稿→归档仅Owner可执行 |

### T2.3 轻量模式差异

| ID | 测试项 | 预期 |
|----|--------|------|
| T2.3.1 | 轻量模式无讨论态与审查态 | 草稿→定稿→归档，不经过讨论/审查 |
| T2.3.2 | 轻量/重型模式选择后不可切换 | 创建工作流锁定模式 |

---

## T3. 模块解耦测试（6 BC）

> 来源: ga.md 架构约定

### T3.1 BC目录结构

| ID | 测试项 | 源码位置预期 |
|----|--------|-------------|
| T3.1.1 | 6 BC有独立目录 | services/api/src/document, collab, ai_forge, approval, auth, audit |
| T3.1.2 | 每个BC有 public `__init__.py` 导出 Service 类 | `from services.api.src.document import DocumentService` |
| T3.1.3 | 每个BC有 `models.py` 定义本BC的数据模型 | `services/api/src/document/models.py` |

### T3.2 跨BC导入隔离

> 核心规则: BC-A/models.py 不可 import BC-B/models.py

| ID | 测试项 | 预期 |
|----|--------|------|
| T3.2.1 | Document/models.py 不 import AI/models.py | AST静态分析通过 |
| T3.2.2 | AI/models.py 不 import Approval/models.py | AST静态分析通过 |
| T3.2.3 | Approval/models.py 不 import Document/models.py | AST静态分析通过 |
| T3.2.4 | 所有BC models.py 不直接import其他BC models | 全量扫描6×5=30对关系 |

### T3.3 依赖方向

> L4前端 → L3AI能力 → L2业务规则 → L1协同数据。反向依赖被CI拒绝。

| ID | 测试项 | 预期 |
|----|--------|------|
| T3.3.1 | L1 shared 不依赖 L2 domain | shared/ 目录下无 `from services.api.src.{document,collab,ai_forge,approval,auth,audit}` |
| T3.3.2 | L2 domain services 不 import FastAPI/数据库IO | 仅依赖 contracts 和 L1 shared |
| T3.3.3 | contracts.py 无框架import | 无 `fastapi`, `sqlalchemy`, `pydantic` 等 |

### T3.4 基础设施隔离

| ID | 测试项 | 预期 |
|----|--------|------|
| T3.4.1 | BC间通信走Redis事件总线 | 无DB直连查其他BC的表 |
| T3.4.2 | AuditService是所有L2的依赖 | 所有L2 service的构造函数接受AuditService |
| T3.4.3 | Yjs独立进程 | Yjs进程可独立启动/停止，不依赖Python进程 |

### T3.5 数据所有权

| ID | 测试项 | 预期 |
|----|--------|------|
| T3.5.1 | Document内容单一写入者：Yjs doc | 桌面端不通过REST直接写Block内容 |
| T3.5.2 | 权限标签单一写入者：Auth BC | 前端不包含 `setPermissionTag`、`writePermission` |
| T3.5.3 | Anchor单一写入者：Document BC anchor模块 | AI BC不直接写Anchor |
| T3.5.4 | TypeScript类型由contracts.py生成 | `services/web/src/shared/types/contracts.ts` 存在且与 `contracts/contracts.py` 同步 |

---

## T4. 数字阈值测试（17项）

> 来源: PRD + design_report + UI design

### T4.1 已量化的阈值（可做边界值测试）

| ID | 阈值 | 数值 | 来源 | 边界测试点 |
|----|------|------|------|-----------|
| T4.1.1 | 信任分自动采纳 | ≥ 80 | PRD 模块三 | 79→否, 80→是, 81→是 |
| T4.1.2 | 申诉论据质量硬关闭 | < 7 | UI design | 6→关闭, 7→不关闭 |
| T4.1.3 | Token饱和度警示 | ≥ 80% | UI design | 79%→不警示, 80%→警示, 81%→警示 |
| T4.1.4 | 非焦点区域淡化 | 20% opacity | UI design | 焦点100%, 非焦点20%, 非焦点不大于焦点 |
| T4.1.5 | MVP团队规模 | 3-5人 | ga.md | 0→否, 2→否, 3→是, 5→是, 6→否 |
| T4.1.6 | 审查维度(MVP) | 2维 | ga.md | 表述精准+立场一致，不超过5维全量 |
| T4.1.7 | 审查维度(全量) | 5维 | PRD | 逻辑结构+读者适配+领域合规+表述精准+立场一致 |
| T4.1.8 | 漂移检测召回率 | ≥ 80% | ga.md MVP标准 | 10测试用例中≥8检出 |
| T4.1.9 | MVP审批选项 | 3项 | ga.md | 接受/拒绝/手动编辑，不超过完整4项 |
| T4.1.10 | 冲突仲裁触发 | ≥ 2 AI角色 | PRD 模块四 | 1个→不触发, 2个→触发 |
| T4.1.11 | 角色层级数 | 5 | PRD 模块六 | Owner > LeadEditor > Editor > Reviewer > Reader |
| T4.1.12 | 文档状态数 | 5 | PRD 六 | 草稿/讨论/审查/定稿/归档 |
| T4.1.13 | 限界上下文数 | 6 | design_report | Document/Collaboration/AI/Approval/Auth/Audit |
| T4.1.14 | 设计轮次收敛 | R6=0 | design_report | 16→9→14→5→4→0 |

### T4.2 已解决 / 已有初值 / 延后的阈值（对应 solution.md）

> 圆桌讨论后，9个阈值已有明确决议。以下按决议状态分类（R=Resolved / I=InitialValue / D=Deferred / C=Complete）。

#### T4.2-R 已解决（有精确数值）

| ID | 对应问题 | 决议 | 数值 |
|----|---------|------|------|
| T4.2.1R | P-001 余弦相似度 | 固定阈值 0.8，模型 `dashscope/text-embedding-v3`，仅审查态触发；监控漂移速率——连续3次<0.85预警/单次<0.8拦截。后续用4领域×4梯度16对样例集校准 | **0.8** |
| T4.2.4R | P-004 Block上限 | 1000 Block/20万字硬上限；>100 Block触发 SubDoc 分片（Root存元数据+章节独立SubDoc按需加载）；前端虚拟滚动仅渲染20-30 Block | **1000** |
| T4.2.5R | P-005 AI提案上限 | 公共池800/私有池400/全局1200；80%橙色/95%弹窗/100%阻断；私有提案移出Yjs存PostgreSQL；公共提案仍走Yjs | **800/400/1200** |

#### T4.2-I 有初始值（后续实测校准）

| ID | 对应问题 | 决议 | 初始值 |
|----|---------|------|--------|
| T4.2.3I | P-003 P99延迟 | Yjs同步<500ms / REST<300ms / AI<8s / 切换<200ms。MVP上线后用Locust压测（含Yjs WS协议），按实测P99的1.2x~1.5x校准 | **500ms/300ms/8s/200ms** |
| T4.2.2I | P-002 信任分公式 | MVP=50（冷启动，不启用自动采纳）。v1公式: [0,100]，采纳+3/拒绝-2/仲裁成功+10/仲裁失败-15，衰减0.95/月，反刷分（连续采纳加权递减）。跨BC：AI_Forge订阅Approval Redis事件 | **MVP=50** |

#### T4.2-D 延后至 v1

| ID | 对应问题 | 决议 |
|----|---------|------|
| T4.2.6D | P-006 仲裁超时 | deferred to v1（对齐ga.md"决策上浮链→v1"）。MVP由段落Owner手动裁决+仲裁台筛选标签（可解决/待解决） |
| T4.2.7D | P-007 申诉评分 | MVP仅二元判断（合理/不合理），基于向量相似度+结构化完整性。v1三维量化：论据相关性/数据支撑度/逻辑一致性各1~10→总分<21硬关闭 |

#### T4.2-C 已完成

| ID | 对应问题 | 决议 |
|----|---------|------|
| T4.2.9C | P-009 公私记忆 | 六层隔离: 存储(PostgreSQL+Yjs)/访问(API网关)/写入规则(私域/公共/双路)/可见性切换(模式/状态)/生命周期/固化(≥3次)。MySQL→PostgreSQL统一 |
| T4.2.8C | P-008 model_repo | 批准补全。从design_report.md R2~R6提取回填 |

| ID | 对应问题 | 来源原文 | 当前状态 | 试探样例（怎么做） | 期望产出 |
|----|---------|---------|---------|------------------|---------|
---


## T5. 设计内一致性测试

> 这些测试不依赖代码，在设计阶段即可执行——检查设计文档间的交叉引用是否一致

| ID | 测试项 | 校验内容 | 来源对 |
|----|--------|---------|--------|
| T5.1 | model_repo 结构校验 | concepts/flow/constraints 字段完整，id无重复 | model_repo.yaml |
| T5.2 | model_repo 所有实体有verification标记 | `verified: true` 覆盖率 100% | model_repo.yaml |
| T5.3 | BC名称一致 | design_report BC 列表 vs ga.md 架构约定 | design_report ↔ ga.md |
| T5.4 | ADR数量一致 | ga.md ADR-001~008 vs design_report ADR节 | ga.md ↔ design_report |
| T5.5 | 外部系统映射 | model_repo c5(DashScope) c6(Yjs) c7(PostgreSQL) c8(前端) | model_repo ↔ ga.md |
| T5.6 | 5状态名称一致 | PRD六 vs design_report StateMachine | PRD ↔ design_report |
| T5.7 | Transition矩阵覆盖 | design_report 8条transition vs StateMachine图 | design_report 内部 |
| T5.8 | 发现率收敛 | 6轮发现率 16→9→14→5→4→0 | design_report |
| T5.9 | 核心约束存在 | AI零直改(NEVER) + 人类主权(ALWAYS) 在 model_repo 有约束记录 | PRD ↔ model_repo |
| T5.10 | UI阈值得有后端支撑 | Token饱和度警戒、申诉分硬关闭、淡化20% 在PRD/ga.md有对应机制 | UI design ↔ PRD/ga.md |

---

## T6. 对抗性测试场景

> 不测happy path——测边界、竞态、降级、恶意输入

| ID | 场景 | 测试方法 | 优先级 |
|----|------|---------|--------|
| T6.1 | 双人同时触发状态切换 | Yjs并发→冲突解决，最终状态一致 | P1 |
| T6.2 | AI润色中途网络断开 | 超时恢复→不丢提案、不残留锁 | P1 |
| T6.3 | 审查态进行中文档被编辑 | Snapshot不变，编辑在漂移检测中标记 | P1 |
| T6.4 | Owner归档后有人试图编辑 | 归档态全量封存→所有写操作拒绝 | P0 |
| T6.5 | AI以人类身份调用API | Auth BC的5级角色校验不可绕过 | P0 |
| T6.6 | Redis事件总线断开 | BC间通信降级→本地缓存→重连恢复 | P2 |
| T6.7 | 大规模文档(>1000 Block) | Yjs同步性能、UI渲染不卡顿 | P2 |
| T6.8 | 空文档/纯空Block | 边界输入不崩溃 | P1 |
| T6.9 | Unicode/emoji/RTL文字 | 全字符集支持 | P2 |
| T6.10 | 立意锚被篡改后漂移检测 | 修改Anchor→漂移检测应触发（假阳性测试） | P1 |

---

## T7. 三轴权限模型测试（problem.md → ADR-021/022）

> 验证两域权限拆分 + 视图隔离 + 面板显隐 + 实时角色变更通知

| ID | 场景 | 测试方法 | 优先级 |
|----|------|---------|--------|
| T7.1 | 全局普通用户登录 → 视图切换器 | 「团队管理」选项disabled+tooltip说明权限边界 | P0 |
| T7.2 | 普通用户创建文档 → 顶部标签 | 显示「全局身份：个人普通用户 \| 当前文档身份：文档所有者」 | P0 |
| T7.3 | 普通用户强制路由 `/team-view` | HTTP 403 + 前端自动跳转创作视图 | P0 |
| T7.4 | 团队管理员打开他人文档（审查者角色）→ 归档操作 | 归档/记忆重置按钮隐藏（非置灰） | P0 |
| T7.5 | 团队管理员打开他人文档 → 顶部标签 | 「全局身份：团队管理员 \| 当前文档身份：文档审查者」 | P1 |
| T7.6 | 只读用户打开文档 → AI锻造面板 | 锻造/提案/状态流转面板全部隐藏 | P0 |
| T7.7 | 审查者打开文档 → 段落分配面板 | 段落批量分配/文档归档面板隐藏，审查/审批/仲裁保留 | P1 |
| T7.8 | Owner在线调整协作者角色 → 被调整者收到通知 | WS ROLE_CHANGED → toast「您的角色已变更为XX」 | P1 |
| T7.9 | 角色变更后面板显隐 | 面板200ms淡出动画，非突然消失 | P2 |
| T7.10 | 运维账号二次密码校验 | 正确密码→运维视图解锁；错误→拒绝；30min无操作→自动锁定 | P1 |
| T7.11 | 运维账号在运维视图 → 协作者presence | 运维显示「只读」状态，不参与编辑事件广播 | P2 |
| T7.12 | 团队管理员查看消耗团队预算的文档 → 预算熔断 | 管理员可对团队预算文档执行预算熔断（不动文档内容/角色） | P1 |
| T7.13 | 创作视图信任分展示 | 仅文字标签「谨慎审批/适度信任/高度信任」，无0-100数字 | P1 |
| T7.14 | hover信任分标签 → 追溯原因 | 提示「信任等级下降：近期2次提案被驳回」等具体原因 | P2 |

---

## 实施优先级建议

| 阶段 | 包含测试 | 触发条件 |
|------|---------|---------|
| **阶段0（现在）** | T5.1-T5.10 设计一致性 | 有设计文档即可 |
| **阶段1（MVP骨架）** | T1.1-T1.4, T2全部, T3全部 | 后端核心模块代码就绪 |
| **阶段2（MVP完成）** | T4已量化阈值, T6.1-T6.6 | MVP全链路走通 |
| **阶段3（v1发布）** | T1.5, T4未量化阈值, T6.7-T6.10 | 全部功能就绪 |
