import { useAuthStore } from '@/shared/store/authStore'
import { formatGlobalRoleLabel, formatDocRoleLabel } from '@/shared/authz'

export default function DoubleIdentityBar() {
  const globalRole = useAuthStore((s) => s.globalRole)
  const docRole = useAuthStore((s) => s.docRole)

  const globalLabel = globalRole ? formatGlobalRoleLabel(globalRole) : '未登录'
  const docLabel = docRole ? formatDocRoleLabel(docRole) : '只读成员'

  return (
    <div
      title="账号全局身份决定您可访问的视图；文档内角色仅决定当前文档内操作权限"
      style={{
        height: 32,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end',
        gap: 'var(--space-4)',
        padding: '0 var(--space-4)',
        background: 'var(--bg-elevated)',
        borderBottom: '1px solid var(--border-default)',
        fontSize: 'var(--text-xs)',
        color: 'var(--text-muted)',
        flexShrink: 0,
      }}
    >
      <span>
        全局身份：<span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{globalLabel}</span>
      </span>
      <span style={{ color: 'var(--border-default)' }}>|</span>
      <span>
        当前文档身份：<span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{docLabel}</span>
      </span>
    </div>
  )
}
