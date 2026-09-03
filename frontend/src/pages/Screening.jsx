import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DocumentUpload from '../components/DocumentUpload'
import CameraPanel from '../components/CameraPanel'

function Screening() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [filePreview, setFilePreview] = useState(null)
  const [cameraPhoto, setCameraPhoto] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)

  const navigate = useNavigate()

  const handleFileSelect = (file, previewUrl) => {
    setSelectedFile(file)
    setFilePreview(previewUrl)
  }

  const handleCapture = (photoUrl) => {
    setCameraPhoto(photoUrl)
  }

  const handleStartScreening = () => {
    setIsProcessing(true)

    setTimeout(() => {
      setIsProcessing(false)

      const resultPayload = {
        timestamp: new Date().toISOString(),
        riskScore: selectedFile ? 18 : 65,
        documentImage: filePreview,
        passengerPhoto: cameraPhoto,
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
            details: 'All required MRZ fields successfully extracted.'
          },
          validation: {
            status: 'Passed',
            details: 'ICAO 9303 checksum digits and expiration dates valid.'
          },
          tampering: {
            status: 'No Issues Detected',
            details: 'Surface compression and text fonts are consistent.'
          },
          face: {
            status: 'Match Confirmed',
            score: '96.2%',
            details: 'High facial similarity between document photo and live feed.'
          }
        }
      }

      navigate('/result', { state: { screeningResult: resultPayload } })
    }, 2000)
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-white">
        Document Screening
      </h1>
      <p className="mt-2 text-sm text-gray-400">
        Upload a travel document and capture passenger photo for identity verification.
      </p>

      {/* Upload and Camera Cards */}
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DocumentUpload onFileSelect={handleFileSelect} />
        <CameraPanel onCapture={handleCapture} />
      </div>

      {/* Bottom Start Button */}
      <div className="mt-8 flex items-center justify-between rounded-xl border border-gray-800 bg-gray-900 p-4">
        <p className="text-xs text-gray-400">
          Make sure document details and passenger photo are clear before starting.
        </p>

        <button
          type="button"
          onClick={handleStartScreening}
          disabled={isProcessing}
          className="rounded-lg bg-yellow-400 px-6 py-2.5 text-sm font-semibold text-black hover:bg-yellow-300 disabled:cursor-not-allowed disabled:opacity-50 transition"
        >
          {isProcessing ? 'Verifying Document...' : 'Start Screening'}
        </button>
      </div>
    </div>
  )
}

export default Screening