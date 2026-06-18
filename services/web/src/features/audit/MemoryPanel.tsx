import { useState, type FC } from 'react'

interface MemoryRule {
  id: number
  rule_text: string
  source_type: 'arbitration' | 'approval'
  source_ref: number
  trigger_count: number
}

interface AnchorStatement {
  id: number
  statement: string
  created_at: string
}

interface MemoryPanelProps {
  anchorStatements?: AnchorStatement[]
  rules?: MemoryRule[]
  currentTriggers?: MemoryRule[]
}

const MOCK_ANCHORS: AnchorStatement[] = [
  { id: 1, statement: '本系统架构设计遵循"安全优先、合规先行"原则', created_at: '2026-06-10' },
  { id: 2, statement: '所有用户数据处理必须在 EU 境内完成，不得跨境传输', created_at: '2026-06-12' },
]

const MOCK_RULES: MemoryRule[] = [
  { id: 1, rule_text: '微服务拆分必须先完成 GDPR 合规审计', source_type: 'arbitration', source_ref: 1, trigger_count: 4 },
  { id: 2, rule_text: '缓存 TTL 不得超过 2 小时，需用户明确授权', source_type: 'arbitration', source_ref: 2, trigger_count: 3 },
  { id: 3, rule_text: '日志写入前必须完成 PII 数据脱敏', source_type: 'arbitration', source_ref: 3, trigger_count: 5 },
  { id: 4, rule_text: 'API 限流统一 50 req/s，不分用户等级', source_type: 'arbitration', source_ref: 4, trigger_count: 2 },
  { id: 5, rule_text: '系统性能优化不得以牺牲合规性为代价', source_type: 'approval', source_ref: 12, trigger_count: 3 },
  { id: 6, rule_text: '新功能上线前需通过 TechReviewer 审查', source_type: 'approval', source_ref: 8, trigger_count: 1 },
]

const MOCK_TRIGGERS: MemoryRule[] = [
  { id: 1, rule_text: '微服务拆分必须先完成 GDPR 合规审计', source_type: 'arbitration', source_ref: 1, trigger_count: 4 },
  { id: 2, rule_text: '缓存 TTL 不得超过 2 小时，需用户明确授权', source_type: 'arbitration', source_ref: 2, trigger_count: 3 },
]

const MemoryPanel: FC<MemoryPanelProps> = ({
  anchorStatements: propAnchors,
  rules: propRules,
  currentTriggers: propTriggers,
}) => {
  const [expanded, setExpanded] = useState(true)
  const anchors = propAnchors ?? MOCK_ANCHORS
  const rules = propRules ?? MOCK_RULES
  const triggers = propTriggers ?? MOCK_TRIGGERS

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-default)',
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
      }}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: '100%',
          padding: 'var(--space-3) var(--space-4)',
          background: 'var(--bg-elevated)',
          border: 'none',
          color: 'var(--text-primary)',
          cursor: 'pointer',
          fontSize: 'var(--text-sm)',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: expanded ? '1px solid var(--border-default)' : 'none',
        }}
      >
        <span>项目记忆 [{expanded ? '收起' : '展开'}]</span>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          {expanded ? '▲' : '▼'}
        </span>
      </button>

      {expanded && (
        <div
          style={{
            padding: 'var(--space-4)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-4)',
            maxHeight: 500,
            overflow: 'auto',
          }}
        >
          <div>
            <div
              style={{
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                marginBottom: 'var(--space-2)',
              }}
            >
              锚点陈述
            </div>
            {anchors.map((a) => (
              <div
                key={a.id}
                style={{
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-2) var(--space-3)',
                  marginBottom: 'var(--space-2)',
                  fontSize: 'var(--text-sm)',
                  color: 'var(--text-primary)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span>• {a.statement}</span>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', flexShrink: 0, marginLeft: 'var(--space-2)' }}>
                  {a.created_at}
                </span>
              </div>
            ))}
          </div>

          <div>
            <div
              style={{
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                marginBottom: 'var(--space-2)',
              }}
            >
              立场法则
            </div>
            {rules.map((rule) => {
              const isSolidified = rule.trigger_count >= 3
              return (
                <div
                  key={rule.id}
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-3)',
                    marginBottom: 'var(--space-2)',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 'var(--space-2)',
                      marginBottom: 'var(--space-2)',
                    }}
                  >
                    <span
                      style={{
                        color: isSolidified ? 'var(--success)' : 'var(--text-secondary)',
                        fontWeight: 700,
                        flexShrink: 0,
                      }}
                    >
                      •
                    </span>
                    <span
                      style={{
                        fontSize: 'var(--text-sm)',
                        color: 'var(--text-primary)',
                        lineHeight: 1.5,
                        flex: 1,
                      }}
                    >
                      {rule.rule_text}
                    </span>
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      fontSize: 'var(--text-xs)',
                    }}
                  >
                    <span style={{ color: 'var(--text-muted)' }}>
                      来源: {rule.source_type === 'arbitration' ? '仲裁裁决' : '审批反馈'} #{rule.source_ref}
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                      <span style={{ color: 'var(--text-muted)' }}>
                        触发: {rule.trigger_count}次
                      </span>
                      <span
                        style={{
                          background: isSolidified ? 'var(--success-bg)' : 'var(--bg-subtle)',
                          color: isSolidified ? 'var(--success)' : 'var(--text-muted)',
                          padding: '1px 8px',
                          borderRadius: 'var(--radius-sm)',
                          fontWeight: 500,
                        }}
                      >
                        {isSolidified ? '已固化' : '待固化'}
                      </span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {triggers.length > 0 && (
            <div>
              <div
                style={{
                  fontSize: 'var(--text-xs)',
                  fontWeight: 600,
                  color: 'var(--text-muted)',
                  textTransform: 'uppercase',
                  marginBottom: 'var(--space-2)',
                }}
              >
                当前编辑触发
              </div>
              <div
                style={{
                  background: 'var(--warning-bg)',
                  border: '1px solid rgba(228,87,61,0.3)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-3)',
                }}
              >
                <div
                  style={{
                    fontSize: 'var(--text-xs)',
                    fontWeight: 600,
                    color: 'var(--warning)',
                    marginBottom: 'var(--space-2)',
                  }}
                >
                  ⚠ 当前编辑内容触发了以下项目记忆：
                </div>
                {triggers.map((t) => (
                  <div
                    key={t.id}
                    style={{
                      fontSize: 'var(--text-sm)',
                      color: 'var(--text-primary)',
                      marginBottom: 'var(--space-1)',
                    }}
                  >
                    • {t.rule_text}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default MemoryPanel
export type { MemoryRule, AnchorStatement }
