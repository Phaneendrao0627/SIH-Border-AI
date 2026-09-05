import { useState } from 'react'
import { useTheme } from '../context/ThemeContext'

function AnalyticsTrendChart() {
  const { isDark } = useTheme()
  const [hoveredDay, setHoveredDay] = useState(null)

  const weeklyData = [
    { day: 'Mon', screened: 165, flagged: 14 },
    { day: 'Tue', screened: 190, flagged: 18 },
    { day: 'Wed', screened: 215, flagged: 21 },
    { day: 'Thu', screened: 180, flagged: 12 },
    { day: 'Fri', screened: 245, flagged: 29 },
    { day: 'Sat', screened: 290, flagged: 34 },
    { day: 'Sun', screened: 210, flagged: 17 }
  ]

  const maxScreened = 320
  const chartHeight = 170

  return (
    <div className={`rounded-xl border p-6 transition-colors flex flex-col justify-between ${
      isDark ? 'border-gray-800 bg-gray-900 text-white' : 'border-gray-200 bg-white text-gray-900 shadow-sm'
    }`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b pb-4 mb-4 border-inherit">
        <div>
          <h2 className="text-lg font-semibold">
            Weekly Screening & Anomaly Volume
          </h2>
          <p className={`text-xs mt-0.5 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
            Daily passenger throughput and flagged security incidents (Past 7 Days)
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm bg-yellow-400" />
            <span className={isDark ? 'text-gray-300' : 'text-gray-600'}>Total Screened</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm bg-rose-500" />
            <span className={isDark ? 'text-gray-300' : 'text-gray-600'}>Flagged / Intercepted</span>
          </div>
        </div>
      </div>

      {/* Bar Chart Area */}
      <div className="pt-2 pb-1">
        <div className="flex items-end justify-between gap-3 sm:gap-6 h-[170px] relative px-2">
          {/* Subtle Gridlines */}
          <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-20">
            <div className={`border-b w-full ${isDark ? 'border-gray-700' : 'border-gray-400'}`} />
            <div className={`border-b w-full ${isDark ? 'border-gray-700' : 'border-gray-400'}`} />
            <div className={`border-b w-full ${isDark ? 'border-gray-700' : 'border-gray-400'}`} />
          </div>

          {weeklyData.map((item, idx) => {
            const barHeight = Math.round((item.screened / maxScreened) * chartHeight)
            const flaggedHeight = Math.round((item.flagged / maxScreened) * chartHeight)
            const isHovered = hoveredDay === item.day

            return (
              <div
                key={idx}
                className="flex-1 flex flex-col items-center h-full justify-end relative group cursor-pointer z-10"
                onMouseEnter={() => setHoveredDay(item.day)}
                onMouseLeave={() => setHoveredDay(null)}
              >
                {/* Floating Tooltip */}
                {isHovered && (
                  <div className={`absolute -top-12 z-30 rounded-md px-2.5 py-1 text-[11px] whitespace-nowrap shadow-lg border transition-all ${
                    isDark
                      ? 'bg-gray-950 border-gray-700 text-white'
                      : 'bg-white border-gray-300 text-gray-900'
                  }`}>
                    <span className="font-bold">{item.day}: </span>
                    <span className="text-yellow-500 font-semibold">{item.screened} screened</span> •{' '}
                    <span className="text-rose-500 font-semibold">{item.flagged} flagged</span>
                  </div>
                )}

                {/* Stacked Bars */}
                <div
                  className={`w-full max-w-[36px] rounded-t-md transition-all duration-300 relative flex flex-col justify-end overflow-hidden ${
                    isHovered ? 'opacity-100 scale-y-[1.03]' : 'opacity-85'
                  }`}
                  style={{
                    height: `${barHeight}px`,
                    backgroundColor: isDark ? '#facc15' : '#eab308'
                  }}
                >
                  {/* Flagged sub-bar on top */}
                  <div
                    className="w-full bg-rose-500 rounded-t-sm transition-all"
                    style={{ height: `${flaggedHeight}px` }}
                  />
                </div>

                {/* Day label */}
                <span className={`mt-2 text-xs font-medium transition-colors ${
                  isHovered
                    ? 'text-yellow-500 font-bold'
                    : isDark
                    ? 'text-gray-400'
                    : 'text-gray-500'
                }`}>
                  {item.day}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Summary Footer */}
      <div className={`mt-4 pt-3 border-t flex items-center justify-between text-xs border-inherit ${
        isDark ? 'text-gray-400' : 'text-gray-500'
      }`}>
        <span>Peak Traffic: <strong>Saturday (290 passengers)</strong></span>
        <span>Average Daily Clearance: <strong className="text-emerald-500">89.4%</strong></span>
      </div>
    </div>
  )
}

export default AnalyticsTrendChart
