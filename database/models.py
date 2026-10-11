import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    barcode = Column(String, index=True, nullable=True)
    name = Column(String, nullable=False)
    length = Column(Float, nullable=False)  # in mm
    width = Column(Float, nullable=False)   # in mm
    height = Column(Float, nullable=False)  # in mm
    weight = Column(Float, nullable=False)  # in kg
    fragile = Column(Boolean, default=False)
    stackable = Column(Boolean, default=True)
    max_stack_weight = Column(Float, default=9999.0)  # in kg
    allowed_rotations = Column(String, default="XYZ")  # E.g., "XYZ", "XY", "Z"
    category = Column(String, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "sku": self.sku,
            "barcode": self.barcode,
            "name": self.name,
            "length": self.length,
            "width": self.width,
            "height": self.height,
            "weight": self.weight,
            "fragile": self.fragile,
            "stackable": self.stackable,
            "max_stack_weight": self.max_stack_weight,
            "allowed_rotations": self.allowed_rotations,
            "category": self.category
        }


class Carton(Base):
    __tablename__ = "cartons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    length = Column(Float, nullable=False)  # in mm
    width = Column(Float, nullable=False)   # in mm
    height = Column(Float, nullable=False)  # in mm
    empty_weight = Column(Float, default=0.0)  # in kg
    max_weight = Column(Float, nullable=False)  # in kg
    cost = Column(Float, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "length": self.length,
            "width": self.width,
            "height": self.height,
            "empty_weight": self.empty_weight,
            "max_weight": self.max_weight,
            "cost": self.cost
        }


class Courier(Base):
    __tablename__ = "couriers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    volumetric_factor = Column(Float, default=5000.0)  # e.g., 5000 (standard delivery divisor)
    rate_per_kg = Column(Float, nullable=False)
    minimum_charge = Column(Float, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "volumetric_factor": self.volumetric_factor,
            "rate_per_kg": self.rate_per_kg,
            "minimum_charge": self.minimum_charge
        }


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    selected_products = Column(String, nullable=False)  # JSON string of product IDs and quantities
    carton_id = Column(Integer, ForeignKey("cartons.id"), nullable=True)
    layout = Column(String, nullable=False)  # JSON representation of coordinates, rotations, layer indexing
    utilization = Column(Float, nullable=False)  # Space utilization score
    actual_weight = Column(Float, nullable=False)
    volumetric_weight = Column(Float, nullable=False)
    chargeable_weight = Column(Float, nullable=False)
    shipping_cost = Column(Float, nullable=False)
    report_path = Column(String, nullable=True)
    statistics = Column(String, nullable=True)  # JSON details (stability, CoG coords, efficiency)

    carton = relationship("Carton")

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "selected_products": self.selected_products,
            "carton_id": self.carton_id,
            "layout": self.layout,
            "utilization": self.utilization,
            "actual_weight": self.actual_weight,
            "volumetric_weight": self.volumetric_weight,
            "chargeable_weight": self.chargeable_weight,
            "shipping_cost": self.shipping_cost,
            "report_path": self.report_path,
            "statistics": self.statistics
        }
