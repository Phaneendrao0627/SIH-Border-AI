function CameraPanel() {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
      <h2 className="text-xl font-semibold text-white">
        Live Passenger Camera
      </h2>

      <p className="mt-2 text-sm text-gray-400">
        Capture the passenger for face verification.
      </p>

      <div className="mt-6 flex h-64 items-center justify-center rounded-lg bg-black border border-gray-800">
        <div className="text-center">
          <div className="text-4xl">📷</div>

          <p className="mt-3 text-gray-400">
            Camera feed will appear here
          </p>
        </div>
      </div>
    </div>
  )
}

export default CameraPanel