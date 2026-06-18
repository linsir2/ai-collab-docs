import { useEffect, useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../shared/store/authStore';
import ViewSwitcher from '../components/ViewSwitcher';
import { ViewType, MenuGroup, allowedMenuGroups } from '../shared/authz';
import { GlobalRole } from '../shared/types/contracts';

interface MenuItem {
  label: string;
  to: string;
  activePaths: string[];
}

interface MenuGroupDef {
  group: MenuGroup;
  label: string;
  items: MenuItem[];
}

const MENU_GROUPS: MenuGroupDef[] = [
  {
    group: MenuGroup.FORGE_TOOLS,
    label: '文档锻造工具',
    items: [
      { label: '文档列表', to: '/dashboard', activePaths: ['/dashboard'] },
      { label: '新建文档', to: '/documents/new', activePaths: ['/documents/new'] },
      { label: '锻造台', to: '/forge/workbench', activePaths: ['/forge'] },
    ],
  },
  {
    group: MenuGroup.TEAM_MGMT,
    label: '团队管控',
    items: [
      { label: '成员管理', to: '/team', activePaths: ['/team'] },
      { label: '预算配置', to: '/team/budget', activePaths: ['/team/budget'] },
      { label: '团队审计摘要', to: '/team/audit', activePaths: ['/team/audit'] },
    ],
  },
  {
    group: MenuGroup.OPS_MONITOR,
    label: '系统运维监控',
    items: [
      { label: '性能监控', to: '/ops', activePaths: ['/ops'] },
      { label: '记忆修复', to: '/ops/memory', activePaths: ['/ops/memory'] },
      { label: '原始日志', to: '/ops/logs', activePaths: ['/ops/logs'] },
    ],
  },
];

function isItemActive(pathname: string, item: MenuItem): boolean {
  return item.activePaths.some((p) => pathname === p || pathname.startsWith(p + '/'));
}

function isAnyItemActive(pathname: string, items: MenuItem[]): boolean {
  return items.some((item) => isItemActive(pathname, item));
}

export default function AppLayout() {
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const globalRole = useAuthStore((s) => s.globalRole);
  const currentView = useAuthStore((s) => s.currentView);
  const loadFromStorage = useAuthStore((s) => s.loadFromStorage);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const location = useLocation();

  const [collapsedGroups, setCollapsedGroups] = useState<Record<MenuGroup, boolean>>({
    [MenuGroup.FORGE_TOOLS]: false,
    [MenuGroup.TEAM_MGMT]: true,
    [MenuGroup.OPS_MONITOR]: true,
  });

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  useEffect(() => {
    const pathname = location.pathname;
    if (pathname.startsWith('/team')) {
      useAuthStore.getState().setView(ViewType.TEAM);
    } else if (pathname.startsWith('/ops')) {
      useAuthStore.getState().setView(ViewType.OPS);
    } else {
      useAuthStore.getState().setView(ViewType.FORGE);
    }
  }, [location.pathname]);

  const activeGroups = globalRole ? allowedMenuGroups(globalRole, currentView) : [];

  const visibleGroups = MENU_GROUPS.filter((g) => {
    if (!activeGroups.includes(g.group)) return false;
    if (g.group === MenuGroup.TEAM_MGMT && globalRole === GlobalRole.PERSONAL) return false;
    return true;
  });

  const toggleGroup = (group: MenuGroup) => {
    setCollapsedGroups((prev) => ({ ...prev, [group]: !prev[group] }));
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const pageTitle = (() => {
    for (const group of visibleGroups) {
      for (const item of group.items) {
        if (isItemActive(location.pathname, item)) {
          return item.label;
        }
      }
    }
    return '';
  })();

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      <aside
        style={{
          width: 220,
          minWidth: 220,
          background: 'var(--bg-elevated)',
          borderRight: '1px solid var(--border-default)',
          display: 'flex',
          flexDirection: 'column',
          padding: 'var(--space-3) 0',
          overflowY: 'auto',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
          {visibleGroups.map((group) => {
            const isCollapsed = collapsedGroups[group.group];
            const hasActiveItem = isAnyItemActive(location.pathname, group.items);

            const isForgeAlwaysExpanded =
              group.group === MenuGroup.FORGE_TOOLS && currentView === ViewType.FORGE;

            const collapsible = !isForgeAlwaysExpanded;
            const showItems = isForgeAlwaysExpanded || !isCollapsed;

            return (
              <div key={group.group} style={{ marginBottom: 'var(--space-3)' }}>
                <button
                  onClick={() => collapsible && toggleGroup(group.group)}
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    padding: '6px var(--space-4)',
                    fontSize: 'var(--text-xs)',
                    fontWeight: 700,
                    color: hasActiveItem ? 'var(--text-primary)' : 'var(--text-muted)',
                    background: 'transparent',
                    border: 'none',
                    cursor: collapsible ? 'pointer' : 'default',
                    textTransform: 'uppercase',
                    letterSpacing: 0.5,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span>{group.label}</span>
                  {collapsible && (
                    <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                      {isCollapsed ? '▸' : '▾'}
                    </span>
                  )}
                </button>
                {showItems && (
                  <div style={{ display: 'flex', flexDirection: 'column', marginTop: 2 }}>
                    {group.items.map((item) => {
                      const active = isItemActive(location.pathname, item);
                      return (
                        <button
                          key={item.to}
                          onClick={() => navigate(item.to)}
                          style={{
                            textAlign: 'left',
                            padding: '6px var(--space-4)',
                            fontSize: 'var(--text-sm)',
                            color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
                            background: active ? 'var(--accent-subtle)' : 'transparent',
                            border: 'none',
                            borderLeft: active ? '2px solid var(--accent)' : '2px solid transparent',
                            cursor: 'pointer',
                            transition: 'background-color 0.15s, color 0.15s',
                          }}
                        >
                          {item.label}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div
          style={{
            padding: 'var(--space-3) var(--space-4)',
            borderTop: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
          }}
        >
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
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
            {isAuthenticated ? '已连接' : '未连接'}
          </span>
        </div>
      </aside>

      <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
        <header
          style={{
            height: 48,
            minHeight: 48,
            background: 'var(--bg-surface)',
            borderBottom: '1px solid var(--border-default)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 var(--space-4)',
            gap: 'var(--space-4)',
          }}
        >
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
            {pageTitle}
          </div>

          <ViewSwitcher />

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
