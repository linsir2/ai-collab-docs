# 测试用例 (Test Cases)

> 项目: AI文档锻造平台 (ai-collab-docs) | 版本: V1.0
> 依据: [testing_sop.md] §四 — 用例设计五铁律 + 标准字段模板

**当前状态**：项目处于设计阶段，代码未就绪。以下为按 SOP 标准格式编写的**样例用例**，覆盖所有测试类型，作为开发阶段编写完整用例集的模板和标准。

---

## 用例字段模板

| 字段 | 必填 | 说明 | 示例 |
|------|------|------|------|
| 用例ID | ✅ | TC-{模块}-{序号} | TC-INV-001 |
| 版本号 | ✅ | 用例版本，变更递增 | V1.0 |
| 所属模块 | ✅ | 被测功能模块 | 不可变底线 |
| 测试阶段 | ✅ | 单元/集成/系统/验收 | 系统测试 |
| 优先级 | ✅ | P0(阻塞)/P1(重要)/P2(一般)/P3(边缘) | P0 |
| 前置条件 | ✅ | 执行前系统必须满足的状态 | 写到"换一个人执行也不需要额外查资料"的程度 |
| 测试数据 | 推荐 | 具体的输入值 | 用户名: owner@x.com / 文档ID: doc-001 |
| 执行步骤 | ✅ | 序号+动作+输入 | 1. 打开文档 2. 以AI身份调用Block.write 3. 检查返回值 |
| 预期结果 | ✅ | 每步对应的确定性输出 | HTTP 200, response.body.type = "Proposal" |
| 关联需求 | 推荐 | 需求文档追溯 | REQ-INV-01 |

---

## A. 不可变底线 — Happy Path + Boundary + Error

### TC-INV-001: AI零直改 — Happy Path（AI正常提案）

| 字段 | 值 |
|------|-----|
| **用例ID** | TC-INV-001 |
| **版本号** | V1.0 |
| **所属模块** | 不可变底线 (Invariants) |
| **测试阶段** | 系统测试 |
| **优先级** | P0 |
| **前置条件** | 1. 文档 doc-001 已创建，Owner = owner@x.com  <br>2. 文档状态 = 草稿态  <br>3. Block blk-001 内容 = "本季度营收增长15%，主要驱动因素为..."  <br>4. 已以 docAI 身份登录（角色=AI，无人类权限） |
| **测试数据** | Block ID: blk-001 / 润色指令: "优化表达，使更正式" |
| **执行步骤** | 1. 以 docAI 身份调用润色API: `POST /api/forge/refine {block_id: "blk-001", instruction: "优化表达，使更正式"}`  <br>2. 检查响应体类型字段  <br>3. 检查 Block blk-001 的 content 是否被直接修改 |
| **预期结果** | 1. HTTP 200  <br>2. response.body.type = "Proposal"（非直接修改） <br>3. response.body.proposal.patch_content = Diff格式的新旧对比  <br>4. response.body.proposal.status = "pending"  <br>5. Block blk-001.content 保持不变（等待人类审批） |
| **关联需求** | REQ-INV-01 (PRD 二: AI零直改) |

### TC-INV-002: AI零直改 — Boundary（AI试图调用Block.write）

| 字段 | 值 |
|------|-----|
| **用例ID** | TC-INV-002 |
| **版本号** | V1.0 |
| **所属模块** | 不可变底线 (Invariants) |
| **测试阶段** | 系统测试 |
| **优先级** | P0 |
| **前置条件** | 同 TC-INV-001 |
| **测试数据** | Block ID: blk-001 / 新内容: "修改后的内容" |
| **执行步骤** | 1. 以 docAI 身份直接调用 `POST /api/document/blocks/blk-001/update {content: "修改后的内容"}`  <br>2. 检查HTTP状态码  <br>3. 检查响应体 |
| **预期结果** | 1. HTTP 403 Forbidden  <br>2. response.body.error.code = "AI_DIRECT_EDIT_DENIED"  <br>3. response.body.error.message = 人类可读的拒绝原因  <br>4. Block blk-001.content 未变 |
| **关联需求** | REQ-INV-01 (PRD 二: AI零直改) |

