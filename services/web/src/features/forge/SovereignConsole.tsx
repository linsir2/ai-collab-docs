import { useState, type FC } from 'react'
import { useAuthStore } from '../../shared/store/authStore'
import { canDoInDocument } from '../../shared/authz'

interface AIPanelState {
  activity: number
  triggerMode: 'mention' | 'phase' | 'full'
}

interface SovereignConsoleProps {
  onEStop: () => void
  isEStopped: boolean
}

const SovereignConsole: FC<SovereignConsoleProps> = ({ onEStop, isEStopped }) => {
  const [minimized, setMinimized] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [globalTrigger, setGlobalTrigger] = useState('phase')

  const docRole = useAuthStore((s) => s.docRole)
  const currentView = useAuthStore((s) => s.currentView)

  const isOps = currentView === 'ops'
  const isOwner = canDoInDocument(docRole, 'state_transition')
  const isReviewer = !isOwner && canDoInDocument(docRole, 'start_review')

  const [techReviewer, setTechReviewer] = useState<AIPanelState>({
    activity: 80,
    triggerMode: 'phase',
  })
  const [legalAgent, setLegalAgent] = useState<AIPanelState>({
    activity: 60,
    triggerMode: 'mention',
  })

  const handleEStopClick = () => {
    if (isEStopped) {
      return
    }
    setShowConfirm(true)
  }

  const confirmEStop = () => {
    onEStop()
    setShowConfirm(false)
  }

  if (minimized) {
    return (
      <div
        style={{
          position: 'fixed',
          bottom: 'var(--space-4)',
          right: 'var(--space-4)',
          zIndex: 500,
        }}
      >
        <button
          onClick={() => setMinimized(false)}
          style={{
            background: 'var(--bg-elevated)',
            color: 'var(--accent)',
            border: '1px solid var(--border-default)',
            padding: 'var(--space-2) var(--space-4)',
            borderRadius: 'var(--radius-md)',
            cursor: 'pointer',
            fontSize: 'var(--text-sm)',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
          }}
        >
          <span>{isEStopped ? '🛑' : '🤖'}</span>
          AI控制台
        </button>
      </div>
    )
  }

  if (!isOwner && !isReviewer) {
    return null
  }

  return (
    <>
      <div
        style={{
          position: 'fixed',
          bottom: 'var(--space-4)',
          right: 'var(--space-4)',
          width: 320,
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: '0 12px 40px rgba(0,0,0,0.5)',
          zIndex: 500,
          overflow: 'hidden',
        }}
      >
        {isEStopped && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: 'rgba(13,13,15,0.85)',
              zIndex: 10,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 'var(--radius-lg)',
              backdropFilter: 'blur(2px)',
            }}
          >
            <span
              style={{
                color: 'var(--danger)',
                fontSize: 'var(--text-xl)',
                fontWeight: 700,
                letterSpacing: 2,
              }}
            >
              [AI已冻结]
            </span>
          </div>
        )}

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: 'var(--space-3) var(--space-4)',
            background: 'var(--bg-elevated)',
            borderBottom: '1px solid var(--border-default)',
          }}
        >
          <h3
            style={{
              margin: 0,
              fontSize: 'var(--text-sm)',
              fontWeight: 600,
              color: 'var(--text-primary)',
            }}
          >
            AI控制台
          </h3>
          <button
            onClick={() => setMinimized(true)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              fontSize: 'var(--text-base)',
              padding: 0,
            }}
          >
            _
          </button>
        </div>

        <div style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {isOwner && isOps && (
            <>
              <div>
                <div
                  style={{
                    fontSize: 'var(--text-xs)',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    marginBottom: 'var(--space-3)',
                  }}
                >
                  TechReviewer
                </div>
                <div style={{ marginBottom: 'var(--space-2)' }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      marginBottom: 'var(--space-1)',
                    }}
                  >
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>活跃度</span>
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--accent)' }}>{techReviewer.activity}%</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={techReviewer.activity}
                    onChange={(e) =>
                      setTechReviewer({ ...techReviewer, activity: Number(e.target.value) })
                    }
                    style={{
                      width: '100%',
                      accentColor: 'var(--accent)',
                      height: 4,
                      cursor: 'pointer',
                    }}
                  />
                </div>
                <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
                  {(['mention', 'phase', 'full'] as const).map((mode) => (
                    <label
                      key={mode}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--space-1)',
                        fontSize: 'var(--text-xs)',
                        color:
                          techReviewer.triggerMode === mode
                            ? 'var(--accent)'
                            : 'var(--text-muted)',
                        cursor: 'pointer',
                      }}
                    >
                      <input
                        type="radio"
                        name="techReviewer_trigger"
                        checked={techReviewer.triggerMode === mode}
                        onChange={() =>
                          setTechReviewer({ ...techReviewer, triggerMode: mode })
                        }
                        style={{ accentColor: 'var(--accent)' }}
                      />
                      {mode === 'mention' ? '仅@触发' : mode === 'phase' ? '阶段触发' : '全程监听'}
                    </label>
                  ))}
                </div>
              </div>

              <div
                style={{
                  borderTop: '1px solid var(--border-default)',
                  paddingTop: 'var(--space-4)',
                }}
              >
                <div
                  style={{
                    fontSize: 'var(--text-xs)',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    marginBottom: 'var(--space-3)',
                  }}
                >
                  LegalAgent
                </div>
                <div style={{ marginBottom: 'var(--space-2)' }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      marginBottom: 'var(--space-1)',
                    }}
                  >
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>活跃度</span>
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--accent)' }}>{legalAgent.activity}%</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={legalAgent.activity}
                    onChange={(e) =>
                      setLegalAgent({ ...legalAgent, activity: Number(e.target.value) })
                    }
                    style={{
                      width: '100%',
                      accentColor: 'var(--accent)',
                      height: 4,
                      cursor: 'pointer',
                    }}
                  />
                </div>
                <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
                  {(['mention', 'phase', 'full'] as const).map((mode) => (
                    <label
                      key={mode}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--space-1)',
                        fontSize: 'var(--text-xs)',
                        color:
                          legalAgent.triggerMode === mode
                            ? 'var(--accent)'
                            : 'var(--text-muted)',
                        cursor: 'pointer',
                      }}
                    >
                      <input
                        type="radio"
                        name="legalAgent_trigger"
                        checked={legalAgent.triggerMode === mode}
                        onChange={() =>
                          setLegalAgent({ ...legalAgent, triggerMode: mode })
                        }
                        style={{ accentColor: 'var(--accent)' }}
                      />
                      {mode === 'mention' ? '仅@触发' : mode === 'phase' ? '阶段触发' : '全程监听'}
                    </label>
                  ))}
                </div>
              </div>

              <div
                style={{
                  borderTop: '1px solid var(--border-default)',
                  paddingTop: 'var(--space-4)',
                }}
              >
                <div
                  style={{
                    fontSize: 'var(--text-xs)',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    marginBottom: 'var(--space-3)',
                  }}
                >
                  全局AI触发模式
                </div>
                <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
                  {(['mention', 'phase', 'full'] as const).map((mode) => (
                    <label
                      key={mode}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--space-1)',
                        fontSize: 'var(--text-xs)',
                        color:
                          globalTrigger === mode ? 'var(--accent)' : 'var(--text-muted)',
                        cursor: 'pointer',
                      }}
                    >
                      <input
                        type="radio"
                        name="global_trigger"
                        checked={globalTrigger === mode}
                        onChange={() => setGlobalTrigger(mode)}
                        style={{ accentColor: 'var(--accent)' }}
                      />
                      {mode === 'mention' ? '仅@触发' : mode === 'phase' ? '阶段触发' : '全程监听'}
                    </label>
                  ))}
                </div>
              </div>
            </>
          )}

          {isOwner && !isOps && (
            <div
              style={{
                fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)',
                lineHeight: 1.6,
              }}
            >
              AI代理正在后台运行。可通过下方按钮暂停所有 AI 建议。
            </div>
          )}

          {isReviewer && (
            <div
              style={{
                fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)',
                lineHeight: 1.6,
              }}
            >
              状态：AI 系统运行中。作为审查者，您可以查看 AI 摘要，但无法更改配置。
            </div>
          )}

          {isOwner && (
            <button
              onClick={handleEStopClick}
              disabled={isEStopped}
              style={{
                width: '100%',
                background: isEStopped ? 'var(--bg-subtle)' : 'var(--danger)',
                color: isEStopped ? 'var(--text-muted)' : '#fff',
                border: 'none',
                padding: 'var(--space-4) var(--space-3)',
                borderRadius: 'var(--radius-md)',
                cursor: isEStopped ? 'not-allowed' : 'pointer',
                fontSize: 'var(--text-lg)',
                fontWeight: 700,
                letterSpacing: 2,
                transition: 'background 0.2s',
              }}
            >
              {isEStopped ? '已暂停 AI 建议' : '暂停所有 AI 建议'}
            </button>
          )}
        </div>
      </div>

      {showConfirm && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 600,
            background: 'rgba(0,0,0,0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          onClick={() => setShowConfirm(false)}
        >
          <div
            style={{
              background: 'var(--bg-surface)',
              border: '2px solid var(--danger)',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--space-6)',
              maxWidth: 400,
              textAlign: 'center',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                fontSize: 'var(--text-3xl)',
                fontWeight: 700,
                color: 'var(--danger)',
                marginBottom: 'var(--space-4)',
              }}
            >
              ⚠ 确认操作
            </div>
            <div
              style={{
                fontSize: 'var(--text-lg)',
                color: 'var(--danger)',
                fontWeight: 700,
                marginBottom: 'var(--space-3)',
                letterSpacing: 2,
              }}
            >
              暂停所有 AI 建议
            </div>
            <div
              style={{
                fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)',
                marginBottom: 'var(--space-5)',
                lineHeight: 1.6,
              }}
            >
              此操作将立即停止所有 AI 代理的活动。已提交但未审批的提案将被保留，AI 不再主动响应直到手动恢复。
            </div>
            <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'center' }}>
              <button
                onClick={() => setShowConfirm(false)}
                style={{
                  background: 'var(--bg-subtle)',
                  color: 'var(--text-secondary)',
                  border: '1px solid var(--border-default)',
                  padding: 'var(--space-2) var(--space-5)',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                  fontSize: 'var(--text-sm)',
                }}
              >
                取消
              </button>
              <button
                onClick={confirmEStop}
                style={{
                  background: 'var(--danger)',
                  color: '#fff',
                  border: 'none',
                  padding: 'var(--space-2) var(--space-5)',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                  fontSize: 'var(--text-sm)',
                  fontWeight: 700,
                }}
              >
                确认暂停
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default SovereignConsole
