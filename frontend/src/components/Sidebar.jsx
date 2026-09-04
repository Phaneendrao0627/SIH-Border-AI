import { Link, useLocation } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'

function Sidebar() {
  const { isDark } = useTheme()
  const location = useLocation()

  const links = [
    { to: '/', label: 'Dashboard' },
    { to: '/screening', label: 'New Screening' },
    { to: '/history', label: 'History' },
    { to: '/analytics', label: 'Analytics' }
  ]

  return (
    <aside className={`w-64 min-h-screen border-r p-6 transition-colors ${
      isDark ? 'bg-black text-white border-gray-800' : 'bg-white text-gray-900 border-gray-200 shadow-sm'
    }`}>
      <h1 className="text-2xl font-bold text-yellow-400">
        BorderGuard
      </h1>
      <p className={`text-xs mt-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
        AI Screening Platform
      </p>

      <nav className="mt-8 flex flex-col gap-2">
        {links.map((link) => {
          const isActive = location.pathname === link.to
          return (
            <Link
              key={link.to}
              to={link.to}
              className={`rounded-lg px-4 py-2.5 text-sm font-medium transition ${
                isActive
                  ? 'bg-yellow-400 text-black font-semibold'
                  : isDark
                  ? 'text-gray-300 hover:bg-gray-900 hover:text-white'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-black'
              }`}
            >
              {link.label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}

export default Sidebar