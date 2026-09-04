import { useTheme } from '../context/ThemeContext'

function RiskScore({ score = 18 }) {
  const { isDark } = useTheme()
  let label = 'Low Risk'
  let badgeColor = 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'

  if (score >= 70) {
    label = 'High Risk'
    badgeColor = 'bg-red-500/15 text-red-400 border-red-500/30'
  } else if (score >= 40) {
    label = 'Medium Risk'
    badgeColor = 'bg-amber-500/15 text-amber-400 border-amber-500/30'
  }

  return (
    <div className={`flex items-center gap-4 rounded-xl border p-4 transition-colors ${
      isDark ? 'border-gray-800 bg-gray-950' : 'border-gray-200 bg-gray-50 shadow-sm'
    }`}>
      <div>
        <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>Risk Assessment</p>
        <p className={`text-3xl font-bold mt-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{score}%</p>
      </div>

      <span className={`text-xs font-semibold px-2.5 py-1 rounded-md border ${badgeColor}`}>
        {label}
      </span>
    </div>
  )
}

export default RiskScore