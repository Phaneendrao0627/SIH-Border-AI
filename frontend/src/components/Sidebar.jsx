import { Link } from 'react-router-dom'

function Sidebar() {
  return (
    <aside className="w-64 min-h-screen bg-black text-white border-r border-gray-800 p-6">
      <h1 className="text-2xl font-bold text-yellow-400">
        BorderGuard
      </h1>

      <nav className="mt-10 flex flex-col gap-3">
        
        {/* Dashboard */}
        <Link
          to="/"
          className="rounded-lg px-4 py-3 text-gray-300 hover:bg-yellow-400 hover:text-black"
        >
          Dashboard
        </Link>

        {/* New Screening */}
        <Link
          to="/screening"
          className="rounded-lg px-4 py-3 text-gray-300 hover:bg-yellow-400 hover:text-black"
        >
          New Screening
        </Link>

        {/* History */}
        <Link
          to="/history"
          className="rounded-lg px-4 py-3 text-gray-300 hover:bg-yellow-400 hover:text-black"
        >
          History
        </Link>

        {/* Analytics */}
        <Link
          to="/analytics"
          className="rounded-lg px-4 py-3 text-gray-300 hover:bg-yellow-400 hover:text-black"
        >
          Analytics
        </Link>

      </nav>
    </aside>
  )
}

export default Sidebar