"""
Yjs 文档结构契约（内存映射，非持久化schema）
==========================================
项目: ai-collab-docs | 用于: collab BC 的 Yjs 集成

Yjs Y.Doc 顶层共享类型映射:

Y.Doc
├── Y.Map("meta")
│   ├── "docId":       string          — 文档唯一ID
│   ├── "anchor":      JSON string     — Anchor序列化（只读参考副本）
│   └── "state":       string          — DocumentState值
│
├── Y.Array("blocks")
│   └── Y.Map (per block)
│       ├── "blockId":     string      — Block唯一ID
│       ├── "content":     Y.Text      — 实际文档内容（CRDT同步主体）
│       └── "order":       number      — 排序权重（支持拖拽）
│
├── Y.Map("cursorPositions")
│   └── Y.Map(per user)
│       ├── "blockId":     string
│       ├── "offset":      number
│       └── "selection":   JSON string — {anchor, head}
│
└── Y.Map("awareness")
    └── Y.Map(per user)
        ├── "name":        string
        ├── "color":       string
        └── "onlineAt":    string      — ISO timestamp

注意:
- BlockMeta (tags/claimantId/driftScore) 存储在PostgreSQL，不在Yjs中
- Yjs中的 meta.anchor 是只读参考副本，权威源在PostgreSQL
- cursorPositions 和 awareness 也可通过 Yjs Awareness API 管理
"""