### TC-INV-003: AI零直改 — Error（AI以人类身份伪造调用）

| 字段 | 值 |
|------|-----|
| **用例ID** | TC-INV-003 |
| **版本号** | V1.0 |
| **所属模块** | 不可变底线 (Invariants) |
| **测试阶段** | 系统测试 |
| **优先级** | P0 |
| **前置条件** | 同 TC-INV-001 |
| **测试数据** | 请求头 X-Role 伪造为 "Owner" |
| **执行步骤** | 1. 以 docAI 身份调用 Block.write，请求头添加 X-Role: Owner  <br>2. 检查HTTP状态码 |
| **预期结果** | 1. HTTP 403  <br>2. Auth BC 的身份校验不可绕过——即使请求头伪造，JWT/Token中实际角色为AI  <br>3. 审计日志记录此次未授权访问尝试 |
| **关联需求** | REQ-INV-01 + REQ-AUTH-01 |

---

## B. 状态机 — Transition 权限矩阵

### TC-SM-001: 审查→定稿 — Happy Path（仅 Owner）

| 字段 | 值 |
|------|-----|
| **用例ID** | TC-SM-001 |
| **版本号** | V1.0 |
| **所属模块** | 状态机 (State Machine) |
| **测试阶段** | 系统测试 |
| **优先级** | P0 |
| **前置条件** | 1. 文档 doc-001 状态 = 审查态  <br>2. 所有审查者已批准（审查完成）  <br>3. 登录用户 = Owner (owner@x.com) |
| **测试数据** | transition: 审查→定稿 |
| **执行步骤** | 1. 以 Owner 身份调用 `POST /api/document/doc-001/transition {to: "定稿态"}`  <br>2. 检查HTTP状态码  <br>3. 检查文档状态 |
| **预期结果** | 1. HTTP 200  <br>2. 文档状态 = 定稿态  <br>3. Snapshot自动创建（关联审查快照）  <br>4. 审计日志记录: 角色=Owner, 操作=审查→定稿 |
| **关联需求** | REQ-SM-01 (PRD 六: 状态锁止) |

### TC-SM-002: 审查→定稿 — Boundary（LeadEdit 被拒）

| 字段 | 值 |
|------|-----|
| **用例ID** | TC-SM-002 |
| **版本号** | V1.0 |
| **所属模块** | 状态机 (State Machine) |
| **测试阶段** | 系统测试 |
| **优先级** | P0 |
| **前置条件** | 1. 文档 doc-001 状态 = 审查态  <br>2. 所有审查者已批准  <br>3. 登录用户 = LeadEdit (editor@x.com) |
| **测试数据** | transition: 审查→定稿 |
| **执行步骤** | 1. 以 LeadEdit 身份调用 transition  <br>2. 检查HTTP状态码  <br>3. 检查文档状态 |
| **预期结果** | 1. HTTP 403 Forbidden  <br>2. response.body.error = "TRANSITION_DENIED: 审查→定稿 需 Owner 权限"  <br>3. 文档状态保持 = 审查态 |
| **关联需求** | REQ-SM-01 (PRD 六: 审查→定稿仅Owner可执行) |

### TC-SM-003: 草稿→定稿 — Error（跳级）

| 字段 | 值 |
|------|-----|
| **用例ID** | TC-SM-003 |
| **版本号** | V1.0 |
| **所属模块** | 状态机 (State Machine) |
| **测试阶段** | 系统测试 |
| **优先级** | P0 |
| **前置条件** | 1. 文档 doc-001 状态 = 草稿态  <br>2. 登录用户 = Owner |
| **测试数据** | transition: 草稿→定稿（跳级尝试） |
| **执行步骤** | 1. 以 Owner 身份调用 `POST /api/document/doc-001/transition {to: "定稿态"}`  <br>2. 检查HTTP状态码 |
| **预期结果** | 1. HTTP 400 Bad Request  <br>2. response.body.error = "TRANSITION_NOT_ALLOWED: 草稿→定稿 不存在，必须经过 草稿→讨论→审查→定稿"  <br>3. 文档状态保持 = 草稿态 |
| **关联需求** | REQ-INV-04 (PRD 二: 状态不可跳级) |

