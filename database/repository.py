import csv
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models import Product, Carton, Courier, Job

class ProductRepository:
    @staticmethod
    def create(db: Session, sku: str, name: str, length: float, width: float, height: float, 
               weight: float, barcode: str = None, fragile: bool = False, 
               stackable: bool = True, max_stack_weight: float = 9999.0, 
               allowed_rotations: str = "XYZ", category: str = None) -> Product:
        product = Product(
            sku=sku, name=name, length=length, width=width, height=height, weight=weight,
            barcode=barcode, fragile=fragile, stackable=stackable, max_stack_weight=max_stack_weight,
            allowed_rotations=allowed_rotations, category=category
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def get_by_id(db: Session, product_id: int) -> Optional[Product]:
        return db.query(Product).filter(Product.id == product_id).first()

    @staticmethod
    def get_by_sku(db: Session, sku: str) -> Optional[Product]:
        return db.query(Product).filter(Product.sku == sku).first()

    @staticmethod
    def get_all(db: Session, search: str = None) -> List[Product]:
        query = db.query(Product)
        if search:
            query = query.filter(
                Product.sku.contains(search) | 
                Product.name.contains(search) | 
                Product.category.contains(search)
            )
        return query.all()

    @staticmethod
    def update(db: Session, product_id: int, updates: Dict[str, Any]) -> Optional[Product]:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            for key, val in updates.items():
                if hasattr(product, key):
                    setattr(product, key, val)
            db.commit()
            db.refresh(product)
        return product

    @staticmethod
    def delete(db: Session, product_id: int) -> bool:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            db.delete(product)
            db.commit()
            return True
        return False

    @staticmethod
    def import_csv(db: Session, file_path: str) -> int:
        """Legacy CSV importer wrapper."""
        result = ProductRepository.import_excel_or_csv(db, file_path)
        return result["total"]

    @staticmethod
    def import_excel_or_csv(db: Session, file_path: str) -> dict:
        """
        Imports products from an Excel (.xlsx, .xls) or CSV file.
        Returns dict: {"imported": int, "updated": int, "total": int, "errors": list}
        """
        import os
        import csv

        ext = os.path.splitext(file_path)[1].lower()
        rows_data = []

        if ext in ('.xlsx', '.xls'):
            try:
                import pandas as pd
                df = pd.read_excel(file_path)
                df = df.where(pd.notnull(df), None)
                rows_data = df.to_dict(orient='records')
            except Exception as e:
                # Fallback if pandas read fails
                raise RuntimeError(f"Could not parse Excel file: {e}")
        else:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows_data = list(reader)

        imported_count = 0
        updated_count = 0
        errors = []

        def get_val(row, *aliases, default=""):
            for key in row.keys():
                if key is None:
                    continue
                k_clean = str(key).strip().lower().replace("_", "").replace(" ", "").replace("-", "")
                for suffix in ["(mm)", "(kg)", "mm", "kg"]:
                    k_clean = k_clean.replace(suffix, "")
                for a in aliases:
                    a_clean = a.lower().replace("_", "").replace(" ", "").replace("-", "")
                    if k_clean == a_clean:
                        val = row[key]
                        if val is not None and str(val).strip() != "" and str(val).strip().lower() != "nan":
                            return val
            return default

        for idx, row in enumerate(rows_data):
            try:
                sku = str(get_val(row, "sku", "skuid", "productsku", "itemsku", default="")).strip()
                if not sku:
                    continue

                name = str(get_val(row, "name", "productname", "itemname", "title", default=sku)).strip()
                length = float(get_val(row, "length", "lengthmm", "len", "l", default=0.0))
                width = float(get_val(row, "width", "widthmm", "wid", "w", default=0.0))
                height = float(get_val(row, "height", "heightmm", "hei", "h", default=0.0))
                weight = float(get_val(row, "weight", "weightkg", "wt", default=0.0))

                barcode_raw = get_val(row, "barcode", "upc", "ean", default=None)
                barcode = str(barcode_raw).strip() if barcode_raw is not None else None

                category_raw = get_val(row, "category", "cat", "group", default=None)
                category = str(category_raw).strip() if category_raw is not None else None

                fragile_raw = str(get_val(row, "fragile", "isfragile", default="false")).strip().lower()
                fragile = fragile_raw in ("true", "1", "yes", "y", "t")

                stackable_raw = str(get_val(row, "stackable", "isstackable", default="true")).strip().lower()
                stackable = stackable_raw in ("true", "1", "yes", "y", "t")

                max_stack_w = float(get_val(row, "maxstackweight", "maxstack", "stacklimit", default=9999.0))

                rot_raw = str(get_val(row, "allowedrotations", "rotations", "rotationrules", default="XYZ")).strip().upper()
                if "XYZ" in rot_raw or "ALL" in rot_raw:
                    allowed_rotations = "XYZ"
                elif "XY" in rot_raw:
                    allowed_rotations = "XY"
                else:
                    allowed_rotations = "Z"

                data = {
                    "sku": sku,
                    "name": name,
                    "length": length,
                    "width": width,
                    "height": height,
                    "weight": weight,
                    "barcode": barcode,
                    "fragile": fragile,
                    "stackable": stackable,
                    "max_stack_weight": max_stack_w,
                    "allowed_rotations": allowed_rotations,
                    "category": category
                }

                existing = ProductRepository.get_by_sku(db, sku)
                if existing:
                    ProductRepository.update(db, existing.id, data)
                    updated_count += 1
                else:
                    ProductRepository.create(db, **data)
                    imported_count += 1

            except Exception as ex:
                errors.append(f"Row {idx + 2}: {ex}")

        return {
            "imported": imported_count,
            "updated": updated_count,
            "total": imported_count + updated_count,
            "errors": errors
        }


class CartonRepository:
    @staticmethod
    def create(db: Session, name: str, length: float, width: float, height: float, 
               empty_weight: float = 0.0, max_weight: float = 0.0, cost: float = 0.0) -> Carton:
        carton = Carton(
            name=name, length=length, width=width, height=height,
            empty_weight=empty_weight, max_weight=max_weight, cost=cost
        )
        db.add(carton)
        db.commit()
        db.refresh(carton)
        return carton

    @staticmethod
    def get_by_id(db: Session, carton_id: int) -> Optional[Carton]:
        return db.query(Carton).filter(Carton.id == carton_id).first()

    @staticmethod
    def get_all(db: Session) -> List[Carton]:
        return db.query(Carton).all()

    @staticmethod
    def update(db: Session, carton_id: int, updates: Dict[str, Any]) -> Optional[Carton]:
        carton = db.query(Carton).filter(Carton.id == carton_id).first()
        if carton:
            for key, val in updates.items():
                if hasattr(carton, key):
                    setattr(carton, key, val)
            db.commit()
            db.refresh(carton)
        return carton

    @staticmethod
    def delete(db: Session, carton_id: int) -> bool:
        carton = db.query(Carton).filter(Carton.id == carton_id).first()
        if carton:
            db.delete(carton)
            db.commit()
            return True
        return False


class CourierRepository:
    @staticmethod
    def create(db: Session, name: str, rate_per_kg: float, volumetric_factor: float = 5000.0, 
               minimum_charge: float = 0.0) -> Courier:
        courier = Courier(
            name=name, rate_per_kg=rate_per_kg, volumetric_factor=volumetric_factor,
            minimum_charge=minimum_charge
        )
        db.add(courier)
        db.commit()
        db.refresh(courier)
        return courier

    @staticmethod
    def get_by_id(db: Session, courier_id: int) -> Optional[Courier]:
        return db.query(Courier).filter(Courier.id == courier_id).first()

    @staticmethod
    def get_all(db: Session) -> List[Courier]:
        return db.query(Courier).all()

    @staticmethod
    def update(db: Session, courier_id: int, updates: Dict[str, Any]) -> Optional[Courier]:
        courier = db.query(Courier).filter(Courier.id == courier_id).first()
        if courier:
            for key, val in updates.items():
                if hasattr(courier, key):
                    setattr(courier, key, val)
            db.commit()
            db.refresh(courier)
        return courier

    @staticmethod
    def delete(db: Session, courier_id: int) -> bool:
        courier = db.query(Courier).filter(Courier.id == courier_id).first()
        if courier:
            db.delete(courier)
            db.commit()
            return True
        return False


class JobRepository:
    @staticmethod
    def create(db: Session, selected_products: Dict[int, int], carton_id: int, 
               layout: List[Dict[str, Any]], utilization: float, actual_weight: float, 
               volumetric_weight: float, chargeable_weight: float, shipping_cost: float, 
               report_path: str = None, statistics: Dict[str, Any] = None) -> Job:
        job = Job(
            selected_products=json.dumps(selected_products),
            carton_id=carton_id,
            layout=json.dumps(layout),
            utilization=utilization,
            actual_weight=actual_weight,
            volumetric_weight=volumetric_weight,
            chargeable_weight=chargeable_weight,
            shipping_cost=shipping_cost,
            report_path=report_path,
            statistics=json.dumps(statistics) if statistics else None
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_by_id(db: Session, job_id: int) -> Optional[Job]:
        return db.query(Job).filter(Job.id == job_id).first()

    @staticmethod
    def get_all(db: Session) -> List[Job]:
        return db.query(Job).order_by(Job.date.desc()).all()

    @staticmethod
    def delete(db: Session, job_id: int) -> bool:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            db.delete(job)
            db.commit()
            return True
        return False
