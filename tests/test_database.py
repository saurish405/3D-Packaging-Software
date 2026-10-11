import unittest
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure the root of the project is on the python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from database.database import Base
from database.repository import ProductRepository, CartonRepository, CourierRepository

class TestDatabaseRepository(unittest.TestCase):
    def setUp(self):
        # Create a clean in-memory database for unit testing
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def test_product_crud(self):
        # 1. Create
        p = ProductRepository.create(
            db=self.db,
            sku="TEST_SKU",
            name="Test Product",
            length=100.0,
            width=80.0,
            height=50.0,
            weight=0.50,
            fragile=False,
            stackable=True,
            max_stack_weight=10.0,
            allowed_rotations="XYZ",
            category="Test"
        )
        self.assertIsNotNone(p.id)
        self.assertEqual(p.sku, "TEST_SKU")

        # 2. Read
        retrieved = ProductRepository.get_by_sku(self.db, "TEST_SKU")
        self.assertEqual(retrieved.id, p.id)
        self.assertEqual(retrieved.name, "Test Product")

        # 3. Update
        updated = ProductRepository.update(self.db, p.id, {"name": "Updated Name", "weight": 0.75})
        self.assertEqual(updated.name, "Updated Name")
        self.assertEqual(updated.weight, 0.75)

        # 4. Delete
        success = ProductRepository.delete(self.db, p.id)
        self.assertTrue(success)
        self.assertIsNone(ProductRepository.get_by_id(self.db, p.id))

    def test_carton_crud(self):
        c = CartonRepository.create(
            db=self.db,
            name="Test Carton",
            length=300.0,
            width=200.0,
            height=200.0,
            empty_weight=0.2,
            max_weight=15.0,
            cost=2.0
        )
        self.assertIsNotNone(c.id)
        
        cartons = CartonRepository.get_all(self.db)
        self.assertEqual(len(cartons), 1)
        self.assertEqual(cartons[0].name, "Test Carton")

if __name__ == "__main__":
    unittest.main()
