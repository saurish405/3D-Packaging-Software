from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ProductSchema:
    sku: str
    name: str
    length: float
    width: float
    height: float
    weight: float
    barcode: Optional[str] = None
    fragile: bool = False
    stackable: bool = True
    max_stack_weight: float = 9999.0
    allowed_rotations: str = "XYZ"
    category: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductSchema":
        return cls(
            sku=str(data.get("sku", "")),
            name=str(data.get("name", "")),
            length=float(data.get("length", 0.0)),
            width=float(data.get("width", 0.0)),
            height=float(data.get("height", 0.0)),
            weight=float(data.get("weight", 0.0)),
            barcode=data.get("barcode"),
            fragile=bool(data.get("fragile", False)),
            stackable=bool(data.get("stackable", True)),
            max_stack_weight=float(data.get("max_stack_weight", 9999.0)),
            allowed_rotations=str(data.get("allowed_rotations", "XYZ")),
            category=data.get("category")
        )

@dataclass
class CartonSchema:
    name: str
    length: float
    width: float
    height: float
    max_weight: float
    empty_weight: float = 0.0
    cost: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CartonSchema":
        return cls(
            name=str(data.get("name", "")),
            length=float(data.get("length", 0.0)),
            width=float(data.get("width", 0.0)),
            height=float(data.get("height", 0.0)),
            max_weight=float(data.get("max_weight", 0.0)),
            empty_weight=float(data.get("empty_weight", 0.0)),
            cost=float(data.get("cost", 0.0))
        )
