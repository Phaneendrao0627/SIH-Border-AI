function History() {
  const history = [
    {
      id: "BG-1042",
      document: "Passport",
      date: "01 Sep 2026",
      risk: 18,
      status: "PASS"
    },
    {
      id: "BG-1041",
      document: "Passport",
      date: "01 Sep 2026",
      risk: 58,
      status: "REVIEW"
    },
    {
      id: "BG-1040",
      document: "National ID",
      date: "31 Aug 2026",
      risk: 82,
      status: "REJECT"
    }
  ]

  return (
    <div>
      <h1 className="text-3xl font-bold">
        Screening History
      </h1>

      <p className="mt-2 text-gray-400">
        View previous document screening records.
      </p>

      <div className="mt-8 overflow-hidden rounded-xl border border-gray-800 bg-gray-900">

        <table className="w-full text-left">

          <thead className="border-b border-gray-800 text-sm text-gray-400">
            <tr>
              <th className="px-6 py-4">Screening ID</th>
              <th className="px-6 py-4">Document</th>
              <th className="px-6 py-4">Date</th>
              <th className="px-6 py-4">Risk Score</th>
              <th className="px-6 py-4">Status</th>
            </tr>
          </thead>

          <tbody>
            {history.map((record) => (
              <tr
                key={record.id}
                className="border-b border-gray-800"
              >
                <td className="px-6 py-4 font-medium">
                  {record.id}
                </td>

                <td className="px-6 py-4">
                  {record.document}
                </td>

                <td className="px-6 py-4 text-gray-400">
                  {record.date}
                </td>

                <td className="px-6 py-4">
                  {record.risk}%
                </td>

                <td className="px-6 py-4 font-semibold text-yellow-400">
                  {record.status}
                </td>
              </tr>
            ))}
          </tbody>

        </table>
      </div>
    </div>
  )
}

export default History