import { useState } from 'react'

function DocumentUpload() {
  const [file, setFile] = useState(null)
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
      <h2 className="text-xl font-semibold text-white">
        Upload Document
      </h2>

      <p className="mt-2 text-sm text-gray-400">
        Upload a passport, visa, ID or other travel document.
      </p>

      <label className="mt-6 flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-700 p-10 text-center hover:border-yellow-400">
        <span className="text-4xl">📄</span>

        <span className="mt-4 font-medium text-white">
          Click to upload
        </span>

        <span className="mt-2 text-sm text-gray-500">
          PNG, JPG or JPEG
        </span>

        {file && (
  <p className="mt-3 text-sm text-yellow-400">
    Selected: {file.name}
  </p>
)}

        <input
  type="file"
  accept="image/png, image/jpeg"
  className="hidden"
  onChange={(event) => setFile(event.target.files[0])}
/>
      </label>
    </div>
  )
}

export default DocumentUpload