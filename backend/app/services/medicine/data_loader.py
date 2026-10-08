"""Load and normalize medicine data from CSV files into the database."""
import csv
import json
import re
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.medicine import BrandedMedicine, JanAushadhiProduct, Ingredient
from app.core.normalization import (
    normalize_salt_name,
    normalize_dosage_form,
    extract_strength,
    extract_release_type,
    parse_composition,
    normalize_medicine_name,
)


def load_branded_medicines(db: Session, csv_path: str, batch_size: int = 1000) -> int:
    """Load branded medicines from CSV into database."""
    count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse composition
            comp1 = row.get("short_composition1", "").strip()
            comp2 = row.get("short_composition2", "").strip()
            full_comp = ", ".join([c for c in [comp1, comp2] if c])
            ingredients = parse_composition(full_comp)

            # Extract dosage form from name or pack_size
            name = row.get("name", "")
            pack_size = row.get("pack_size_label", "")
            dosage_form = _extract_dosage_form_from_text(f"{name} {pack_size}")

            # Extract release type
            release_type = extract_release_type(name)

            # Create or get ingredients
            ingredient_objects = []
            for ing in ingredients:
                norm_name = ing["normalized_name"]
                if not norm_name:
                    continue
                # Check if ingredient exists
                ing_obj = db.query(Ingredient).filter(
                    Ingredient.canonical_name == norm_name
                ).first()
                if not ing_obj:
                    ing_obj = Ingredient(
                        name=ing["name"],
                        canonical_name=norm_name,
                    )
                    db.add(ing_obj)
                    db.flush()
                ingredient_objects.append(ing_obj)

            # Create branded medicine
            branded = BrandedMedicine(
                name=name,
                manufacturer=row.get("manufacturer_name", ""),
                price=float(row["price(₹)"]) if row.get("price(₹)") else None,
                is_discontinued=row.get("Is_discontinued", "FALSE").upper() == "TRUE",
                medicine_type=row.get("type", ""),
                pack_size_label=pack_size,
                dosage_form=dosage_form,
                release_type=release_type,
            )
            branded.ingredients = ingredient_objects
            db.add(branded)
            count += 1

            if count % batch_size == 0:
                db.commit()
                print(f"Loaded {count} branded medicines...")

    db.commit()
    print(f"Total branded medicines loaded: {count}")
    return count


def load_jan_aushadhi_products(db: Session, csv_path: str, batch_size: int = 500) -> int:
    """Load Jan Aushadhi products from CSV into database."""
    count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            generic_name = row.get("Generic Name", "").strip()
            if not generic_name:
                continue

            # Parse ingredients from generic name
            ingredients = parse_composition(generic_name)

            # Extract dosage form
            dosage_form = _extract_dosage_form_from_text(generic_name)

            # Extract release type
            release_type = extract_release_type(generic_name)

            # Create Jan Aushadhi product
            product = JanAushadhiProduct(
                drug_code=row.get("Drug Code", ""),
                generic_name=generic_name,
                unit_size=row.get("Unit Size", ""),
                mrp=float(row["MRP"]) if row.get("MRP") else None,
                group_name=row.get("Group Name", ""),
                dosage_form=dosage_form,
                release_type=release_type,
                ingredients=json.dumps(ingredients),
                raw_name=generic_name,
            )
            db.add(product)
            count += 1

            if count % batch_size == 0:
                db.commit()
                print(f"Loaded {count} Jan Aushadhi products...")

    db.commit()
    print(f"Total Jan Aushadhi products loaded: {count}")
    return count


def _extract_dosage_form_from_text(text: str) -> str:
    """Extract dosage form from text."""
    if not text:
        return ""
    text_lower = text.lower()
    # Common patterns
    if "tablet" in text_lower or " tab" in text_lower:
        return "tablet"
    if "capsule" in text_lower or " cap" in text_lower:
        return "capsule"
    if "syrup" in text_lower or " syp" in text_lower:
        return "syrup"
    if "injection" in text_lower or " inj" in text_lower:
        return "injection"
    if "drops" in text_lower or " drop" in text_lower:
        return "drops"
    if "cream" in text_lower:
        return "cream"
    if "ointment" in text_lower:
        return "ointment"
    if "gel" in text_lower:
        return "gel"
    if "lotion" in text_lower:
        return "lotion"
    if "powder" in text_lower:
        return "powder"
    if "inhaler" in text_lower:
        return "inhaler"
    if "patch" in text_lower:
        return "patch"
    if "suppository" in text_lower:
        return "suppository"
    if "suspension" in text_lower or "susp" in text_lower:
        return "suspension"
    if "solution" in text_lower:
        return "solution"
    if "vial" in text_lower:
        return "vial"
    if "ampoule" in text_lower or "amp" in text_lower:
        return "ampoule"
    if "sachet" in text_lower:
        return "sachet"
    if "spray" in text_lower:
        return "spray"
    if "lozenge" in text_lower:
        return "lozenge"
    if "mouthwash" in text_lower:
        return "mouthwash"
    if "gargle" in text_lower:
        return "gargle"
    if "shampoo" in text_lower:
        return "shampoo"
    if "soap" in text_lower:
        return "soap"
    if "liniment" in text_lower:
        return "liniment"
    if "paste" in text_lower:
        return "paste"
    if "jelly" in text_lower:
        return "jelly"
    return ""
