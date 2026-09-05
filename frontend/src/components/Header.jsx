import { useTheme } from '../context/ThemeContext'

function Header() {
  const { isDark, toggleTheme } = useTheme()

  return (
    <header className={`flex items-center justify-between pb-6 mb-6 border-b transition-colors ${
      isDark ? 'border-gray-800' : 'border-gray-200'
    }`}>
      <div className="flex items-center gap-3">
        <div className={`h-2.5 w-2.5 rounded-full ${
          isDark ? 'bg-emerald-400 animate-pulse' : 'bg-emerald-500'
        }`} />
        <span className={`text-xs font-medium ${
          isDark ? 'text-gray-400' : 'text-gray-500'
        }`}>
          Border Security Terminal • Officer Workstation
        </span>
      </div>

      {/* Option B: Top-Right Theme Toggle Button */}
      <button
        type="button"
        onClick={toggleTheme}
        aria-label="Toggle dark and light mode"
        className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold border transition ${
          isDark
            ? 'bg-gray-900 border-gray-700 text-gray-200 hover:bg-gray-800'
            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-100 shadow-sm'
        }`}
      >
        <span>{isDark ? '☀️' : '🌙'}</span>
        <span>{isDark ? 'Light Mode' : 'Dark Mode'}</span>
      </button>
    </header>
  )
}

export default Header
