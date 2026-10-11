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

from optimizer.python.carton_selector import CartonSelector

def main():
    print("Running what fits diagnostic search...")
    carton = {
        "id": 1,
        "name": "Large Box (L)",
        "length": 600.0,
        "width": 400.0,
        "height": 250.0,
        "max_weight": 20.0,
        "empty_weight": 0.5,
        "cost": 3.0
    }
    product = {
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
    }

    selector = CartonSelector()
    
    # Trace the optimize call step by step for quantities
    for qty in [1, 2, 3, 4]:
        print(f"\n--- Testing optimization for qty = {qty} ---")
        result = selector.optimizer.optimize(
            carton=carton,
            products=[product],
            quantities=[qty],
            top_clearance=20.0,
            cell_size=10.0,
            height_tolerance=5.0,
            required_support=0.70,
            max_steps=20000
        )
        print(f"Success: {result['success']}")
        print(f"Total packed: {result['total_packed_items']}")
        print(f"Unpacked list: {result['unpacked']}")
        if len(result['layers']) > 0:
            for i, l in enumerate(result['layers']):
                print(f"  Layer {i+1}: placements={len(l['placements'])}")
        else:
            print("  No layers generated.")

if __name__ == "__main__":
    main()
