import { useAuthStore } from '@/shared/store/authStore'
import { formatGlobalRoleLabel, formatDocRoleLabel } from '@/shared/authz'

interface PermissionDeniedModalProps {
  open: boolean
  onClose: () => void
  action?: string
}

export default function PermissionDeniedModal({ open, onClose, action }: PermissionDeniedModalProps) {
  const globalRole = useAuthStore((s) => s.globalRole)
  const docRole = useAuthStore((s) => s.docRole)

  if (!open) return null

  const globalLabel = globalRole ? formatGlobalRoleLabel(globalRole) : '未登录'
  const docLabel = docRole ? formatDocRoleLabel(docRole) : '只读成员'

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.6)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 2000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-6)',
          maxWidth: 480,
          width: '90%',
          textAlign: 'left',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            fontSize: 'var(--text-lg)',
            fontWeight: 700,
            color: 'var(--danger)',
            marginBottom: 'var(--space-4)',
          }}
        >
          权限不足
        </div>

        <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: 'var(--space-4)' }}>
          {action && (
            <p style={{ marginBottom: 'var(--space-2)' }}>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>操作：</span>
              {action}
            </p>
          )}
          <p>
            您当前的全局身份是{' '}
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{globalLabel}</span>
            ，文档角色是{' '}
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{docLabel}</span>
            。此操作需要更高权限。
          </p>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
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
            关闭
          </button>
        </div>
      </div>
    </div>
  )
}
