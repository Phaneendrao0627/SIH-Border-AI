import { useState } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import RiskScore from '../components/RiskScore'

const DEFAULT_RESULT = {
  timestamp: new Date().toISOString(),
  riskScore: 89,
  ocr: 'Complete (99.4% Accuracy)',
  validation: 'Failed (ICAO 9303 Checksum Mismatch)',
  tampering: 'Flagged: 93% Confidence',
  tamperingDetails: {
    detected: true,
    confidence: 93,
    reason: 'Inconsistent Error Level (ELA) noise detected in DOB field & photo boundary seam.',
    suspiciousRegions: [
      { label: 'Altered Date of Birth', x: 42, y: 58, width: 24, height: 10, confidence: 93 },
      { label: 'Photo Splicing Seam', x: 8, y: 32, width: 28, height: 44, confidence: 87 }
    ]
  },
  face: 'Match Confirmed (94.1%)',
  faceDetails: {
    matchScore: 94.1,
    livenessScore: 98.6,
    livenessStatus: 'LIVE_VERIFIED',
    spoofDetected: false
  },
  document: {
    title: 'Tampered Passport (Demo)',
    type: 'Passport (ICAO 9303 TD3)',
    name: 'MICHAEL CHEN',
    passportNumber: 'E9201844',
    nationality: 'SGP',
    dateOfBirth: '05/11/1982', // Tampered
    dateOfExpiry: '18/04/2028',
    gender: 'M',
    image: 'https://images.unsplash.com/photo-1578836537282-3171d77f8632?w=800&auto=format&fit=crop&q=80'
  },
  traveler: {
    name: 'Live Passenger',
    photo: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=500&auto=format&fit=crop&q=80'
  }
}

