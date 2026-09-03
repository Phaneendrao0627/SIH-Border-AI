import { useState, useRef, useEffect } from 'react'

export const SAMPLE_TRAVELERS = {
  genuine: {
    id: 'genuine',
    name: 'Live Passenger (Matches Document)',
    photo: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&auto=format&fit=crop&q=80',
    livenessScore: 99.2,
    livenessStatus: 'LIVE_VERIFIED',
    faceMatchScore: 96.4,
    spoofDetected: false
  },
  tampered: {
    id: 'tampered',
    name: 'Live Passenger (Traveler Matches Photo)',
    photo: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=500&auto=format&fit=crop&q=80',
    livenessScore: 98.6,
    livenessStatus: 'LIVE_VERIFIED',
    faceMatchScore: 94.1,
    spoofDetected: false
  },
  impersonation: {
    id: 'impersonation',
    name: 'Impersonating Passenger (Face Mismatch)',
    photo: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=500&auto=format&fit=crop&q=80',
    livenessScore: 97.5,
    livenessStatus: 'LIVE_VERIFIED',
    faceMatchScore: 31.8, // Face Mismatch!
    spoofDetected: false
  },
  spoof: {
    id: 'spoof',
    name: 'Screen / Replay Attack (Spoof Attempt)',
    photo: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=500&auto=format&fit=crop&q=80',
    livenessScore: 14.2, // Failed liveness!
    livenessStatus: 'SPOOF_SUSPECTED',
    faceMatchScore: 89.0,
    spoofDetected: true
  }
}

