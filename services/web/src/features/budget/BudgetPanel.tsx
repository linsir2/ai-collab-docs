import { type FC } from 'react'

interface TokenStat {
  doc_name: string
  tokens: number
  percentage: number
  proposals: number
  trend: 'up' | 'down' | 'flat'
}

interface BudgetPanelProps {
  teamMonthlyUsed?: number
  teamMonthlyTotal?: number
  publicPoolUsed?: number
  publicPoolTotal?: number
  privatePoolUsed?: number
  privatePoolTotal?: number
  globalPrivateUsed?: number
  globalPrivateTotal?: number
  tokenStats?: TokenStat[]
}

const MOCK_TOKEN_STATS: TokenStat[] = [
  { doc_name: '系统架构设计文档', tokens: 124500, percentage: 30.4, proposals: 15, trend: 'up' },
  { doc_name: 'API 接口规范', tokens: 98500, percentage: 24.0, proposals: 8, trend: 'flat' },
  { doc_name: '安全合规策略', tokens: 76200, percentage: 18.6, proposals: 12, trend: 'up' },
  { doc_name: '数据治理规范', tokens: 54800, percentage: 13.4, proposals: 6, trend: 'down' },
  { doc_name: '运维手册', tokens: 32100, percentage: 7.8, proposals: 4, trend: 'down' },
  { doc_name: '用户隐私政策', tokens: 23900, percentage: 5.8, proposals: 3, trend: 'flat' },
]

function formatTokens(n: number): string {
  if (n >= 1000000) return `${(n / 1000000).toFixed(2)}M`
  if (n >= 1000) return `${(n / 1000).toFixed(0)}K`
  return String(n)
}

