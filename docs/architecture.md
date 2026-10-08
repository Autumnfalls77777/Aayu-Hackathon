# SASTI DAWAI — Architecture Document

> **Aayu 2026 — T06** | Mobile-first AI prototype to scan medicine strips/boxes and find affordable generic equivalents with the same salt.

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [API Contracts](#2-api-contracts)
3. [Database Schema](#3-database-schema)
4. [OCR Pipeline](#4-ocr-pipeline)
5. [Exact Matching Engine](#5-exact-matching-engine)
6. [Project Structure](#6-project-structure)
7. [Risk Assessment](#7-risk-assessment)
8. [Implementation Plan](#8-implementation-plan)

---

## 1. System Architecture

### 1.1 High-Level Overview

The system is a **monolithic FastAPI backend** with a **PostgreSQL database** and an **Expo React Native mobile client**. The mobile app captures medicine images, sends them to the backend for OCR processing, and displays matched generic alternatives with price comparisons.

**Data Flow:**

1. Mobile app captures medicine strip/box image
2. Image uploaded to backend via `POST /api/v1/scan`
3. Backend runs Tesseract OCR to extract text
4. OCR text parsed to identify medicine name and/or composition
5. Medicine looked up in branded_medicines table
6. Matching engine finds generic equivalents by comparing salt signatures
7. Results returned to mobile app with price comparison

### 1.2 Design Principles

| Principle | Rationale |
|-----------|-----------|
| **Monolith** | Single deployable, no service discovery, no inter-service auth. Hackathon = speed. |
| **Deterministic matching** | No LLM calls for equivalence decisions. Rule-based normalization + exact set comparison. Safety > cleverness. |
| **Server-side OCR** | Tesseract runs on backend. Mobile just captures + uploads. No on-device ML model to manage. |
| **PostgreSQL** | Structured relational data, mature full-text search, zero-config for local dev. |
| **Expo (React Native)** | Mobile-first, single codebase iOS/Android, OTA updates, fast iteration. |
| **No auth / no payments** | Out of scope. Demo only. |

### 1.3 Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Mobile | Expo SDK + React Native + TypeScript | SDK 53+ |
| Backend | FastAPI + Uvicorn | 0.115+ |
| ORM | SQLAlchemy | 2.0+ |
| Database | PostgreSQL | 16 |
| OCR | pytesseract + Pillow | 0.3.10+ |
| Data | pandas (for CSV import) | 2.2+ |
| Validation | Pydantic | 2.0+ |
| Deployment | Docker + docker-compose | — |

---

## 2. API Contracts

### 2.1 `POST /api/v1/scan`

Upload a medicine strip/box image. Returns identified medicine + generic alternatives.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | file | Yes | JPEG/PNG image of medicine strip/box |

**Response:** `200 OK`

```json
{
  "success": true,
  "scan_id": "uuid-v4",
  "ocr_text": "Augmentin 625 Duo Tablet Amoxycillin (500mg) Clavulanic Acid (125mg)",
  "identified_medicine": {
    "id": 1,
    "name": "Augmentin 625 Duo Tablet",
    "brand": "Glaxo SmithKline Pharmaceuticals Ltd",
    "price_inr": 223.42,
    "pack_size": "strip of 10 tablets",
    "composition": [
      {"salt": "Amoxycillin", "dosage": "500mg"},
      {"salt": "Clavulanic Acid", "dosage": "125mg"}
    ]
  },
  "generics": [
    {
      "id": 150,
      "generic_name": "Amoxycillin and Clavulanic Acid Tablets IP 500mg/125mg",
      "manufacturer": "Jan Aushadhi",
      "price_inr": 45.00,
      "savings_pct": 79.9,
      "savings_inr": 178.42,
      "unit_size": "10's",
      "group_name": "Antibiotics"
    }
  ],
  "match_confidence": "exact",
  "alternative_names": ["Amoxyclav 625", "Augmentin Duo"]
}
```

**Error Responses:**

| Status | Body | When |
|--------|------|------|
| 400 | `{"error": "No image provided"}` | Missing file |
| 422 | `{"error": "Could not identify medicine from image"}` | OCR found text but no match |
| 500 | `{"error": "Internal server error"}` | Unexpected failure |

### 2.2 `GET /api/v1/medicines/search`

Search branded medicines by name (for manual lookup / autocomplete).

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `q` | string | Yes | Search query (min 2 chars) |
| `limit` | int | No | Max results (default 20, max 50) |

**Response:** `200 OK`

```json
{
  "query": "augmentin",
  "count": 3,
  "results": [
    {
      "id": 1,
      "name": "Augmentin 625 Duo Tablet",
      "price_inr": 223.42,
      "manufacturer": "Glaxo SmithKline Pharmaceuticals Ltd",
      "pack_size": "strip of 10 tablets"
    },
    {
      "id": 7,
      "name": "Amoxyclav 625 Tablet",
      "price_inr": 223.27,
      "manufacturer": "Abbott",
      "pack_size": "strip of 10 tablets"
    }
  ]
}
```

### 2.3 `GET /api/v1/medicines/{id}`

Get full details of a branded medicine including composition and matching generics.

**Response:** `200 OK`

```json
{
  "id": 1,
  "name": "Augmentin 625 Duo Tablet",
  "price_inr": 223.42,
  "is_discontinued": false,
  "manufacturer": "Glaxo SmithKline Pharmaceuticals Ltd",
  "type": "allopathy",
  "pack_size": "strip of 10 tablets",
  "composition": [
    {"salt": "Amoxycillin", "dosage": "500mg", "dosage_mg": 500.0},
    {"salt": "Clavulanic Acid", "dosage": "125mg", "dosage_mg": 125.0}
  ],
  "salt_signature": "amoxycillin:500.0|clavulanic acid:125.0",
  "generics": [
    {
      "id": 150,
      "generic_name": "Amoxycillin and Clavulanic Acid Tablets IP 500mg/125mg",
      "price_inr": 45.00,
      "savings_pct": 79.9,
      "unit_size": "10's",
      "group_name": "Antibiotics"
    }
  ],
  "generic_count": 1
}
```

### 2.4 `GET /api/v1/health`

Health check for monitoring.

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "database": "connected",
  "ocr_engine": "tesseract",
  "version": "1.0.0"
}
```

### 2.5 `GET /api/v1/generics/search`

Search Jan Aushadhi generic products directly.

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `q` | string | Yes | Search by generic name or salt |
| `limit` | int | No | Max results (default 20) |

**Response:** `200 OK`

```json
{
  "query": "paracetamol",
  "count": 5,
  "results": [
    {
      "id": 42,
      "generic_name": "Paracetamol Tablets IP 500mg",
      "price_inr": 2.50,
      "unit_size": "10's",
      "group_name": "Analgesic/Antipyretic/Anti-Inflammatory"
    }
  ]
}
```

---

## 3. Database Schema

### 3.1 Entity-Relationship Diagram

```
branded_medicines ──< branded_medicine_salt >── salts
                                              │
generic_products  ──< generic_product_salt  ───┘
```

**Tables:**

- **branded_medicines** — 254K rows from indian_medicine_data.csv
- **generic_products** — 2.4K rows from jan_aushadhi_products.csv
- **salts** — 5K-15K unique (name, dosage) pairs
- **branded_medicine_salt** — Many-to-many link (300K-400K rows)
- **generic_product_salt** — Many-to-many link (3K-5K rows)

### 3.2 DDL

```sql
-- ============================================
-- SASTI DAWAI - PostgreSQL Schema
-- ============================================

-- Branded medicines (from indian_medicine_data.csv)
CREATE TABLE branded_medicines (
    id              SERIAL PRIMARY KEY,
    external_id     INTEGER,
    name            TEXT NOT NULL,
    price_inr        DECIMAL(10, 2),
    is_discontinued  BOOLEAN DEFAULT FALSE,
    manufacturer_name TEXT,
    type            TEXT,
    pack_size_label TEXT,
    composition_raw TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Normalized salts (extracted from compositions)
CREATE TABLE salts (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    dosage          TEXT,
    dosage_mg       DECIMAL(10, 4),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, dosage)
);

-- Link branded medicines to their salts
CREATE TABLE branded_medicine_salt (
    branded_medicine_id INTEGER NOT NULL REFERENCES branded_medicines(id) ON DELETE CASCADE,
    salt_id             INTEGER NOT NULL REFERENCES salts(id) ON DELETE CASCADE,
    PRIMARY KEY (branded_medicine_id, salt_id)
);

-- Jan Aushadhi generic products
CREATE TABLE generic_products (
    id              SERIAL PRIMARY KEY,
    drug_code       INTEGER,
    generic_name    TEXT NOT NULL,
    unit_size       TEXT,
    mrp             DECIMAL(10, 2),
    group_name      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Link generic products to their salts
CREATE TABLE generic_product_salt (
    generic_product_id  INTEGER NOT NULL REFERENCES generic_products(id) ON DELETE CASCADE,
    salt_id             INTEGER NOT NULL REFERENCES salts(id) ON DELETE CASCADE,
    PRIMARY KEY (generic_product_id, salt_id)
);

-- ============================================
-- INDEXES
-- ============================================

-- Full-text search on medicine names
CREATE INDEX idx_branded_name_fts ON branded_medicines
    USING gin(to_tsvector('english', name));

CREATE INDEX idx_generic_name_fts ON generic_products
    USING gin(to_tsvector('english', generic_name));

-- B-tree indexes for exact name lookups
CREATE INDEX idx_branded_name ON branded_medicines (name);
CREATE INDEX idx_generic_name ON generic_products (generic_name);

-- Matching engine indexes
CREATE INDEX idx_branded_salt ON branded_medicine_salt (salt_id);
CREATE INDEX idx_generic_salt ON generic_product_salt (salt_id);

-- Price sorting
CREATE INDEX idx_branded_price ON branded_medicines (price_inr);
CREATE INDEX idx_generic_mrp ON generic_products (mrp);

-- Filter active medicines
CREATE INDEX idx_branded_active ON branded_medicines (is_discontinued) WHERE is_discontinued = FALSE;
```

### 3.3 Data Volume Estimates

| Table | Rows | Notes |
|-------|------|-------|
| `branded_medicines` | ~254,000 | From CSV |
| `salts` | ~5,000-15,000 | Unique (name, dosage) pairs |
| `branded_medicine_salt` | ~300,000-400,000 | 1-3 salts per medicine |
| `generic_products` | ~2,439 | From CSV |
| `generic_product_salt` | ~3,000-5,000 | 1-3 salts per product |

All tables fit comfortably in memory. No partitioning needed.

---

## 4. OCR Pipeline

### 4.1 Pipeline Flow

1. **Image Capture** - Mobile camera captures medicine strip/box
2. **Image Upload** - Sent to backend as multipart form data
3. **Preprocessing** - Grayscale, contrast enhancement, resize, threshold
4. **OCR** - Tesseract extracts raw text
5. **Text Parsing** - Extract medicine name and composition
6. **Medicine Lookup** - Search database by name
7. **Matching** - Find generic equivalents by salt signature
8. **Response** - Return results to mobile app

### 4.2 OCR Processing

```python
# services/ocr/engine.py

def process_medicine_image(image_bytes: bytes) -> OCRResult:
    """Full OCR pipeline for a medicine strip/box image."""
    img = Image.open(io.BytesIO(image_bytes))
    img = preprocess_image(img)

    custom_config = r'--oem 3 --psm 6 -l eng'
    text = pytesseract.image_to_string(img, config=custom_config)
    text = clean_ocr_text(text)

    parsed = parse_medicine_text(text)

    return OCRResult(
        raw_text=text,
        medicine_name=parsed.name,
        composition=parsed.composition,
        confidence=parsed.confidence
    )
```

### 4.3 Image Preprocessing

```python
def preprocess_image(img: Image.Image) -> Image.Image:
    """Enhance image for OCR accuracy."""
    img = img.convert('L')
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    w, h = img.size
    if w < 1000:
        scale = 1000 / w
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    img = img.point(lambda x: 0 if x < 128 else 255, '1')
    return img
```

### 4.4 Text Parsing Strategy

OCR text from a medicine strip typically contains:
- Brand name (e.g., "Augmentin 625 Duo Tablet")
- Salt composition (e.g., "Amoxycillin (500mg), Clavulanic Acid (125mg)")
- Manufacturer, pack size, etc.

**Parsing approach:**

```python
def parse_medicine_text(text: str) -> ParsedMedicine:
    """Extract medicine name and composition from OCR text."""
    lines = text.strip().split('\n')

    # Strategy 1: Look for composition pattern "SaltName (dosage)"
    composition_pattern = r'([A-Za-z\s]+)\s*\((\d+\.?\d*\s*(?:mg|g|ml|%|mcg|IU)[^)]*)\)'
    compositions = re.findall(composition_pattern, text)

    if compositions:
        name = extract_name_from_lines(lines, compositions)
        return ParsedMedicine(name=name, composition=compositions, confidence='high')

    # Strategy 2: Look for known medicine names in text
    known_name = search_known_medicine_names(text)
    if known_name:
        return ParsedMedicine(name=known_name, composition=[], confidence='medium')

    # Strategy 3: Return raw text for manual search
    return ParsedMedicine(name=None, composition=[], confidence='low')
```

### 4.5 Fallback: Manual Text Entry

If OCR confidence is low, the mobile app allows the user to:
1. Type the medicine name manually
2. Select from search results
3. View composition and generic alternatives

This ensures the demo always works even with poor quality images.

---

## 5. Exact Matching Engine

### 5.1 Core Concept: Salt Signature

Every medicine (branded or generic) can be represented as a **salt signature** - a normalized set of (salt_name, dosage) pairs. Two medicines are equivalent if and only if their salt signatures are identical.

**Example:**

```
Branded: "Augmentin 625 Duo Tablet"
  Composition: "Amoxycillin (500mg), Clavulanic Acid (125mg)"
  Salt Signature: {("amoxycillin", 500.0), ("clavulanic acid", 125.0)}

Generic: "Amoxycillin and Clavulanic Acid Tablets IP 500mg/125mg"
  Salt Signature: {("amoxycillin", 500.0), ("clavulanic acid", 125.0)}

  MATCH! Same salt signature.
```

### 5.2 Normalization Pipeline

```
Raw Text -> Tokenize -> Normalize Salt Name -> Normalize Dosage -> Salt Signature
```

#### 5.2.1 Salt Name Normalization

```python
# services/matching/normalizer.py

SALT_NAME_MAPPINGS = {
    'amoxycillin': 'amoxicillin',
    'amoxycillin trihydrate': 'amoxicillin',
    'paracetamol': 'acetaminophen',
    'acetaminophen': 'acetaminophen',
    'diclofenac sodium': 'diclofenac',
    'diclofenac potassium': 'diclofenac',
    'chlorpheniramine maleate': 'chlorpheniramine',
    'chlorphenamine maleate': 'chlorpheniramine',
}

def normalize_salt_name(name: str) -> str:
    """Normalize salt name for matching."""
    name = name.strip().lower()
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'\([^)]*\)', '', name)
    name = name.strip()
    name = SALT_NAME_MAPPINGS.get(name, name)
    return name
```

#### 5.2.2 Dosage Normalization

```python
def normalize_dosage(dosage_str: str) -> tuple:
    """
    Normalize dosage string to (unit, value_in_mg).

    Examples:
        "500mg"     -> ("mg", 500.0)
        "1g"        -> ("mg", 1000.0)
        "5ml"       -> ("ml", 5.0)
        "30mg/5ml"  -> ("mg/ml", 6.0)
        "0.10% w/w" -> ("percent", 0.10)
    """
    dosage_str = dosage_str.strip().lower()
    match = re.match(r'(\d+\.?\d*)\s*(mg|g|ml|mcg|iu|%|w/w|w/v)?', dosage_str)
    if not match:
        return (dosage_str, None)

    value = float(match.group(1))
    unit = match.group(2) or 'mg'

    conversion = {
        'mg': 1.0, 'g': 1000.0, 'mcg': 0.001,
        'ml': 1.0, '%': 1.0, 'iu': 1.0,
    }

    normalized_value = value * conversion.get(unit, 1.0)
    return (unit, normalized_value)
```

### 5.3 Composition Parsing

#### 5.3.1 Branded Medicine Composition

Branded medicines have composition in `short_composition1` and `short_composition2` fields:

```python
def parse_branded_composition(comp1: str, comp2: str = '') -> list:
    """
    Parse branded medicine composition into salt list.

    Input: "Amoxycillin (500mg)" + "Clavulanic Acid (125mg)"
    Output: [SaltDosage("amoxicillin", "500mg", 500.0),
             SaltDosage("clavulanic acid", "125mg", 125.0)]
    """
    combined = f"{comp1}, {comp2}" if comp2 else comp1
    return parse_composition_string(combined)
```

#### 5.3.2 Generic Product Name

Generic products have composition embedded in the name:

```python
def parse_generic_name(generic_name: str) -> list:
    """
    Parse Jan Aushadhi generic name into salt list.

    Input: "Aceclofenac 100mg and Paracetamol 325mg Tablets"
    Output: [SaltDosage("aceclofenac", "100mg", 100.0),
             SaltDosage("acetaminophen", "325mg", 325.0)]
    """
    form_words = ['tablets', 'capsules', 'injection', 'syrup', 'gel',
                  'cream', 'ointment', 'drops', 'suspension', 'ip', 'usp']
    name = generic_name.lower()
    for word in form_words:
        name = name.replace(f' {word}', '').replace(f'{word} ', '')

    parts = re.split(r'\s+and\s+|,', name)

    salts = []
    for part in parts:
        part = part.strip()
        match = re.match(r'([a-z\s]+?)\s*(\d+\.?\d*\s*(?:mg|g|ml|mcg|iu|%)[^a-z]*)', part)
        if match:
            salt_name = normalize_salt_name(match.group(1))
            dosage_str = match.group(2).strip()
            unit, dosage_mg = normalize_dosage(dosage_str)
            salts.append(SaltDosage(salt_name, dosage_str, dosage_mg))

    return salts
```

### 5.4 Matching Algorithm

```python
# services/matching/engine.py

def find_generic_equivalents(branded_medicine_id: int) -> list:
    """Find all Jan Aushadhi generic products equivalent to a branded medicine."""
    branded_salts = get_branded_salts(branded_medicine_id)
    branded_signature = create_salt_signature(branded_salts)

    if not branded_signature:
        return []

    matching_generics = db.query(GenericProduct).join(
        generic_product_salt
    ).filter(
        generic_product_salt.c.salt_id.in_([s.id for s in branded_salts])
    ).all()

    results = []
    for generic in matching_generics:
        generic_salts = get_generic_salts(generic.id)
        generic_signature = create_salt_signature(generic_salts)

        if generic_signature == branded_signature:
            savings = calculate_savings(branded_price, generic.mrp)
            results.append(GenericMatch(
                generic=generic, savings_pct=savings.pct, savings_inr=savings.inr
            ))

    results.sort(key=lambda x: x.generic.mrp)
    return results


def create_salt_signature(salts: list) -> frozenset:
    """Create a hashable signature from a list of salts."""
    return frozenset((s.normalized_name, s.dosage_mg) for s in salts)
```

### 5.5 Match Confidence Levels

| Confidence | Criteria | Action |
|------------|----------|--------|
| `exact` | Salt signatures match exactly | Return results |
| `partial` | Some salts match but not all | Return with warning |
| `none` | No salt match found | Suggest manual search |

### 5.6 Pre-computation Strategy

For fast API responses, pre-compute all matches during data import using a materialized view:

```sql
CREATE MATERIALIZED VIEW medicine_matches AS
SELECT
    bm.id AS branded_medicine_id,
    gp.id AS generic_product_id,
    gp.mrp AS generic_mrp,
    bm.price_inr AS branded_price,
    ROUND((1 - gp.mrp / NULLIF(bm.price_inr, 0)) * 100, 1) AS savings_pct
FROM branded_medicines bm
JOIN branded_medicine_salt bms ON bm.id = bms.branded_medicine_id
JOIN generic_product_salt gps ON bms.salt_id = gps.salt_id
JOIN generic_products gp ON gps.generic_product_id = gp.id
WHERE bm.is_discontinued = FALSE
GROUP BY bm.id, gp.id, gp.mrp, bm.price_inr
HAVING COUNT(DISTINCT bms.salt_id) = (
    SELECT COUNT(DISTINCT salt_id) FROM branded_medicine_salt WHERE branded_medicine_id = bm.id
)
AND COUNT(DISTINCT gps.salt_id) = (
    SELECT COUNT(DISTINCT salt_id) FROM generic_product_salt WHERE generic_product_id = gp.id
);

CREATE UNIQUE INDEX idx_medicine_matches ON medicine_matches(branded_medicine_id, generic_product_id);
```

---

## 6. Project Structure

### 6.1 Final Directory Layout

```
sasti-dawai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py              # All API endpoints
│   │   │   └── schemas.py             # Pydantic request/response models
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py              # Settings (DB URL, etc.)
│   │   │   └── database.py            # SQLAlchemy engine + session
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── models.py              # SQLAlchemy ORM models
│   │   │   └── repositories.py        # Data access layer
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ocr/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── engine.py          # OCR pipeline
│   │   │   │   └── parser.py          # Text parsing
│   │   │   ├── matching/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── normalizer.py      # Salt/dosage normalization
│   │   │   │   └── engine.py          # Matching logic
│   │   │   ├── medicine/
│   │   │   │   ├── __init__.py
│   │   │   │   └── service.py         # Medicine lookup service
│   │   │   └── pricing/
│   │   │       ├── __init__.py
│   │   │       └── service.py         # Price comparison
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_matching.py
│   │       ├── test_ocr.py
│   │       └── test_api.py
│   ├── alembic/
│   │   └── versions/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── apps/
│   └── mobile/
│       ├── App.tsx                    # Root component + navigation
│       ├── app.json                   # Expo config
│       ├── package.json
│       ├── tsconfig.json
│       ├── babel.config.js
│       ├── src/
│       │   ├── screens/
│       │   │   ├── ScanScreen.tsx     # Camera + OCR upload
│       │   │   ├── ResultsScreen.tsx  # Medicine + generics display
│       │   │   ├── SearchScreen.tsx   # Manual search
│       │   │   └── DetailScreen.tsx   # Generic product details
│       │   ├── components/
│       │   │   ├── CameraView.tsx
│       │   │   ├── MedicineCard.tsx
│       │   │   ├── GenericCard.tsx
│       │   │   ├── SavingsBadge.tsx
│       │   │   └── SearchBar.tsx
│       │   ├── services/
│       │   │   └── api.ts             # API client
│       │   ├── types/
│       │   │   └── index.ts
│       │   └── utils/
│       │       └── format.ts
│       └── assets/
│
├── scripts/
│   ├── import_data.py                 # CSV -> PostgreSQL
│   ├── normalize_salts.py             # Extract and normalize salts
│   ├── precompute_matches.py          # Pre-compute matches
│   └── seed_test_data.py              # Seed test data
│
├── data/
│   ├── raw/                           # Original CSV files
│   ├── normalized/                     # Cleaned CSV files
│   └── processed/                     # Pre-computed data
│
├── docs/
│   └── architecture.md                # This document
│
├── tests/
│   └── e2e/
│       └── test_full_flow.py
│
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.mobile
├── .env.example
├── .gitignore
└── README.md
```

### 6.2 Key Files

#### `backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.database import engine
from app.db.models import Base

app = FastAPI(
    title="SASTI DAWAI API",
    description="Find affordable generic medicine equivalents",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}
```

#### `backend/app/api/routes.py`

```python
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from app.api.schemas import ScanResponse, MedicineSearchResponse, MedicineDetailResponse
from app.services.ocr.engine import process_medicine_image
from app.services.matching.engine import find_generic_equivalents
from app.services.medicine.service import search_medicines, get_medicine_detail

router = APIRouter()

@router.post("/scan", response_model=ScanResponse)
async def scan_medicine(image: UploadFile = File(...)):
    contents = await image.read()
    ocr_result = process_medicine_image(contents)

    if not ocr_result.medicine_name:
        raise HTTPException(422, "Could not identify medicine from image")

    medicine = search_medicines(ocr_result.medicine_name, limit=1)
    if not medicine:
        raise HTTPException(422, "Medicine not found in database")

    generics = find_generic_equivalents(medicine.id)

    return ScanResponse(
        success=True,
        ocr_text=ocr_result.raw_text,
        identified_medicine=medicine,
        generics=generics,
        match_confidence=ocr_result.confidence
    )

@router.get("/medicines/search", response_model=MedicineSearchResponse)
async def search(q: str = Query(..., min_length=2), limit: int = 20):
    results = search_medicines(q, limit)
    return MedicineSearchResponse(query=q, count=len(results), results=results)

@router.get("/medicines/{medicine_id}", response_model=MedicineDetailResponse)
async def medicine_detail(medicine_id: int):
    medicine = get_medicine_detail(medicine_id)
    if not medicine:
        raise HTTPException(404, "Medicine not found")
    return medicine
```

#### `apps/mobile/App.tsx`

```tsx
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { ScanScreen } from './src/screens/ScanScreen';
import { ResultsScreen } from './src/screens/ResultsScreen';
import { SearchScreen } from './src/screens/SearchScreen';

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Scan">
        <Stack.Screen name="Scan" component={ScanScreen} options={{ title: 'Scan Medicine' }} />
        <Stack.Screen name="Results" component={ResultsScreen} options={{ title: 'Results' }} />
        <Stack.Screen name="Search" component={SearchScreen} options={{ title: 'Search' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

---

## 7. Risk Assessment

### 7.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| OCR accuracy on medicine strips | High | High | Fallback to manual text entry; allow user to edit OCR text; use image preprocessing |
| Salt name spelling variations | Medium | High | Comprehensive normalization mapping; manual curation of common variations |
| Dosage format inconsistencies | Medium | Medium | Robust regex parsing; handle mg/g/ml/%/IU; unit conversion |
| Combination drugs (2+ salts) | High | Medium | Parse all salts from composition; match on complete salt set |
| No exact match found | Medium | Medium | Show partial matches; suggest similar medicines; manual search |
| Database import errors | Low | High | Validate CSV data; handle encoding issues; test import script |
| Tesseract not installed | Medium | High | Docker image includes Tesseract; fallback to cloud OCR API |
| Mobile camera quality variance | High | Medium | Image preprocessing; guide user with camera overlay; manual entry fallback |

### 7.2 Data Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Incomplete composition data | Medium | High | Some medicines may have empty composition; handle gracefully |
| Discontinued medicines | Low | Low | Filter out discontinued; show warning if scanned medicine is discontinued |
| Price changes | Low | Low | Prices are snapshot; add "last updated" timestamp |
| Jan Aushadhi stock availability | Medium | Medium | Out of scope for prototype; note in UI |

### 7.3 Demo Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Demo image not in database | Medium | High | Pre-load test images; ensure common medicines are in dataset |
| Network latency | Medium | Medium | Optimize queries; add loading states; cache results |
| Mobile build issues | Medium | High | Use Expo Go for development; EAS Build for production |

### 7.4 Safety Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Incorrect matching | Low | Critical | Deterministic exact matching only; no fuzzy/LLM matching; show composition for user verification |
| Outdated price data | Medium | Medium | Add disclaimer; show "last updated" date |
| Missing safety info | Medium | Medium | Add "consult doctor" disclaimer; show full composition |

---

## 8. Implementation Plan

### 8.1 Phase 1: Data Pipeline (Hours 0-2)

**Goal:** Import and normalize all data into PostgreSQL.

- [ ] 1.1  Set up PostgreSQL (Docker)
- [ ] 1.2  Create database schema (DDL)
- [ ] 1.3  Write import script for branded medicines
- [ ] 1.4  Write import script for Jan Aushadhi products
- [ ] 1.5  Extract and normalize salts from compositions
- [ ] 1.6  Build salt signature index
- [ ] 1.7  Pre-compute matches (materialized view)
- [ ] 1.8  Validate data quality (row counts, sample checks)

**Key scripts:**
- `scripts/import_data.py` - Main import script
- `scripts/normalize_salts.py` - Salt extraction and normalization
- `scripts/precompute_matches.py` - Match pre-computation

### 8.2 Phase 2: Backend API (Hours 2-4)

**Goal:** Working FastAPI backend with all endpoints.

- [ ] 2.1  Set up FastAPI project structure
- [ ] 2.2  Configure SQLAlchemy + database connection
- [ ] 2.3  Implement Pydantic schemas
- [ ] 2.4  Implement medicine search endpoint
- [ ] 2.5  Implement medicine detail endpoint
- [ ] 2.6  Implement matching engine service
- [ ] 2.7  Implement OCR endpoint (basic)
- [ ] 2.8  Test all endpoints with curl/Postman

### 8.3 Phase 3: OCR Pipeline (Hours 4-5)

**Goal:** Working OCR pipeline for medicine images.

- [ ] 3.1  Install and configure Tesseract
- [ ] 3.2  Implement image preprocessing
- [ ] 3.3  Implement OCR text extraction
- [ ] 3.4  Implement text parsing (name + composition)
- [ ] 3.5  Integrate OCR with matching engine
- [ ] 3.6  Test with sample medicine images
- [ ] 3.7  Add fallback for low-confidence OCR

### 8.4 Phase 4: Mobile App (Hours 5-7)

**Goal:** Working Expo app with camera, search, and results.

- [ ] 4.1  Set up Expo project
- [ ] 4.2  Implement camera screen (expo-camera)
- [ ] 4.3  Implement image upload to backend
- [ ] 4.4  Implement results screen (medicine + generics)
- [ ] 4.5  Implement search screen (manual lookup)
- [ ] 4.6  Add loading states and error handling
- [ ] 4.7  Polish UI (savings badge, comparison view)
- [ ] 4.8  Test on device/emulator

### 8.5 Phase 5: Integration and Testing (Hours 7-8)

**Goal:** End-to-end working demo.

- [ ] 5.1  Integration test: camera -> OCR -> match -> display
- [ ] 5.2  Test with multiple medicine images
- [ ] 5.3  Fix bugs and edge cases
- [ ] 5.4  Add error handling and fallbacks
- [ ] 5.5  Performance optimization (if needed)
- [ ] 5.6  Final UI polish
- [ ] 5.7  Prepare demo script
- [ ] 5.8  Deploy (Docker / Expo EAS)

### 8.6 Demo Script (5 minutes)

1. **Open app** -> Camera screen
2. **Scan Augmentin 625 strip** -> OCR extracts name
3. **Show results** -> Branded price Rs.223 vs Generic Rs.45 (80% savings)
4. **Scan another medicine** -> e.g., Azithral 500 -> Generic Rs.15
5. **Manual search** -> Type "Paracetamol" -> Show all variants
6. **Show comparison** -> Side-by-side price comparison

### 8.7 Fallback Plans

| If this fails... | Do this instead |
|-------------------|-----------------|
| OCR doesn't work | Manual text entry -> search -> results |
| Tesseract not installed | Use cloud OCR API (Google Vision) |
| Mobile build too slow | Use PWA (React + WebCamera) |
| Database too slow | Use SQLite for demo (switch to PostgreSQL later) |
| No exact match | Show partial matches + similar medicines |

---

## Appendix A: Data Samples

### A.1 Branded Medicine (indian_medicine_data.csv)

| id | name | price | manufacturer | composition1 | composition2 |
|----|------|-------|-------------|---------------|--------------|
| 1 | Augmentin 625 Duo Tablet | 223.42 | GSK | Amoxycillin (500mg) | Clavulanic Acid (125mg) |
| 2 | Azithral 500 Tablet | 132.36 | Alembic | Azithromycin (500mg) | -- |
| 3 | Ascoril LS Syrup | 118.00 | Glenmark | Ambroxol (30mg/5ml) | Levosalbutamol (1mg/5ml) |

### A.2 Jan Aushadhi Generic (jan_aushadhi_products.csv)

| drug_code | generic_name | mrp | group_name |
|-----------|-------------|-----|------------|
| 1 | Aceclofenac 100mg and Paracetamol 325mg Tablets | 10.32 | Analgesic |
| 2 | Aceclofenac Tablets IP 100 mg | 8.25 | Analgesic |
| 3 | Pregabalin Capsules IP 75 mg | 22.69 | CNS |

---

## Appendix B: Environment Variables

```bash
# .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sasti_dawai
OCR_ENGINE=tesseract
TESSERACT_CMD=/usr/bin/tesseract
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=*
```

---

## Appendix C: Docker Compose

```yaml
version: '3.8'

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: sasti_dawai
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/sasti_dawai
    ports:
      - "8000:8000"
    depends_on:
      - db
    volumes:
      - ./data:/app/data

volumes:
  pgdata:
```

---

*Document Version: 1.0*
*Last Updated: 2026-10-08*
*Author: SASTI DAWAI Team - Aayu 2026 T06*
