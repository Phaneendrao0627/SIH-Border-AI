import { useState } from 'react'
import { useTheme } from '../context/ThemeContext'

function ScreeningPieChart({ data }) {
  const { isDark } = useTheme()
  const [hoveredSlice, setHoveredSlice] = useState(null)

  const items = data || [
    { label: 'Passed', count: 111, color: '#10b981', hoverColor: '#059669', badgeBg: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30', desc: 'Clearance approved without flags' },
    { label: 'Needs Review', count: 14, color: '#f59e0b', hoverColor: '#d97706', badgeBg: 'bg-amber-500/15 text-amber-500 border-amber-500/30', desc: 'Secondary physical inspection needed' },
    { label: 'Rejected', count: 3, color: '#ef4444', hoverColor: '#dc2626', badgeBg: 'bg-red-500/15 text-red-500 border-red-500/30', desc: 'Fraud or tampering detected' }
  ]

  const total = items.reduce((acc, curr) => acc + curr.count, 0)
  const radius = 54
  const circumference = 2 * Math.PI * radius
  let accumulatedOffset = 0

  return (
    <div className={`rounded-xl border p-6 transition-colors ${
      isDark ? 'border-gray-800 bg-gray-900 text-white' : 'border-gray-200 bg-white text-gray-900 shadow-sm'
    }`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b pb-4 mb-6 transition-colors border-inherit">
        <div>
          <h2 className="text-lg font-semibold">
            Today's Screening Distribution
          </h2>
          <p className={`text-xs mt-0.5 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
            Live outcome breakdown of all travelers screened today at checkpoint terminals
          </p>
        </div>

        <span className={`text-xs font-semibold px-3 py-1 rounded-full border self-start sm:self-auto ${
          isDark ? 'bg-gray-800 text-gray-300 border-gray-700' : 'bg-gray-100 text-gray-700 border-gray-200'
        }`}>
          Total: {total} Screenings
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left: Donut Chart Graphic */}
        <div className="lg:col-span-5 flex flex-col items-center justify-center relative">
          <div className="relative flex items-center justify-center">
            <svg
              className="w-56 h-56 -rotate-90 transform"
              viewBox="0 0 140 140"
            >
              {/* Background Track */}
              <circle
                cx="70"
                cy="70"
                r={radius}
                className={isDark ? 'stroke-gray-800' : 'stroke-gray-100'}
                strokeWidth="18"
                fill="transparent"
              />

              {/* Slices */}
              {items.map((item, index) => {
                const percentage = (item.count / total) * 100
                const strokeLength = (item.count / total) * circumference
                const currentOffset = -accumulatedOffset
                accumulatedOffset += strokeLength

                const isHovered = hoveredSlice === item.label

                return (
                  <circle
                    key={index}
                    cx="70"
                    cy="70"
                    r={radius}
                    stroke={isHovered ? item.hoverColor : item.color}
                    strokeWidth={isHovered ? '22' : '18'}
                    strokeDasharray={`${strokeLength} ${circumference}`}
                    strokeDashoffset={currentOffset}
                    fill="transparent"
                    className="transition-all duration-300 cursor-pointer"
                    onMouseEnter={() => setHoveredSlice(item.label)}
                    onMouseLeave={() => setHoveredSlice(null)}
                  />
                )
              })}
            </svg>

            {/* Inner Center Label */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
              <span className={`text-3xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
                {hoveredSlice
                  ? items.find((i) => i.label === hoveredSlice)?.count
                  : total}
              </span>
              <span className={`text-[11px] font-semibold uppercase tracking-wider ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                {hoveredSlice
                  ? hoveredSlice
                  : 'Total Screened'}
              </span>
              <span className="text-[10px] text-emerald-500 font-medium mt-0.5">
                {hoveredSlice
                  ? `${((items.find((i) => i.label === hoveredSlice)?.count / total) * 100).toFixed(1)}% of Total`
                  : `${((items[0].count / total) * 100).toFixed(1)}% Pass Rate`}
              </span>
            </div>
          </div>

          <p className={`text-[11px] mt-4 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
            Hover over any ring segment to view details
          </p>
        </div>

        {/* Right: Legend and Statistics Breakdown */}
        <div className="lg:col-span-7 space-y-3.5">
          {items.map((item, index) => {
            const percentage = ((item.count / total) * 100).toFixed(1)
            const isHovered = hoveredSlice === item.label

            return (
              <div
                key={index}
                onMouseEnter={() => setHoveredSlice(item.label)}
                onMouseLeave={() => setHoveredSlice(null)}
                className={`rounded-xl border p-3.5 transition cursor-pointer ${
                  isHovered
                    ? isDark
                      ? 'border-gray-700 bg-gray-800/80 scale-[1.01]'
                      : 'border-gray-300 bg-gray-50 shadow-sm scale-[1.01]'
                    : isDark
                    ? 'border-gray-800/70 bg-gray-950/40 hover:bg-gray-800/40'
                    : 'border-gray-200 bg-gray-50/50 hover:bg-gray-100/50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span
                      className="h-3 w-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: item.color }}
                    />
                    <div>
                      <span className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                        {item.label}
                      </span>
                      <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                        {item.desc}
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className={`text-base font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>
                      {item.count}
                    </span>
                    <span className={`block text-xs font-semibold ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                      {percentage}%
                    </span>
                  </div>
                </div>

                {/* Progress Bar indicator */}
                <div className={`mt-2.5 h-1.5 w-full rounded-full overflow-hidden ${
                  isDark ? 'bg-gray-800' : 'bg-gray-200'
                }`}>
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${percentage}%`,
                      backgroundColor: item.color
                    }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default ScreeningPieChart
