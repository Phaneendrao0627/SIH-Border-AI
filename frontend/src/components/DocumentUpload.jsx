import { useState } from 'react'

export const SAMPLE_DOCUMENTS = {
  genuine: {
    id: 'genuine',
    title: 'Genuine Passport (Low Risk)',
    type: 'Passport (ICAO 9303)',
    name: 'ARJUN SHARMA',
    passportNumber: 'Z5839201',
    nationality: 'IND',
    dob: '12/08/1994',
    expiry: '11/08/2034',
    gender: 'M',
    tampered: false,
    tamperConfidence: 4,
    tamperReason: 'No digital manipulation or splicing detected.',
    suspiciousRegions: [],
    mrzValid: true,
    checksumValid: true,
    riskScore: 12,
    imagePreview: 'https://images.unsplash.com/photo-1544717305-2782549b5136?w=600&auto=format&fit=crop&q=80'
  },
  tampered: {
    id: 'tampered',
    title: 'Tampered Passport (Altered DOB & Photo Seam)',
    type: 'Passport (ICAO 9303)',
    name: 'MICHAEL CHEN',
    passportNumber: 'E9201844',
    nationality: 'SGP',
    dob: '05/11/1982',
    expiry: '18/04/2028',
    gender: 'M',
    tampered: true,
    tamperConfidence: 93,
    tamperReason: 'Inconsistent Error Level (ELA) noise detected in DOB field & photo boundary seam.',
    suspiciousRegions: [
      { label: 'Altered Date of Birth', x: 42, y: 58, width: 22, height: 9, confidence: 93 },
      { label: 'Photo Border Splicing', x: 8, y: 32, width: 28, height: 42, confidence: 87 }
    ],
    mrzValid: false,
    checksumValid: false,
    riskScore: 89,
    imagePreview: 'https://images.unsplash.com/photo-1578836537282-3171d77f8632?w=600&auto=format&fit=crop&q=80'
  },
  impersonation: {
    id: 'impersonation',
    title: 'Stolen / Impersonated Identity',
    type: 'National ID Card',
    name: 'DAVID K. WILSON',
    passportNumber: 'N4820199',
    nationality: 'GBR',
    dob: '23/02/1990',
    expiry: '20/09/2027',
    gender: 'M',
    tampered: false,
    tamperConfidence: 8,
    tamperReason: 'Document surface is authentic, but traveler face does not match document holder.',
    suspiciousRegions: [],
    mrzValid: true,
    checksumValid: true,
    riskScore: 84,
    imagePreview: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&auto=format&fit=crop&q=80'
  }
}

