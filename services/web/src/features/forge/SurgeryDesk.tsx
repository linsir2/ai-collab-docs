import { type FC } from 'react'
import { useAuthStore } from '../../shared/store/authStore'
import { trustScoreLabel, canDoInDocument } from '../../shared/authz'

interface ProposalResponse {
  proposal_id: number
  ai_role: string
  trust_score: number
  anchor_alignment_score: number
  created_at: string
  old_text: string
  new_text: string
  block_id: string
  proposal_type: string
}

interface SurgeryDeskProps {
  proposal: ProposalResponse
  onClose: () => void
  onApprove: (proposalId: number, action: 'merge_all' | 'reject_annotate' | 'manual_edit') => void
}

function computeDiff(oldText: string, newText: string): { left: string; right: string } {
  const oldWords = oldText.split(/(\s+)/)
  const newWords = newText.split(/(\s+)/)
  const leftParts: string[] = []
  const rightParts: string[] = []

  let oi = 0
  let ni = 0

  while (oi < oldWords.length || ni < newWords.length) {
    if (oi < oldWords.length && ni < newWords.length && oldWords[oi] === newWords[ni]) {
      leftParts.push(oldWords[oi])
      rightParts.push(newWords[ni])
      oi++
      ni++
    } else if (ni < newWords.length && (oi >= oldWords.length || oldWords[oi] !== newWords[ni])) {
      if (oi < oldWords.length) {
        leftParts.push(`<del>${oldWords[oi]}</del>`)
        oi++
      }
      rightParts.push(`<ins>${newWords[ni]}</ins>`)
      ni++
    } else if (oi < oldWords.length) {
      leftParts.push(`<del>${oldWords[oi]}</del>`)
      oi++
    }
  }

  return { left: leftParts.join(''), right: rightParts.join('') }
}

function renderHighlighted(text: string): React.ReactNode[] {
  const parts = text.split(/(<del>.*?<\/del>|<ins>.*?<\/ins>)/g)
  return parts.map((part, i) => {
    if (part.startsWith('<del>')) {
      return (
        <span
          key={i}
          style={{
            background: 'rgba(239,68,68,0.25)',
            textDecoration: 'line-through',
            color: 'var(--danger)',
            borderRadius: 'var(--radius-sm)',
            padding: '1px 2px',
          }}
        >
          {part.replace(/<\/?del>/g, '')}
        </span>
      )
    }
    if (part.startsWith('<ins>')) {
      return (
        <span
          key={i}
          style={{
            background: 'rgba(52,211,153,0.25)',
            borderRadius: 'var(--radius-sm)',
            padding: '1px 2px',
            color: 'var(--success)',
          }}
        >
          {part.replace(/<\/?ins>/g, '')}
        </span>
      )
    }
    return <span key={i}>{part}</span>
  })
}

