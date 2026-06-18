import { useState, type FC, type FormEvent } from 'react'

interface DiscussionMessage {
  id: number
  sender_name: string
  sender_role: string
  is_ai: boolean
  content: string
  timestamp: string
  ai_warning?: string
}

interface DiscussionZoneProps {
  messages?: DiscussionMessage[]
  onSendMessage: (content: string) => void
  onSummarize: () => void
}

const MOCK_MESSAGES: DiscussionMessage[] = [
  {
    id: 1,
    sender_name: '张工',
    sender_role: 'TechLead',
    is_ai: false,
    content: '@TechReviewer 请审查一下这个微服务拆分方案的可行性和潜在风险。',
    timestamp: '10:30:15',
  },
  {
    id: 2,
    sender_name: 'TechReviewer',
    sender_role: 'AI',
    is_ai: true,
    content: '已审查微服务拆分方案。主要关注点：\n1. 服务边界划分合理，但数据库拆分策略需要更详细的迁移计划\n2. 建议增加熔断和降级机制\n3. 服务间通信延迟需要压测验证',
    timestamp: '10:30:28',
    ai_warning: 'TechReviewer 本话题已发言 1/3 次',
  },
  {
    id: 3,
    sender_name: '李法务',
    sender_role: 'Legal',
    is_ai: false,
    content: '@LegalAgent 请确认微服务拆分是否涉及数据跨境传输，需要评估 GDPR 合规风险。',
    timestamp: '10:31:02',
  },
  {
    id: 4,
    sender_name: 'LegalAgent',
    sender_role: 'AI',
    is_ai: true,
    content: '已识别以下合规风险：\n1. 如拆分的微服务部署在不同区域的节点上，可能触发数据跨境传输条款\n2. 建议所有数据处理节点限制在 EU 境内\n3. 需要更新数据处理协议(DPA)',
    timestamp: '10:31:18',
  },
  {
    id: 5,
    sender_name: 'TechReviewer',
    sender_role: 'AI',
    is_ai: true,
    content: '补充建议：使用 API Gateway 统一入口可以有效控制数据流向，配合地理路由策略确保数据不出境。推荐 Kong 或 APISIX。',
    timestamp: '10:31:45',
    ai_warning: '⚠ LegalAgent 本话题已发言 2/3 次',
  },
]

function getInitials(name: string): string {
  return name.slice(0, 2).toUpperCase()
}

const DiscussionZone: FC<DiscussionZoneProps> = ({
  messages: propMessages,
  onSendMessage,
  onSummarize,
}) => {
  const [activeTab, setActiveTab] = useState<'public' | 'private'>('public')
  const [input, setInput] = useState('')
  const messages = propMessages ?? MOCK_MESSAGES

  const handleSend = (e: FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return
    onSendMessage(input.trim())
    setInput('')
  }

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-default)',
        borderRadius: 'var(--radius-lg)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          display: 'flex',
          borderBottom: '1px solid var(--border-default)',
          flexShrink: 0,
        }}
      >
        <button
          onClick={() => setActiveTab('public')}
          style={{
            flex: 1,
            padding: 'var(--space-3)',
            background: activeTab === 'public' ? 'var(--bg-elevated)' : 'transparent',
            border: 'none',
            color: activeTab === 'public' ? 'var(--accent)' : 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: 'var(--text-sm)',
            fontWeight: activeTab === 'public' ? 600 : 400,
            borderBottom: activeTab === 'public' ? '2px solid var(--accent)' : '2px solid transparent',
          }}
        >
          公共讨论
        </button>
        <button
          onClick={() => setActiveTab('private')}
          style={{
            flex: 1,
            padding: 'var(--space-3)',
            background: activeTab === 'private' ? 'var(--bg-elevated)' : 'transparent',
            border: 'none',
            color: activeTab === 'private' ? 'var(--accent)' : 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: 'var(--text-sm)',
            fontWeight: activeTab === 'private' ? 600 : 400,
            borderBottom: activeTab === 'private' ? '2px solid var(--accent)' : '2px solid transparent',
          }}
        >
          个人讨论
        </button>
      </div>

      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: 'var(--space-4)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-3)',
        }}
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: 'flex',
              gap: 'var(--space-3)',
            }}
          >
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: '50%',
                background: msg.is_ai ? 'var(--accent-subtle)' : 'var(--info-bg)',
                color: msg.is_ai ? 'var(--accent)' : 'var(--info)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 'var(--text-xs)',
                fontWeight: 700,
                flexShrink: 0,
                fontFamily: 'var(--font-mono)',
              }}
            >
              {getInitials(msg.sender_name)}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-2)',
                  marginBottom: 'var(--space-1)',
                }}
              >
                <span
                  style={{
                    fontSize: 'var(--text-sm)',
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                  }}
                >
                  {msg.sender_name}
                </span>
                <span
                  style={{
                    fontSize: 'var(--text-xs)',
                    color: 'var(--text-muted)',
                  }}
                >
                  {msg.sender_role}
                </span>
                <span
                  style={{
                    fontSize: 'var(--text-xs)',
                    color: 'var(--text-muted)',
                    marginLeft: 'auto',
                  }}
                >
                  {msg.timestamp}
                </span>
              </div>
              <div
                style={{
                  background: msg.is_ai ? 'var(--bg-subtle)' : 'var(--bg-elevated)',
                  borderLeft: `2px solid ${msg.is_ai ? 'var(--accent)' : 'var(--info)'}`,
                  padding: 'var(--space-3)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: 'var(--text-sm)',
                  lineHeight: 1.7,
                  color: 'var(--text-primary)',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {msg.content}
              </div>
              {msg.ai_warning && (
                <div
                  style={{
                    marginTop: 'var(--space-1)',
                    fontSize: 'var(--text-xs)',
                    color: 'var(--warning)',
                    padding: 'var(--space-1) var(--space-2)',
                    background: 'var(--warning-bg)',
                    borderRadius: 'var(--radius-sm)',
                    display: 'inline-block',
                  }}
                >
                  {msg.ai_warning}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div
        style={{
          borderTop: '1px solid var(--border-default)',
          padding: 'var(--space-3)',
          background: 'var(--bg-elevated)',
          flexShrink: 0,
        }}
      >
        <form onSubmit={handleSend}>
          <div style={{ display: 'flex', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="@角色名 输入讨论内容..."
              style={{
                flex: 1,
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-2) var(--space-3)',
                color: 'var(--text-primary)',
                fontSize: 'var(--text-sm)',
                outline: 'none',
              }}
            />
            <button
              type="submit"
              style={{
                background: 'var(--accent)',
                color: '#000',
                border: 'none',
                padding: 'var(--space-2) var(--space-4)',
                borderRadius: 'var(--radius-md)',
                cursor: 'pointer',
                fontSize: 'var(--text-sm)',
                fontWeight: 600,
              }}
            >
              发送
            </button>
          </div>
        </form>
        <button
          onClick={onSummarize}
          style={{
            width: '100%',
            background: 'var(--bg-subtle)',
            color: 'var(--text-secondary)',
            border: '1px solid var(--border-default)',
            padding: 'var(--space-2) var(--space-3)',
            borderRadius: 'var(--radius-md)',
            cursor: 'pointer',
            fontSize: 'var(--text-xs)',
          }}
        >
          一键收束讨论 → 生成文档段落
        </button>
      </div>
    </div>
  )
}

export default DiscussionZone
export type { DiscussionMessage }