function DocumentUpload({ selectedDoc, onSelectDoc, customFile, onCustomFileUpload }) {
  const [dragActive, setDragActive] = useState(false)

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      const previewUrl = URL.createObjectURL(file)
      onCustomFileUpload(file, previewUrl)
    }
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      const previewUrl = URL.createObjectURL(file)
      onCustomFileUpload(file, previewUrl)
    }
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-6 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <span>📄</span> Travel Document
          </h2>
          <span className="text-xs font-mono uppercase bg-yellow-400/10 text-yellow-400 border border-yellow-400/30 px-2 py-0.5 rounded">
            Module 1 & 3 Input
          </span>
        </div>

        <p className="mt-2 text-sm text-gray-400">
          Upload a passport, visa, or national ID for OCR extraction and forgery analysis.
        </p>

        {/* Quick Demo Presets */}
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">
            ⚡ Quick Demo Scenarios (One-Click Test)
          </p>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => onSelectDoc(SAMPLE_DOCUMENTS.genuine)}
              className={`p-2 rounded-lg text-left text-xs transition border ${
                selectedDoc?.id === 'genuine'
                  ? 'border-emerald-500 bg-emerald-950/40 text-emerald-300'
                  : 'border-gray-800 bg-gray-950/60 text-gray-400 hover:border-gray-700 hover:text-white'
              }`}
            >
              <div className="font-semibold text-emerald-400">✓ Genuine</div>
              <div className="truncate text-[10px] text-gray-400">Low risk (12%)</div>
            </button>

            <button
              type="button"
              onClick={() => onSelectDoc(SAMPLE_DOCUMENTS.tampered)}
              className={`p-2 rounded-lg text-left text-xs transition border ${
                selectedDoc?.id === 'tampered'
                  ? 'border-rose-500 bg-rose-950/40 text-rose-300'
                  : 'border-gray-800 bg-gray-950/60 text-gray-400 hover:border-gray-700 hover:text-white'
              }`}
            >
              <div className="font-semibold text-rose-400">⚠ Tampered</div>
              <div className="truncate text-[10px] text-gray-400">Altered DOB (89%)</div>
            </button>

            <button
              type="button"
              onClick={() => onSelectDoc(SAMPLE_DOCUMENTS.impersonation)}
              className={`p-2 rounded-lg text-left text-xs transition border ${
                selectedDoc?.id === 'impersonation'
                  ? 'border-amber-500 bg-amber-950/40 text-amber-300'
                  : 'border-gray-800 bg-gray-950/60 text-gray-400 hover:border-gray-700 hover:text-white'
              }`}
            >
              <div className="font-semibold text-amber-400">👤 Impersonator</div>
              <div className="truncate text-[10px] text-gray-400">Face Mismatch</div>
            </button>
          </div>
        </div>

        {/* Upload / Preview Area */}
        <div className="mt-4">
          {selectedDoc?.imagePreview ? (
            <div className="relative rounded-lg border border-gray-700 bg-gray-950 p-3 overflow-hidden">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-gray-800">
                <span className="text-xs font-medium text-gray-300">
                  {selectedDoc.title || customFile?.name || 'Selected Document'}
                </span>
                <button
                  type="button"
                  onClick={() => onSelectDoc(null)}
                  className="text-xs text-rose-400 hover:underline"
                >
                  Change
                </button>
              </div>

              <div className="relative h-44 w-full rounded bg-black flex items-center justify-center overflow-hidden">
                <img
                  src={selectedDoc.imagePreview}
                  alt="Document Preview"
                  className="h-full w-full object-cover opacity-90"
                />

                {/* Simulated scan overlay */}
                <div className="absolute inset-0 border border-yellow-400/40 pointer-events-none flex flex-col justify-between p-2">
                  <div className="flex justify-between text-[10px] font-mono text-yellow-400 bg-black/60 px-1.5 py-0.5 rounded w-fit">
                    ICAO 9303 COMPLIANT
                  </div>
                  <div className="text-[10px] font-mono text-emerald-400 bg-black/60 px-1.5 py-0.5 rounded w-fit">
                    STATUS: READY FOR SCAN
                  </div>
                </div>
              </div>

              <div className="mt-2 flex items-center justify-between text-xs text-gray-400">
                <span>Type: <strong className="text-white">{selectedDoc.type || 'Travel Document'}</strong></span>
                <span>ID: <strong className="text-white font-mono">{selectedDoc.passportNumber || 'N/A'}</strong></span>
              </div>
            </div>
          ) : (
            <label
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition ${
                dragActive
                  ? 'border-yellow-400 bg-yellow-400/5'
                  : 'border-gray-700 hover:border-yellow-400/80 bg-gray-950/40'
              }`}
            >
              <span className="text-4xl">📂</span>
              <span className="mt-3 font-medium text-white text-sm">
                Drop passport / ID image here, or <span className="text-yellow-400 underline">browse</span>
              </span>
              <span className="mt-1 text-xs text-gray-500">
                Supports PNG, JPG, JPEG (Max 10MB)
              </span>

              <input
                type="file"
                accept="image/png, image/jpeg, image/jpg"
                className="hidden"
                onChange={handleFileChange}
              />
            </label>
          )}
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-gray-800 text-[11px] text-gray-500 flex items-center justify-between">
        <span>Supported: Passports, Visas, Driving Licenses</span>
        <span className="text-yellow-400/80">MRZ Auto-Detection Active</span>
      </div>
    </div>
  )
}

export default DocumentUpload