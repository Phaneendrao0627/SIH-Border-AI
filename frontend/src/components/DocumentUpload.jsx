import { useState } from 'react'

function DocumentUpload({ onFileSelect }) {
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
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-6 flex flex-col justify-between">
      <div>
        <h2 className="text-lg font-semibold text-white">
          Travel Document
        </h2>
        <p className="mt-1 text-sm text-gray-400">
          Upload a passport, visa, or national identity card.
        </p>

        <div className="mt-5">
          {preview ? (
            <div className="space-y-3">
              <div className="h-56 w-full overflow-hidden rounded-lg border border-gray-700 bg-black flex items-center justify-center">
                <img
                  src={preview}
                  alt="Uploaded Document"
                  className="h-full w-full object-contain"
                />
              </div>

              <div className="flex items-center justify-between text-xs text-gray-300">
                <span className="truncate max-w-[220px] text-gray-400">{fileName}</span>
                <button
                  type="button"
                  onClick={handleRemove}
                  className="text-red-400 hover:text-red-300 font-medium"
                >
                  Remove file
                </button>
              </div>
            </div>
          ) : (
            <label className="flex h-56 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-700 bg-gray-950/50 p-6 text-center transition hover:border-gray-500">
              <span className="text-3xl text-gray-400">📄</span>
              <p className="mt-3 text-sm font-medium text-white">
                Choose a document file
              </p>
              <p className="mt-1 text-xs text-gray-400">
                PNG, JPG or JPEG up to 10MB
              </p>
              <span className="mt-3 rounded-md bg-gray-800 px-3 py-1.5 text-xs text-gray-200 border border-gray-700 hover:bg-gray-700">
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

      <p className="mt-4 text-xs text-gray-400">
        Supports ICAO Doc 9303 passports and standard national identity cards.
      </p>
    </div>
  )
}

export default DocumentUpload