---

## C. 模块解耦 — AST静态扫描

### TC-DEC-001: 跨BC导入隔离 — Happy Path（合规BC）

| 字段 | 值 |
|------|-----|
| **用例ID** | TC-DEC-001 |
| **版本号** | V1.0 |
| **所属模块** | 模块解耦 (Decoupling) |
| **测试阶段** | 单元测试 |
| **优先级** | P1 |
| **前置条件** | 1. services/api/src/ 下6个BC目录已创建  <br>2. 每个BC有 models.py |
| **测试数据** | 扫描目标: services/api/src/ai_forge/models.py |
| **执行步骤** | 1. 用AST解析 ai_forge/models.py 的所有 import 语句  <br>2. 过滤出 `from services.api.src.xxx.models import` 语句  <br>3. 检查过滤结果 |
| **预期结果** | 过滤结果为空列表 — ai_forge/models.py 不导入任何其他 BC 的 models |
| **关联需求** | REQ-DEC-01 (ga.md: BC物理隔离) |

### TC-DEC-002: contracts.py纯净性 — Happy Path

| 字段 | 值 |
|------|-----|
| **用例ID** | TC-DEC-002 |
| **版本号** | V1.0 |
| **所属模块** | 模块解耦 (Decoupling) |
| **测试阶段** | 单元测试 |
| **优先级** | P1 |
| **前置条件** | contracts/contracts.py 已存在 |
| **测试数据** | 扫描目标: contracts/contracts.py |
| **执行步骤** | 1. 用AST解析 contracts.py 的所有 import  <br>2. 检查是否包含 fastapi / sqlalchemy / pydantic / starlette / aiohttp  <br>3. 检查结果 |
| **预期结果** | 检查结果为空 — contracts.py 仅含 Python stdlib + typing |
| **关联需求** | REQ-DEC-03 (ga.md ADR-008: contracts.py框架无关) |

---

## D. 数字阈值 — 信任分边界值

### TC-THR-001: 信任分 ≥ 82 — Happy Path（触发自动采纳，仅v1）

> ⚠️ MVP阶段信任分固定50，不启用自动采纳。此用例仅在v1激活信任分系统后执行。

| 字段 | 值 |
|------|-----|
| **用例ID** | TC-THR-001 |
| **版本号** | V1.0 |
| **所属模块** | 数字阈值 (Thresholds) |
| **测试阶段** | 系统测试 |
| **优先级** | P1(v1) — MVP阶段信任分固定50，不启用自动采纳 |
| **前置条件** | 1. 文档 doc-001 状态 = 草稿态  <br>2. 个人AI trust_score = 82  <br>3. 个人AI proposal#42 提交后超过自动采纳等待期 |
| **测试数据** | AI trust_score = 82 |
| **执行步骤** | 1. 个人AI 提交润色 proposal#42  <br>2. 等待自动采纳等待期结束  <br>3. 检查 proposal#42 状态  <br>4. 检查 Block 内容 |
| **预期结果** | 1. proposal#42.status = "accepted"  <br>2. Block 内容已更新为提案内容  <br>3. proposal#42.accepted_by = "system(trust_score)"  <br>4. proposal#42.undo_available = true |
| **关联需求** | REQ-TRUST-01 (PRD 模块三: 渐进信任，v1启用) |

### TC-THR-002: 信任分 79 — Boundary（不触发，仅v1）

> ⚠️ MVP阶段信任分固定50，不启用自动采纳。此用例仅在v1激活信任分系统后执行。

