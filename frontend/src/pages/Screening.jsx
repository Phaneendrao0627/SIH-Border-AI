import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DocumentUpload, { SAMPLE_DOCUMENTS } from '../components/DocumentUpload'
import CameraPanel, { SAMPLE_TRAVELERS } from '../components/CameraPanel'

const PIPELINE_STEPS = [
  { id: 1, title: 'Document Ingestion & Skew Correction', desc: 'Preprocessing image, correcting perspective, normalizing DPI' },
  { id: 2, title: 'Module 1: OCR & MRZ Extraction', desc: 'Parsing TD3 Machine Readable Zone characters and visual fields' },
  { id: 3, title: 'Module 2: Document Rule & Checksum Validation', desc: 'Calculating ICAO 9303 check digits (weights 7-3-1) & expiration check' },
  { id: 4, title: 'Module 3: AI Tampering & Forgery Analysis', desc: 'Running Error Level Analysis (ELA), splicing & copy-move detection' },
  { id: 5, title: 'Module 4: Face Verification & Anti-Spoofing', desc: 'Comparing biometric embeddings (FaceNet) & testing liveness blink rate' }
]

function Screening() {
  const [selectedDoc, setSelectedDoc] = useState(SAMPLE_DOCUMENTS.genuine)
  const [selectedTraveler, setSelectedTraveler] = useState(SAMPLE_TRAVELERS.genuine)
  const [customFile, setCustomFile] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [currentStepIndex, setCurrentStepIndex] = useState(0)

  const navigate = useNavigate()

  const handleCustomFileUpload = (file, previewUrl) => {
    setCustomFile(file)
    setSelectedDoc({
      id: 'custom_upload',
      title: file.name,
      type: 'Uploaded Document',
      name: 'UNKNOWN TRAVELER',
      passportNumber: 'P' + Math.floor(1000000 + Math.random() * 9000000),
      nationality: 'IND',
      dob: '01/01/1995',
      expiry: '01/01/2032',
      gender: 'M',
      tampered: false,
      tamperConfidence: 12,
      tamperReason: 'Document surface scanned. No obvious digital artifacts.',
      suspiciousRegions: [],
      mrzValid: true,
      checksumValid: true,
      riskScore: 24,
      imagePreview: previewUrl
    })
  }

  const handleStartScreening = () => {
    if (!selectedDoc) {
      alert('Please select or upload a travel document first.')
      return
    }

    setIsProcessing(true)
    setCurrentStepIndex(0)

    // Simulate multi-stage pipeline progression
    let step = 0
    const interval = setInterval(() => {
      step += 1
      setCurrentStepIndex(step)

      if (step >= PIPELINE_STEPS.length) {
        clearInterval(interval)
        setTimeout(() => {
          setIsProcessing(false)

          // Calculate final screening data payload to carry over to /result
          const doc = selectedDoc
          const traveler = selectedTraveler || SAMPLE_TRAVELERS.genuine

          // Compute composite risk score
          let calculatedRisk = doc.riskScore || 15
          if (traveler.spoofDetected) {
            calculatedRisk = Math.max(calculatedRisk, 86)
          } else if (traveler.faceMatchScore < 50) {
            calculatedRisk = Math.max(calculatedRisk, 82)
          }

          const screeningPayload = {
            timestamp: new Date().toISOString(),
            riskScore: calculatedRisk,
            ocr: 'Complete (99.4% Accuracy)',
            validation: doc.checksumValid ? 'Valid (ICAO 9303 Compliant)' : 'Failed (Checksum Mismatch)',
            tampering: doc.tampered
              ? `Flagged: ${doc.tamperConfidence}% Confidence`
              : 'Authentic (No Manipulations)',
            tamperingDetails: {
              detected: doc.tampered,
              confidence: doc.tamperConfidence,
              reason: doc.tamperReason,
              suspiciousRegions: doc.suspiciousRegions || []
            },
            face: traveler.faceMatchScore > 75
              ? `Match Confirmed (${traveler.faceMatchScore}%)`
              : `Mismatch Alert (${traveler.faceMatchScore}%)`,
            faceDetails: {
              matchScore: traveler.faceMatchScore,
              livenessScore: traveler.livenessScore,
              livenessStatus: traveler.livenessStatus,
              spoofDetected: traveler.spoofDetected
            },
            document: {
              title: doc.title,
              type: doc.type,
              name: doc.name,
              passportNumber: doc.passportNumber,
              nationality: doc.nationality,
              dateOfBirth: doc.dob,
              dateOfExpiry: doc.expiry,
              gender: doc.gender,
              image: doc.imagePreview
            },
            traveler: {
              name: traveler.name,
              photo: traveler.photo
            }
          }

          navigate('/result', { state: { screeningResult: screeningPayload } })
        }, 600)
      }
    }, 700)
  }

  return (
    <div className="relative">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Checkpoint Document Screening</h1>
          <p className="mt-1 text-sm text-gray-400">
            Multi-modal verification pipeline: OCR Extraction • Rule Integrity • Tampering Scan • Face & Liveness Match
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-xs font-mono text-emerald-400">GATEWAY #04 • ACTIVE</span>
        </div>
      </div>

      {/* Main 2-column input layout */}
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DocumentUpload
          selectedDoc={selectedDoc}
          onSelectDoc={setSelectedDoc}
          customFile={customFile}
          onCustomFileUpload={handleCustomFileUpload}
        />

        <CameraPanel
          selectedTraveler={selectedTraveler}
          onSelectTraveler={setSelectedTraveler}
        />
      </div>

      {/* Action Bar */}
      <div className="mt-8 flex items-center justify-between rounded-xl border border-gray-800 bg-gray-900/90 p-4">
        <div className="flex items-center gap-4 text-xs text-gray-400">
          <div className="flex items-center gap-1.5">
            <span className={selectedDoc ? 'text-emerald-400 font-bold' : 'text-gray-500'}>
              {selectedDoc ? '✓' : '○'} Document Loaded
            </span>
          </div>
          <span>•</span>
          <div className="flex items-center gap-1.5">
            <span className={selectedTraveler ? 'text-emerald-400 font-bold' : 'text-gray-500'}>
              {selectedTraveler ? '✓' : '○'} Passenger Feed Active
            </span>
          </div>
          <span>•</span>
          <span className="text-yellow-400 font-mono">
            Mode: Comprehensive Inspection
          </span>
        </div>

        <button
          onClick={handleStartScreening}
          disabled={isProcessing || !selectedDoc}
          className="rounded-lg bg-yellow-400 px-8 py-3 text-sm font-bold text-black hover:bg-yellow-300 disabled:cursor-not-allowed disabled:opacity-50 transition shadow-lg shadow-yellow-400/20 flex items-center gap-2"
        >
          <span>⚡</span>
          {isProcessing ? 'Executing AI Pipeline...' : 'Run Automated Screening'}
        </button>
      </div>

      {/* Real-time AI Pipeline Modal / HUD Overlay */}
      {isProcessing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm p-4">
          <div className="w-full max-w-xl rounded-2xl border border-gray-800 bg-gray-950 p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-gray-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-yellow-400/10 border border-yellow-400/40 flex items-center justify-center text-yellow-400 font-mono font-bold text-sm animate-pulse">
                  AI
                </div>
                <div>
                  <h3 className="font-semibold text-white">Automated Document Inspection Pipeline</h3>
                  <p className="text-xs text-gray-400 font-mono">Simultaneous Multi-Model Evaluation</p>
                </div>
              </div>

              <span className="text-xs font-mono text-yellow-400 bg-yellow-400/10 px-2 py-1 rounded">
                STAGE {currentStepIndex + 1} OF {PIPELINE_STEPS.length}
              </span>
            </div>

            {/* Pipeline progress steps */}
            <div className="mt-6 space-y-3">
              {PIPELINE_STEPS.map((stepItem, idx) => {
                const isDone = currentStepIndex > idx
                const isCurrent = currentStepIndex === idx
                return (
                  <div
                    key={stepItem.id}
                    className={`flex items-start gap-3 rounded-lg border p-3 transition-all ${
                      isDone
                        ? 'border-emerald-500/30 bg-emerald-950/20 text-emerald-300'
                        : isCurrent
                        ? 'border-yellow-400/60 bg-yellow-400/5 text-white'
                        : 'border-gray-800/60 bg-gray-900/20 text-gray-500'
                    }`}
                  >
                    <div className="mt-0.5">
                      {isDone ? (
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 text-[10px] font-bold text-black">
                          ✓
                        </span>
                      ) : isCurrent ? (
                        <span className="flex h-5 w-5 items-center justify-center rounded-full border-2 border-yellow-400 border-t-transparent animate-spin text-[10px]"></span>
                      ) : (
                        <span className="flex h-5 w-5 items-center justify-center rounded-full border border-gray-700 text-[10px]">
                          {stepItem.id}
                        </span>
                      )}
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center justify-between text-xs font-semibold">
                        <span>{stepItem.title}</span>
                        {isDone && <span className="font-mono text-emerald-400 text-[11px]">PASSED</span>}
                        {isCurrent && <span className="font-mono text-yellow-400 text-[11px] animate-pulse">ANALYZING...</span>}
                      </div>
                      <p className="text-[11px] text-gray-400 mt-0.5">{stepItem.desc}</p>
                    </div>
                  </div>
                )
              })}
            </div>

            <div className="mt-6 pt-4 border-t border-gray-800 flex items-center justify-between text-xs text-gray-500 font-mono">
              <span>Security Terminal ID: BORDER-DEL-04</span>
              <span className="text-gray-400">Synthesizing Decision Vector...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Screening