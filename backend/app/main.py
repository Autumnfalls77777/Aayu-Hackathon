"""SASTI DAWAI - FastAPI Backend."""
import json
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional

from app.core.config import settings
from app.db.database import get_db, engine, Base
from app.models.medicine import BrandedMedicine, JanAushadhiProduct, Ingredient
from app.schemas.medicine import (
    MedicineIdentification,
    MatchRequest,
    MatchResult,
    SavingsInfo,
    SearchResult,
)
from app.services.matching.exact_matcher import exact_match, find_exact_matches
from app.services.medicine.data_loader import load_branded_medicines, load_jan_aushadhi_products
from app.core.normalization import (
    normalize_salt_name,
    normalize_dosage_form,
    parse_composition,
    extract_strength,
)
from app.api.scan import router as scan_router

app = FastAPI(
    title="SASTI DAWAI API",
    description="Find exact lower-cost generic equivalents for medicines",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
def startup_event():
    """Initialize database and load data on startup."""
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        # Check if data is already loaded
        branded_count = db.query(BrandedMedicine).count()
        generic_count = db.query(JanAushadhiProduct).count()

        if branded_count == 0:
            print("Loading branded medicines...")
            raw_path = Path(__file__).parent.parent.parent / "data" / "raw"
            branded_csv = raw_path / "indian_medicine_data.csv"
            if branded_csv.exists():
                load_branded_medicines(db, str(branded_csv))

        if generic_count == 0:
            print("Loading Jan Aushadhi products...")
            raw_path = Path(__file__).parent.parent.parent / "data" / "raw"
            generic_csv = raw_path / "jan_aushadhi_products.csv"
            if generic_csv.exists():
                load_jan_aushadhi_products(db, str(generic_csv))

        print(f"Database ready: {branded_count} branded, {generic_count} generic")
    finally:
        db.close()


@app.get("/api/v1/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "sasti-dawai-api"}


@app.get("/api/v1/medicines/search")
def search_medicines(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search for medicines by name."""
    search_pattern = f"%{q}%"
    results = (
        db.query(BrandedMedicine)
        .filter(
            or_(
                BrandedMedicine.name.ilike(search_pattern),
                BrandedMedicine.manufacturer.ilike(search_pattern),
            )
        )
        .filter(BrandedMedicine.is_discontinued == False)
        .limit(limit)
        .all()
    )

    output = []
    for med in results:
        composition = ", ".join([
            f"{ing.name} ({ing.canonical_name})"
            for ing in med.ingredients
        ])
        output.append(SearchResult(
            id=med.id,
            name=med.name,
            manufacturer=med.manufacturer,
            price=med.price,
            composition=composition,
            dosage_form=med.dosage_form,
            pack_size=med.pack_size_label,
        ))
    return output


@app.get("/api/v1/medicines/{medicine_id}")
def get_medicine(medicine_id: int, db: Session = Depends(get_db)):
    """Get a specific branded medicine by ID."""
    med = db.query(BrandedMedicine).filter(BrandedMedicine.id == medicine_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")

    return {
        "id": med.id,
        "name": med.name,
        "manufacturer": med.manufacturer,
        "price": med.price,
        "is_discontinued": med.is_discontinued,
        "medicine_type": med.medicine_type,
        "pack_size_label": med.pack_size_label,
        "dosage_form": med.dosage_form,
        "release_type": med.release_type,
        "ingredients": [
            {
                "name": ing.name,
                "canonical_name": ing.canonical_name,
            }
            for ing in med.ingredients
        ],
    }


@app.post("/api/v1/match", response_model=MatchResult)
def match_medicine(request: MatchRequest, db: Session = Depends(get_db)):
    """
    Find exact Jan Aushadhi equivalents for a given medicine.
    Uses deterministic exact matching - same salt, strength, and form.
    """
    # Build branded medicine dict from request
    branded = {
        "name": request.brand_name,
        "ingredients": [
            {
                "name": ing.name,
                "strength": ing.strength,
                "unit": ing.unit,
            }
            for ing in request.ingredients
        ],
        "dosage_form": request.dosage_form,
        "release_type": request.release_type,
    }

    # Get all Jan Aushadhi products
    generics = db.query(JanAushadhiProduct).all()

    # Convert to dicts
    generic_dicts = []
    for g in generics:
        try:
            ingredients = json.loads(g.ingredients) if g.ingredients else []
        except json.JSONDecodeError:
            ingredients = []
        generic_dicts.append({
            "id": g.id,
            "name": g.generic_name,
            "ingredients": ingredients,
            "dosage_form": g.dosage_form,
            "release_type": g.release_type,
            "mrp": g.mrp,
            "unit_size": g.unit_size,
            "group_name": g.group_name,
        })

    # Find exact matches
    matches = find_exact_matches(branded, generic_dicts)

    if not matches:
        return MatchResult(
            exact_match=False,
            match_confidence=0.0,
            match_reasons=["No exact equivalent found in our current database."],
            safety_notice="Confirm with your doctor or pharmacist before switching.",
        )

    # Return best match
    best = matches[0]
    generic = best["generic"]

    # Calculate savings
    savings = None
    # Try to find branded price
    branded_price = None
    if request.brand_name:
        branded_med = (
            db.query(BrandedMedicine)
            .filter(BrandedMedicine.name.ilike(f"%{request.brand_name}%"))
            .first()
        )
        if branded_med and branded_med.price:
            branded_price = branded_med.price

    if branded_price and generic.get("mrp"):
        saving = branded_price - generic["mrp"]
        pct = (saving / branded_price) * 100 if branded_price > 0 else 0
        savings = SavingsInfo(
            current_price=branded_price,
            equivalent_price=generic["mrp"],
            absolute_saving=saving,
            percentage_saving=round(pct, 1),
            annual_saving=round(saving * 12, 2),
            note="Potential saving per pack. Actual savings may vary.",
        )

    return MatchResult(
        exact_match=True,
        branded_medicine={
            "name": request.brand_name,
            "ingredients": [
                {"name": ing.name, "strength": ing.strength, "unit": ing.unit}
                for ing in request.ingredients
            ],
            "dosage_form": request.dosage_form,
        },
        jan_aushadhi_product={
            "id": generic["id"],
            "name": generic["name"],
            "mrp": generic["mrp"],
            "unit_size": generic["unit_size"],
            "group_name": generic["group_name"],
            "ingredients": generic["ingredients"],
        },
        savings=savings,
        match_confidence=best["confidence"],
        match_reasons=best["reasons"],
        safety_notice="Confirm with your doctor or pharmacist before switching.",
    )


@app.get("/api/v1/medicines/{medicine_id}/alternatives")
def get_alternatives(medicine_id: int, db: Session = Depends(get_db)):
    """Get exact alternatives for a branded medicine."""
    med = db.query(BrandedMedicine).filter(BrandedMedicine.id == medicine_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")

    branded = {
        "name": med.name,
        "ingredients": [
            {
                "name": ing.name,
                "strength": None,
                "unit": "mg",
            }
            for ing in med.ingredients
        ],
        "dosage_form": med.dosage_form,
        "release_type": med.release_type,
    }

    generics = db.query(JanAushadhiProduct).all()
    generic_dicts = []
    for g in generics:
        try:
            ingredients = json.loads(g.ingredients) if g.ingredients else []
        except json.JSONDecodeError:
            ingredients = []
        generic_dicts.append({
            "id": g.id,
            "name": g.generic_name,
            "ingredients": ingredients,
            "dosage_form": g.dosage_form,
            "release_type": g.release_type,
            "mrp": g.mrp,
        })

    matches = find_exact_matches(branded, generic_dicts)
    return {
        "exact_matches": len(matches),
        "matches": [
            {
                "id": m["generic"]["id"],
                "name": m["generic"]["name"],
                "mrp": m["generic"]["mrp"],
                "confidence": m["confidence"],
                "reasons": m["reasons"],
            }
            for m in matches
        ],
        "safety_notice": "Confirm with your doctor or pharmacist before switching.",
    }


@app.get("/api/v1/medicines/{medicine_id}/savings")
def get_savings(medicine_id: int, db: Session = Depends(get_db)):
    """Calculate savings for a branded medicine."""
    med = db.query(BrandedMedicine).filter(BrandedMedicine.id == medicine_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")

    if not med.price:
        return {"error": "No price data available for this medicine"}

    # Find exact matches
    branded = {
        "name": med.name,
        "ingredients": [{"name": ing.name, "strength": None, "unit": "mg"} for ing in med.ingredients],
        "dosage_form": med.dosage_form,
        "release_type": med.release_type,
    }

    generics = db.query(JanAushadhiProduct).all()
    generic_dicts = []
    for g in generics:
        try:
            ingredients = json.loads(g.ingredients) if g.ingredients else []
        except json.JSONDecodeError:
            ingredients = []
        generic_dicts.append({
            "id": g.id,
            "name": g.generic_name,
            "ingredients": ingredients,
            "dosage_form": g.dosage_form,
            "release_type": g.release_type,
            "mrp": g.mrp,
        })

    matches = find_exact_matches(branded, generic_dicts)
    if not matches:
        return {"error": "No exact equivalent found"}

    best = matches[0]
    generic = best["generic"]
    if not generic.get("mrp"):
        return {"error": "No price data available for generic equivalent"}

    saving = med.price - generic["mrp"]
    pct = (saving / med.price) * 100 if med.price > 0 else 0

    return {
        "current_price": med.price,
        "equivalent_price": generic["mrp"],
        "absolute_saving": round(saving, 2),
        "percentage_saving": round(pct, 1),
        "annual_saving": round(saving * 12, 2),
        "monthly_quantity": 1,
        "note": "Potential saving per pack. Actual savings may vary.",
        "safety_notice": "Confirm with your doctor or pharmacist before switching.",
    }


@app.get("/api/v1/kendras/nearby")
def get_nearby_kendras(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: float = Query(10.0, description="Radius in km"),
    db: Session = Depends(get_db),
):
    """Get nearby Jan Aushadhi Kendras."""
    from app.models.medicine import Kendra
    from math import radians, cos, sin, asin, sqrt

    def haversine(lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth radius in km
        return c * r

    kendras = db.query(Kendra).filter(
        Kendra.latitude.isnot(None),
        Kendra.longitude.isnot(None),
    ).all()

    nearby = []
    for k in kendras:
        dist = haversine(lat, lng, k.latitude, k.longitude)
        if dist <= radius:
            nearby.append({
                "id": k.id,
                "name": k.name,
                "address": k.address,
                "state": k.state,
                "district": k.district,
                "pincode": k.pincode,
                "distance_km": round(dist, 2),
            })

    nearby.sort(key=lambda x: x["distance_km"])
    return {
        "kendras": nearby,
        "note": "Jan Aushadhi Kendra nearby. Medicine availability not confirmed.",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
