function RiskScore({ score }) {

  let riskLevel

  if (score < 40) {
    riskLevel = "Low Risk"
  } else if (score < 70) {
    riskLevel = "Review"
  } else {
    riskLevel = "High Risk"
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
      <p className="text-sm text-gray-400">
        Risk Score
      </p>

      <p className="mt-2 text-4xl font-bold text-yellow-400">
        {score}%
      </p>

      <p className="mt-2 text-sm text-gray-400">
        {riskLevel}
      </p>
    </div>
  )
}

export default RiskScore