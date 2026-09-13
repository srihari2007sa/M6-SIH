import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Server, Code2, Database, GitMerge, Shield, Activity, ClipboardList, RotateCcw, Settings, LogOut, Radio } from 'lucide-react'
import { authStore } from '../../store/auth'

const NAV = [
  { to: '/dashboard',     icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/sources',       icon: Server,          label: 'Sources' },
  { to: '/parsers',       icon: Code2,           label: 'Parsers' },
  { to: '/schemas',       icon: Database,        label: 'Schemas' },
  { to: '/mappings',      icon: GitMerge,        label: 'Mappings' },
  { to: '/policies',      icon: Shield,          label: 'Policies' },
  { to: '/services',      icon: Activity,        label: 'Services' },
  { to: '/audit',         icon: ClipboardList,   label: 'Audit' },
  { to: '/replay',        icon: RotateCcw,       label: 'Replay' },
  { to: '/configuration', icon: Settings,        label: 'Configuration' },
]

const linkStyle = (isActive: boolean): React.CSSProperties => ({
  display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px',
  borderRadius: 6, color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
  background: isActive ? 'var(--bg-hover)' : 'transparent',
  fontWeight: isActive ? 600 : 400, fontSize: 13, transition: 'all 0.15s',
  textDecoration: 'none',
})

export function Sidebar() {
  const navigate = useNavigate()
  const handleLogout = () => { authStore.clearAuth(); navigate('/login') }

  return (
    <aside style={{
      width: 'var(--sidebar-w)', flexShrink: 0,
      background: 'var(--bg-surface)', borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column', height: '100vh', position: 'sticky', top: 0,
    }}>
      {/* Brand */}
      <div style={{ padding: '16px 16px 12px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Radio size={18} color="var(--accent)" />
          <div>
            <div style={{ fontWeight: 700, fontSize: 13, color: 'var(--text-primary)' }}>ULPF</div>
            <div style={{ fontSize: 10, color: 'var(--text-dim)', letterSpacing: '0.05em' }}>M6 CONTROL PLANE</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '8px 8px', overflowY: 'auto' }}>
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} style={({ isActive }) => linkStyle(isActive)}>
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div style={{ padding: '8px', borderTop: '1px solid var(--border)' }}>
        <button
          onClick={handleLogout}
          style={{ ...linkStyle(false), width: '100%', border: 'none', background: 'transparent', cursor: 'pointer' }}
        >
          <LogOut size={15} />
          Logout
        </button>
      </div>
    </aside>
  )
}