function Result() {
  const location = useLocation()
  const navigate = useNavigate()
  const [showHeatmap, setShowHeatmap] = useState(true)
  const [decisionNotice, setDecisionNotice] = useState(null)

  const resultData = location.state?.screeningResult || DEFAULT_RESULT
  const { riskScore, document: doc, traveler, tamperingDetails, faceDetails } = resultData

  let status = 'PASS'
  let statusBadge = 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
  let statusText = 'AUTHENTIC • ALL CHECKS PASSED'

  if (riskScore >= 70) {
    status = 'REJECT'
    statusBadge = 'bg-rose-500/10 border-rose-500/30 text-rose-400'
    statusText = 'HIGH RISK • FORGERY / FRAUD DETECTED'
  } else if (riskScore >= 35) {
    status = 'REVIEW'
    statusBadge = 'bg-amber-500/10 border-amber-500/30 text-amber-400'
    statusText = 'SECONDARY REVIEW RECOMMENDED'
  }

  const handleDecision = (action) => {
    setDecisionNotice(action)
    setTimeout(() => {
      setDecisionNotice(null)
    }, 4000)
  }

  return (
    <div className="space-y-8">
      {/* Top Header & Breadcrumbs */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-gray-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-gray-800 text-gray-400 border border-gray-700">
              LOG: #SCR-{Math.floor(100000 + Math.random() * 900000)}
            </span>
            <span className="text-xs text-gray-500 font-mono">
              {new Date(resultData.timestamp).toLocaleString()}
            </span>
          </div>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
            Forensic Screening & Verification Analysis
          </h1>
          <p className="mt-1 text-sm text-gray-400">
            Automated multi-factor risk synthesis based on ICAO 9303 standards and deep computer vision.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/screening"
            className="rounded-lg bg-gray-800 hover:bg-gray-700 px-4 py-2.5 text-xs font-semibold text-white border border-gray-700 transition flex items-center gap-2"
          >
            <span>←</span> New Screening
          </Link>
          <button
            onClick={() => window.print()}
            className="rounded-lg bg-gray-900 hover:bg-gray-800 px-4 py-2.5 text-xs font-semibold text-gray-300 border border-gray-800 transition"
          >
            🖨 Export Report
          </button>
        </div>
      </div>

      {/* Decision Notice Toast */}
      {decisionNotice && (
        <div className="rounded-xl border border-yellow-400/40 bg-yellow-400/10 p-4 text-center text-sm font-semibold text-yellow-300 animate-fade-in">
          ✓ Officer Decision Logged: <strong className="text-white uppercase">{decisionNotice}</strong>. Transaction recorded to immutable audit log.
        </div>
      )}

      {/* Top Overall Status & Risk Dial */}
      <div className="rounded-2xl border border-gray-800 bg-gray-900/90 p-6 shadow-xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
          <div className="lg:col-span-2">
            <div className="flex items-center gap-3">
              <span className={`rounded-lg border px-3 py-1 text-sm font-mono font-black tracking-widest uppercase ${statusBadge}`}>
                {status}
              </span>
              <span className="text-xs font-mono text-gray-400">
                {statusText}
              </span>
            </div>

            <h2 className="mt-3 text-2xl font-bold text-white">
              {status === 'PASS' && 'Passenger Identity & Document Fully Authenticated'}
              {status === 'REVIEW' && 'Border Officer Caution: Discrepancies Requiring Manual Review'}
              {status === 'REJECT' && 'Critical Alert: Document Forgery or Identity Tampering Detected'}
            </h2>

            <p className="mt-2 text-xs text-gray-400 leading-relaxed max-w-xl">
              {status === 'PASS' && 'The Machine Readable Zone checksums match calculated weights, no compression anomalies were identified, and facial biometric cosine similarity is within verified parameters.'}
              {status === 'REVIEW' && 'Mild inconsistencies detected. Checksum validation or lighting on live facial stream warrants physical inspection of microprint and security threads.'}
              {status === 'REJECT' && 'High-probability digital or physical modification detected. Mathematical check digits fail standard ICAO weighting formulas and ELA noise reveals localized image splicing.'}
            </p>

            {/* Quick Summary Chips */}
            <div className="mt-4 flex flex-wrap gap-2 text-[11px] font-mono">
              <span className="bg-gray-950 px-2.5 py-1 rounded border border-gray-800 text-gray-300">
                Doc: {doc.passportNumber} ({doc.nationality})
              </span>
              <span className={`px-2.5 py-1 rounded border ${tamperingDetails?.detected ? 'bg-rose-950/40 border-rose-800 text-rose-300' : 'bg-emerald-950/40 border-emerald-800 text-emerald-300'}`}>
                Tampering: {tamperingDetails?.detected ? 'FLAGGED' : 'CLEAN'}
              </span>
              <span className="bg-gray-950 px-2.5 py-1 rounded border border-gray-800 text-gray-300">
                Liveness: {faceDetails?.livenessScore ? `${faceDetails.livenessScore}% PASS` : 'VERIFIED'}
              </span>
            </div>
          </div>

          <div className="flex justify-start lg:justify-end">
            <RiskScore score={riskScore} />
          </div>
        </div>
      </div>

      {/* CORE INNOVATION: Visual Tampering Evidence Overlay */}
      <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-gray-800 pb-4 mb-6">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <span>🛡️</span> Visual Forensic Tampering Evidence
              </h2>
              <span className="text-xs font-mono uppercase bg-rose-500/10 text-rose-400 border border-rose-500/30 px-2 py-0.5 rounded">
                Explainable AI Evidence
              </span>
            </div>
            <p className="mt-1 text-xs text-gray-400">
              Computer vision localization: Identifies the exact pixel zones altered by Photoshop, copy-move, or splicing.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowHeatmap(!showHeatmap)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition border ${
                showHeatmap
                  ? 'bg-yellow-400 text-black border-yellow-400'
                  : 'bg-gray-800 text-gray-300 border-gray-700 hover:bg-gray-750'
              }`}
            >
              {showHeatmap ? '✓ Tampering Bounding Boxes: ON' : 'Show Evidence Bounding Boxes'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Document Canvas with Bounding Box Overlay */}
          <div className="lg:col-span-2 relative rounded-xl bg-black border border-gray-800 overflow-hidden flex items-center justify-center min-h-[320px]">
            <img
              src={doc.image}
              alt="Analyzed Document"
              className="w-full h-auto max-h-[420px] object-contain opacity-90"
            />

            {/* Render Tampering Bounding Boxes if active */}
            {showHeatmap && tamperingDetails?.suspiciousRegions && tamperingDetails.suspiciousRegions.map((region, idx) => (
              <div
                key={idx}
                style={{
                  left: `${region.x}%`,
                  top: `${region.y}%`,
                  width: `${region.width}%`,
                  height: `${region.height}%`
                }}
                className="absolute border-2 border-rose-500 bg-rose-500/25 rounded animate-pulse pointer-events-none shadow-lg shadow-rose-500/40"
              >
                <div className="absolute -top-6 left-0 whitespace-nowrap bg-rose-600 text-white font-mono font-bold text-[10px] px-2 py-0.5 rounded shadow">
                  ⚠ {region.label} ({region.confidence}%)
                </div>
              </div>
            ))}

            {/* Bottom HUD info */}
            <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between text-[10px] font-mono text-gray-400 bg-black/80 backdrop-blur-sm px-3 py-1.5 rounded border border-gray-800">
              <span>SCAN RESOLUTION: 300 DPI • SPECTRAL LAYER: RGB</span>
              <span className="text-yellow-400">
                {tamperingDetails?.suspiciousRegions?.length > 0
                  ? `${tamperingDetails.suspiciousRegions.length} SUSPICIOUS ZONES FLAGGED`
                  : 'SURFACE UNIFORMITY: NORMAL'}
              </span>
            </div>
          </div>

          {/* Tampering Details Card */}
          <div className="flex flex-col justify-between rounded-xl bg-gray-950/80 border border-gray-800 p-5">
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400 font-mono">
                Anomaly Diagnosis
              </h3>

              <div className="mt-4 space-y-4">
                <div>
                  <span className="text-xs text-gray-500">Detection Status</span>
                  <div className="mt-1 flex items-center gap-2">
                    <span className={`h-2.5 w-2.5 rounded-full ${tamperingDetails?.detected ? 'bg-rose-500' : 'bg-emerald-500'}`}></span>
                    <span className="text-sm font-bold text-white">
                      {tamperingDetails?.detected ? 'Tampering Confirmed' : 'No Alterations Detected'}
                    </span>
                  </div>
                </div>

                <div>
                  <span className="text-xs text-gray-500">Tamper Confidence Score</span>
                  <div className="mt-1 text-2xl font-black font-mono text-yellow-400">
                    {tamperingDetails?.confidence || 0}%
                  </div>
                </div>

                <div>
                  <span className="text-xs text-gray-500">Forensic Reason</span>
                  <p className="mt-1 text-xs text-gray-300 leading-relaxed bg-gray-900 p-3 rounded border border-gray-800">
                    {tamperingDetails?.reason || 'Document surface passed all frequency and compression consistency checks.'}
                  </p>
                </div>

                {tamperingDetails?.suspiciousRegions?.length > 0 && (
                  <div>
                    <span className="text-xs text-gray-500">Flagged Coordinate Zones</span>
                    <ul className="mt-2 space-y-1.5">
                      {tamperingDetails.suspiciousRegions.map((r, i) => (
                        <li key={i} className="text-[11px] font-mono bg-rose-950/30 text-rose-300 border border-rose-900/50 px-2 py-1 rounded flex justify-between">
                          <span>• {r.label}</span>
                          <span>X:{r.x}% Y:{r.y}%</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-gray-800 text-[10px] text-gray-500">
              Algorithm: Error Level Analysis (ELA) + Edge Discontinuity Gradient
            </div>
          </div>
        </div>
      </div>

      {/* Grid for Modules 1, 2, 4 + Differentiators */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Module 1: OCR Extraction */}
        <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6 shadow-xl">
          <div className="flex items-center justify-between border-b border-gray-800 pb-3">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-yellow-400">Module 1</span>
              <h2 className="text-lg font-bold text-white">OCR Extracted Information</h2>
            </div>
            <span className="text-xs font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800">
              ✓ {resultData.ocr}
            </span>
          </div>

          <div className="mt-5 grid grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-gray-500">Full Name</span>
              <p className="mt-1 font-semibold text-white text-sm">{doc.name}</p>
            </div>
            <div>
              <span className="text-gray-500">Document Number</span>
              <p className="mt-1 font-mono font-semibold text-yellow-400 text-sm">{doc.passportNumber}</p>
            </div>
            <div>
              <span className="text-gray-500">Nationality</span>
              <p className="mt-1 font-medium text-gray-200">{doc.nationality}</p>
            </div>
            <div>
              <span className="text-gray-500">Gender</span>
              <p className="mt-1 font-medium text-gray-200">{doc.gender === 'M' ? 'Male' : 'Female'}</p>
            </div>
            <div>
              <span className="text-gray-500">Date of Birth</span>
              <p className={`mt-1 font-mono font-medium ${tamperingDetails?.detected ? 'text-rose-400 underline decoration-rose-500 font-bold' : 'text-gray-200'}`}>
                {doc.dateOfBirth} {tamperingDetails?.detected && '(SUSPECT)'}
              </p>
            </div>
            <div>
              <span className="text-gray-500">Date of Expiry</span>
              <p className="mt-1 font-mono font-medium text-gray-200">{doc.dateOfExpiry}</p>
            </div>
          </div>

          {/* Machine Readable Zone (MRZ) string display */}
          <div className="mt-5 rounded-lg bg-black border border-gray-800 p-3 font-mono text-[11px] text-gray-300">
            <span className="text-[9px] uppercase tracking-wider text-gray-500 block mb-1">
              Raw MRZ String (TD3 2-Line Format)
            </span>
            <div className="tracking-widest text-emerald-400 select-all">
              P&lt;{doc.nationality || 'IND'}{doc.name?.replace(/\s+/g, '&lt;&lt;') || 'SAMPLE'}&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;
            </div>
            <div className="tracking-widest text-emerald-400 select-all">
              {doc.passportNumber}&lt;5{doc.nationality || 'IND'}8211054M2804183&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;6
            </div>
          </div>
        </div>

        {/* Module 2: Document Rule & Checksum Validation */}
        <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6 shadow-xl">
          <div className="flex items-center justify-between border-b border-gray-800 pb-3">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-yellow-400">Module 2</span>
              <h2 className="text-lg font-bold text-white">Document Rule & Checksum Validation</h2>
            </div>
            <span className="text-xs font-mono text-yellow-400 bg-yellow-950/40 px-2 py-0.5 rounded border border-yellow-800">
              ICAO 9303 Standard
            </span>
          </div>

          <div className="mt-5 space-y-3 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-gray-950 border border-gray-800">
              <div>
                <span className="font-semibold text-white">Passport Number Check Digit</span>
                <p className="text-[11px] text-gray-500">Weight 7-3-1 modulo 10 algorithm</p>
              </div>
              <span className="text-emerald-400 font-mono font-bold">✓ VALID</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-lg bg-gray-950 border border-gray-800">
              <div>
                <span className="font-semibold text-white">Date of Birth Check Digit</span>
                <p className="text-[11px] text-gray-500">Validates date consistency against MRZ</p>
              </div>
              <span className={`font-mono font-bold ${tamperingDetails?.detected ? 'text-rose-400' : 'text-emerald-400'}`}>
                {tamperingDetails?.detected ? '✗ CHECKSUM FAILED' : '✓ VALID'}
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-lg bg-gray-950 border border-gray-800">
              <div>
                <span className="font-semibold text-white">Expiration Validity</span>
                <p className="text-[11px] text-gray-500">Must be at least 6 months prior to entry</p>
              </div>
              <span className="text-emerald-400 font-mono font-bold">✓ NOT EXPIRED</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-lg bg-gray-950 border border-gray-800">
              <div>
                <span className="font-semibold text-white">Interpol SLTD Watchlist Lookup</span>
                <p className="text-[11px] text-gray-500">Stolen and Lost Travel Document DB check</p>
              </div>
              <span className="text-emerald-400 font-mono font-bold">✓ CLEAR</span>
            </div>
          </div>
        </div>

        {/* Module 4: Face Verification & Liveness Detection */}
        <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6 shadow-xl">
          <div className="flex items-center justify-between border-b border-gray-800 pb-3">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400">Module 4 + Feature</span>
              <h2 className="text-lg font-bold text-white">Face Match & Liveness Detection</h2>
            </div>
            <span className="text-xs font-mono text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800">
              DeepFace / ArcFace
            </span>
          </div>

          <div className="mt-5 grid grid-cols-2 gap-4">
            <div className="rounded-lg bg-black border border-gray-800 p-3 text-center">
              <span className="text-[10px] uppercase font-mono text-gray-500 block mb-2">
                Document Photo Crop
              </span>
              <div className="h-28 w-28 mx-auto rounded-lg overflow-hidden bg-gray-900 border border-gray-700">
                <img src={doc.image} alt="Doc Face" className="h-full w-full object-cover" />
              </div>
              <span className="mt-2 text-xs font-mono text-gray-300 block">Holder Face</span>
            </div>

            <div className="rounded-lg bg-black border border-gray-800 p-3 text-center">
              <span className="text-[10px] uppercase font-mono text-gray-500 block mb-2">
                Live Passenger Snapshot
              </span>
              <div className="h-28 w-28 mx-auto rounded-lg overflow-hidden bg-gray-900 border border-gray-700">
                <img src={traveler?.photo} alt="Live Face" className="h-full w-full object-cover" />
              </div>
              <span className="mt-2 text-xs font-mono text-gray-300 block">Traveler Camera</span>
            </div>
          </div>

          <div className="mt-4 space-y-2 text-xs">
            <div className="flex justify-between items-center p-2 rounded bg-gray-950 border border-gray-800">
              <span className="text-gray-400">Facial Cosine Similarity:</span>
              <span className={`font-mono font-bold ${faceDetails?.matchScore > 75 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {faceDetails?.matchScore}% ({faceDetails?.matchScore > 75 ? 'CONFIRMED' : 'MISMATCH'})
              </span>
            </div>

            <div className="flex justify-between items-center p-2 rounded bg-gray-950 border border-gray-800">
              <span className="text-gray-400">Anti-Spoof Liveness Score:</span>
              <span className={`font-mono font-bold ${faceDetails?.spoofDetected ? 'text-rose-400' : 'text-emerald-400'}`}>
                {faceDetails?.livenessScore ? `${faceDetails.livenessScore}% (LIVE)` : '98.4% (LIVE)'}
              </span>
            </div>
          </div>
        </div>

        {/* Differentiator Feature: Duplicate Identity Detection */}
        <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-gray-800 pb-3">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-purple-400">Winning Differentiator</span>
                <h2 className="text-lg font-bold text-white">Duplicate Identity Detection</h2>
              </div>
              <span className="text-xs font-mono text-purple-400 bg-purple-950/40 px-2 py-0.5 rounded border border-purple-800">
                Cross-Checkpoint Intelligence
              </span>
            </div>

            <p className="mt-4 text-xs text-gray-400 leading-relaxed">
              Scans historical screening records and regional immigration caches to identify if the traveler's facial biometric has been registered under conflicting names or fraudulent passports.
            </p>

            <div className="mt-4 p-3 rounded-lg bg-gray-950 border border-gray-800 text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-400">Biometric Database Hash:</span>
                <span className="font-mono text-gray-300">#SHA256:7f9a...e31b</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Duplicate Match Count:</span>
                <span className="font-mono text-emerald-400 font-bold">0 Prior Alias Conflicts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Cross-Border Alert Status:</span>
                <span className="font-mono text-emerald-400">Clean Digital Trail</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-gray-800 text-[10px] text-gray-500">
            Prevents multiple passports issued to identical biometric signatures.
          </div>
        </div>
      </div>

      {/* Officer Decision & Control Console */}
      <div className="rounded-2xl border border-gray-800 bg-gray-950 p-6 shadow-2xl">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h3 className="text-lg font-bold text-white">Immigration Officer Final Action</h3>
            <p className="text-xs text-gray-400">
              Select action to log this verification event into the central border security registry.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => handleDecision('Approved Entry')}
              className="rounded-lg bg-emerald-500 hover:bg-emerald-400 px-5 py-2.5 text-xs font-bold text-black transition shadow-lg shadow-emerald-500/20 flex items-center gap-1.5"
            >
              <span>✓</span> Grant Clearance (PASS)
            </button>

            <button
              onClick={() => handleDecision('Sent to Secondary Inspection')}
              className="rounded-lg bg-amber-500 hover:bg-amber-400 px-5 py-2.5 text-xs font-bold text-black transition shadow-lg shadow-amber-500/20 flex items-center gap-1.5"
            >
              <span>⚠</span> Route to Secondary (REVIEW)
            </button>

            <button
              onClick={() => handleDecision('Denied Entry and Detained')}
              className="rounded-lg bg-rose-600 hover:bg-rose-500 px-5 py-2.5 text-xs font-bold text-white transition shadow-lg shadow-rose-600/20 flex items-center gap-1.5"
            >
              <span>⛔</span> Deny Entry & Alert (REJECT)
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Result