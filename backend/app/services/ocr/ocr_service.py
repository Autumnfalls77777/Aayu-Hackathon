"""OCR service for medicine strip/box text extraction."""
import io
import re
from PIL import Image
import pytesseract
import cv2
import numpy as np
from app.core.normalization import (
    normalize_salt_name,
    normalize_dosage_form,
    extract_strength,
    extract_release_type,
    parse_composition,
)


def preprocess_image(image: Image.Image) -> np.ndarray:
    """Preprocess image for better OCR results."""
    # Convert to numpy array
    img = np.array(image)

    # Convert to grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img

    # Resize if too small
    height, width = gray.shape
    if height < 1000 or width < 1000:
        scale = max(1000 / height, 1000 / width)
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

    # Adaptive thresholding
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    return binary


def extract_text(image: Image.Image) -> str:
    """Extract text from image using Tesseract OCR."""
    try:
        processed = preprocess_image(image)
        # Convert back to PIL for pytesseract
        processed_pil = Image.fromarray(processed)
        text = pytesseract.image_to_string(processed_pil, config='--psm 6')
        return text
    except Exception as e:
        print(f"OCR error: {e}")
        # Fallback to original image
        try:
            text = pytesseract.image_to_string(image)
            return text
        except:
            return ""


def extract_medicine_info(text: str) -> dict:
    """Extract structured medicine information from OCR text."""
    result = {
        "brand_name": None,
        "ingredients": [],
        "dosage_form": None,
        "release_type": None,
        "pack_size": None,
        "confidence": 0.0,
        "raw_text": text,
        "evidence": [],
    }

    lines = text.strip().split('\n')
    lines = [l.strip() for l in lines if l.strip()]

    if not lines:
        return result

    # First non-empty line is often the brand name
    result["brand_name"] = lines[0].strip()
    result["evidence"].append({"field": "brand_name", "text": lines[0]})

    # Look for composition patterns
    composition_patterns = [
        r'([A-Za-z\s]+)\s*\(?(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|iu|%)\)?',
        r'([A-Za-z\s]+)\s+(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|iu|%)',
    ]

    full_text = ' '.join(lines).lower()

    # Extract ingredients
    for pattern in composition_patterns:
        matches = re.finditer(pattern, full_text, re.IGNORECASE)
        for match in matches:
            name = match.group(1).strip()
            strength = float(match.group(2))
            unit = match.group(3).lower()

            # Clean up name
            name = re.sub(r'\s+', ' ', name)
            name = name.strip()

            if name and len(name) > 2:
                result["ingredients"].append({
                    "name": name,
                    "normalized_name": normalize_salt_name(name),
                    "strength": strength,
                    "unit": unit,
                })
                result["evidence"].append({
                    "field": "ingredient",
                    "text": match.group(0),
                })

    # Extract dosage form
    form_keywords = {
        "tablet": "tablet", "tab": "tablet", "capsule": "capsule", "cap": "capsule",
        "syrup": "syrup", "syp": "syrup", "injection": "injection", "inj": "injection",
        "drops": "drops", "cream": "cream", "ointment": "ointment", "gel": "gel",
        "lotion": "lotion", "powder": "powder", "inhaler": "inhaler",
    }

    for keyword, form in form_keywords.items():
        if keyword in full_text:
            result["dosage_form"] = form
            result["evidence"].append({"field": "dosage_form", "text": keyword})
            break

    # Extract release type
    release = extract_release_type(full_text)
    if release:
        result["release_type"] = release
        result["evidence"].append({"field": "release_type", "text": release})

    # Extract pack size
    pack_match = re.search(r'(\d+)\s*(?:tablets?|capsules?|tabs?|caps?|strip|blister)', full_text, re.IGNORECASE)
    if pack_match:
        result["pack_size"] = int(pack_match.group(1))
        result["evidence"].append({"field": "pack_size", "text": pack_match.group(0)})

    # Calculate confidence
    confidence = 0.0
    if result["brand_name"]:
        confidence += 0.3
    if result["ingredients"]:
        confidence += 0.4
    if result["dosage_form"]:
        confidence += 0.2
    if result["pack_size"]:
        confidence += 0.1

    result["confidence"] = min(confidence, 1.0)

    return result


def process_medicine_image(image_bytes: bytes) -> dict:
    """Process a medicine image and extract all information."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return {
            "error": "Invalid image",
            "confidence": 0.0,
            "raw_text": "",
        }

    # Extract text
    text = extract_text(image)

    # Extract medicine info
    result = extract_medicine_info(text)

    return result
