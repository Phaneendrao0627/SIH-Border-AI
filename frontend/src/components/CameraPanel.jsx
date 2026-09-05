import { useState, useRef, useEffect } from 'react'
import { useTheme } from '../context/ThemeContext'

function CameraPanel({ onCapture }) {
  const { isDark } = useTheme()
  const [cameraActive, setCameraActive] = useState(false)
  const [capturedPhoto, setCapturedPhoto] = useState(null)
  const videoRef = useRef(null)
  const streamRef = useRef(null)

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 }
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
      streamRef.current = stream
      setCameraActive(true)
      setCapturedPhoto(null)
    } catch (err) {
      alert('Unable to access camera. Please allow camera permissions.')
    }
  }

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    setCameraActive(false)
  }

  const takeSnapshot = () => {
    if (videoRef.current) {
      const canvas = document.createElement('canvas')
      canvas.width = videoRef.current.videoWidth || 640
      canvas.height = videoRef.current.videoHeight || 480
      const ctx = canvas.getContext('2d')
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height)
      const dataUrl = canvas.toDataURL('image/jpeg')
      setCapturedPhoto(dataUrl)
      stopCamera()
      if (onCapture) onCapture(dataUrl)
    }
  }

  const handleRetake = () => {
    setCapturedPhoto(null)
    if (onCapture) onCapture(null)
    startCamera()
  }

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
      }
    }
  }, [])

  return (
    <div className={`rounded-xl border p-6 flex flex-col justify-between transition-colors ${
      isDark
        ? 'border-gray-800 bg-gray-900 text-white'
        : 'border-gray-200 bg-white text-gray-900 shadow-sm'
    }`}>
      <div>
        <h2 className="text-lg font-semibold">
          Live Identity Capture
        </h2>
        <p className={`mt-1 text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
          Capture a live passenger image for liveness and facial verification.
        </p>

        <div className="mt-5">
          <div className={`h-56 w-full overflow-hidden rounded-lg border flex items-center justify-center relative ${
            isDark ? 'border-gray-700 bg-black' : 'border-gray-200 bg-gray-100'
          }`}>
            {cameraActive ? (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="h-full w-full object-cover"
              />
            ) : capturedPhoto ? (
              <img
                src={capturedPhoto}
                alt="Captured Passenger"
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="text-center p-6 text-gray-400">
                <span className="text-3xl">📷</span>
                <p className="mt-2 text-sm">Camera is currently off</p>
                <button
                  type="button"
                  onClick={startCamera}
                  className={`mt-3 rounded-md px-3 py-1.5 text-xs border transition ${
                    isDark
                      ? 'bg-gray-800 text-gray-200 border-gray-700 hover:bg-gray-700'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 shadow-sm'
                  }`}
                >
                  Start Camera
                </button>
              </div>
            )}
          </div>

          {/* Controls */}
          <div className="mt-3 flex items-center justify-between text-xs">
            {cameraActive && (
              <>
                <button
                  type="button"
                  onClick={takeSnapshot}
                  className="rounded-md bg-yellow-400 px-4 py-1.5 font-semibold text-black hover:bg-yellow-300 transition"
                >
                  Take Snapshot
                </button>
                <button
                  type="button"
                  onClick={stopCamera}
                  className="text-gray-400 hover:text-gray-600"
                >
                  Turn off
                </button>
              </>
            )}

            {capturedPhoto && (
              <div className="flex items-center justify-between w-full">
                <span className="text-emerald-500 font-medium">✓ Photo captured</span>
                <button
                  type="button"
                  onClick={handleRetake}
                  className="text-yellow-500 hover:underline"
                >
                  Retake photo
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <p className={`mt-4 text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
        Live camera snapshot is compared against the document photograph.
      </p>
    </div>
  )
}

export default CameraPanel