import { useState, type FC } from 'react'
import { useAuthStore } from '../../shared/store/authStore'
import { auditActionLabel } from '../../shared/authz'

interface AuditEntry {
  id: number
  timestamp: string
  operator: string
  operation_type: string
  target: string
  detail: string
}

interface AuditLogProps {
  entries?: AuditEntry[]
  docId: string
}

const MOCK_ENTRIES: AuditEntry[] = [
  { id: 1, timestamp: '2026-06-18T18:32:01.423', operator: '张工', operation_type: '编辑文档', target: 'Block #3', detail: '修改了微服务架构描述段落' },
  { id: 2, timestamp: '2026-06-18T18:31:45.112', operator: 'TechReviewer', operation_type: '提交提案', target: 'Block #5', detail: '提交润色提案 #42' },
  { id: 3, timestamp: '2026-06-18T18:30:22.880', operator: '李法务', operation_type: '审批操作', target: 'Proposal #38', detail: '采纳了 LegalAgent 的合规建议' },
  { id: 4, timestamp: '2026-06-18T18:28:15.657', operator: 'LegalAgent', operation_type: '提交提案', target: 'Block #5', detail: '提交合规审查提案 #41' },
  { id: 5, timestamp: '2026-06-18T18:25:03.234', operator: '张工', operation_type: '仲裁裁决', target: 'Arbitration #3', detail: '采纳 TechReviewer 方案，仲裁解决' },
  { id: 6, timestamp: '2026-06-18T18:22:47.901', operator: 'TechReviewer', operation_type: '提交提案', target: 'Block #2', detail: '提交技术审查提案 #40' },
  { id: 7, timestamp: '2026-06-18T18:20:11.543', operator: '张工', operation_type: 'E-STOP', target: '全局AI', detail: '冻结全域AI（原因：提案冲突）' },
  { id: 8, timestamp: '2026-06-18T18:19:58.210', operator: '李法务', operation_type: '添加注释', target: 'Block #7', detail: '标注 GDPR 合规注意事项' },
  { id: 9, timestamp: '2026-06-18T18:15:34.089', operator: 'LegalAgent', operation_type: '提交提案', target: 'Block #7', detail: '提交合规审查提案 #39' },
  { id: 10, timestamp: '2026-06-18T18:10:02.456', operator: '张工', operation_type: '编辑文档', target: 'Block #1', detail: '更新项目概述和目标' },
  { id: 11, timestamp: '2026-06-18T17:55:18.333', operator: 'TechReviewer', operation_type: '自动检测', target: 'Block #4', detail: '检测到性能隐患，标注风险点' },
  { id: 12, timestamp: '2026-06-18T17:40:44.127', operator: '李法务', operation_type: '恢复AI', target: '全局AI', detail: '解除 E-STOP，恢复 AI 运行' },
]

const OPERATION_TYPES = ['全部', '编辑文档', '提交提案', '审批操作', '仲裁裁决', 'E-STOP', '恢复AI', '添加注释', '自动检测']
const MEMBERS = ['全部', '张工', '李法务', 'TechReviewer', 'LegalAgent']

function formatTimestamp(iso: string): string {
  const d = new Date(iso)
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  const ss = String(d.getSeconds()).padStart(2, '0')
  const ms = String(d.getMilliseconds()).padStart(3, '0')
  return `${hh}:${mm}:${ss}.${ms}`
}

function getTimeRangeLabel(range: string): string {
  switch (range) {
    case '1h': return '最近1小时'
    case '6h': return '最近6小时'
    case '24h': return '最近24小时'
    case '7d': return '最近7天'
    default: return '全部时间'
  }
}

