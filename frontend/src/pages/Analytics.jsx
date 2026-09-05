import { useTheme } from '../context/ThemeContext'
import AnalyticsTrendChart from '../components/AnalyticsTrendChart'

function Analytics() {
  const { isDark } = useTheme()

  const stats = [
    {
      label: "Total Screenings",
      value: "1,248",
      subtext: "+14% from last week",
      color: "text-yellow-500"
    },
    {
      label: "Passed (Clearance)",
      value: "82%",
      subtext: "1,023 authentic travelers",
      color: "text-emerald-500"
    },
    {
      label: "Under Review",
      value: "12%",
      subtext: "150 routed to secondary",
      color: "text-amber-500"
    },
    {
      label: "Rejected / Detained",
      value: "6%",
      subtext: "75 fraud & forgery alerts",
      color: "text-rose-500"
    }
  ]

  const flags = [
    {
      name: "Expired / Invalid Validity",
      count: 24,
      percentage: 41,
      color: "bg-amber-500"
    },
    {
      name: "ICAO 9303 MRZ Mismatch",
      count: 17,
      percentage: 29,
      color: "bg-rose-500"
    },
    {
      name: "Digital & Image Tampering (ELA)",
      count: 11,
      percentage: 19,
      color: "bg-rose-600"
    },
    {
      name: "Biometric Face & Spoof Anomaly",
      count: 7,
      percentage: 11,
      color: "bg-purple-500"
    }
  ]

  return (
    <div className="space-y-8 max-w-6xl">
      {/* Page Header */}
      <div>
        <h1 className={`text-3xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Analytics & Inspection Metrics
        </h1>
        <p className={`mt-1 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aggregated performance insights across document checkpoints and computer vision modules.
        </p>
      </div>

      {/* Top 4 KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className={`rounded-xl border p-5 transition-colors ${
              isDark ? 'border-gray-800 bg-gray-900 text-white' : 'border-gray-200 bg-white text-gray-900 shadow-sm'
            }`}
          >
            <p className={`text-xs font-medium ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              {stat.label}
            </p>

            <p className={`mt-2 text-3xl font-bold font-mono ${stat.color}`}>
              {stat.value}
            </p>

            <p className={`mt-1 text-[11px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              {stat.subtext}
            </p>
          </div>
        ))}
      </div>

      {/* Middle Row: Trend Chart (Balanced size) + Common Flags */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Trend Graph - 7 columns */}
        <div className="lg:col-span-7">
          <AnalyticsTrendChart />
        </div>

        {/* Common Flags - 5 columns */}
        <div className={`lg:col-span-5 rounded-xl border p-6 flex flex-col justify-between transition-colors ${
          isDark ? 'border-gray-800 bg-gray-900 text-white' : 'border-gray-200 bg-white text-gray-900 shadow-sm'
        }`}>
          <div>
            <div className="flex items-center justify-between border-b pb-4 mb-4 border-inherit">
              <div>
                <h2 className="text-lg font-semibold">
                  Common Detection Flags
                </h2>
                <p className={`text-xs mt-0.5 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                  Primary factors triggering secondary review or rejection
                </p>
              </div>
              <span className={`text-xs px-2.5 py-0.5 rounded border font-mono ${
                isDark ? 'bg-gray-800 text-gray-300 border-gray-700' : 'bg-gray-100 text-gray-700 border-gray-200'
              }`}>
                59 Total Flags
              </span>
            </div>

            <div className="space-y-4">
              {flags.map((flag) => (
                <div key={flag.name} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className={`font-medium ${isDark ? 'text-gray-200' : 'text-gray-700'}`}>
                      {flag.name}
                    </span>
                    <span className="font-mono font-bold">
                      {flag.count} cases ({flag.percentage}%)
                    </span>
                  </div>

                  <div className={`h-1.5 w-full rounded-full overflow-hidden ${
                    isDark ? 'bg-gray-800' : 'bg-gray-100'
                  }`}>
                    <div
                      className={`h-full rounded-full ${flag.color}`}
                      style={{ width: `${flag.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className={`mt-5 pt-3 border-t text-[11px] border-inherit ${
            isDark ? 'text-gray-400' : 'text-gray-500'
          }`}>
            <span>Most frequent trigger: <strong>Expired Document (41%)</strong></span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Analytics