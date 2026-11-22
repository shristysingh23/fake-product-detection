"""Run the Day 6 preprocessing pipeline on an image and save a PNG result."""

import argparse
from pathlib import Path
import sys

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.preprocessing import preprocess_image


def main() -> int:
    parser = argparse.ArgumentParser(description="Preprocess a product image for later analysis.")
    parser.add_argument("image_path", help="Path to the source image")
    parser.add_argument(
        "output_folder",
        nargs="?",
        default="output",
        help="Folder for the processed PNG (default: ml-service/output)",
    )
    args = parser.parse_args()

    source_path = Path(args.image_path)
    try:
        image_bytes = source_path.read_bytes()
    except FileNotFoundError:
        print(f"Image file not found: {source_path}")
        return 1
    except OSError as error:
        print(f"Could not read image file {source_path}: {error}")
        return 1

    try:
        result = preprocess_image(image_bytes)
    except ValueError as error:
        print(f"Could not preprocess image {source_path}: {error}")
        return 1

    output_folder = Path(args.output_folder)
    output_path = output_folder / f"{source_path.stem}_processed.png"
    success, encoded = cv2.imencode(".png", result.image)
    if not success:
        print(f"Could not encode processed image: {output_path}")
        return 1

    try:
        output_folder.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(encoded.tobytes())
    except OSError as error:
        print(f"Could not save processed image {output_path}: {error}")
        return 1

    print(f"Original size: {result.original_size}")
    print(f"Processed size: {result.processed_size}")
    print(f"Steps: {result.steps}")
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
