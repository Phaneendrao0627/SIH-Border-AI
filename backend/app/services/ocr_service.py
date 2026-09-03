import sys
from pathlib import Path
import importlib.util

# Project root:
# /Users/joshitha/border_backend
PROJECT_ROOT = Path(__file__).resolve().parents[3]

OCR_MODULE_PATH = PROJECT_ROOT / "modules" / "ocr" / "module1_ocr"
OCR_APP_PATH = OCR_MODULE_PATH / "app.py"

# Allow OCR's internal modules to import correctly
if str(OCR_MODULE_PATH) not in sys.path:
    sys.path.insert(0, str(OCR_MODULE_PATH))

# Load OCR app under a unique name so it doesn't conflict
# with FastAPI's own "app" package.
spec = importlib.util.spec_from_file_location(
    "sih_ocr_app",
    OCR_APP_PATH
)

if spec is None or spec.loader is None:
    raise ImportError(f"Could not load OCR module from {OCR_APP_PATH}")

ocr_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ocr_app)


def run_ocr(image_path: str) -> dict:
    output_dir = OCR_MODULE_PATH / "output"

    return ocr_app.process_document(
        image_path=image_path,
        output_dir=str(output_dir),
    )
