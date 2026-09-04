from pathlib import Path
import shutil
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.services.ocr_service import run_ocr


app = FastAPI(title="SIH Border AI Backend")

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
def read_root():
    return {"message": "SIH Border AI Backend"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/api/v1/screen")
async def screen_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}

    extension = Path(file.filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use JPG, JPEG, PNG, or WEBP.",
        )

    file_id = uuid.uuid4().hex
    saved_path = UPLOAD_DIR / f"{file_id}{extension}"

    try:
        with saved_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = run_ocr(str(saved_path))

        return {
            "success": True,
            "filename": file.filename,
            "ocr_result": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {str(exc)}",
        )

    finally:
        if saved_path.exists():
            saved_path.unlink()
