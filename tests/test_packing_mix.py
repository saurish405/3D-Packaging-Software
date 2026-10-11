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

from optimizer.python.optimizer import PackageOptimizer

def main():
    print("Running packing mix diagnostic...")
    carton = {
        "id": 1,
        "name": "Large Box (L)",
        "length": 600.0,
        "width": 400.0,
        "height": 250.0,
        "max_weight": 30.0,
        "empty_weight": 0.5,
        "cost": 3.0
    }
    
    products = [
        {
            "id": 1,
            "sku": "USB_A",
            "name": "USB Flash Drive 32GB",
            "length": 80.0,
            "width": 20.0,
            "height": 10.0,
            "weight": 0.02,
            "fragile": False,
            "stackable": True,
            "max_stack_weight": 10.0,
            "allowed_rotations": "XYZ"
        },
        {
            "id": 2,
            "sku": "KEY_K",
            "name": "Mechanical Keyboard RGB",
            "length": 450.0,
            "width": 140.0,
            "height": 40.0,
            "weight": 1.20,
            "fragile": False,
            "stackable": True,
            "max_stack_weight": 80.0,
            "allowed_rotations": "XY"
        },
        {
            "id": 3,
            "sku": "MOU_M",
            "name": "Wireless Optical Mouse",
            "length": 110.0,
            "width": 60.0,
            "height": 40.0,
            "weight": 0.15,
            "fragile": False,
            "stackable": True,
            "max_stack_weight": 20.0,
            "allowed_rotations": "XYZ"
        }
    ]
    
    quantities = [20, 5, 20] # USB, Keyboard, Mouse

    optimizer = PackageOptimizer()
    result = optimizer.optimize(
        carton=carton,
        products=products,
        quantities=quantities,
        top_clearance=20.0,
        cell_size=10.0,
        height_tolerance=5.0,
        required_support=0.70,
        max_steps=20000
    )

    print(f"Success: {result['success']}")
    print(f"Total packed: {result['total_packed_items']}")
    print(f"Unpacked items details: {result['unpacked']}")
    
    for idx, layer in enumerate(result['layers']):
        print(f"\nLayer {idx+1}: Z Start = {layer['z_start']}, Height = {layer['height']}")
        # Group counts by SKU
        counts = {}
        for pl in layer['placements']:
            counts[pl['sku']] = counts.get(pl['sku'], 0) + 1
        print(f"  Packed SKUs: {counts}")

if __name__ == "__main__":
    main()
