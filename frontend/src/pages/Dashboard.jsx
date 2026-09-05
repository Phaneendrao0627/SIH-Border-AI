import { Link } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'
import ScreeningPieChart from '../components/ScreeningPieChart'

function Dashboard() {
  const { isDark } = useTheme()

  const recentScreenings = [
    {
      id: "BG-1042",
      passenger: "Arjun Sharma",
      document: "Passport (Z5839201)",
      risk: 18,
      status: "PASS"
    },
    {
      id: "BG-1041",
      passenger: "Michael Chen",
      document: "Passport (E9201844)",
      risk: 58,
      status: "REVIEW"
    },
    {
      id: "BG-1040",
      passenger: "Elena Rostova",
      document: "National ID (ID4091)",
      risk: 82,
      status: "REJECT"
    }
  ]

  return (
    <div className="space-y-8 max-w-6xl">
      {/* Top Header & Quick Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className={`text-3xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Officer Dashboard
          </h1>
          <p className={`mt-1 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Track & Verify Identities at Airport & Border Checkpoints.
          </p>
        </div>

        <Link
          to="/screening"
          className="inline-flex items-center gap-2 rounded-lg bg-yellow-400 hover:bg-yellow-300 px-5 py-2.5 font-semibold text-black transition shadow-sm self-start sm:self-auto"
        >
          <span>+</span>
          <span>New Screening</span>
        </Link>
      </div>

      {/* Replaced Button Cards with Interactive Pie Chart */}
      <ScreeningPieChart />

      {/* Recent Screenings Card */}
      <div className={`rounded-xl border p-6 transition-colors ${
        isDark ? 'border-gray-800 bg-gray-900 text-white' : 'border-gray-200 bg-white text-gray-900 shadow-sm'
      }`}>
        <div className="flex items-center justify-between border-b pb-4 mb-5 border-inherit">
          <div>
            <h2 className="text-lg font-semibold">
              Recent Screenings
            </h2>
            <p className={`text-xs mt-0.5 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              Latest passenger screening activities logged at this station.
            </p>
          </div>

          <Link
            to="/history"
            className="text-xs font-semibold text-yellow-500 hover:underline"
          >
            View All History →
          </Link>
        </div>

        <div className="divide-y divide-inherit">
          {recentScreenings.map((screening) => {
            const isPass = screening.status === 'PASS'
            const isReview = screening.status === 'REVIEW'

            return (
              <div
                key={screening.id}
                className="flex items-center justify-between py-3.5 first:pt-0 last:pb-0"
              >
                <div>
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono text-xs font-semibold text-yellow-500">
                      {screening.id}
                    </span>
                    <span className={`text-sm font-medium ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
                      {screening.passenger}
                    </span>
                  </div>
                  <p className={`text-xs mt-0.5 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                    {screening.document}
                  </p>
                </div>

                <div className="text-right flex items-center gap-4">
                  <div>
                    <span className={`text-xs font-mono font-bold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      {screening.risk}% Risk
                    </span>
                  </div>

                  <span className={`px-2.5 py-0.5 rounded text-xs font-semibold border ${
                    isPass
                      ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30'
                      : isReview
                      ? 'bg-amber-500/10 text-amber-500 border-amber-500/30'
                      : 'bg-red-500/10 text-red-500 border-red-500/30'
                  }`}>
                    {screening.status}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default Dashboard