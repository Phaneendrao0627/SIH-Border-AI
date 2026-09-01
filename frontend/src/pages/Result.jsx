import RiskScore from '../components/RiskScore'
function Result() {
  const screeningResult = {
  riskScore: 18,
  ocr: "Complete",
  validation: "Valid",
  tampering: "No Issues Detected",
  face: "Match Confirmed",

  document: {
    name: "John Doe",
    passportNumber: "P1234567",
    nationality: "Indian",
    dateOfBirth: "15 Jan 2000",
    dateOfExpiry: "14 Jan 2030",
    gender: "Male"
  }
}

let status

if (screeningResult.riskScore < 40) {
  status = "PASS"
} else if (screeningResult.riskScore < 70) {
  status = "REVIEW"
} else {
  status = "REJECT"
}
  return (
    <div>
      <h1 className="text-3xl font-bold">
        Screening Result
      </h1>

      <p className="mt-2 text-gray-400">
        Screening analysis and verification results.
      </p>

      {/* Overall Result */}
      <div className="mt-8 rounded-xl border border-gray-800 bg-gray-900 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-400">
              Overall Status
            </p>

            <p className="mt-2 text-2xl font-bold text-yellow-400">
              {status}
            </p>
          </div>

          <RiskScore score={screeningResult.riskScore} />
        </div>
      </div>

      {/* Verification Modules */}
      <div className="mt-6 grid grid-cols-2 gap-6">

        {/* Module 1 */}
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
          <p className="text-sm text-gray-400">
            Module 1
          </p>

          <h2 className="mt-2 text-xl font-semibold">
            OCR Extraction
          </h2>

          <p className="mt-3 text-yellow-400">
            ✓ {screeningResult.ocr}
          </p>
        </div>

        {/* Module 2 */}
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
          <p className="text-sm text-gray-400">
            Module 2
          </p>

          <h2 className="mt-2 text-xl font-semibold">
            Document Validation
          </h2>

          <p className="mt-3 text-yellow-400">
            ✓ {screeningResult.validation}
          </p>
        </div>

        {/* Module 3 */}
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
          <p className="text-sm text-gray-400">
            Module 3
          </p>

          <h2 className="mt-2 text-xl font-semibold">
            Tampering Detection
          </h2>

          <p className="mt-3 text-yellow-400">
            ✓ {screeningResult.tampering}
          </p>
        </div>

        {/* Module 4 */}
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
          <p className="text-sm text-gray-400">
            Module 4
          </p>

          <h2 className="mt-2 text-xl font-semibold">
            Face Verification
          </h2>

          <p className="mt-3 text-yellow-400">
            ✓ {screeningResult.face}
          </p>
        </div>

        <div className="mt-6 rounded-xl border border-gray-800 bg-gray-900 p-6">

  <h2 className="text-xl font-semibold">
    Extracted Document Information
  </h2>

  <div className="mt-6 grid grid-cols-2 gap-6">

    <div>
      <p className="text-sm text-gray-400">Name</p>
      <p className="mt-1 font-medium">
        {screeningResult.document.name}
      </p>
    </div>

    <div>
      <p className="text-sm text-gray-400">Passport Number</p>
      <p className="mt-1 font-medium">
        {screeningResult.document.passportNumber}
      </p>
    </div>

    <div>
      <p className="text-sm text-gray-400">Nationality</p>
      <p className="mt-1 font-medium">
        {screeningResult.document.nationality}
      </p>
    </div>

    <div>
      <p className="text-sm text-gray-400">Date of Birth</p>
      <p className="mt-1 font-medium">
        {screeningResult.document.dateOfBirth}
      </p>
    </div>

    <div>
      <p className="text-sm text-gray-400">Date of Expiry</p>
      <p className="mt-1 font-medium">
        {screeningResult.document.dateOfExpiry}
      </p>
    </div>

    <div>
      <p className="text-sm text-gray-400">Gender</p>
      <p className="mt-1 font-medium">
        {screeningResult.document.gender}
      </p>
    </div>

  </div>
</div>

      </div>
    </div>
  )
}

export default Result