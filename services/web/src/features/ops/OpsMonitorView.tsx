import { useAuthStore } from '../../shared/store/authStore';

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-default)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-5)',
        flex: 1,
        minWidth: 0,
      }}
    >
      <h3
        style={{
          fontSize: 'var(--text-lg)',
          fontWeight: 700,
          margin: 0,
          marginBottom: 'var(--space-3)',
          color: 'var(--text-primary)',
        }}
      >
        {title}
      </h3>
      {children}
    </div>
  );
}

const LLM_SERVICES = [
  { name: 'primary-gpt', status: 'healthy', latency_ms: 243, rpm: 1823, error_rate: 0.12 },
  { name: 'secondary-claude', status: 'healthy', latency_ms: 311, rpm: 912, error_rate: 0.04 },
  { name: 'fallback-local', status: 'degraded', latency_ms: 982, rpm: 128, error_rate: 3.21 },
];

const MEMORY_ISSUES = [
  { id: 'mem-001', type: 'vector-drift', score: 0.72, affected_docs: 18, last_occurrence: '2026-06-18T08:42:11Z' },
  { id: 'mem-002', type: 'index-stale', score: 0.48, affected_docs: 6, last_occurrence: '2026-06-18T07:15:03Z' },
  { id: 'mem-003', type: 'embedding-mismatch', score: 0.91, affected_docs: 3, last_occurrence: '2026-06-18T06:03:57Z' },
];

export default function OpsMonitorView() {
  const user = useAuthStore((s) => s.user);

  return (
    <div style={{ padding: 'var(--space-6)' }}>
      <div
        style={{
          background: 'linear-gradient(90deg, var(--danger-subtle), var(--bg-surface))',
          border: '1px solid var(--danger)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-4) var(--space-5)',
          marginBottom: 'var(--space-5)',
          fontSize: 'var(--text-sm)',
          color: 'var(--text-secondary)',
        }}
      >
        <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>
          全局身份：运维技术账号
        </div>
        <div>
          当前账号：{user?.display_name ?? '—'} · 此视图包含原始技术数据，请注意受控使用
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 'var(--space-4)',
        }}
      >
        <Card title="LLM 服务监控">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            {LLM_SERVICES.map((svc) => (
              <div
                key={svc.name}
                style={{
                  padding: 'var(--space-3)',
                  background: 'var(--bg-page)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--text-sm)',
                  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: 'var(--space-2)',
                  }}
                >
                  <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{svc.name}</span>
                  <span
                    style={{
                      color: svc.status === 'healthy' ? 'var(--success)' : 'var(--warning)',
                      fontSize: 'var(--text-xs)',
                      textTransform: 'uppercase',
                      letterSpacing: 0.5,
                    }}
                  >
                    {svc.status}
                  </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-1)', color: 'var(--text-secondary)' }}>
                  <span>latency: {svc.latency_ms}ms</span>
                  <span>rpm: {svc.rpm}</span>
                  <span>error_rate: {svc.error_rate}%</span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="记忆修复">
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--space-3)', fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>
            检测到 {MEMORY_ISSUES.length} 项记忆异常
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            {MEMORY_ISSUES.map((issue) => (
              <div
                key={issue.id}
                style={{
                  padding: 'var(--space-3)',
                  background: 'var(--bg-page)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--text-xs)',
                  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
                  color: 'var(--text-secondary)',
                }}
              >
                <div style={{ color: 'var(--text-primary)', fontWeight: 600, marginBottom: 4 }}>
                  {issue.id} · {issue.type}
                </div>
                <div>drift_score: {issue.score.toFixed(3)}</div>
                <div>affected_docs: {issue.affected_docs}</div>
                <div>last_occurrence: {issue.last_occurrence}</div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="性能指标">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)',
              }}
            >
              <span>p50_latency</span>
              <span style={{ color: 'var(--text-primary)' }}>187 ms</span>
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)',
              }}
            >
              <span>p95_latency</span>
              <span style={{ color: 'var(--text-primary)' }}>842 ms</span>
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)',
              }}
            >
              <span>p99_latency</span>
              <span style={{ color: 'var(--warning)' }}>2,318 ms</span>
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)',
              }}
            >
              <span>request_count (24h)</span>
              <span style={{ color: 'var(--text-primary)' }}>48,921</span>
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)',
              }}
            >
              <span>token_consumption (24h)</span>
              <span style={{ color: 'var(--text-primary)' }}>112,482,190</span>
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)',
              }}
            >
              <span>uptime (30d)</span>
              <span style={{ color: 'var(--success)' }}>99.873%</span>
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)',
              }}
            >
              <span>active_users</span>
              <span style={{ color: 'var(--text-primary)' }}>342</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
