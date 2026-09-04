import { useState } from 'react'
import { useTheme } from '../context/ThemeContext'

function DocumentUpload({ onFileSelect }) {
  const { isDark } = useTheme()
  const [preview, setPreview] = useState(null)
  const [fileName, setFileName] = useState('')

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setFileName(file.name)
      const url = URL.createObjectURL(file)
      setPreview(url)
      if (onFileSelect) onFileSelect(file, url)
    }
  }

  const handleRemove = () => {
    setPreview(null)
    setFileName('')
    if (onFileSelect) onFileSelect(null, null)
  }

  return (
    <div className={`rounded-xl border p-6 flex flex-col justify-between transition-colors ${
      isDark
        ? 'border-gray-800 bg-gray-900 text-white'
        : 'border-gray-200 bg-white text-gray-900 shadow-sm'
    }`}>
      <div>
        <h2 className="text-lg font-semibold">
          Travel Document
        </h2>
        <p className={`mt-1 text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
          Upload a passport, visa, or national identity card.
        </p>

        <div className="mt-5">
          {preview ? (
            <div className="space-y-3">
              <div className={`h-56 w-full overflow-hidden rounded-lg border flex items-center justify-center ${
                isDark ? 'border-gray-700 bg-black' : 'border-gray-200 bg-gray-50'
              }`}>
                <img
                  src={preview}
                  alt="Uploaded Document"
                  className="h-full w-full object-contain"
                />
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className={`truncate max-w-[220px] ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  {fileName}
                </span>
                <button
                  type="button"
                  onClick={handleRemove}
                  className="text-red-500 hover:text-red-600 font-medium"
                >
                  Remove file
                </button>
              </div>
            </div>
          ) : (
            <label className={`flex h-56 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 text-center transition ${
              isDark
                ? 'border-gray-700 bg-gray-950/50 hover:border-gray-500'
                : 'border-gray-300 bg-gray-50/50 hover:border-gray-400'
            }`}>
              <span className="text-3xl text-gray-400">📄</span>
              <p className="mt-3 text-sm font-medium">
                Choose a document file
              </p>
              <p className={`mt-1 text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                PNG, JPG or JPEG up to 10MB
              </p>
              <span className={`mt-3 rounded-md px-3 py-1.5 text-xs border transition ${
                isDark
                  ? 'bg-gray-800 text-gray-200 border-gray-700 hover:bg-gray-700'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 shadow-sm'
              }`}>
                Browse file
              </span>
              <input
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileChange}
              />
            </label>
          )}
        </div>
      </div>

      <p className={`mt-4 text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
        Supports ICAO Doc 9303 passports and standard national identity cards.
      </p>
    </div>
  )
}

export default DocumentUpload