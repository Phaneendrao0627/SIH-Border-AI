import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DocumentUpload from '../components/DocumentUpload'
import CameraPanel from '../components/CameraPanel'

function Screening() {
  const [isProcessing, setIsProcessing] = useState(false)
  const navigate = useNavigate()
const handleStartScreening = () => {
  

  setIsProcessing(true)

  setTimeout(() => {
    console.log("NAVIGATING TO RESULT")
    setIsProcessing(false)
    navigate('/result')
  }, 3000)
}
  return (
    <div>
      <h1 className="text-3xl font-bold">New Screening</h1>

      <p className="mt-2 text-gray-400">
        Upload a travel document and verify passenger identity.
      </p>

      <div className="mt-8 grid grid-cols-2 gap-6">
        <DocumentUpload />
        <CameraPanel />
      </div>

      <button
        onClick={handleStartScreening}
        disabled={isProcessing}
        className="mt-8 rounded-lg bg-yellow-400 px-6 py-3 font-semibold text-black hover:bg-yellow-300 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isProcessing ? 'Processing...' : 'Start Screening'}
      </button>
    </div>
  )
}

export default Screening