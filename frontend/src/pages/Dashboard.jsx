import StatCard from '../components/StatCard'
import { Link } from 'react-router-dom'

function Dashboard() {

  const recentScreenings = [
    {
      id: "BG-1042",
      document: "Passport",
      risk: 18,
      status: "PASS"
    },
    {
      id: "BG-1041",
      document: "Passport",
      risk: 58,
      status: "REVIEW"
    },
    {
      id: "BG-1040",
      document: "National ID",
      risk: 82,
      status: "REJECT"
    }
  ]

  return (
    <div>

      <h1 className="text-3xl font-bold">
        Officer Dashboard
      </h1>

      <p className="mt-2 text-gray-400">
        Monitor and manage identity screenings.
      </p>

      <Link
        to="/screening"
        className="mt-6 inline-block rounded-lg bg-yellow-400 px-5 py-3 font-semibold text-black hover:bg-yellow-300"
      >
        + New Screening
      </Link>

      {/* Statistics */}

      <div className="mt-8 grid grid-cols-4 gap-6">

        <StatCard
          title="Screened Today"
          value={128}
        />

        <StatCard
          title="Passed"
          value={111}
        />

        <StatCard
          title="Needs Review"
          value={14}
        />

        <StatCard
          title="Rejected"
          value={3}
        />

      </div>

      {/* Recent Screenings */}

      <div className="mt-8 rounded-xl border border-gray-800 bg-gray-900 p-6">

        <div className="flex items-center justify-between">

          <div>
            <h2 className="text-xl font-semibold">
              Recent Screenings
            </h2>

            <p className="mt-1 text-sm text-gray-400">
              Latest passenger screening activity.
            </p>
          </div>

          <Link
            to="/history"
            className="text-sm font-medium text-yellow-400 hover:text-yellow-300"
          >
            View History →
          </Link>

        </div>

        <div className="mt-6 space-y-4">

          {recentScreenings.map((screening) => (

            <div
              key={screening.id}
              className="flex items-center justify-between border-b border-gray-800 pb-4"
            >

              <div>

                <p className="font-medium">
                  {screening.id}
                </p>

                <p className="text-sm text-gray-400">
                  {screening.document}
                </p>

              </div>

              <div className="text-right">

                <p className="font-medium">
                  {screening.risk}%
                </p>

                <p className="text-sm text-yellow-400">
                  {screening.status}
                </p>

              </div>

            </div>

          ))}

        </div>

      </div>

    </div>
  )
}

export default Dashboard