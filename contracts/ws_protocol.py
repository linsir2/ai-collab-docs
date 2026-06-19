"""
WebSocket 自定义消息契约（外层JSON）
====================================
项目: ai-collab-docs | 用于: collab BC 的 WS 网关
注意: Yjs 二进制同步走通道A（Yjs Provider），不经过此 JSON 通道
"""
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class WSMessageType(StrEnum):
    """WebSocket自定义消息类型"""
    # Yjs官方二进制同步 — 不走此JSON通道，直接Yjs Provider处理
    # 以下为自定义业务消息

    # 状态事件
    STATE_CHANGE         = "state_change"         # 文档状态变更通知
    DRIFT_ALERT          = "drift_alert"          # 立意锚漂移预警
    CONFLICT_DETECTED    = "conflict_detected"    # 新冲突触发
    ARBITRATION_RESOLVED = "arbitration_resolved" # 冲突已裁决

    # 提案事件
    PROPOSAL_CREATED = "proposal_created"  # 新AI提案
    PROPOSAL_UPDATED = "proposal_updated"  # 提案状态变更

    # 审查事件
    REVIEW_STARTED   = "review_started"    # 进入审查态
    REVIEW_COMPLETED = "review_completed"  # 审查完成
    APPROVAL_CHANGED = "approval_changed"  # 审批状态变更

    # 分页/同步指令
    PAGINATION_SYNC = "pagination_sync"    # 分页同步（大文档）

    # 权限/角色变更（problem.md §三审查意见#7） — 实时协作场景
    ROLE_CHANGED     = "role_changed"       # 文档局部角色变更通知（面板显隐触发toast）
    PERMISSION_UPDATED = "permission_updated"  # 权限配置更新（如Owner调整协作者角色）

    # 运维认证（problem.md §三审查意见#5）
    REAUTH_REQUIRED  = "reauth_required"    # 运维视图要求二次密码校验
    REAUTH_GRANTED   = "reauth_granted"     # 二次校验通过
    REAUTH_EXPIRED   = "reauth_expired"     # 运维会话过期

    # 心跳
    PING = "ping"
    PONG = "pong"


@dataclass(frozen=True)
class WSMessage:
    """WebSocket自定义消息外层信封"""
    type: WSMessageType
    doc_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    sender_id: str = ""
    timestamp: str = ""

    # Yjs同步数据不经过此JSON通道。
    # Yjs Provider 通过独立的二进制通道同步 Y.Doc 的 update 消息。
    # 参见: y-protocols/sync 的 SyncStep1/SyncStep2/Update


"""
WS双通道架构说明:
┌─────────────────────────────────────────────┐
│              WebSocket 连接                   │
├─────────────────────────────────────────────┤
│  通道A: Yjs Sync Protocol (二进制)           │
│  - 由 y-websocket provider 处理             │
│  - 格式: Yjs官方 sync protocol messages     │
│  - 内容: Y.Doc 增量更新 (update),            │
│          awareness state, sync step          │
│  - 开发者不自定义此通道格式                   │
├─────────────────────────────────────────────┤
│  通道B: 自定义业务消息 (JSON)                 │
│  - WSMessage(type + docId + payload)         │
│  - 状态变更、漂移预警、冲突检测、提案通知等    │
│  - 不携带Yjs文档内容                         │
└─────────────────────────────────────────────┘

实现建议:
- 前端: y-websocket 库处理通道A;
        通道B在同一个WebSocket连接上通过自定义事件处理
- 服务端: python-yjs + y-py 处理通道A;
          JSON消息路由处理通道B
- 或者: 使用两个独立的WebSocket连接（简化通道隔离）
"""
