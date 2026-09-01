from PIL import Image


def analyze_metadata(image_path):
    """
    Analyze basic image metadata for forensic clues.
    """

    image = Image.open(image_path)

    metadata = image.getexif()

    findings = []

    if not metadata:
        findings.append(
            "No EXIF metadata found"
        )

    else:
        findings.append(
            f"EXIF metadata fields found: {len(metadata)}"
        )

    # Basic image information
    width, height = image.size

    return {
        "format": image.format,
        "width": width,
        "height": height,
        "metadata_fields": len(metadata),
        "findings": findings
    }


if __name__ == "__main__":

    image_path = (
        "test_images/tampered/tampered.jpg"
    )

    result = analyze_metadata(image_path)

    print()
    print("================================")
    print("       METADATA ANALYSIS")
    print("================================")

    print("Format:", result["format"])
    print("Width:", result["width"])
    print("Height:", result["height"])
    print(
        "Metadata fields:",
        result["metadata_fields"]
    )

    for finding in result["findings"]:
        print("Finding:", finding)

    print("================================")