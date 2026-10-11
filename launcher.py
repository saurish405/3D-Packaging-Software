import os
import sys
import subprocess
import logging

if sys.platform == 'win32':
    for path in ["C:/msys64/ucrt64/bin", "C:/msys64/mingw64/bin"]:
        if os.path.exists(path):
            try:
                os.add_dll_directory(path)
            except Exception:
                pass

# Configure launcher logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Launcher")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

def check_and_compile_cpp():
    """Checks for optimizer_cpp module availability and compiles it if missing."""
    try:
        import optimizer_cpp
        logger.info("C++ optimization module (optimizer_cpp) is compiled and ready.")
        return True
    except ImportError:
        logger.info("optimizer_cpp binary not found. Initiating automated C++ compilation...")
        
        # Check toolchain availability
        setup_path = os.path.join(CURRENT_DIR, "setup.py")
        if not os.path.exists(setup_path):
            logger.error(f"Cannot compile: setup.py not found at {setup_path}.")
            return False

        try:
            # Build extension inplace
            # We run python setup.py build_ext --inplace
            logger.info("Executing build: python setup.py build_ext --inplace")
            result = subprocess.run(
                [sys.executable, "setup.py", "build_ext", "--inplace"],
                cwd=CURRENT_DIR,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("C++ compilation completed successfully!")
                return True
            else:
                logger.error(f"C++ compilation failed with exit code: {result.returncode}")
                logger.error(f"Compilation Stdout:\n{result.stdout}")
                logger.error(f"Compilation Stderr:\n{result.stderr}")
                return False
        except Exception as ex:
            logger.error(f"Exception triggered during compilation run: {ex}")
            return False

def seed_database_defaults():
    """Initializes schema and inserts product/carton/courier catalog presets."""
    from database.database import init_db, SessionLocal
    from database.models import Product, Carton, Courier

    init_db()
    db = SessionLocal()

    try:
        # 1. Seed Cartons
        existing_carton_names = {c.name for c in db.query(Carton.name).all()}
        cartons_to_add = []
        default_cartons = [
            Carton(name="Small Box (S)", length=300.0, width=200.0, height=150.0, empty_weight=0.15, max_weight=10.0, cost=1.00),
            Carton(name="Medium Box (M)", length=400.0, width=300.0, height=250.0, empty_weight=0.30, max_weight=20.0, cost=1.80),
            Carton(name="Large Box (L)", length=600.0, width=400.0, height=400.0, empty_weight=0.50, max_weight=30.0, cost=2.80),
            Carton(name="Extra Large Box (XL)", length=800.0, width=600.0, height=500.0, empty_weight=0.80, max_weight=45.0, cost=4.50),
            Carton(name="Jumbo Cargo Box (XXL)", length=1300.0, width=800.0, height=850.0, empty_weight=1.50, max_weight=80.0, cost=8.50)
        ]
        for c in default_cartons:
            if c.name not in existing_carton_names:
                cartons_to_add.append(c)
        if cartons_to_add:
            logger.info(f"Seeding {len(cartons_to_add)} missing Carton sizes...")
            db.add_all(cartons_to_add)
            db.commit()

        # 2. Seed Products
        existing_product_skus = {p.sku for p in db.query(Product.sku).all()}
        products_to_add = []
        default_products = [
            Product(sku="USB_A", name="USB Flash Drive 32GB", length=80.0, width=20.0, height=10.0, weight=0.05, fragile=False, stackable=True, max_stack_weight=100.0, allowed_rotations="XYZ", category="Electronics"),
            Product(sku="KEY_K", name="Mechanical Keyboard RGB", length=450.0, width=140.0, height=40.0, weight=1.20, fragile=False, stackable=True, max_stack_weight=80.0, allowed_rotations="XY", category="Electronics"),
            Product(sku="MOU_M", name="Wireless Optical Mouse", length=110.0, width=60.0, height=40.0, weight=0.15, fragile=False, stackable=True, max_stack_weight=50.0, allowed_rotations="XYZ", category="Electronics"),
            Product(sku="MON_LED", name="24-inch LED Monitor Screen", length=560.0, width=380.0, height=80.0, weight=4.50, fragile=True, stackable=False, max_stack_weight=0.0, allowed_rotations="Z", category="Electronics"),
            Product(sku="TV_55", name="Smart LED TV 55 inch", length=1230.0, width=150.0, height=750.0, weight=14.0, fragile=True, stackable=False, max_stack_weight=0.0, allowed_rotations="Z", category="Electronics")
        ]
        for p in default_products:
            if p.sku not in existing_product_skus:
                products_to_add.append(p)
        if products_to_add:
            logger.info(f"Seeding {len(products_to_add)} missing Product catalogs...")
            db.add_all(products_to_add)
            db.commit()

        # 3. Seed Couriers
        if db.query(Courier).count() == 0:
            logger.info("Seeding default Courier shipping profiles...")
            couriers = [
                Courier(name="DHL Ground Saver", volumetric_factor=5000.0, rate_per_kg=1.80, minimum_charge=8.00),
                Courier(name="FedEx Express Cargo", volumetric_factor=4000.0, rate_per_kg=2.80, minimum_charge=12.00)
            ]
            db.add_all(couriers)
            db.commit()

    except Exception as ex:
        logger.error(f"Error seeding database defaults: {ex}")
        db.rollback()
    finally:
        db.close()

def main():
    logger.info("Initializing Packaging Optimizer application loader...")
    
    # 1. C++ Build
    check_and_compile_cpp()

    # 2. Schema check
    seed_database_defaults()

    # 3. Launch UI Window
    logger.info("Launching PySide6 Graphic Interface...")
    
    from PySide6.QtWidgets import QApplication
    from app.main import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