const AuditLog: FC<AuditLogProps> = ({ entries: propEntries, docId: _docId }) => {
  const [timeRange, setTimeRange] = useState('24h')
  const [opType, setOpType] = useState('全部')
  const [member, setMember] = useState('全部')
  const entries = propEntries ?? MOCK_ENTRIES
  const currentView = useAuthStore((s) => s.currentView)
  const isOps = currentView === 'ops'

  const filtered = entries.filter((e) => {
    if (opType !== '全部' && e.operation_type !== opType) return false
    if (member !== '全部' && e.operator !== member) return false
    return true
  })

  const handleExportCsv = () => {
    const headers = '时间,操作人,操作类型,目标,详情'
    const rows = filtered.map((e) =>
      `"${formatTimestamp(e.timestamp)}","${e.operator}","${e.operation_type}","${e.target}","${e.detail}"`
    )
    const csv = [headers, ...rows].join('\n')
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit-log-${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'var(--bg-page)',
        padding: 'var(--space-6)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 'var(--space-6)',
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: 'var(--text-3xl)',
            fontWeight: 700,
            color: 'var(--text-primary)',
          }}
        >
          操作审计日志
        </h1>
        <button
          onClick={handleExportCsv}
          style={{
            background: 'var(--bg-elevated)',
            color: 'var(--text-secondary)',
            border: '1px solid var(--border-default)',
            padding: 'var(--space-2) var(--space-4)',
            borderRadius: 'var(--radius-md)',
            cursor: 'pointer',
            fontSize: 'var(--text-sm)',
            fontWeight: 500,
          }}
        >
          导出 CSV
        </button>
      </div>

      <div
        style={{
          display: 'flex',
          gap: 'var(--space-3)',
          marginBottom: 'var(--space-4)',
          flexWrap: 'wrap',
        }}
      >
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          style={{
            background: 'var(--bg-elevated)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-2) var(--space-3)',
            fontSize: 'var(--text-sm)',
            cursor: 'pointer',
          }}
        >
          {['all', '1h', '6h', '24h', '7d'].map((v) => (
            <option key={v} value={v}>{getTimeRangeLabel(v)}</option>
          ))}
        </select>

        <select
          value={opType}
          onChange={(e) => setOpType(e.target.value)}
          style={{
            background: 'var(--bg-elevated)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-2) var(--space-3)',
            fontSize: 'var(--text-sm)',
            cursor: 'pointer',
          }}
        >
          {OPERATION_TYPES.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>

        <select
          value={member}
          onChange={(e) => setMember(e.target.value)}
          style={{
            background: 'var(--bg-elevated)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-2) var(--space-3)',
            fontSize: 'var(--text-sm)',
            cursor: 'pointer',
          }}
        >
          {MEMBERS.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>

        <span
          style={{
            marginLeft: 'auto',
            fontSize: 'var(--text-sm)',
            color: 'var(--text-muted)',
            alignSelf: 'center',
          }}
        >
          共 {filtered.length} 条记录
        </span>
      </div>

      <div
        style={{
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: isOps
              ? '120px 120px 120px 120px 120px 1fr'
              : '180px 120px 140px 1fr',
            background: 'var(--bg-elevated)',
            borderBottom: '1px solid var(--border-default)',
          }}
        >
          {(isOps
            ? ['时间', '操作ID', '操作人', '操作类型', '目标ID', '详情']
            : ['时间', '操作人', '操作类型', '详情']
          ).map((h) => (
            <div
              key={h}
              style={{
                padding: 'var(--space-3) var(--space-4)',
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}
            >
              {h}
            </div>
          ))}
        </div>

        <div>
          {filtered.map((entry, idx) => (
            <div
              key={entry.id}
              style={{
                display: 'grid',
                gridTemplateColumns: isOps
                  ? '120px 120px 120px 120px 120px 1fr'
                  : '180px 120px 140px 1fr',
                background: idx % 2 === 0 ? 'var(--bg-surface)' : 'var(--bg-elevated)',
                borderBottom: '1px solid var(--border-default)',
              }}
            >
              <div
                style={{
                  padding: 'var(--space-2) var(--space-4)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--text-sm)',
                  color: 'var(--text-primary)',
                }}
              >
                {formatTimestamp(entry.timestamp)}
              </div>
              {isOps && (
                <div
                  style={{
                    padding: 'var(--space-2) var(--space-4)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 'var(--text-sm)',
                    color: 'var(--text-muted)',
                  }}
                >
                  op-{String(entry.id).padStart(4, '0')}
                </div>
              )}
              <div
                style={{
                  padding: 'var(--space-2) var(--space-4)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--text-sm)',
                  color: 'var(--text-secondary)',
                }}
              >
                {entry.operator}
              </div>
              <div
                style={{
                  padding: 'var(--space-2) var(--space-4)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--text-sm)',
                  color: 'var(--accent)',
                }}
              >
                {auditActionLabel(entry.operation_type)}
              </div>
              {isOps && (
                <div
                  style={{
                    padding: 'var(--space-2) var(--space-4)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 'var(--text-sm)',
                    color: 'var(--text-muted)',
                  }}
                >
                  {entry.target}
                </div>
              )}
              <div
                style={{
                  padding: 'var(--space-2) var(--space-4)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--text-sm)',
                  color: 'var(--text-primary)',
                }}
              >
                {entry.detail}
              </div>
            </div>
          ))}
        </div>
      </div>

      {filtered.length === 0 && (
        <div
          style={{
            textAlign: 'center',
            padding: 'var(--space-12)',
            color: 'var(--text-muted)',
            fontSize: 'var(--text-sm)',
          }}
        >
          无匹配的审计记录
        </div>
      )}
    </div>
  )
}

export default AuditLog
export type { AuditEntry }
