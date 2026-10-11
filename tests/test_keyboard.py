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

def main():
    print("Running keyboard diagnostic packing test...")
    # Define keyboard product matching database seeder exactly
    p = optimizer_cpp.Product()
    p.id = 1
    p.sku = "KEY_K"
    p.name = "Mechanical Keyboard RGB"
    p.length = 450.0
    p.width = 140.0
    p.height = 40.0
    p.weight = 1.20
    p.fragile = False
    p.stackable = True
    p.max_stack_weight = 80.0
    p.allowed_rotations = "XY"

    products = [p]
    quantities = [1]

    # Large Box: 600x400x400
    layers = optimizer_cpp.run_optimization(
        carton_w=600.0,
        carton_l=400.0,
        carton_h=400.0,
        products=products,
        quantities=quantities,
        top_clearance=20.0,
        cell_size=10.0,
        height_tolerance=5.0,
        required_support_ratio=0.70,
        max_steps=20000
    )

    print(f"Number of layers packed: {len(layers)}")
    if len(layers) > 0:
        for idx, layer in enumerate(layers):
            print(f"Layer {idx+1}: Z Start = {layer.z_start}, Height = {layer.height}")
            print(f"  Placements: {len(layer.placements)}")
            for pl in layer.placements:
                print(f"    - SKU: {pl.sku}, X: {pl.x}, Y: {pl.y}, Z: {pl.z}, L: {pl.length}, W: {pl.width}, H: {pl.height}")
    else:
        print("No layers were packed! Keyboard failed to pack completely.")

if __name__ == "__main__":
    main()
