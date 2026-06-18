import { useState } from 'react';
import { useAuthStore } from '../shared/store/authStore';
import { GlobalRole } from '../shared/types/contracts';
import { ViewType, canAccessView, allowedViews } from '../shared/authz';
import { Modal } from '../shared/components/Modal';

const VIEW_LABELS: Record<ViewType, string> = {
  [ViewType.FORGE]: '创作',
  [ViewType.TEAM]: '团队管理',
  [ViewType.OPS]: '运维监控',
};

export default function ViewSwitcher() {
  const globalRole = useAuthStore((s) => s.globalRole);
  const currentView = useAuthStore((s) => s.currentView);
  const opsConfirmed = useAuthStore((s) => s.opsConfirmed);
  const setView = useAuthStore((s) => s.setView);
  const confirmOps = useAuthStore((s) => s.confirmOps);

  const [opsModalOpen, setOpsModalOpen] = useState(false);
  const [opsInput, setOpsInput] = useState('');
  const [opsError, setOpsError] = useState('');

  const visibleViews = globalRole ? allowedViews(globalRole) : [];
  if (visibleViews.length === 0) return null;

  const handleClick = (view: ViewType) => {
    if (!globalRole || !canAccessView(globalRole, view)) return;

    if (view === ViewType.OPS && globalRole === GlobalRole.OPS && !opsConfirmed) {
      setOpsInput('');
      setOpsError('');
      setOpsModalOpen(true);
      return;
    }

    setView(view);
  };

  const handleConfirmOps = () => {
    if (!opsInput.trim()) {
      setOpsError('请输入确认信息');
      return;
    }
    confirmOps();
    setOpsModalOpen(false);
    setView(ViewType.OPS);
  };

  return (
    <>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-1)',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: 2,
        }}
      >
        {visibleViews.map((view) => {
          const isActive = currentView === view;
          return (
            <button
              key={view}
              onClick={() => handleClick(view)}
              style={{
                padding: '4px 12px',
                fontSize: 'var(--text-sm)',
                fontWeight: 500,
                border: 'none',
                borderRadius: 'calc(var(--radius-md) - 2px)',
                background: isActive ? 'var(--accent)' : 'transparent',
                color: isActive ? '#fff' : 'var(--text-secondary)',
                cursor: 'pointer',
                transition: 'background-color 0.15s, color 0.15s',
              }}
            >
              {VIEW_LABELS[view]}
            </button>
          );
        })}
      </div>

      <Modal
        isOpen={opsModalOpen}
        onClose={() => setOpsModalOpen(false)}
        title="运维监控二次确认"
        footer={
          <>
            <button
              onClick={() => setOpsModalOpen(false)}
              style={{
                padding: '6px 16px',
                fontSize: 'var(--text-sm)',
                background: 'transparent',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              取消
            </button>
            <button
              onClick={handleConfirmOps}
              style={{
                padding: '6px 16px',
                fontSize: 'var(--text-sm)',
                background: 'var(--accent)',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                color: '#fff',
                cursor: 'pointer',
                fontWeight: 600,
              }}
            >
              确认进入
            </button>
          </>
        }
      >
        <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--space-4)' }}>
          运维监控区域包含原始技术数据，请确认你在受控环境下使用。输入任意非空值表示已确认。
        </div>
        <input
          type="text"
          value={opsInput}
          onChange={(e) => { setOpsInput(e.target.value); if (opsError) setOpsError(''); }}
          placeholder="请输入确认信息"
          autoFocus
          style={{
            width: '100%',
            padding: 'var(--space-2) var(--space-3)',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-primary)',
            fontSize: 'var(--text-base)',
            outline: 'none',
            boxSizing: 'border-box',
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleConfirmOps();
          }}
        />
        {opsError && (
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--danger)', marginTop: 'var(--space-2)' }}>
            {opsError}
          </div>
        )}
      </Modal>
    </>
  );
}
