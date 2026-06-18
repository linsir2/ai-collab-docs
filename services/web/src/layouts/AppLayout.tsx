import { useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../shared/store/authStore';

const NAV_ITEMS = [
  { to: '/dashboard', icon: '📄', label: '文档' },
  { to: '/team', icon: '👥', label: '团队' },
  { to: '/budget', icon: '📊', label: '预算' },
  { to: '/audit', icon: '📋', label: '审计' },
];

export default function AppLayout() {
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const loadFromStorage = useAuthStore((s) => s.loadFromStorage);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const pageTitle = (() => {
    if (location.pathname === '/dashboard') return '控制台';
    if (location.pathname.startsWith('/documents/new')) return '新建文档';
    if (location.pathname.includes('/forge/light')) return '轻量创作';
    if (location.pathname.includes('/forge')) return '文档锻造台';
    if (location.pathname === '/team') return '团队管理';
    if (location.pathname === '/budget') return '预算管理';
    if (location.pathname === '/audit') return '审计日志';
    return '';
  })();

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      <aside
        style={{
          width: 56,
          minWidth: 56,
          background: 'var(--bg-elevated)',
          borderRight: '1px solid var(--border-default)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingTop: 'var(--space-3)',
          paddingBottom: 'var(--space-3)',
        }}
      >
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
          {NAV_ITEMS.map((item) => {
            const isActive = location.pathname === item.to
              || (item.to === '/dashboard' && location.pathname === '/dashboard');
            return (
              <button
                key={item.to}
                onClick={() => navigate(item.to)}
                title={item.label}
                style={{
                  width: 40,
                  height: 40,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 18,
                  background: 'transparent',
                  border: 'none',
                  borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
                  borderRadius: 'var(--radius-sm)',
                  cursor: 'pointer',
                  color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
                  transition: 'color 0.15s, border-color 0.15s',
                }}
              >
                {item.icon}
              </button>
            );
          })}
        </nav>

        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: isAuthenticated ? 'var(--success)' : 'var(--danger)',
            boxShadow: isAuthenticated
              ? '0 0 6px var(--success)'
              : '0 0 6px var(--danger)',
          }}
          title={isAuthenticated ? '已连接' : '未连接'}
        />
      </aside>

      <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
        <header
          style={{
            height: 40,
            minHeight: 40,
            background: 'var(--bg-surface)',
            borderBottom: '1px solid var(--border-default)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 var(--space-4)',
          }}
        >
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>
            {pageTitle}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>
              {user?.display_name ?? '未登录'}
            </span>
            <button
              onClick={handleLogout}
              style={{
                background: 'transparent',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-muted)',
                fontSize: 'var(--text-xs)',
                padding: '2px 10px',
                cursor: 'pointer',
                transition: 'color 0.15s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--danger)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-muted)'; }}
            >
              退出
            </button>
          </div>
        </header>

        <main style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
