from PIL import Image, ImageChops, ImageEnhance
import os


def perform_ela(image_path, output_path, quality=90):
    """
    Generate an Error Level Analysis (ELA) image.
    """

    original = Image.open(image_path).convert("RGB")

    temp_path = "temp_ela.jpg"

    original.save(temp_path, "JPEG", quality=quality)

    compressed = Image.open(temp_path).convert("RGB")

    difference = ImageChops.difference(original, compressed)

    extrema = difference.getextrema()

    max_difference = max(
        channel_max
        for channel_min, channel_max in extrema
    )

    if max_difference == 0:
        max_difference = 1

    scale = 255.0 / max_difference

    ela_image = ImageEnhance.Brightness(
        difference
    ).enhance(scale)

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True
    )

    ela_image.save(output_path)

    if os.path.exists(temp_path):
        os.remove(temp_path)

    return output_path


def calculate_ela_difference(image1_path, image2_path):
    """
    Compare two ELA images and return
    an average difference score.
    """

    image1 = Image.open(image1_path).convert("RGB")
    image2 = Image.open(image2_path).convert("RGB")

    # Make both images the same size
    image2 = image2.resize(image1.size)

    difference = ImageChops.difference(
        image1,
        image2
    )

    # Calculate average pixel difference
    histogram = difference.histogram()

    total_pixels = image1.size[0] * image1.size[1]

    total_difference = sum(
        value * (index % 256)
        for index, value in enumerate(histogram)
    )

    score = total_difference / (
        total_pixels * 3
    )

    return round(score, 2)