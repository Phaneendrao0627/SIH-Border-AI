import { useLocation, Link } from 'react-router-dom'
import RiskScore from '../components/RiskScore'

const DEFAULT_DATA = {
  timestamp: new Date().toLocaleDateString(),
  riskScore: 18,
  document: {
    name: 'ARJUN SHARMA',
    passportNumber: 'Z5839201',
    nationality: 'Indian',
    dateOfBirth: '12 Aug 1994',
    dateOfExpiry: '11 Aug 2034',
    gender: 'Male'
  },
  modules: {
    ocr: {
      status: 'Passed',
      details: 'All identity fields successfully extracted from Machine Readable Zone.'
    },
    validation: {
      status: 'Passed',
      details: 'Document meets ICAO 9303 standards. Checksum digits are valid.'
    },
    tampering: {
      status: 'No Issues Detected',
      details: 'No signs of digital tampering, photo substitution, or text modification.'
    },
    face: {
      status: 'Match Confirmed',
      score: '96.2%',
      details: 'Document photo matches passenger live camera capture.'
    }
  }
}

function Result() {
  const location = useLocation()
  const data = location.state?.screeningResult || DEFAULT_DATA
  const { riskScore, document: doc, modules } = data

  let status = 'PASS'
  let statusBadge = 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'

  if (riskScore >= 70) {
    status = 'REJECT'
    statusBadge = 'bg-red-500/15 text-red-400 border-red-500/30'
  } else if (riskScore >= 40) {
    status = 'REVIEW'
    statusBadge = 'bg-amber-500/15 text-amber-400 border-amber-500/30'
  }

  return (
    <div className="space-y-8 max-w-6xl">
      {/* Page Header */}
      <div className="flex items-center justify-between border-b border-gray-800 pb-5">
        <div>
          <h1 className="text-3xl font-bold text-white">
            Screening Result
          </h1>
          <p className="mt-1 text-sm text-gray-400">
            Verification summary for passenger {doc.name}.
          </p>
        </div>

        <Link
          to="/screening"
          className="rounded-lg bg-gray-800 hover:bg-gray-700 px-4 py-2 text-xs font-semibold text-white border border-gray-700 transition"
        >
          ← New Screening
        </Link>
      </div>

      {/* Top Status & Risk Card */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs text-gray-400">Overall Verification Status</p>
          <div className="mt-2 flex items-center gap-3">
            <span className={`text-xl font-bold px-3 py-1 rounded-md border ${statusBadge}`}>
              {status}
            </span>
            <span className="text-sm text-gray-300">
              {status === 'PASS' && 'Identity verified successfully'}
              {status === 'REVIEW' && 'Manual inspection recommended'}
              {status === 'REJECT' && 'Potential document forgery detected'}
            </span>
          </div>
        </div>

        <RiskScore score={riskScore} />
      </div>

      {/* Extracted Document Information */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
        <h2 className="text-base font-semibold text-white">
          Extracted Document Information
        </h2>
        <p className="mt-1 text-xs text-gray-400">
          Data read from the identity document via OCR.
        </p>

        <div className="mt-5 grid grid-cols-2 md:grid-cols-3 gap-5 text-sm">
          <div>
            <span className="text-xs text-gray-400">Full Name</span>
            <p className="mt-1 font-medium text-white">{doc.name}</p>
          </div>
          <div>
            <span className="text-xs text-gray-400">Passport / ID Number</span>
            <p className="mt-1 font-medium text-white">{doc.passportNumber}</p>
          </div>
          <div>
            <span className="text-xs text-gray-400">Nationality</span>
            <p className="mt-1 font-medium text-white">{doc.nationality}</p>
          </div>
          <div>
            <span className="text-xs text-gray-400">Date of Birth</span>
            <p className="mt-1 font-medium text-white">{doc.dateOfBirth}</p>
          </div>
          <div>
            <span className="text-xs text-gray-400">Date of Expiry</span>
            <p className="mt-1 font-medium text-white">{doc.dateOfExpiry}</p>
          </div>
          <div>
            <span className="text-xs text-gray-400">Gender</span>
            <p className="mt-1 font-medium text-white">{doc.gender}</p>
          </div>
        </div>
      </div>

      {/* Verification Modules 2x2 Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Module 1 */}
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              Module 1: OCR Extraction
            </span>
            <span className="text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
              ✓ {modules?.ocr?.status || 'Passed'}
            </span>
          </div>
          <p className="mt-3 text-sm text-gray-300">
            {modules?.ocr?.details}
          </p>
        </div>

        {/* Module 2 */}
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              Module 2: Document Validation
            </span>
            <span className="text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
              ✓ {modules?.validation?.status || 'Passed'}
            </span>
          </div>
          <p className="mt-3 text-sm text-gray-300">
            {modules?.validation?.details}
          </p>
        </div>

        {/* Module 3 */}
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              Module 3: Tampering Detection
            </span>
            <span className="text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
              ✓ {modules?.tampering?.status || 'No Issues'}
            </span>
          </div>
          <p className="mt-3 text-sm text-gray-300">
            {modules?.tampering?.details}
          </p>
        </div>

        {/* Module 4 */}
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              Module 4: Face Verification
            </span>
            <span className="text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
              ✓ {modules?.face?.status || 'Match Confirmed'}
            </span>
          </div>
          <p className="mt-3 text-sm text-gray-300">
            {modules?.face?.details}
          </p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-800">
        <button
          type="button"
          onClick={() => alert('Clearance approved.')}
          className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-5 py-2 text-sm font-semibold text-white transition"
        >
          Approve Entry
        </button>

        <button
          type="button"
          onClick={() => alert('Flagged for secondary inspection.')}
          className="rounded-lg bg-gray-800 hover:bg-gray-700 px-5 py-2 text-sm font-semibold text-gray-200 border border-gray-700 transition"
        >
          Secondary Inspection
        </button>

        <button
          type="button"
          onClick={() => alert('Entry denied.')}
          className="rounded-lg bg-red-600 hover:bg-red-500 px-5 py-2 text-sm font-semibold text-white transition"
        >
          Deny Entry
        </button>
      </div>
    </div>
  )
}

export default Result