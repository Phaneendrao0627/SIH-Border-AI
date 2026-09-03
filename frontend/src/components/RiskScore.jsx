function RiskScore({ score = 18 }) {
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
    <div className="flex items-center gap-4 rounded-xl border border-gray-800 bg-gray-950 p-4">
      <div>
        <p className="text-xs text-gray-400">Risk Assessment</p>
        <p className="text-3xl font-bold text-white mt-1">{score}%</p>
      </div>

      <span className={`text-xs font-semibold px-2.5 py-1 rounded-md border ${badgeColor}`}>
        {label}
      </span>
    </div>
  )
}

export default RiskScore