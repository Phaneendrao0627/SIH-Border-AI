function Analytics() {
  const stats = [
    {
      label: "Total Screenings",
      value: "1,248"
    },
    {
      label: "Passed",
      value: "82%"
    },
    {
      label: "Under Review",
      value: "12%"
    },
    {
      label: "Rejected",
      value: "6%"
    }
  ]

  const flags = [
    {
      name: "Expired Document",
      count: 24
    },
    {
      name: "MRZ Mismatch",
      count: 17
    },
    {
      name: "Possible Tampering",
      count: 11
    },
    {
      name: "Face Mismatch",
      count: 7
    }
  ]

  return (
    <div>
      <h1 className="text-3xl font-bold">
        Analytics
      </h1>

      <p className="mt-2 text-gray-400">
        Overview of document screening activity and detected risks.
      </p>

      {/* Statistics */}

      <div className="mt-8 grid grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="rounded-xl border border-gray-800 bg-gray-900 p-6"
          >
            <p className="text-sm text-gray-400">
              {stat.label}
            </p>

            <p className="mt-3 text-3xl font-bold text-yellow-400">
              {stat.value}
            </p>
          </div>
        ))}
      </div>

      {/* Detection Flags */}

      <div className="mt-8 rounded-xl border border-gray-800 bg-gray-900 p-6">

        <h2 className="text-xl font-semibold">
          Common Detection Flags
        </h2>

        <div className="mt-6 space-y-4">
          {flags.map((flag) => (
            <div
              key={flag.name}
              className="flex items-center justify-between border-b border-gray-800 pb-4"
            >
              <p className="text-gray-300">
                {flag.name}
              </p>

              <p className="font-semibold text-yellow-400">
                {flag.count}
              </p>
            </div>
          ))}
        </div>

      </div>
    </div>
  )
}

export default Analytics