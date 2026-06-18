import { useAuthStore } from '../../shared/store/authStore';

const SAMPLE_MEMBERS = [
  { name: '李编辑', role: '主编辑', email: 'editor@example.com' },
  { name: '王审查', role: '审查者', email: 'reviewer@example.com' },
  { name: '张只读', role: '只读成员', email: 'reader@example.com' },
];

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

export default function TeamManagementView() {
  const user = useAuthStore((s) => s.user);

  return (
    <div style={{ padding: 'var(--space-6)' }}>
      <div
        style={{
          background: 'linear-gradient(90deg, var(--accent-subtle), var(--bg-surface))',
          border: '1px solid var(--accent)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-4) var(--space-5)',
          marginBottom: 'var(--space-5)',
          fontSize: 'var(--text-sm)',
          color: 'var(--text-secondary)',
        }}
      >
        <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>
          全局身份：团队管理员
        </div>
        <div>
          当前账号：{user?.display_name ?? '—'} · 该视图用于团队成员与配额管理
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 'var(--space-4)',
        }}
      >
        <Card title="成员管理">
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--space-3)' }}>
            共 {SAMPLE_MEMBERS.length} 位成员
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            {SAMPLE_MEMBERS.map((m) => (
              <div
                key={m.email}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: 'var(--space-2) var(--space-3)',
                  background: 'var(--bg-page)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--text-sm)',
                }}
              >
                <div>
                  <div style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{m.name}</div>
                  <div style={{ color: 'var(--text-muted)', fontSize: 'var(--text-xs)' }}>{m.email}</div>
                </div>
                <span
                  style={{
                    fontSize: 'var(--text-xs)',
                    color: 'var(--text-secondary)',
                    background: 'var(--bg-elevated)',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  {m.role}
                </span>
              </div>
            ))}
          </div>
        </Card>

        <Card title="预算配置">
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--space-3)' }}>
            团队每月 LLM 调用预算
          </div>
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-2)',
              fontSize: 'var(--text-sm)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>月度预算</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>10,000,000 tokens</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>已使用</span>
              <span style={{ color: 'var(--text-primary)' }}>3,421,890 tokens</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>剩余</span>
              <span style={{ color: 'var(--success)', fontWeight: 600 }}>6,578,110 tokens</span>
            </div>
          </div>
          <div
            style={{
              marginTop: 'var(--space-3)',
              height: 6,
              background: 'var(--bg-page)',
              borderRadius: 'var(--radius-sm)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: '34%',
                height: '100%',
                background: 'var(--accent)',
              }}
            />
          </div>
        </Card>

        <Card title="全局规则模板">
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--space-3)' }}>
            默认应用于所有新文档的规则
          </div>
          <ul
            style={{
              margin: 0,
              padding: 0,
              paddingLeft: 'var(--space-4)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-2)',
              fontSize: 'var(--text-sm)',
              color: 'var(--text-secondary)',
            }}
          >
            <li>新文档默认为私密，仅所有者可见</li>
            <li>成员加入需经团队管理员审批</li>
            <li>每月预算超过阈值自动发邮件通知</li>
            <li>审计日志保留 180 天</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
