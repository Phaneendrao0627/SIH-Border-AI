from document_classifier import classify_document


tests = {
    "Passport": "REPUBLIC OF INDIA PASSPORT",
    "Visa": "VISA REPUBLIC OF INDIA",
    "Driving Licence": "DRIVING LICENCE GOVERNMENT",
    "National ID": "NATIONAL ID IDENTITY CARD",
    "Permit": "WORK PERMIT GOVERNMENT"
}


print("\n========== DOCUMENT CLASSIFIER TEST ==========\n")

for expected, text in tests.items():

    result = classify_document(text)

    print(f"Expected: {expected}")
    print(f"Detected: {result}")
    print("--------------------------------------")