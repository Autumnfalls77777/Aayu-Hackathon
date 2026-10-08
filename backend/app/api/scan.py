"""OCR scan API endpoint."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ocr.ocr_service import process_medicine_image
from app.core.config import settings

router = APIRouter()


@router.post("/scan")
async def scan_medicine(file: UploadFile = File(...)):
    """
    Upload a medicine image and extract information using OCR.
    Returns structured medicine data with confidence scores.
    """
    # Validate file type
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {settings.ALLOWED_IMAGE_TYPES}",
        )

    # Read file
    contents = await file.read()

    # Validate file size
    if len(contents) > settings.MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum {settings.MAX_IMAGE_SIZE_MB}MB allowed.",
        )

    # Process image
    result = process_medicine_image(contents)

    if result.get("confidence", 0) < settings.MIN_CONFIDENCE_THRESHOLD:
        result["warning"] = "Low confidence. Please verify the extracted information."

    return result