| 字段 | 值 |
|------|-----|
| **用例ID** | TC-THR-002 |
| **版本号** | V1.0 |
| **所属模块** | 数字阈值 (Thresholds) |
| **测试阶段** | 系统测试 |
| **优先级** | P1(v1) — MVP阶段信任分固定50，不启用自动采纳 |
| **前置条件** | 同 TC-THR-001，但 trust_score = 79 |
| **测试数据** | AI trust_score = 79 |
| **执行步骤** | 同 TC-THR-001 |
| **预期结果** | 1. proposal#42.status = "pending"（未被自动采纳） <br>2. Block 内容保持不变  <br>3. 人类可手动审批 |
| **关联需求** | REQ-TRUST-01 (v1启用) |

---

## E. 新增阈值用例（solution.md 决议后补充）

### TC-DRF-001: 漂移速率检测 — Boundary（连续3次<0.85触发预警）

| 字段 | 值 |
|------|-----|
| **用例ID** | TC-DRF-001 |
| **版本号** | V1.0 |
| **所属模块** | 数字阈值 — 漂移检测 (Drift) |
| **测试阶段** | 系统测试 |
| **优先级** | P1 |
| **前置条件** | 1. 文档 doc-001 处于审查态 <br>2. Block blk-001 已与立意锚建立基线余弦相似度=0.92 <br>3. 已有连续2次修改后的余弦相似度为 0.83、0.82 |
| **测试数据** | 第3次修改后余弦相似度 = 0.81 |
| **执行步骤** | 1. 编辑 Block blk-001 内容（触发第3次漂移检测） <br>2. 检查漂移检测结果 <br>3. 检查UI反馈 |
| **预期结果** | 1. 漂移速率预警触发（连续3次 < 0.85） <br>2. Block 标签 Drift-Warning 置为 true <br>3. 前端显示黄色预警提示，附带当前相似度/历史基准/漂移速率 <br>4. 不触发拦截（仅预警，单次<0.8才拦截） |
| **关联需求** | REQ-DRIFT-01 (PRD 模块二: 漂移速率预警) |

### TC-DRF-002: 漂移检测单次拦截 — Boundary（单次<0.8）

| 字段 | 值 |
|------|-----|
| **用例ID** | TC-DRF-002 |
| **版本号** | V1.0 |
| **所属模块** | 数字阈值 — 漂移检测 (Drift) |
| **测试阶段** | 系统测试 |
| **优先级** | P0 |
| **前置条件** | 1. 文档 doc-001 处于审查态 <br>2. Block blk-001 已与立意锚建立基线余弦相似度=0.92 |
| **测试数据** | 修改后余弦相似度 = 0.78 |
| **执行步骤** | 1. 编辑 Block blk-001 内容使其严重偏离立意锚 <br>2. 检查漂移检测结果 <br>3. 检查 Block 编辑是否提交成功 |
| **预期结果** | 1. 漂移拦截触发（单次 < 0.8） <br>2. Block 编辑被硬拦截，不进入 Yjs 文档 <br>3. 前端显示红色拦截提示 + 「内容修正/立意迭代/忽略本次」三路径 <br>4. 忽略后记录到项目记忆 |
| **关联需求** | REQ-DRIFT-01 (PRD 模块二: 余弦阈值0.8) |

### TC-PROP-001: AI提案数80%溢出 — Boundary（橙色预警）

| 字段 | 值 |
|------|-----|
| **用例ID** | TC-PROP-001 |
| **版本号** | V1.0 |
| **所属模块** | 数字阈值 — 提案上限 (Proposal) |
| **测试阶段** | 系统测试 |
| **优先级** | P1 |
| **前置条件** | 1. 文档 doc-001 公共池提案上限=800 <br>2. 当前公共池提案数=640（80%阈值） |
| **测试数据** | 新提交提案 → 公共池计数=641 |
| **执行步骤** | 1. 以 docAI 身份提交润色提案 <br>2. 检查提案提交是否成功 <br>3. 检查前端UI指示器 |
| **预期结果** | 1. 提案提交成功（80%仅预警不阻断） <br>2. 前端计数条变橙色，显示"公共提案池已用80%（640/800）" <br>3. 不弹窗 |
| **关联需求** | REQ-PROP-01 (PRD 模块四.5: 提案上限800/400/1200) |