function CameraPanel({ selectedTraveler, onSelectTraveler }) {
  const [useWebcam, setUseWebcam] = useState(false)
  const [cameraActive, setCameraActive] = useState(false)
  const [capturedImage, setCapturedImage] = useState(null)
  const videoRef = useRef(null)
  const streamRef = useRef(null)

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
      streamRef.current = stream
      setCameraActive(true)
      setUseWebcam(true)
    } catch (err) {
      console.warn('Webcam permission denied or camera not found:', err)
      alert('Could not access webcam. Falling back to traveler photo presets.')
      setUseWebcam(false)
    }
  }

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    setCameraActive(false)
    setUseWebcam(false)
  }

  const captureSnapshot = () => {
    if (videoRef.current) {
      const canvas = document.createElement('canvas')
      canvas.width = videoRef.current.videoWidth || 640
      canvas.height = videoRef.current.videoHeight || 480
      const ctx = canvas.getContext('2d')
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height)
      const dataUrl = canvas.toDataURL('image/jpeg')
      setCapturedImage(dataUrl)
      onSelectTraveler({
        id: 'webcam_captured',
        name: 'Live Traveler (Camera Snapshot)',
        photo: dataUrl,
        livenessScore: 98.4,
        livenessStatus: 'LIVE_VERIFIED',
        faceMatchScore: 92.0,
        spoofDetected: false
      })
      stopCamera()
    }
  }

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
      }
    }
  }, [])

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-6 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <span>📹</span> Passenger Live Feed
          </h2>
          <span className="text-xs font-mono uppercase bg-cyan-400/10 text-cyan-400 border border-cyan-400/30 px-2 py-0.5 rounded">
            Module 4: Face & Liveness
          </span>
        </div>

        <p className="mt-2 text-sm text-gray-400">
          Real-time checkpoint camera for biometric verification and anti-spoof liveness detection.
        </p>

        {/* Camera toggle options */}
        <div className="mt-4 flex items-center gap-2">
          {!cameraActive ? (
            <button
              type="button"
              onClick={startCamera}
              className="flex items-center gap-2 rounded-lg bg-gray-800 hover:bg-gray-700 px-3 py-1.5 text-xs font-medium text-white border border-gray-700 transition"
            >
              <span>📷</span> Open Live Webcam
            </button>
          ) : (
            <>
              <button
                type="button"
                onClick={captureSnapshot}
                className="flex items-center gap-2 rounded-lg bg-yellow-400 hover:bg-yellow-300 px-3 py-1.5 text-xs font-semibold text-black transition"
              >
                <span>📸</span> Capture Snapshot
              </button>
              <button
                type="button"
                onClick={stopCamera}
                className="rounded-lg bg-rose-950/60 hover:bg-rose-900 border border-rose-800 px-3 py-1.5 text-xs font-medium text-rose-300 transition"
              >
                Cancel
              </button>
            </>
          )}

          <span className="text-xs text-gray-500">or pick demo traveler:</span>
        </div>

        {/* Traveler Quick Presets */}
        <div className="mt-2 grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => {
              stopCamera()
              setCapturedImage(null)
              onSelectTraveler(SAMPLE_TRAVELERS.genuine)
            }}
            className={`p-2 rounded-lg text-left text-xs transition border ${
              selectedTraveler?.id === 'genuine'
                ? 'border-emerald-500 bg-emerald-950/40 text-emerald-300'
                : 'border-gray-800 bg-gray-950/60 text-gray-400 hover:border-gray-700 hover:text-white'
            }`}
          >
            <div className="font-semibold text-emerald-400">✓ Matching Face</div>
            <div className="text-[10px] text-gray-400">Live verified (96% match)</div>
          </button>

          <button
            type="button"
            onClick={() => {
              stopCamera()
              setCapturedImage(null)
              onSelectTraveler(SAMPLE_TRAVELERS.impersonation)
            }}
            className={`p-2 rounded-lg text-left text-xs transition border ${
              selectedTraveler?.id === 'impersonation'
                ? 'border-rose-500 bg-rose-950/40 text-rose-300'
                : 'border-gray-800 bg-gray-950/60 text-gray-400 hover:border-gray-700 hover:text-white'
            }`}
          >
            <div className="font-semibold text-rose-400">⚠ Face Mismatch</div>
            <div className="text-[10px] text-gray-400">Different person (31%)</div>
          </button>
        </div>

        {/* Video / Photo Preview Container */}
        <div className="mt-4 relative h-48 w-full rounded-lg bg-black border border-gray-800 flex items-center justify-center overflow-hidden">
          {cameraActive ? (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="h-full w-full object-cover"
            />
          ) : capturedImage || selectedTraveler?.photo ? (
            <img
              src={capturedImage || selectedTraveler.photo}
              alt="Passenger Snapshot"
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="text-center p-4">
              <div className="text-4xl">👤</div>
              <p className="mt-2 text-xs text-gray-400">
                No passenger feed selected. Click "Open Live Webcam" or choose a demo traveler.
              </p>
            </div>
          )}

          {/* Biometric Frame & Liveness HUD Overlay */}
          {(cameraActive || selectedTraveler?.photo) && (
            <div className="absolute inset-0 pointer-events-none p-3 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-black/75 px-2 py-0.5 rounded border border-emerald-500/40">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  {cameraActive ? 'LIVE CAMERA STREAM' : 'TRAVELER CAPTURED'}
                </span>

                <span className="text-[10px] font-mono text-cyan-400 bg-black/75 px-2 py-0.5 rounded border border-cyan-500/40">
                  FPS: 30 • 720P
                </span>
              </div>

              {/* Centered Target Box */}
              <div className="mx-auto h-28 w-28 rounded-full border border-dashed border-cyan-400/70 flex items-center justify-center">
                <div className="h-24 w-24 rounded-full border border-cyan-400/30"></div>
              </div>

              {/* Bottom Liveness Badge */}
              <div className="flex justify-between items-center bg-black/80 px-2 py-1 rounded border border-gray-800 text-[11px]">
                <span className="text-gray-300">
                  Anti-Spoof Liveness:
                </span>
                <span className={`font-mono font-semibold ${
                  selectedTraveler?.spoofDetected ? 'text-rose-400' : 'text-emerald-400'
                }`}>
                  {selectedTraveler?.spoofDetected ? '⚠ SPOOF RISK (14%)' : '✓ 98.4% (BLINK PASS)'}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-gray-800 text-[11px] text-gray-500 flex items-center justify-between">
        <span>DeepFace / FaceNet ArcFace Embeddings</span>
        <span className="text-emerald-400">Active Anti-Spoofing</span>
      </div>
    </div>
  )
}

export default CameraPanel