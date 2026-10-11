import unittest
import sys
import os

# Ensure the root of the project is on the python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

if sys.platform == 'win32':
    for path in ["C:/msys64/ucrt64/bin", "C:/msys64/mingw64/bin"]:
        if os.path.exists(path):
            try:
                os.add_dll_directory(path)
            except Exception:
                pass

import optimizer_cpp

class TestSolverBindings(unittest.TestCase):
    def test_cpp_product_creation(self):
        p = optimizer_cpp.Product()
        p.id = 99
        p.sku = "TEST_ITEM"
        p.name = "Test Item"
        p.length = 100.0
        p.width = 80.0
        p.height = 50.0
        p.weight = 1.50
        p.fragile = False
        p.stackable = True
        p.max_stack_weight = 20.0
        p.allowed_rotations = "XYZ"

        self.assertEqual(p.id, 99)
        self.assertEqual(p.sku, "TEST_ITEM")
        self.assertEqual(p.length, 100.0)

    def test_solve_simple_packing(self):
        # 1. Prepare products
        p = optimizer_cpp.Product()
        p.id = 1
        p.sku = "BOX_S"
        p.name = "Small Box"
        p.length = 100.0
        p.width = 100.0
        p.height = 50.0
        p.weight = 0.50
        p.fragile = False
        p.stackable = True
        p.max_stack_weight = 100.0
        p.allowed_rotations = "Z" # Keep vertical Z

        products = [p]
        quantities = [4] # 4 of them

        # 2. Run solver on a 200 x 200 x 100 carton
        # 4 boxes of size 100x100x50 fit exactly in a 200x200 footprint on layer 1 (total height 50)
        layers = optimizer_cpp.run_optimization(
            carton_w=200.0,
            carton_l=200.0,
            carton_h=100.0,
            products=products,
            quantities=quantities,
            top_clearance=0.0,  # no top clearance for unit test
            cell_size=10.0,     # 10mm grid cell resolution
            height_tolerance=5.0,
            required_support_ratio=0.0, # no support check for layer 0
            max_steps=5000
        )

        self.assertEqual(len(layers), 1) # Should pack in 1 layer of height 50
        layer = layers[0]
        self.assertEqual(layer.height, 50.0)
        self.assertEqual(len(layer.placements), 4) # All 4 should fit

        # Check coordinates of placements (they should tile the 200x200 floor)
        coords = [(pl.x, pl.y) for pl in layer.placements]
        self.assertTrue((0.0, 0.0) in coords)
        self.assertTrue((100.0, 0.0) in coords)
        self.assertTrue((0.0, 100.0) in coords)
        self.assertTrue((100.0, 100.0) in coords)

if __name__ == "__main__":
    unittest.main()
