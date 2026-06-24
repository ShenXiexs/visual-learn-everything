"""FastAPI application: upload a document, get back a learning package.

Run with:  uvicorn backend.main:app --reload
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .ingestion import SUPPORTED_EXTENSIONS, load_document
from .genai import get_provider
from .pipeline import build_learning_package

app = FastAPI(
    title="visual-learn-everything",
    description="Turn any PDF / Markdown / text file into interactive visual learning material.",
    version="0.1.0",
)


@app.get("/api/health")
def health():
    provider = get_provider()
    return {
        "status": "ok",
        "provider": provider.name,
        "model": provider.model,
        "supported_extensions": SUPPORTED_EXTENSIONS,
        "max_upload_mb": round(config.MAX_UPLOAD_BYTES / (1024 * 1024), 1),
    }


@app.post("/api/process")
async def process(file: UploadFile = File(...)):
    filename = file.filename or "upload"
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    job_id = uuid.uuid4().hex[:12]
    job_dir = config.DATA_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    source_path = job_dir / f"source{ext}"

    # Stream the upload to disk while enforcing the size cap.
    size = 0
    try:
        with source_path.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > config.MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds the {config.MAX_UPLOAD_BYTES // (1024*1024)} MB limit.",
                    )
                out.write(chunk)
    except HTTPException:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise

    try:
        doc = load_document(source_path, media_dir=job_dir)
    except Exception as exc:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(status_code=422, detail=f"Could not parse file: {exc}") from exc

    if not doc.text.strip() and not doc.images:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(
            status_code=422,
            detail="No readable text or images were found in the document.",
        )

    try:
        package = build_learning_package(doc, job_id=job_id, source_filename=filename)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Generation failed: {exc}"
        ) from exc

    return JSONResponse(package.model_dump())


# Serve extracted images. Mounted before the catch-all frontend mount.
app.mount("/media", StaticFiles(directory=str(config.DATA_DIR)), name="media")

# Serve bundled sample documents (used by the "Try the sample" button).
_samples_dir = config.BASE_DIR / "samples"
if _samples_dir.exists():
    app.mount("/samples", StaticFiles(directory=str(_samples_dir)), name="samples")

# Serve the single-page frontend at the root.
if config.FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(config.FRONTEND_DIR), html=True), name="frontend")
