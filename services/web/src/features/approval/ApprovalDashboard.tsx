import { useState, type FC } from 'react'
import { useAuthStore } from '../../shared/store/authStore'
import { canDoInDocument } from '../../shared/authz'
import type { ProposalResponse } from '../forge/SurgeryDesk'

interface ApprovalDashboardProps {
  proposals: ProposalResponse[]
  onPreviewDiff: (proposal: ProposalResponse) => void
  onApprove: (proposalId: number) => void
  onReject: (proposalId: number) => void
  onUndoApprove: (proposalId: number) => void
  acceptedProposals: Map<number, string>
}

function timeAgo(dateStr: string): string {
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diff = now - then
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  return `${Math.floor(hours / 24)}天前`
}

const ApprovalDashboard: FC<ApprovalDashboardProps> = ({
  proposals,
  onPreviewDiff,
  onApprove,
  onReject,
  onUndoApprove,
  acceptedProposals,
}) => {
  const [filter, setFilter] = useState('全部')
  const roles = ['全部', 'TechReviewer', 'LegalAgent']
  const docRole = useAuthStore((s) => s.docRole)
  const canReview = canDoInDocument(docRole, 'start_review')

  const filtered = filter === '全部' ? proposals : proposals.filter((p) => p.ai_role === filter)

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
          padding: 'var(--space-4)',
          borderBottom: '1px solid var(--border-default)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}
      >
        <h3
          style={{
            margin: 0,
            fontSize: 'var(--text-lg)',
            fontWeight: 600,
            color: 'var(--text-primary)',
          }}
        >
          待审批提案 ({filtered.length})
        </h3>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{
            background: 'var(--bg-elevated)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-1) var(--space-3)',
            fontSize: 'var(--text-sm)',
            cursor: 'pointer',
          }}
        >
          {roles.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>

      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: 'var(--space-3)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-3)',
        }}
      >
        {filtered.map((p) => {
          const acceptedTime = acceptedProposals.get(p.proposal_id)
          return (
            <div
              key={p.proposal_id}
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-3)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: 'var(--space-2)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <span
                    style={{
                      fontWeight: 600,
                      fontSize: 'var(--text-sm)',
                      color: 'var(--text-primary)',
                    }}
                  >
                    #{p.proposal_id} {p.ai_role}
                  </span>
                  <span
                    style={{
                      background: p.proposal_type === '润色' ? 'var(--accent-subtle)' : 'var(--info-bg)',
                      color: p.proposal_type === '润色' ? 'var(--accent)' : 'var(--info)',
                      padding: '1px 8px',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: 'var(--text-xs)',
                      fontWeight: 500,
                    }}
                  >
                    {p.proposal_type}
                  </span>
                </div>
                <span
                  style={{
                    fontSize: 'var(--text-xs)',
                    color: 'var(--text-muted)',
                  }}
                >
                  {timeAgo(p.created_at)}
                </span>
              </div>

              <div
                style={{
                  display: 'flex',
                  gap: 'var(--space-4)',
                  marginBottom: 'var(--space-2)',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--text-secondary)',
                }}
              >
                <span>Block: {p.block_id}</span>
                <span>对齐分: {(p.anchor_alignment_score * 100).toFixed(0)}%</span>
              </div>

              {acceptedTime ? (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: 'var(--success-bg)',
                    padding: 'var(--space-1) var(--space-3)',
                    borderRadius: 'var(--radius-md)',
                  }}
                >
                  <span style={{ color: 'var(--success)', fontSize: 'var(--text-sm)' }}>
                    已采纳 — {acceptedTime}
                  </span>
                  {canReview && (
                    <button
                      onClick={() => onUndoApprove(p.proposal_id)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--warning)',
                        cursor: 'pointer',
                        fontSize: 'var(--text-xs)',
                        textDecoration: 'underline',
                      }}
                    >
                      撤销采纳
                    </button>
                  )}
                </div>
              ) : canReview ? (
                <div style={{ display: 'flex', gap: 'var(--space-2)', justifyContent: 'flex-end' }}>
                  <button
                    onClick={() => onPreviewDiff(p)}
                    style={{
                      background: 'var(--bg-subtle)',
                      color: 'var(--text-secondary)',
                      border: '1px solid var(--border-default)',
                      padding: 'var(--space-1) var(--space-3)',
                      borderRadius: 'var(--radius-md)',
                      cursor: 'pointer',
                      fontSize: 'var(--text-xs)',
                    }}
                  >
                    预览Diff
                  </button>
                  <button
                    onClick={() => onApprove(p.proposal_id)}
                    style={{
                      background: 'var(--accent)',
                      color: '#000',
                      border: 'none',
                      padding: 'var(--space-1) var(--space-3)',
                      borderRadius: 'var(--radius-md)',
                      cursor: 'pointer',
                      fontSize: 'var(--text-xs)',
                      fontWeight: 600,
                    }}
                  >
                    采纳
                  </button>
                  <button
                    onClick={() => onReject(p.proposal_id)}
                    style={{
                      background: 'var(--danger-bg)',
                      color: 'var(--danger)',
                      border: '1px solid var(--danger)',
                      padding: 'var(--space-1) var(--space-3)',
                      borderRadius: 'var(--radius-md)',
                      cursor: 'pointer',
                      fontSize: 'var(--text-xs)',
                    }}
                  >
                    拒绝
                  </button>
                </div>
              ) : (
                <div
                  style={{
                    fontSize: 'var(--text-xs)',
                    color: 'var(--text-muted)',
                    textAlign: 'right',
                  }}
                >
                  您当前角色无审批权限
                </div>
              )}
            </div>
          )
        })}

        {filtered.length === 0 && (
          <div
            style={{
              color: 'var(--text-muted)',
              textAlign: 'center',
              padding: 'var(--space-8)',
              fontSize: 'var(--text-sm)',
            }}
          >
            暂无待审批提案
          </div>
        )}
      </div>
    </div>
  )
}

export default ApprovalDashboard
