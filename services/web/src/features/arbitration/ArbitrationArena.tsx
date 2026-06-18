import { useState, useEffect, type FC } from 'react'
import { useAuthStore } from '../../shared/store/authStore'
import { canDoInDocument } from '../../shared/authz'

interface ArbitrationItem {
  id: number
  doc_id: string
  ai_role_a: string
  ai_role_b: string
  trust_score_a: number
  trust_score_b: number
  proposal_content_a: string
  proposal_content_b: string
  rationale_a: string
  rationale_b: string
  original_text: string
  conflict_description: string
  divergence_points: string[]
  resolved: boolean
  resolution?: string
  resolved_at?: string
}

interface ArbitrationArenaProps {
  docId: string
  onResolve: (
    arbitrationId: number,
    choice: 'a' | 'b' | 'reject_all',
    solidify: boolean
  ) => void
  onClose: () => void
}

const MOCK_ARBITRATIONS: ArbitrationItem[] = [
  {
    id: 1,
    doc_id: 'doc-1',
    ai_role_a: 'TechReviewer',
    ai_role_b: 'LegalAgent',
    trust_score_a: 87,
    trust_score_b: 92,
    proposal_content_a: '建议将系统架构从单体迁移到微服务，以提高可扩展性和团队并行开发效率。本方案推荐使用 Kubernetes 作为编排平台，配合 gRPC 进行服务间通信。',
    proposal_content_b: '警告：迁移到微服务架构可能违反现有的数据驻留合规要求。根据 GDPR 第 28 条，数据处理者变更需提前通知数据控制方。建议在架构调整前完成合规审计。',
    rationale_a: '微服务架构提升部署灵活性\n降低模块间耦合度\n支持独立扩缩容\n业界主流实践',
    rationale_b: 'GDPR合规风险需优先评估\n数据跨境传输存在法律风险\n建议保留单体核心，渐进式拆分\n需法务团队审核全部数据流',
    original_text: '当前系统使用单体架构部署，所有服务运行在同一进程中。',
    conflict_description: 'TechReviewer 和 LegalAgent 对系统架构演进方向存在根本分歧：技术优化 vs 合规风险。',
    divergence_points: ['架构迁移必要性', '合规风险评估优先级', '实施路径选择'],
    resolved: false,
  },
  {
    id: 2,
    doc_id: 'doc-1',
    ai_role_a: 'TechReviewer',
    ai_role_b: 'LegalAgent',
    trust_score_a: 85,
    trust_score_b: 90,
    proposal_content_a: '用户数据缓存策略应使用 Redis 集群，TTL 设置为 24 小时，以减轻数据库压力。',
    proposal_content_b: '用户数据缓存 24 小时可能违反《个人信息保护法》关于数据最小化存储原则。建议 TTL 不超过 2 小时，且需要用户明确授权。',
    rationale_a: '24小时缓存大幅降低DB负载\n提升API响应速度\n行业标准做法',
    rationale_b: '个人信息保护法要求最小化存储\n缓存时长需在隐私政策中披露\n用户有权要求清除缓存数据',
    original_text: 'API 直接查询数据库，无缓存层。',
    conflict_description: '缓存策略在技术性能和隐私合规之间存在冲突。',
    divergence_points: ['缓存时长', '用户授权要求', '隐私政策更新'],
    resolved: false,
  },
  {
    id: 3,
    doc_id: 'doc-1',
    ai_role_a: 'TechReviewer',
    ai_role_b: 'LegalAgent',
    trust_score_a: 88,
    trust_score_b: 91,
    proposal_content_a: '日志系统建议使用结构化日志，包含完整的请求链路追踪。',
    proposal_content_b: '结构化日志中不能包含用户 PII 数据，需在写入前脱敏。建议增加日志分级和自动过期策略。',
    rationale_a: '结构化日志便于检索分析\n链路追踪提升排障效率',
    rationale_b: 'PII数据不得进入日志\n日志保留期限需符合合规要求',
    original_text: '使用文本格式日志，无结构化输出。',
    conflict_description: '日志方案在功能性和合规性之间需要平衡。',
    divergence_points: ['日志内容范围', '数据脱敏要求', '保留策略'],
    resolved: true,
    resolution: '采纳 LegalAgent 方案，日志结构化但先脱敏',
    resolved_at: '2026-06-17 14:30:00',
  },
  {
    id: 4,
    doc_id: 'doc-1',
    ai_role_a: 'TechReviewer',
    ai_role_b: 'LegalAgent',
    trust_score_a: 90,
    trust_score_b: 88,
    proposal_content_a: 'API 限流策略采用令牌桶算法，每用户 100 req/s。',
    proposal_content_b: '限流策略不应区分付费/免费用户，否则可能构成歧视性服务。建议统一限流阈值。',
    rationale_a: '令牌桶平滑流量峰值\n差异化限流保护核心用户',
    rationale_b: '差异化服务需有合理依据\n避免被认定为不公平商业行为',
    original_text: '当前无限流机制。',
    conflict_description: '限流策略在技术和公平性之间存在分歧。',
    divergence_points: ['限流算法选择', '差异化策略合法性', '阈值设定依据'],
    resolved: true,
    resolution: '统一限流 50 req/s，不分用户等级',
    resolved_at: '2026-06-16 09:15:00',
  },
]

