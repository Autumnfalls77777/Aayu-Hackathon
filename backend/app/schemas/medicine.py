"""Pydantic schemas for API requests/responses."""
from pydantic import BaseModel, Field
from typing import Optional


class IngredientInfo(BaseModel):
    name: str
    strength: float
    unit: str = "mg"


class MedicineIdentification(BaseModel):
    brand_name: Optional[str] = None
    ingredients: list[IngredientInfo] = []
    dosage_form: Optional[str] = None
    release_type: Optional[str] = None
    pack_size: Optional[int] = None
    confidence: float = 0.0
    raw_text: str = ""
    evidence: list[dict] = []


class MatchRequest(BaseModel):
    brand_name: Optional[str] = None
    ingredients: list[IngredientInfo]
    dosage_form: str
    release_type: Optional[str] = None


class SavingsInfo(BaseModel):
    current_price: Optional[float] = None
    equivalent_price: Optional[float] = None
    absolute_saving: Optional[float] = None
    percentage_saving: Optional[float] = None
    annual_saving: Optional[float] = None
    monthly_quantity: Optional[int] = None
    note: str = ""


class MatchResult(BaseModel):
    exact_match: bool
    branded_medicine: Optional[dict] = None
    jan_aushadhi_product: Optional[dict] = None
    savings: Optional[SavingsInfo] = None
    match_confidence: float = 0.0
    match_reasons: list[str] = []
    safety_notice: str = "Confirm with your doctor or pharmacist before switching."


class SearchResult(BaseModel):
    id: int
    name: str
    manufacturer: Optional[str] = None
    price: Optional[float] = None
    composition: str = ""
    dosage_form: Optional[str] = None
    pack_size: Optional[str] = None
