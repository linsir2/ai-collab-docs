import { useState } from 'react';
import { STATE_LABELS, STATE_ORDER, ALLOWED_TRANSITIONS } from '../../shared/types';
import type { DocumentState } from '../../shared/types';

interface StateAirlockProps {
  currentState: DocumentState;
  onTransition: (toState: DocumentState) => void;
}

export default function StateAirlock({ currentState, onTransition }: StateAirlockProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [targetState, setTargetState] = useState<DocumentState | null>(null);

  const allowed = ALLOWED_TRANSITIONS[currentState] ?? [];
  const currentIndex = STATE_ORDER.indexOf(currentState);

  const handleStateClick = (state: string) => {
    const toState = state as DocumentState;
    if (!allowed.includes(toState)) return;
    setTargetState(toState);
    setShowConfirm(true);
  };

  const handleConfirm = () => {
    if (targetState) {
      onTransition(targetState);
    }
    setShowConfirm(false);
    setTargetState(null);
  };

  return (
    <>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 'var(--space-1)',
          padding: 'var(--space-2) var(--space-3)',
          background: 'var(--bg-surface)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-default)',
          marginBottom: 'var(--space-3)',
        }}
      >
        {STATE_ORDER.map((state, idx) => {
          const isCurrent = state === currentState;
          const isAllowed = allowed.includes(state);
          const isPast = idx < currentIndex;

          let circleBg = 'var(--bg-elevated)';
          let circleBorder = '1px solid var(--border-default)';
          let textColor = 'var(--text-muted)';
          let cursor: React.CSSProperties['cursor'] = 'default';

          if (isCurrent) {
            circleBg = 'var(--accent)';
            circleBorder = 'none';
            textColor = 'var(--text-primary)';
          } else if (isAllowed) {
            circleBorder = '1px solid var(--accent)';
            textColor = 'var(--accent)';
            cursor = 'pointer';
          } else if (isPast) {
            textColor = 'var(--text-secondary)';
          }

          return (
            <div
              key={state}
              style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}
            >
              <div
                onClick={() => handleStateClick(state)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: 'var(--space-1) var(--space-2)',
                  borderRadius: 'var(--radius-sm)',
                  cursor,
                  transition: 'background 0.15s',
                  userSelect: 'none',
                }}
              >
                <div
                  style={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    background: circleBg,
                    border: circleBorder,
                    transition: 'all 0.2s',
                  }}
                />
                <span
                  style={{
                    fontSize: 'var(--text-xs)',
                    color: textColor,
                    fontWeight: isCurrent ? 700 : 400,
                  }}
                >
                  {STATE_LABELS[state]}
                </span>
              </div>
              {idx < STATE_ORDER.length - 1 && (
                <span style={{ color: 'var(--border-default)', fontSize: 'var(--text-xs)' }}>
                  →
                </span>
              )}
            </div>
          );
        })}
      </div>

      {showConfirm && targetState && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setShowConfirm(false)}
        >
          <div
            style={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--space-6)',
              maxWidth: 400,
              width: '90%',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ fontSize: 'var(--text-lg)', marginBottom: 'var(--space-3)' }}>
              确认状态流转
            </h3>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-2)',
                marginBottom: 'var(--space-4)',
              }}
            >
              <span
                style={{
                  padding: 'var(--space-1) var(--space-2)',
                  background: 'var(--accent)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--text-sm)',
                  color: '#fff',
                }}
              >
                {STATE_LABELS[currentState]}
              </span>
              <span style={{ color: 'var(--text-muted)' }}>→</span>
              <span
                style={{
                  padding: 'var(--space-1) var(--space-2)',
                  background: 'var(--accent-subtle)',
                  border: '1px solid var(--accent)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--text-sm)',
                  color: 'var(--accent)',
                }}
              >
                {STATE_LABELS[targetState]}
              </span>
            </div>

            <div
              style={{
                padding: 'var(--space-3)',
                background: 'var(--bg-surface)',
                borderRadius: 'var(--radius-md)',
                marginBottom: 'var(--space-4)',
                fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)',
                lineHeight: 1.6,
              }}
            >
              <p style={{ marginBottom: 'var(--space-2)' }}>此次流转将触发以下操作：</p>
              <ul style={{ margin: 0, paddingLeft: 'var(--space-4)' }}>
                <li>生成状态变更审批记录</li>
                <li>通知相关协作人员</li>
                <li>保存当前文档快照</li>
                <li>更新文档访问权限</li>
              </ul>
            </div>

            <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowConfirm(false)}
                style={{
                  padding: 'var(--space-2) var(--space-4)',
                  background: 'transparent',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  fontSize: 'var(--text-sm)',
                }}
              >
                取消
              </button>
              <button
                onClick={handleConfirm}
                style={{
                  padding: 'var(--space-2) var(--space-4)',
                  background: 'var(--accent)',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  color: '#fff',
                  cursor: 'pointer',
                  fontSize: 'var(--text-sm)',
                  fontWeight: 600,
                }}
              >
                确认流转
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
