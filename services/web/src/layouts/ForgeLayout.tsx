import type { ReactNode } from 'react';
import DoubleIdentityBar from '../components/DoubleIdentityBar';

interface ForgeLayoutProps {
  leftPanel: ReactNode;
  centerPanel: ReactNode;
  rightPanel: ReactNode;
  onlineCount?: number;
  lastSaved?: string;
  wordCount?: number;
}

export default function ForgeLayout({
  leftPanel,
  centerPanel,
  rightPanel,
  onlineCount = 0,
  lastSaved = '',
  wordCount = 0,
}: ForgeLayoutProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      <DoubleIdentityBar />
      <div style={{ display: 'flex', flex: 1, minHeight: 0, overflow: 'hidden' }}>
        <aside
          style={{
            width: 280,
            minWidth: 280,
            borderRight: '1px solid var(--border-default)',
            background: 'var(--bg-page)',
            overflowY: 'auto',
            overflowX: 'hidden',
            padding: 'var(--space-3)',
          }}
        >
          {leftPanel}
        </aside>

        <main
          style={{
            flex: 1,
            minWidth: 0,
            overflowY: 'auto',
            overflowX: 'hidden',
            padding: 'var(--space-3)',
            background: 'var(--bg-page)',
          }}
        >
          {centerPanel}
        </main>

        <aside
          style={{
            width: 360,
            minWidth: 360,
            borderLeft: '1px solid var(--border-default)',
            background: 'var(--bg-surface)',
            overflowY: 'auto',
            overflowX: 'hidden',
            padding: 'var(--space-3)',
          }}
        >
          {rightPanel}
        </aside>
      </div>

      <footer
        style={{
          height: 28,
          minHeight: 28,
          background: 'var(--bg-subtle)',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 var(--space-4)',
          fontSize: 'var(--text-xs)',
          color: 'var(--text-muted)',
        }}
      >
        <span>{onlineCount}人在线</span>
        <span>上次保存 {lastSaved}</span>
        <span>字数 {wordCount.toLocaleString()}</span>
      </footer>
    </div>
  );
}
