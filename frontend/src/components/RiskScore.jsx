function RiskScore({ score = 15 }) {
  let riskLevel = 'Low Risk'
  let colorClass = 'text-emerald-400'
  let strokeColor = '#10b981'
  let bgBadge = 'bg-emerald-950/50 border-emerald-500/40 text-emerald-300'
  let actionAdvice = 'Clear for automatic e-Gate entry.'

  if (score >= 70) {
    riskLevel = 'High Risk'
    colorClass = 'text-rose-400'
    strokeColor = '#f43f5e'
    bgBadge = 'bg-rose-950/50 border-rose-500/40 text-rose-300'
    actionAdvice = 'Immediate officer detention & secondary interrogation required.'
  } else if (score >= 35) {
    riskLevel = 'Moderate Risk'
    colorClass = 'text-amber-400'
    strokeColor = '#f59e0b'
    bgBadge = 'bg-amber-950/50 border-amber-500/40 text-amber-300'
    actionAdvice = 'Manual physical document inspection recommended.'
  }

  // Calculate SVG stroke parameters for circular dial
  const radius = 42
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (score / 100) * circumference

  return (
    <div className="flex items-center gap-6 rounded-xl border border-gray-800 bg-gray-950/60 p-4">
      {/* Circular SVG Gauge */}
      <div className="relative flex h-28 w-28 items-center justify-center">
        <svg className="h-full w-full -rotate-90 transform" viewBox="0 0 100 100">
          {/* Background track */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            className="stroke-gray-800"
            strokeWidth="8"
            fill="transparent"
          />
          {/* Animated score bar */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            stroke={strokeColor}
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        <div className="absolute flex flex-col items-center justify-center">
          <span className={`text-2xl font-black tracking-tight ${colorClass}`}>
            {score}%
          </span>
          <span className="text-[9px] uppercase font-mono tracking-widest text-gray-500">
            INDEX
          </span>
        </div>
      </div>

      {/* Text Description */}
      <div>
        <div className="flex items-center gap-2">
          <span className={`rounded-full border px-2.5 py-0.5 text-xs font-mono font-bold uppercase ${bgBadge}`}>
            {riskLevel}
          </span>
        </div>

        <p className="mt-2 text-xs font-medium text-gray-200">
          Composite Risk Assessment
        </p>
        <p className="mt-1 text-[11px] text-gray-400 max-w-[200px] leading-relaxed">
          {actionAdvice}
        </p>
      </div>
    </div>
  )
}

export default RiskScore