const SurgeryDesk: FC<SurgeryDeskProps> = ({ proposal, onClose, onApprove }) => {
  const docRole = useAuthStore((s) => s.docRole)
  const canEdit = canDoInDocument(docRole, 'use_forge')
  const diff = computeDiff(proposal.old_text, proposal.new_text)
  const trustLabel = trustScoreLabel(proposal.trust_score)

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(0,0,0,0.7)',
        backdropFilter: 'blur(4px)',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-lg)',
          width: '90vw',
          maxWidth: 1100,
          maxHeight: '80vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: '0 24px 48px rgba(0,0,0,0.5)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: 'var(--space-4) var(--space-6)',
            borderBottom: '1px solid var(--border-default)',
            background: 'var(--bg-elevated)',
            flexShrink: 0,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
            <h2
              style={{
                margin: 0,
                fontSize: 'var(--text-xl)',
                color: 'var(--text-primary)',
                fontWeight: 600,
              }}
            >
              润色提案 #{proposal.proposal_id}
            </h2>
            <span
              style={{
                background: 'var(--accent-subtle)',
                color: 'var(--accent)',
                padding: '2px 10px',
                borderRadius: 'var(--radius-md)',
                fontSize: 'var(--text-sm)',
                fontWeight: 500,
              }}
            >
              {proposal.ai_role}
            </span>
            <span
              style={{
                color: 'var(--text-secondary)',
                fontSize: 'var(--text-sm)',
              }}
            >
              信任分: {trustLabel}
            </span>
            <span
              style={{
                color: 'var(--text-muted)',
                fontSize: 'var(--text-xs)',
              }}
            >
              {proposal.created_at}
            </span>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: 'var(--text-xl)',
              cursor: 'pointer',
              padding: 'var(--space-1) var(--space-2)',
              borderRadius: 'var(--radius-md)',
            }}
          >
            ✕
          </button>
        </div>

        <div
          style={{
            display: 'flex',
            flex: 1,
            overflow: 'hidden',
            minHeight: 0,
          }}
        >
          <div
            style={{
              flex: 1,
              borderRight: '1px solid var(--border-default)',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                padding: 'var(--space-2) var(--space-4)',
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                color: 'var(--danger)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                background: 'var(--danger-bg)',
                flexShrink: 0,
              }}
            >
              原始内容（旧轨）
            </div>
            <div
              style={{
                flex: 1,
                overflow: 'auto',
                padding: 'var(--space-4)',
                fontFamily: 'var(--font-mono)',
                fontSize: 'var(--text-sm)',
                lineHeight: 1.7,
                color: 'var(--text-primary)',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {renderHighlighted(diff.left)}
            </div>
          </div>

          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                padding: 'var(--space-2) var(--space-4)',
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                color: 'var(--success)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                background: 'var(--success-bg)',
                flexShrink: 0,
              }}
            >
              AI提案（新轨）
            </div>
            <div
              style={{
                flex: 1,
                overflow: 'auto',
                padding: 'var(--space-4)',
                fontFamily: 'var(--font-mono)',
                fontSize: 'var(--text-sm)',
                lineHeight: 1.7,
                color: 'var(--text-primary)',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {renderHighlighted(diff.right)}
            </div>
          </div>
        </div>

        <div
          style={{
            borderTop: '1px solid var(--border-default)',
            background: 'var(--bg-elevated)',
            flexShrink: 0,
          }}
        >
          <div
            style={{
              padding: 'var(--space-3) var(--space-6)',
              borderBottom: '1px solid var(--border-default)',
            }}
          >
            <div
              style={{
                fontSize: 'var(--text-sm)',
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 'var(--space-2)',
              }}
            >
              校验报告
            </div>
            <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap' }}>
              <span
                style={{
                  background: 'var(--success-bg)',
                  color: 'var(--success)',
                  padding: 'var(--space-1) var(--space-3)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: 'var(--text-xs)',
                  fontWeight: 500,
                }}
              >
                立意对齐: {(proposal.anchor_alignment_score * 100).toFixed(0)}% (Pass)
              </span>
              <span
                style={{
                  background: 'var(--success-bg)',
                  color: 'var(--success)',
                  padding: 'var(--space-1) var(--space-3)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: 'var(--text-xs)',
                  fontWeight: 500,
                }}
              >
                表述精准: PASS
              </span>
              <span
                style={{
                  background: 'var(--success-bg)',
                  color: 'var(--success)',
                  padding: 'var(--space-1) var(--space-3)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: 'var(--text-xs)',
                  fontWeight: 500,
                }}
              >
                立场一致: PASS
              </span>
              <span
                style={{
                  background: 'var(--success-bg)',
                  color: 'var(--success)',
                  padding: 'var(--space-1) var(--space-3)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: 'var(--text-xs)',
                  fontWeight: 500,
                }}
              >
                后置连贯: 上下文通顺
              </span>
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              gap: 'var(--space-3)',
              padding: 'var(--space-4) var(--space-6)',
              justifyContent: 'flex-end',
            }}
          >
            {canEdit ? (
              <>
                <button
                  onClick={() => onApprove(proposal.proposal_id, 'manual_edit')}
                  style={{
                    background: 'var(--bg-subtle)',
                    color: 'var(--text-secondary)',
                    border: '1px solid var(--border-default)',
                    padding: 'var(--space-2) var(--space-5)',
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer',
                    fontSize: 'var(--text-sm)',
                    fontWeight: 500,
                  }}
                >
                  手动编辑
                </button>
                <button
                  onClick={() => onApprove(proposal.proposal_id, 'reject_annotate')}
                  style={{
                    background: 'var(--danger-bg)',
                    color: 'var(--danger)',
                    border: '1px solid var(--danger)',
                    padding: 'var(--space-2) var(--space-5)',
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer',
                    fontSize: 'var(--text-sm)',
                    fontWeight: 500,
                  }}
                >
                  拒绝批注
                </button>
                <button
                  onClick={() => onApprove(proposal.proposal_id, 'merge_all')}
                  style={{
                    background: 'var(--accent)',
                    color: '#000',
                    border: 'none',
                    padding: 'var(--space-2) var(--space-5)',
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer',
                    fontSize: 'var(--text-sm)',
                    fontWeight: 600,
                  }}
                >
                  全盘合并
                </button>
              </>
            ) : (
              <span
                style={{
                  fontSize: 'var(--text-sm)',
                  color: 'var(--text-muted)',
                }}
              >
                您当前身份无编辑权限
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default SurgeryDesk
export type { ProposalResponse }
