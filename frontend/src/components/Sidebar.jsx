import { NavLink } from 'react-router-dom';

const links = [
  { to: '/project',    icon: '🏭', label: 'Проект' },
  { to: '/cde',        icon: '📐', label: 'Элементы CDE' },
  { to: '/knowledge',  icon: '🗄️', label: 'База знаний' },
  { to: '/optimize',   icon: '🚀', label: 'Оптимизация' },
  { to: '/guide',      icon: '📘', label: 'Руководство' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <span className="logo-icon">⚙️</span>
        <div>
          <div className="logo-title">MachOpt-6L</div>
          <div className="logo-sub">Оптимизация ТП&nbsp;мехобработки</div>
        </div>
      </div>
      <nav className="sidebar-nav">
        {links.map(l => (
          <NavLink
            key={l.to}
            to={l.to}
            className={({ isActive }) => 'nav-item' + (isActive ? ' active' : '')}
          >
            <span className="nav-icon">{l.icon}</span>
            {l.label}
          </NavLink>
        ))}
      </nav>
      <div style={{ padding: '1rem', borderTop: '1px solid var(--border)', fontSize: '0.72rem', color: 'var(--muted)' }}>
        v1.0.0 · SQLite · NSGA-II
      </div>
    </aside>
  );
}
