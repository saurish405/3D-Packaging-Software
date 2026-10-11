import unittest
import sys
import os

# Ensure the root of the project is on the python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from shipping.volumetric import calculate_volumetric_weight
from shipping.courier import estimate_shipping_fee

class TestShippingCalculations(unittest.TestCase):
    def test_volumetric_weight(self):
        # L=300 mm, W=200 mm, H=150 mm, divisor=5000
        # L_cm = 30, W_cm = 20, H_cm = 15
        # Volume = 30 * 20 * 15 = 9000 cc
        # Volumetric weight = 9000 / 5000 = 1.80 kg
        weight = calculate_volumetric_weight(300.0, 200.0, 150.0, 5000.0)
        self.assertAlmostEqual(weight, 1.80, places=2)

        # Divisor = 4000
        weight_4000 = calculate_volumetric_weight(300.0, 200.0, 150.0, 4000.0)
        self.assertAlmostEqual(weight_4000, 2.25, places=2)

    def test_courier_fee_estimation(self):
        # 2 kg at $2.50/kg, min charge $10.00 -> should be $10.00
        fee = estimate_shipping_fee(2.0, 2.50, 10.00)
        self.assertEqual(fee, 10.00)

        # 8 kg at $2.00/kg, min charge $5.00 -> should be $16.00
        fee_large = estimate_shipping_fee(8.0, 2.00, 5.00)
        self.assertEqual(fee_large, 16.00)

if __name__ == "__main__":
    unittest.main()