const BudgetPanel: FC<BudgetPanelProps> = ({
  teamMonthlyUsed = 410000,
  teamMonthlyTotal = 500000,
  publicPoolUsed = 643,
  publicPoolTotal = 800,
  privatePoolUsed = 127,
  privatePoolTotal = 400,
  globalPrivateUsed = 345,
  globalPrivateTotal = 1200,
  tokenStats: propTokenStats,
}) => {
  const tokenStats = propTokenStats ?? MOCK_TOKEN_STATS
  const teamPct = (teamMonthlyUsed / teamMonthlyTotal) * 100

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'var(--bg-page)',
        padding: 'var(--space-6)',
      }}
    >
      <h1
        style={{
          margin: '0 0 var(--space-6)',
          fontSize: 'var(--text-3xl)',
          fontWeight: 700,
          color: 'var(--text-primary)',
        }}
      >
        预算与成本控制
      </h1>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
        }}
      >
        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-5)',
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
            团队月度Token
          </div>

          <div style={{ marginBottom: 'var(--space-3)' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginBottom: 'var(--space-2)',
              }}
            >
              <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>
                已用 {formatTokens(teamMonthlyUsed)} / 总额 {formatTokens(teamMonthlyTotal)}
              </span>
              <span
                style={{
                  fontSize: 'var(--text-sm)',
                  fontWeight: 600,
                  color: teamPct > 90 ? 'var(--danger)' : teamPct > 75 ? 'var(--warning)' : 'var(--success)',
                }}
              >
                {teamPct.toFixed(0)}%
              </span>
            </div>
            <div
              style={{
                width: '100%',
                height: 8,
                background: 'var(--bg-elevated)',
                borderRadius: 'var(--radius-md)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${teamPct}%`,
                  height: '100%',
                  background: teamPct > 90 ? 'var(--danger)' : teamPct > 75 ? 'var(--warning)' : 'var(--accent)',
                  borderRadius: 'var(--radius-md)',
                  transition: 'width 0.3s',
                }}
              />
            </div>
          </div>

          <div
            style={{
              fontSize: 'var(--text-xs)',
              color: 'var(--text-muted)',
              marginBottom: 'var(--space-3)',
            }}
          >
            预计耗尽: 6月22日 — 剩余 4 天
          </div>

          <button
            style={{
              background: 'var(--bg-elevated)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border-default)',
              padding: 'var(--space-2) var(--space-4)',
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              fontSize: 'var(--text-sm)',
            }}
          >
            调整预算上限
          </button>
        </div>

        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-5)',
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
            提案池容量
          </div>

          {[
            {
              label: '公共池', used: publicPoolUsed, total: publicPoolTotal,
            },
            {
              label: '私有池', used: privatePoolUsed, total: privatePoolTotal,
            },
            {
              label: '全局私有', used: globalPrivateUsed, total: globalPrivateTotal,
            },
          ].map((pool) => {
            const pct = (pool.used / pool.total) * 100
            return (
              <div key={pool.label} style={{ marginBottom: 'var(--space-3)' }}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: 'var(--space-1)',
                    fontSize: 'var(--text-sm)',
                  }}
                >
                  <span style={{ color: 'var(--text-secondary)' }}>{pool.label}</span>
                  <span
                    style={{
                      color:
                        pct > 80
                          ? 'var(--warning)'
                          : 'var(--success)',
                      fontSize: 'var(--text-xs)',
                    }}
                  >
                    {pool.used}/{pool.total} ({pct.toFixed(0)}%)
                  </span>
                </div>
                <div
                  style={{
                    width: '100%',
                    height: 6,
                    background: 'var(--bg-elevated)',
                    borderRadius: 'var(--radius-md)',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width: `${pct}%`,
                      height: '100%',
                      background: pct > 80 ? 'var(--warning)' : 'var(--success)',
                      borderRadius: 'var(--radius-md)',
                      transition: 'width 0.3s',
                    }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          marginBottom: 'var(--space-6)',
        }}
      >
        <div
          style={{
            padding: 'var(--space-4)',
            borderBottom: '1px solid var(--border-default)',
            fontSize: 'var(--text-sm)',
            fontWeight: 600,
            color: 'var(--text-primary)',
          }}
        >
          单文档Token消耗排行
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 140px 100px 80px 80px',
            background: 'var(--bg-elevated)',
            borderBottom: '1px solid var(--border-default)',
          }}
        >
          {['文档名称', 'Token消耗', '占比', '提案数', '趋势'].map((h) => (
            <div
              key={h}
              style={{
                padding: 'var(--space-2) var(--space-4)',
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
              }}
            >
              {h}
            </div>
          ))}
        </div>

        {tokenStats.map((stat, idx) => (
          <div
            key={stat.doc_name}
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 140px 100px 80px 80px',
              background: idx % 2 === 0 ? 'var(--bg-surface)' : 'var(--bg-elevated)',
              borderBottom: '1px solid var(--border-default)',
            }}
          >
            <div
              style={{
                padding: 'var(--space-3) var(--space-4)',
                fontSize: 'var(--text-sm)',
                color: 'var(--text-primary)',
              }}
            >
              {stat.doc_name}
            </div>
            <div
              style={{
                padding: 'var(--space-3) var(--space-4)',
                fontFamily: 'var(--font-mono)',
                fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)',
              }}
            >
              {formatTokens(stat.tokens)}
            </div>
            <div
              style={{
                padding: 'var(--space-3) var(--space-4)',
                fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)',
              }}
            >
              {stat.percentage.toFixed(1)}%
            </div>
            <div
              style={{
                padding: 'var(--space-3) var(--space-4)',
                fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)',
              }}
            >
              {stat.proposals}
            </div>
            <div
              style={{
                padding: 'var(--space-3) var(--space-4)',
                fontSize: 'var(--text-sm)',
                color: stat.trend === 'up' ? 'var(--danger)' : stat.trend === 'down' ? 'var(--success)' : 'var(--text-muted)',
              }}
            >
              {stat.trend === 'up' ? '↑ UP' : stat.trend === 'down' ? '↓ DOWN' : '—'}
            </div>
          </div>
        ))}
      </div>

      <div
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-5)',
        }}
      >
        <div
          style={{
            fontSize: 'var(--text-sm)',
            fontWeight: 600,
            color: 'var(--text-primary)',
            marginBottom: 'var(--space-4)',
          }}
        >
          降级与熔断状态
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
          <div
            style={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4)',
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
              模型层级
            </div>

            <div style={{ marginBottom: 'var(--space-3)' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-2)',
                  marginBottom: 'var(--space-2)',
                }}
              >
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: 'var(--success)',
                  }}
                />
                <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-primary)' }}>
                  qwen-max <span style={{ color: 'var(--success)', fontSize: 'var(--text-xs)' }}>(正常)</span>
                </span>
              </div>
              <div
                style={{
                  fontSize: 'var(--text-xs)',
                  color: 'var(--text-muted)',
                  paddingLeft: 'var(--space-4)',
                }}
              >
                降级触发: Token 95% → qwen-turbo
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-2)',
                marginBottom: 'var(--space-2)',
              }}
            >
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: 'var(--text-muted)',
                }}
              />
              <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
                qwen-turbo (待命)
              </span>
            </div>
            <div
              style={{
                fontSize: 'var(--text-xs)',
                color: 'var(--text-muted)',
                paddingLeft: 'var(--space-4)',
              }}
            >
              备用模型，降级时自动切换
            </div>
          </div>

          <div
            style={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4)',
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
              熔断状态
            </div>

            <div style={{ marginBottom: 'var(--space-3)' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-2)',
                  marginBottom: 'var(--space-2)',
                }}
              >
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: 'var(--success)',
                  }}
                />
                <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-primary)' }}>
                  正常运行
                </span>
              </div>
              <div
                style={{
                  fontSize: 'var(--text-xs)',
                  color: 'var(--text-muted)',
                  paddingLeft: 'var(--space-4)',
                }}
              >
                熔断触发: 连续5次失败 → 暂停30分钟
              </div>
            </div>

            <div
              style={{
                background: 'var(--success-bg)',
                padding: 'var(--space-2) var(--space-3)',
                borderRadius: 'var(--radius-md)',
                display: 'inline-block',
              }}
            >
              <span
                style={{
                  fontSize: 'var(--text-sm)',
                  color: 'var(--success)',
                  fontWeight: 500,
                }}
              >
                熔断计数: 0/5
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default BudgetPanel
export type { TokenStat }