const ArbitrationArena: FC<ArbitrationArenaProps> = ({ docId: _docId, onResolve, onClose }) => {
  const [arbitrations, setArbitrations] = useState<ArbitrationItem[]>([])
  const [activeTab, setActiveTab] = useState<'pending' | 'resolved'>('pending')
  const [solidify, setSolidify] = useState(true)
  const docRole = useAuthStore((s) => s.docRole)
  const canResolve = canDoInDocument(docRole, 'resolve_arbitration')

  useEffect(() => {
    setArbitrations(MOCK_ARBITRATIONS)
  }, [])

  const pending = arbitrations.filter((a) => !a.resolved)
  const resolved = arbitrations.filter((a) => a.resolved)
  const currentList = activeTab === 'pending' ? pending : resolved
  const current = currentList[0] ?? null

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'var(--bg-page)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div
        style={{
          borderBottom: '1px solid var(--border-default)',
          background: 'var(--bg-surface)',
          padding: 'var(--space-4) var(--space-6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: 'var(--text-3xl)',
            fontWeight: 700,
            color: 'var(--accent)',
          }}
        >
          ⚡ CONFLICT 人类最高仲裁法庭
        </h1>
        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--accent)',
            cursor: 'pointer',
            fontSize: 'var(--text-sm)',
            textDecoration: 'underline',
          }}
        >
          关闭仲裁台
        </button>
      </div>

      {current && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div
            style={{
              flex: 1,
              display: 'flex',
              overflow: 'hidden',
              minHeight: 0,
            }}
          >
            <div
              style={{
                flex: 1,
                padding: 'var(--space-6)',
                borderRight: '1px solid var(--border-default)',
                overflow: 'auto',
              }}
            >
              <h2
                style={{
                  fontSize: 'var(--text-xl)',
                  color: 'var(--info)',
                  margin: '0 0 var(--space-4)',
                  fontWeight: 600,
                }}
              >
                攻方: {current.ai_role_a}
              </h2>

              <div
                style={{
                  background: 'var(--info-bg)',
                  color: 'var(--info)',
                  padding: 'var(--space-2) var(--space-3)',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: 'var(--space-4)',
                  fontSize: 'var(--text-sm)',
                  display: 'inline-block',
                }}
              >
                信任分: {current.trust_score_a}
              </div>

              <div style={{ marginBottom: 'var(--space-4)' }}>
                <div
                  style={{
                    fontSize: 'var(--text-xs)',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    marginBottom: 'var(--space-2)',
                  }}
                >
                  提案内容
                </div>
                <div
                  style={{
                    background: 'var(--bg-elevated)',
                    padding: 'var(--space-4)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: 'var(--text-sm)',
                    lineHeight: 1.7,
                    color: 'var(--text-primary)',
                    border: '1px solid var(--border-default)',
                  }}
                >
                  {current.proposal_content_a}
                </div>
              </div>

              <div style={{ marginBottom: 'var(--space-4)' }}>
                <div
                  style={{
                    fontSize: 'var(--text-xs)',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    marginBottom: 'var(--space-2)',
                  }}
                >
                  核心论点
                </div>
                <ul
                  style={{
                    listStyle: 'disc',
                    paddingLeft: 'var(--space-5)',
                    margin: 0,
                    fontSize: 'var(--text-sm)',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.8,
                  }}
                >
                  {current.rationale_a.split('\n').map((line, i) => (
                    <li key={i}>{line}</li>
                  ))}
                </ul>
              </div>

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
                合理
              </span>
            </div>

            <div
              style={{
                flex: '0 0 300px',
                padding: 'var(--space-6) var(--space-4)',
                background: 'var(--bg-surface)',
                borderRight: '1px solid var(--border-default)',
                overflow: 'auto',
              }}
            >
              <h3
                style={{
                  fontSize: 'var(--text-lg)',
                  color: 'var(--accent)',
                  margin: '0 0 var(--space-4)',
                  fontWeight: 600,
                  textAlign: 'center',
                }}
              >
                中央对比区
              </h3>

              <div style={{ marginBottom: 'var(--space-4)' }}>
                <div
                  style={{
                    fontSize: 'var(--text-xs)',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    marginBottom: 'var(--space-2)',
                  }}
                >
                  原始文本
                </div>
                <div
                  style={{
                    background: 'var(--bg-elevated)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: 'var(--text-sm)',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.6,
                    border: '1px solid var(--border-default)',
                  }}
                >
                  {current.original_text}
                </div>
              </div>

              <div style={{ marginBottom: 'var(--space-4)' }}>
                <div
                  style={{
                    fontSize: 'var(--text-xs)',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    marginBottom: 'var(--space-2)',
                  }}
                >
                  冲突描述
                </div>
                <div
                  style={{
                    background: 'var(--warning-bg)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: 'var(--text-sm)',
                    color: 'var(--warning)',
                    lineHeight: 1.6,
                    border: '1px solid rgba(228,87,61,0.3)',
                  }}
                >
                  {current.conflict_description}
                </div>
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
                  关键分歧点
                </div>
                {current.divergence_points.map((point, i) => (
                  <div
                    key={i}
                    style={{
                      background: 'var(--bg-elevated)',
                      padding: 'var(--space-2) var(--space-3)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: 'var(--text-sm)',
                      color: 'var(--text-primary)',
                      marginBottom: 'var(--space-1)',
                      border: '1px solid var(--border-default)',
                    }}
                  >
                    • {point}
                  </div>
                ))}
              </div>

              {current.resolved && (
                <div
                  style={{
                    marginTop: 'var(--space-4)',
                    background: 'var(--success-bg)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid rgba(52,211,153,0.3)',
                  }}
                >
                  <div
                    style={{
                      fontSize: 'var(--text-xs)',
                      fontWeight: 600,
                      color: 'var(--success)',
                      marginBottom: 'var(--space-1)',
                    }}
                  >
                    已解决
                  </div>
                  <div
                    style={{ fontSize: 'var(--text-sm)', color: 'var(--text-primary)' }}
                  >
                    {current.resolution}
                  </div>
                  <div
                    style={{
                      fontSize: 'var(--text-xs)',
                      color: 'var(--text-muted)',
                      marginTop: 'var(--space-1)',
                    }}
                  >
                    {current.resolved_at}
                  </div>
                </div>
              )}
            </div>

            <div
              style={{
                flex: 1,
                padding: 'var(--space-6)',
                overflow: 'auto',
              }}
            >
              <h2
                style={{
                  fontSize: 'var(--text-xl)',
                  color: 'var(--info)',
                  margin: '0 0 var(--space-4)',
                  fontWeight: 600,
                }}
              >
                辩方: {current.ai_role_b}
              </h2>

              <div
                style={{
                  background: 'var(--info-bg)',
                  color: 'var(--info)',
                  padding: 'var(--space-2) var(--space-3)',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: 'var(--space-4)',
                  fontSize: 'var(--text-sm)',
                  display: 'inline-block',
                }}
              >
                信任分: {current.trust_score_b}
              </div>

              <div style={{ marginBottom: 'var(--space-4)' }}>
                <div
                  style={{
                    fontSize: 'var(--text-xs)',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    marginBottom: 'var(--space-2)',
                  }}
                >
                  提案内容
                </div>
                <div
                  style={{
                    background: 'var(--bg-elevated)',
                    padding: 'var(--space-4)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: 'var(--text-sm)',
                    lineHeight: 1.7,
                    color: 'var(--text-primary)',
                    border: '1px solid var(--border-default)',
                  }}
                >
                  {current.proposal_content_b}
                </div>
              </div>

              <div style={{ marginBottom: 'var(--space-4)' }}>
                <div
                  style={{
                    fontSize: 'var(--text-xs)',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    marginBottom: 'var(--space-2)',
                  }}
                >
                  核心论点
                </div>
                <ul
                  style={{
                    listStyle: 'disc',
                    paddingLeft: 'var(--space-5)',
                    margin: 0,
                    fontSize: 'var(--text-sm)',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.8,
                  }}
                >
                  {current.rationale_b.split('\n').map((line, i) => (
                    <li key={i}>{line}</li>
                  ))}
                </ul>
              </div>

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
                合理
              </span>
            </div>
          </div>

          {!current.resolved && (
            <div
              style={{
                borderTop: '1px solid var(--border-default)',
                background: 'var(--bg-surface)',
                padding: 'var(--space-4) var(--space-6)',
                flexShrink: 0,
              }}
            >
              <div
                style={{
                  fontSize: 'var(--text-sm)',
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                  marginBottom: 'var(--space-3)',
                }}
              >
                最高裁决
              </div>
              {canResolve ? (
                <>
                  <div
                    style={{
                      display: 'flex',
                      gap: 'var(--space-4)',
                      marginBottom: 'var(--space-3)',
                    }}
                  >
                    <button
                      onClick={() => onResolve(current.id, 'a', solidify)}
                      style={{
                        flex: 1,
                        background: 'var(--accent)',
                        color: '#000',
                        border: 'none',
                        padding: 'var(--space-3) var(--space-4)',
                        borderRadius: 'var(--radius-md)',
                        cursor: 'pointer',
                        fontSize: 'var(--text-base)',
                        fontWeight: 600,
                      }}
                    >
                      采纳 {current.ai_role_a}
                    </button>
                    <button
                      onClick={() => onResolve(current.id, 'reject_all', solidify)}
                      style={{
                        flex: 1,
                        background: 'var(--danger-bg)',
                        color: 'var(--danger)',
                        border: '1px solid var(--danger)',
                        padding: 'var(--space-3) var(--space-4)',
                        borderRadius: 'var(--radius-md)',
                        cursor: 'pointer',
                        fontSize: 'var(--text-base)',
                        fontWeight: 600,
                      }}
                    >
                      均拒绝
                    </button>
                    <button
                      onClick={() => onResolve(current.id, 'b', solidify)}
                      style={{
                        flex: 1,
                        background: 'var(--accent)',
                        color: '#000',
                        border: 'none',
                        padding: 'var(--space-3) var(--space-4)',
                        borderRadius: 'var(--radius-md)',
                        cursor: 'pointer',
                        fontSize: 'var(--text-base)',
                        fontWeight: 600,
                      }}
                    >
                      采纳 {current.ai_role_b}
                    </button>
                  </div>
                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 'var(--space-2)',
                      fontSize: 'var(--text-sm)',
                      color: 'var(--text-secondary)',
                      cursor: 'pointer',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={solidify}
                      onChange={(e) => setSolidify(e.target.checked)}
                      style={{ accentColor: 'var(--accent)' }}
                    />
                    将此裁决同步固化为项目全局记忆
                  </label>
                </>
              ) : (
                <div
                  style={{
                    fontSize: 'var(--text-sm)',
                    color: 'var(--text-muted)',
                    textAlign: 'center',
                    padding: 'var(--space-3)',
                  }}
                >
                  您当前角色无仲裁权限
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <div
        style={{
          borderTop: '1px solid var(--border-default)',
          display: 'flex',
          flexShrink: 0,
        }}
      >
        <button
          onClick={() => setActiveTab('pending')}
          style={{
            flex: 1,
            padding: 'var(--space-3)',
            background: activeTab === 'pending' ? 'var(--bg-elevated)' : 'var(--bg-surface)',
            border: 'none',
            color: activeTab === 'pending' ? 'var(--accent)' : 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: 'var(--text-sm)',
            fontWeight: activeTab === 'pending' ? 600 : 400,
            borderBottom: activeTab === 'pending' ? '2px solid var(--accent)' : '2px solid transparent',
          }}
        >
          待解决({pending.length})
        </button>
        <button
          onClick={() => setActiveTab('resolved')}
          style={{
            flex: 1,
            padding: 'var(--space-3)',
            background: activeTab === 'resolved' ? 'var(--bg-elevated)' : 'var(--bg-surface)',
            border: 'none',
            color: activeTab === 'resolved' ? 'var(--accent)' : 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: 'var(--text-sm)',
            fontWeight: activeTab === 'resolved' ? 600 : 400,
            borderBottom: activeTab === 'resolved' ? '2px solid var(--accent)' : '2px solid transparent',
          }}
        >
          已解决({resolved.length})
        </button>
      </div>

      {!current && (
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--text-muted)',
            fontSize: 'var(--text-lg)',
          }}
        >
          {activeTab === 'pending' ? '暂无待解决的仲裁' : '暂无已解决的仲裁记录'}
        </div>
      )}
    </div>
  )
}

export default ArbitrationArena
export type { ArbitrationItem }
