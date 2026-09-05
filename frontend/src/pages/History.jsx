import { useState } from 'react'
import { useTheme } from '../context/ThemeContext'

function History() {
  const { isDark } = useTheme()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')

  const records = [
    {
      id: "BG-1042",
      passenger: "Arjun Sharma",
      document: "Passport (Z5839201)",
      date: "05 Sep 2026, 14:32",
      risk: 18,
      status: "PASS"
    },
    {
      id: "BG-1041",
      passenger: "Michael Chen",
      document: "Passport (E9201844)",
      date: "05 Sep 2026, 13:15",
      risk: 58,
      status: "REVIEW"
    },
    {
      id: "BG-1040",
      passenger: "Elena Rostova",
      document: "National ID (ID4091)",
      date: "05 Sep 2026, 11:40",
      risk: 82,
      status: "REJECT"
    },
    {
      id: "BG-1039",
      passenger: "David Miller",
      document: "Passport (P1104821)",
      date: "04 Sep 2026, 19:22",
      risk: 12,
      status: "PASS"
    },
    {
      id: "BG-1038",
      passenger: "Amina Al-Mansoor",
      document: "Passport (N8830192)",
      date: "04 Sep 2026, 18:05",
      risk: 22,
      status: "PASS"
    },
    {
      id: "BG-1037",
      passenger: "Carlos Gomez",
      document: "Passport (G3491022)",
      date: "04 Sep 2026, 16:48",
      risk: 74,
      status: "REJECT"
    },
    {
      id: "BG-1036",
      passenger: "Priya Patel",
      document: "Visa Sticker (V9012388)",
      date: "04 Sep 2026, 15:10",
      risk: 45,
      status: "REVIEW"
    }
  ]

  const filteredRecords = records.filter((r) => {
    const matchesSearch =
      r.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.passenger.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.document.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesStatus =
      statusFilter === 'ALL' || r.status === statusFilter

    return matchesSearch && matchesStatus
  })

  return (
    <div className="space-y-8 max-w-6xl">
      {/* Page Header */}
      <div>
        <h1 className={`text-3xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Screening History & Audit Trail
        </h1>
        <p className={`mt-1 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Search and review historical passenger verification records and inspection decisions.
        </p>
      </div>

      {/* Search & Filter Toolbar */}
      <div className={`rounded-xl border p-4 flex flex-col sm:flex-row items-center justify-between gap-4 transition-colors ${
        isDark ? 'border-gray-800 bg-gray-900' : 'border-gray-200 bg-white shadow-sm'
      }`}>
        {/* Search Input */}
        <div className="relative w-full sm:w-80">
          <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400 text-sm">
            🔍
          </span>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by ID, name, or document..."
            className={`w-full rounded-lg pl-9 pr-4 py-2 text-xs border transition focus:outline-none ${
              isDark
                ? 'bg-gray-950 border-gray-700 text-white placeholder-gray-500 focus:border-yellow-400'
                : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-400 focus:border-yellow-500'
            }`}
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-2 self-start sm:self-auto overflow-x-auto w-full sm:w-auto">
          {['ALL', 'PASS', 'REVIEW', 'REJECT'].map((status) => {
            const isActive = statusFilter === status
            return (
              <button
                key={status}
                type="button"
                onClick={() => setStatusFilter(status)}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition border ${
                  isActive
                    ? 'bg-yellow-400 text-black border-yellow-400'
                    : isDark
                    ? 'bg-gray-950 text-gray-300 border-gray-800 hover:bg-gray-800'
                    : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'
                }`}
              >
                {status === 'ALL' ? 'All Records' : status}
              </button>
            )
          })}
        </div>
      </div>

      {/* History Records Table */}
      <div className={`overflow-hidden rounded-xl border transition-colors ${
        isDark ? 'border-gray-800 bg-gray-900' : 'border-gray-200 bg-white shadow-sm'
      }`}>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className={`border-b ${isDark ? 'border-gray-800 text-gray-400' : 'border-gray-200 text-gray-500'}`}>
              <tr>
                <th className="px-6 py-3.5 font-semibold">Screening ID</th>
                <th className="px-6 py-3.5 font-semibold">Passenger Name</th>
                <th className="px-6 py-3.5 font-semibold">Travel Document</th>
                <th className="px-6 py-3.5 font-semibold">Timestamp</th>
                <th className="px-6 py-3.5 font-semibold">Risk Score</th>
                <th className="px-6 py-3.5 font-semibold">Verdict</th>
              </tr>
            </thead>

            <tbody className={`divide-y ${isDark ? 'divide-gray-800/60' : 'divide-gray-100'}`}>
              {filteredRecords.length > 0 ? (
                filteredRecords.map((record) => {
                  const isPass = record.status === 'PASS'
                  const isReview = record.status === 'REVIEW'

                  return (
                    <tr
                      key={record.id}
                      className={`transition ${isDark ? 'hover:bg-gray-800/30' : 'hover:bg-gray-50'}`}
                    >
                      <td className="px-6 py-4 font-mono font-bold text-yellow-500">
                        {record.id}
                      </td>

                      <td className={`px-6 py-4 font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>
                        {record.passenger}
                      </td>

                      <td className={`px-6 py-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                        {record.document}
                      </td>

                      <td className={`px-6 py-4 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                        {record.date}
                      </td>

                      <td className={`px-6 py-4 font-mono font-bold ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
                        {record.risk}%
                      </td>

                      <td className="px-6 py-4">
                        <span className={`inline-block px-2.5 py-0.5 rounded text-xs font-semibold border ${
                          isPass
                            ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30'
                            : isReview
                            ? 'bg-amber-500/10 text-amber-500 border-amber-500/30'
                            : 'bg-red-500/10 text-red-500 border-red-500/30'
                        }`}>
                          {record.status}
                        </span>
                      </td>
                    </tr>
                  )
                })
              ) : (
                <tr>
                  <td colSpan="6" className={`px-6 py-8 text-center ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                    No matching screening records found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className={`p-4 border-t flex items-center justify-between text-xs ${
          isDark ? 'border-gray-800 text-gray-500' : 'border-gray-200 text-gray-400'
        }`}>
          <span>Showing {filteredRecords.length} of {records.length} records</span>
          <span>Station Terminal #04 • Immutable Audit Trail</span>
        </div>
      </div>
    </div>
  )
}

export default History