### TC-PROP-002: AI提案数100%溢出 — Error（阻断新增）

| 字段 | 值 |
|------|-----|
| **用例ID** | TC-PROP-002 |
| **版本号** | V1.0 |
| **所属模块** | 数字阈值 — 提案上限 (Proposal) |
| **测试阶段** | 系统测试 |
| **优先级** | P0 |
| **前置条件** | 1. 文档 doc-001 公共池提案上限=800 <br>2. 当前公共池提案数=800（100%阈值） |
| **测试数据** | 新提交提案 → 预期计数=801 |
| **执行步骤** | 1. 以 docAI 身份提交润色提案 <br>2. 检查HTTP状态码 <br>3. 检查前端弹窗 <br>4. 检查私有池是否仍可提交 |
| **预期结果** | 1. HTTP 429 Too Many Requests <br>2. 前端弹窗"提案池已满（800/800），请批量归档或清理旧提案后重试" <br>3. 弹窗提供"一键批量合并/归档"快捷入口 <br>4. 私有池不受影响（公私独立计数） |
| **关联需求** | REQ-PROP-02 (PRD 模块四.5: 100%阻断) |

### TC-MEM-001: 记忆固化 ≥3次 — Boundary（触发长期记忆写入）

| 字段 | 值 |
|------|-----|
| **用例ID** | TC-MEM-001 |
| **版本号** | V1.0 |
| **所属模块** | 数字阈值 — 记忆固化 (Memory) |
| **测试阶段** | 系统测试 |
| **优先级** | P1 |
| **前置条件** | 1. 用户对 personalAI 已给出2次相同反馈"不要使用感叹号结尾" <br>2. 当前为第3次相同反馈前的 session <br>3. personalAI private_memory 中暂无此条长期记忆 |
| **测试数据** | 第3次相同反馈: "不要在结尾使用感叹号，保持陈述语气" |
| **执行步骤** | 1. 用户在第3次 session 中给出相同反馈 <br>2. 检查 personalAI private_memory 表 <br>3. 模拟第4次 session 验证记忆持久化 |
| **预期结果** | 1. 第3次反馈后，private_memory 中新增记录: rule="avoid_exclamation_mark" + solidified=true <br>2. 第4次 session AI 自动避免感叹号结尾 <br>3. 前2次反馈未写入长期记忆（仅在 session 缓存中） |
| **关联需求** | REQ-MEM-01 (PRD 模块四.2: ≥3次固化) |

---

## 用例设计说明

### 遵循 SOP 五铁律

1. **预期结果可客观判定**：所有预期写具体状态码/字段值/状态名，不写"系统正常处理"
2. **每个功能点 ≥3条用例**：Happy + Boundary + Error 全覆盖
3. **前置条件到"傻瓜可执行"**：含角色、文档ID、状态、具体数值
4. **基于规范文档**：关联需求ID可追溯至 PRD/ga.md/design_report
5. **版本管理**：初始 V1.0，变更时递增

### 追溯链示例

```
REQ-INV-01 (PRD 二: AI零直改)
  → FP-INV-01 (功能点: AI角色的写入路径返回Proposal)
    → TC-INV-001 (Happy: AI润色返回Proposal)
    → TC-INV-002 (Boundary: AI直接调用Block.write被拒)
    → TC-INV-003 (Error: AI伪造人类身份被Auth拦截)
```

### 后续扩充

开发阶段按 test-matrix.md 中所有测试点（T1~T6）逐条编写标准格式用例，预计总数约 80~100 条。
