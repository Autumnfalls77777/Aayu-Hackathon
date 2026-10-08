"""Seed demo data for SASTI DAWAI - medicines guaranteed to work for demo."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.db.database import SessionLocal, engine, Base
from app.models.medicine import BrandedMedicine, JanAushadhiProduct, Ingredient
from app.core.normalization import normalize_salt_name, parse_composition
import json


def seed_demo_data():
    """Seed demo medicines that have exact matches."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Demo medicines with known exact matches
    demo_medicines = [
        {
            "brand_name": "Glycomet 500",
            "manufacturer": "USV Ltd",
            "price": 45.0,
            "composition": "Metformin Hydrochloride (500mg)",
            "dosage_form": "tablet",
            "pack_size": "strip of 10 tablets",
        },
        {
            "brand_name": "Zoryl 2",
            "manufacturer": "Intas Pharmaceuticals",
            "price": 120.0,
            "composition": "Glimepiride (2mg)",
            "dosage_form": "tablet",
            "pack_size": "strip of 10 tablets",
        },
        {
            "brand_name": "Telma 40",
            "manufacturer": "Glenmark Pharmaceuticals",
            "price": 85.0,
            "composition": "Telmisartan (40mg)",
            "dosage_form": "tablet",
            "pack_size": "strip of 15 tablets",
        },
        {
            "brand_name": "Amlopres 5",
            "manufacturer": "Cipla Ltd",
            "price": 60.0,
            "composition": "Amlodipine (5mg)",
            "dosage_form": "tablet",
            "pack_size": "strip of 10 tablets",
        },
        {
            "brand_name": "Atorva 20",
            "manufacturer": "Pfizer Ltd",
            "price": 150.0,
            "composition": "Atorvastatin (20mg)",
            "dosage_form": "tablet",
            "pack_size": "strip of 10 tablets",
        },
        {
            "brand_name": "Pan 40",
            "manufacturer": "Alkem Laboratories",
            "price": 95.0,
            "composition": "Pantoprazole (40mg)",
            "dosage_form": "tablet",
            "pack_size": "strip of 10 tablets",
        },
        {
            "brand_name": "Azithral 500",
            "manufacturer": "Alembic Pharmaceuticals",
            "price": 132.0,
            "composition": "Azithromycin (500mg)",
            "dosage_form": "tablet",
            "pack_size": "strip of 5 tablets",
        },
        {
            "brand_name": "Augmentin 625",
            "manufacturer": "Glaxo SmithKline",
            "price": 223.0,
            "composition": "Amoxycillin (500mg), Clavulanic Acid (125mg)",
            "dosage_form": "tablet",
            "pack_size": "strip of 10 tablets",
        },
    ]

    # Corresponding Jan Aushadhi equivalents
    demo_generics = [
        {
            "drug_code": "DEMO001",
            "generic_name": "Metformin Hydrochloride Tablets IP 500 mg",
            "unit_size": "10's",
            "mrp": 15.0,
            "group_name": "Antidiabetic",
            "dosage_form": "tablet",
            "ingredients": [{"name": "Metformin Hydrochloride", "strength": 500, "unit": "mg"}],
        },
        {
            "drug_code": "DEMO002",
            "generic_name": "Glimepiride Tablets IP 2 mg",
            "unit_size": "10's",
            "mrp": 25.0,
            "group_name": "Antidiabetic",
            "dosage_form": "tablet",
            "ingredients": [{"name": "Glimepiride", "strength": 2, "unit": "mg"}],
        },
        {
            "drug_code": "DEMO003",
            "generic_name": "Telmisartan Tablets IP 40 mg",
            "unit_size": "10's",
            "mrp": 18.0,
            "group_name": "Antihypertensive",
            "dosage_form": "tablet",
            "ingredients": [{"name": "Telmisartan", "strength": 40, "unit": "mg"}],
        },
        {
            "drug_code": "DEMO004",
            "generic_name": "Amlodipine Tablets IP 5 mg",
            "unit_size": "10's",
            "mrp": 12.0,
            "group_name": "Antihypertensive",
            "dosage_form": "tablet",
            "ingredients": [{"name": "Amlodipine", "strength": 5, "unit": "mg"}],
        },
        {
            "drug_code": "DEMO005",
            "generic_name": "Atorvastatin Tablets IP 20 mg",
            "unit_size": "10's",
            "mrp": 35.0,
            "group_name": "Antihyperlipidemic",
            "dosage_form": "tablet",
            "ingredients": [{"name": "Atorvastatin", "strength": 20, "unit": "mg"}],
        },
        {
            "drug_code": "DEMO006",
            "generic_name": "Pantoprazole Tablets IP 40 mg",
            "unit_size": "10's",
            "mrp": 28.0,
            "group_name": "Antacid/Antiulcer",
            "dosage_form": "tablet",
            "ingredients": [{"name": "Pantoprazole", "strength": 40, "unit": "mg"}],
        },
        {
            "drug_code": "DEMO007",
            "generic_name": "Azithromycin Tablets IP 500 mg",
            "unit_size": "10's",
            "mrp": 45.0,
            "group_name": "Antibiotic",
            "dosage_form": "tablet",
            "ingredients": [{"name": "Azithromycin", "strength": 500, "unit": "mg"}],
        },
        {
            "drug_code": "DEMO008",
            "generic_name": "Amoxycillin and Clavulanic Acid Tablets IP 500mg/125mg",
            "unit_size": "10's",
            "mrp": 65.0,
            "group_name": "Antibiotic",
            "dosage_form": "tablet",
            "ingredients": [
                {"name": "Amoxycillin", "strength": 500, "unit": "mg"},
                {"name": "Clavulanic Acid", "strength": 125, "unit": "mg"},
            ],
        },
    ]

    try:
        # Add branded medicines
        for med in demo_medicines:
            # Check if exists
            existing = db.query(BrandedMedicine).filter(
                BrandedMedicine.name == med["brand_name"]
            ).first()
            if existing:
                continue

            # Parse composition
            ingredients = parse_composition(med["composition"])

            # Create ingredient objects
            ing_objects = []
            for ing in ingredients:
                norm_name = normalize_salt_name(ing["name"])
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
                ing_objects.append(ing_obj)

            branded = BrandedMedicine(
                name=med["brand_name"],
                manufacturer=med["manufacturer"],
                price=med["price"],
                is_discontinued=False,
                medicine_type="allopathy",
                pack_size_label=med["pack_size"],
                dosage_form=med["dosage_form"],
                release_type=None,
            )
            branded.ingredients = ing_objects
            db.add(branded)

        # Add Jan Aushadhi products
        for gen in demo_generics:
            existing = db.query(JanAushadhiProduct).filter(
                JanAushadhiProduct.drug_code == gen["drug_code"]
            ).first()
            if existing:
                continue

            product = JanAushadhiProduct(
                drug_code=gen["drug_code"],
                generic_name=gen["generic_name"],
                unit_size=gen["unit_size"],
                mrp=gen["mrp"],
                group_name=gen["group_name"],
                dosage_form=gen["dosage_form"],
                release_type=None,
                ingredients=json.dumps(gen["ingredients"]),
                raw_name=gen["generic_name"],
            )
            db.add(product)

        db.commit()
        print(f"Seeded {len(demo_medicines)} demo branded medicines")
        print(f"Seeded {len(demo_generics)} demo Jan Aushadhi products")
        print("Demo data ready for hackathon!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding demo data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
