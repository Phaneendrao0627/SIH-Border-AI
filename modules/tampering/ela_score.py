from PIL import Image
import numpy as np


def calculate_ela_score(ela_path, threshold=50):
    """
    Calculate the percentage of pixels
    with high ELA intensity.
    """

    image = Image.open(ela_path).convert("L")

    pixels = np.array(image)

    high_error_pixels = np.sum(
        pixels > threshold
    )

    total_pixels = pixels.size

    percentage = (
        high_error_pixels / total_pixels
    ) * 100

    return round(percentage, 4)


if __name__ == "__main__":

    ela_image = (
        "outputs/batch_ela/"
        "tampered_tampered_ela.jpg"
    )

    score = calculate_ela_score(
        ela_image
    )

    print()
    print("==============================")
    print("       ELA ANALYSIS")
    print("==============================")
    print(
        f"High-error pixel percentage: "
        f"{score}%"
    )
    print("==============================")