"""Database models for medicines."""
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.database import Base


# Association table for many-to-many: branded medicine <-> ingredients
branded_ingredient = Table(
    "branded_ingredient",
    Base.metadata,
    Column("branded_id", Integer, ForeignKey("branded_medicines.id"), primary_key=True),
    Column("ingredient_id", Integer, ForeignKey("ingredients.id"), primary_key=True),
    Column("strength", String(50)),  # e.g., "500mg"
    Column("position", Integer, default=0),  # ordering for display
)


class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, index=True)  # normalized name
    canonical_name = Column(String(200), nullable=False, index=True)


class BrandedMedicine(Base):
    __tablename__ = "branded_medicines"
    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False, index=True)  # brand name
    manufacturer = Column(String(300))
    price = Column(Float)
    is_discontinued = Column(Boolean, default=False)
    medicine_type = Column(String(50))  # allopathy, ayurveda, etc.
    pack_size_label = Column(String(200))
    dosage_form = Column(String(50), index=True)  # tablet, capsule, etc.
    release_type = Column(String(50))  # immediate, extended, etc.

    ingredients = relationship("Ingredient", secondary=branded_ingredient, backref="branded_medicines")


class JanAushadhiProduct(Base):
    __tablename__ = "jan_aushadhi_products"
    id = Column(Integer, primary_key=True)
    drug_code = Column(String(50), unique=True)
    generic_name = Column(String(500), nullable=False, index=True)
    unit_size = Column(String(100))
    mrp = Column(Float)
    group_name = Column(String(300))
    dosage_form = Column(String(50), index=True)
    release_type = Column(String(50))
    ingredients = Column(Text)  # JSON string of normalized ingredients
    raw_name = Column(String(500))  # original name for reference


class Kendra(Base):
    __tablename__ = "kendras"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))
    address = Column(Text)
    state = Column(String(100))
    district = Column(String(100))
    pincode = Column(String(20))
    latitude = Column(Float)
    longitude = Column(Float)
