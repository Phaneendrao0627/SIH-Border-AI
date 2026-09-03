import { useState, useRef, useEffect } from 'react'

function CameraPanel({ onCapture }) {
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
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-6 flex flex-col justify-between">
      <div>
        <h2 className="text-lg font-semibold text-white">
          Passenger Camera
        </h2>
        <p className="mt-1 text-sm text-gray-400">
          Capture the passenger's photo for face matching.
        </p>

        <div className="mt-5">
          <div className="h-56 w-full overflow-hidden rounded-lg border border-gray-700 bg-black flex items-center justify-center relative">
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
                  className="mt-3 rounded-md bg-gray-800 px-3 py-1.5 text-xs text-gray-200 border border-gray-700 hover:bg-gray-700 transition"
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
                  className="text-gray-400 hover:text-white"
                >
                  Turn off
                </button>
              </>
            )}

            {capturedPhoto && (
              <div className="flex items-center justify-between w-full">
                <span className="text-emerald-400 font-medium">✓ Photo captured</span>
                <button
                  type="button"
                  onClick={handleRetake}
                  className="text-yellow-400 hover:underline"
                >
                  Retake photo
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <p className="mt-4 text-xs text-gray-400">
        Live camera snapshot is compared against the document photograph.
      </p>
    </div>
  )
}

export default CameraPanel