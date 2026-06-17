# 数据契约层 (Contracts)

> 跨服务共享数据契约——全平台唯一真相源。框架无关，纯 Python frozen dataclass。
> 项目: AI文档锻造平台 (ai-collab-docs)

---

## 职责

`contracts/contracts.py` 是前后端共享的"通信协议"定义。所有 BC（Bounded Context）之间的消息格式、API 请求/响应结构、枚举值，**必须先在此定义**，再在各自的 `models.py` 中实现。

## 使用规则

### 1. 新增合约
```python
# contracts/contracts.py
from dataclasses import dataclass
from enum import Enum

class BlockTag(str, Enum):
    LOCKED_BY_HUMAN = "Locked-by-Human"
    DUAL_TRACK = "[双轨对标]"
    CLAIMED = "Claimed-by-XXX"
    DRIFT_WARNING = "Drift-Warning"

@dataclass(frozen=True)
class Proposal:
    id: str
    block_id: str
    ai_role: str
    content_before: str
    content_after: str
    status: str  # pending | accepted | rejected
```

### 2. 同步 TypeScript 类型
```bash
cd /home/linsir365/projects/ai-collab-docs
make types  # 执行 contracts/gen_ts_types.py → services/web/src/shared/types/contracts.ts
```

**铁律**: 合约变更后必须先跑 `make types`，否则前端类型不一致。

### 3. 合约 vs 模型
| 层 | 位置 | 作用 | 依赖 |
|----|------|------|------|
| contracts | `contracts/contracts.py` | 框架无关纯数据契约 (frozen dataclass) | 无 |
| models | `services/api/src/{bc}/models.py` | SQLAlchemy ORM + Pydantic schema | contracts 类型引用 |

同一实体在两层中各司其职，不冲突。

### 4. 禁止事项
- ❌ BC 之间互相 import models
- ❌ 在 contracts 中引入 SQLAlchemy / Pydantic / FastAPI 依赖
- ❌ 裸 dict 传参——必须使用 typed dataclass
- ❌ 跳过 contracts 直接在 models 中定义跨 BC 共享的结构
