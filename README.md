# SASTI DAWAI — Aayu 2026 T06

**Scanning Medicine Strips to Find Affordable Generic Equivalents with the Same Salt**

SASTI DAWAI is a mobile-first AI prototype that scans medicine strips/boxes to identify the brand, salt, strength, and dosage form — then finds exact lower-cost Jan Aushadhi equivalents with potential savings.

## Problem Statement

> Build an app that scans a medicine strip, identifies the salt, strength and form, and shows exact lower-cost equivalents, the monthly saving, and where to buy them. It should always end with "confirm with your doctor or pharmacist."

## Features

- **Camera Scanning** — Scan medicine strips/boxes using phone camera
- **OCR Extraction** — Extracts brand name, salt, strength, dosage form using Tesseract OCR
- **Exact Matching** — Deterministic matching engine (same salt + strength + form)
- **Savings Calculation** — Shows potential savings per pack and annual savings
- **Jan Aushadhi Locator** — Find nearby Jan Aushadhi Kendras
- **Manual Search** — Fallback search if scanning fails
- **Safety First** — Always shows "Confirm with your doctor or pharmacist before switching"

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy, SQLite |
| OCR | Tesseract (pytesseract), OpenCV, Pillow |
| Frontend | PWA (HTML/CSS/JS), Mobile-first responsive |
| Database | SQLite (PostgreSQL-ready schema) |

## Project Structure

```
sasti-dawai/
├── apps/
│   └── mobile/              # PWA mobile app
│       ├── index.html       # Main HTML
│       ├── styles.css       # Mobile-first styles
│       ├── app.js           # App logic
│       ├── manifest.json    # PWA manifest
│       └── sw.js            # Service worker
├── backend/
│   └── app/
│       ├── main.py          # FastAPI application
│       ├── api/
│       │   └── scan.py      # OCR scan endpoint
│       ├── core/
│       │   ├── config.py    # Configuration
│       │   └── normalization.py  # Medicine normalization
│       ├── db/
│       │   └── database.py  # Database setup
│       ├── models/
│       │   └── medicine.py  # SQLAlchemy models
│       ├── schemas/
│       │   └── medicine.py  # Pydantic schemas
│       └── services/
│           ├── matching/
│           │   └── exact_matcher.py  # Exact matching engine
│           ├── medicine/
│           │   └── data_loader.py    # CSV data loader
│           └── ocr/
│               └── ocr_service.py    # OCR pipeline
├── data/
│   ├── raw/                 # Original datasets (not committed)
│   ├── processed/           # Processed data
│   └── normalized/          # Normalized data
├── scripts/
│   ├── seed_demo_data.py    # Demo data seeder
│   └── profile_datasets.py  # Dataset profiler
├── docs/
│   └── architecture.md      # Architecture document
├── tests/                   # Test files
├── docker-compose.yml       # Docker setup
├── .env.example             # Environment template
└── .gitignore               # Git ignore rules
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/scan` | Upload medicine image, OCR extraction |
| GET | `/api/v1/medicines/search?q=` | Search medicines by name |
| GET | `/api/v1/medicines/{id}` | Get medicine details |
| POST | `/api/v1/match` | Find exact Jan Aushadhi equivalents |
| GET | `/api/v1/medicines/{id}/alternatives` | Get exact alternatives |
| GET | `/api/v1/medicines/{id}/savings` | Calculate savings |
| GET | `/api/v1/kendras/nearby?lat=&lng=` | Find nearby Kendras |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 24+ (for PWA serving)
- Tesseract OCR installed

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

### Seed Demo Data

```bash
python scripts/seed_demo_data.py
```

### Mobile App

Serve the PWA using any static file server:

```bash
cd apps/mobile
npx serve .
# or
python -m http.server 3000
```

## Safety & Disclaimer

**This application is NOT a doctor.**

- It does NOT diagnose
- It does NOT recommend changing medication independently
- It does NOT invent medicine, composition, dosage, price, or availability
- When confidence is insufficient, it asks the user to verify instead of guessing
- Every result ends with: **"Confirm with your doctor or pharmacist before switching."**

## Exact Matching Rules

The matching engine uses **deterministic exact matching**:

1. Same active ingredient(s) — normalized salt names
2. Same strength(s) — exact numeric match
3. Same dosage form — tablet, capsule, syrup, etc.
4. Same release type — immediate, extended, sustained, etc.

**NO semantic similarity. NO LLM-based equivalence decisions.**

If no exact match exists: "No exact equivalent found in our current database."

## Demo Medicines

The following medicines are seeded for demo:

| Brand | Salt | Strength | Form | Price | Jan Aushadhi | Saving |
|-------|------|----------|------|-------|--------------|--------|
| Glycomet 500 | Metformin HCl | 500mg | Tablet | ₹45 | ₹15 | ₹30 |
| Zoryl 2 | Glimepiride | 2mg | Tablet | ₹120 | ₹25 | ₹95 |
| Telma 40 | Telmisartan | 40mg | Tablet | ₹85 | ₹18 | ₹67 |
| Amlopres 5 | Amlodipine | 5mg | Tablet | ₹60 | ₹12 | ₹48 |
| Atorva 20 | Atorvastatin | 20mg | Tablet | ₹150 | ₹35 | ₹115 |
| Pan 40 | Pantoprazole | 40mg | Tablet | ₹95 | ₹28 | ₹67 |
| Azithral 500 | Azithromycin | 500mg | Tablet | ₹132 | ₹45 | ₹87 |
| Augmentin 625 | Amoxycillin+Clavulanic | 500/125mg | Tablet | ₹223 | ₹65 | ₹158 |

## License

MIT License — Built for Aayu 2026 Hackathon
