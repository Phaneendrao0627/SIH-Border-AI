function StatCard({ title, value }) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
      <p className="text-sm text-gray-400">{title}</p>
      <p className="mt-2 text-3xl font-bold text-yellow-400">{value}</p>
    </div>
  )
}

export default StatCard