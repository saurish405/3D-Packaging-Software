import sys
import os
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PythonOptimizer")

# Ensure the root of the project is in python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

class PackageOptimizer:
    def __init__(self):
        self.cpp_engine = None
        self._load_cpp_engine()

    def _load_cpp_engine(self):
        """Attempts to load the compiled C++ pybind11 module."""
        try:
            import optimizer_cpp
            self.cpp_engine = optimizer_cpp
            logger.info("Successfully loaded C++ packaging optimizer module.")
        except ImportError as e:
            logger.warning(f"Could not load C++ optimizer module: {e}. Compilation will be needed.")

    def is_engine_available(self) -> bool:
        """Returns True if the C++ binary is compiled and loaded, False otherwise."""
        if self.cpp_engine is None:
            self._load_cpp_engine()
        return self.cpp_engine is not None

    def optimize(
        self,
        carton: dict,  # {"length": float, "width": float, "height": float, "id": int}
        products: list,  # List of dicts matching database Product format
        quantities: list,  # Quantities matching products list order
        top_clearance: float = 20.0,
        cell_size: float = 10.0,
        height_tolerance: float = 5.0,
        required_support: float = 0.70,
        max_steps: int = 20000
    ) -> dict:
        """
        Executes optimization using C++ engine.
        Returns a dictionary with result status, layers layout, unpacked items, and scoring statistics.
        """
        if not self.is_engine_available():
            raise RuntimeError("C++ Optimization Engine is not compiled. Please compile using setup.py.")

        # Create C++ product objects
        cpp_products = []
        for p in products:
            cpp_p = self.cpp_engine.Product()
            cpp_p.id = p["id"]
            cpp_p.sku = p["sku"]
            cpp_p.name = p["name"]
            cpp_p.length = float(p["length"])
            cpp_p.width = float(p["width"])
            cpp_p.height = float(p["height"])
            cpp_p.weight = float(p["weight"])
            cpp_p.fragile = bool(p["fragile"])
            cpp_p.stackable = bool(p["stackable"])
            cpp_p.max_stack_weight = float(p["max_stack_weight"])
            cpp_p.allowed_rotations = str(p["allowed_rotations"])
            cpp_products.append(cpp_p)

        # Run C++ optimization
        layers = self.cpp_engine.run_optimization(
            carton_w=float(carton["length"]),
            carton_l=float(carton["width"]),
            carton_h=float(carton["height"]),
            products=cpp_products,
            quantities=quantities,
            top_clearance=float(top_clearance),
            cell_size=float(cell_size),
            height_tolerance=float(height_tolerance),
            required_support_ratio=float(required_support),
            max_steps=int(max_steps)
        )

        # Build list of packed placements
        all_placements = []
        layers_data = []
        
        for k, layer in enumerate(layers):
            layer_placements = []
            for pl in layer.placements:
                pl_dict = {
                    "id": pl.id,
                    "sku": pl.sku,
                    "name": pl.name,
                    "x": pl.x,
                    "y": pl.y,
                    "z": pl.z,
                    "length": pl.length,
                    "width": pl.width,
                    "height": pl.height,
                    "weight": pl.weight,
                    "gx": pl.gx,
                    "gy": pl.gy,
                    "gw": pl.gw,
                    "gl": pl.gl
                }
                layer_placements.append(pl_dict)
                all_placements.append(pl_dict)
                
            layers_data.append({
                "layer_idx": k,
                "z_start": layer.z_start,
                "height": layer.height,
                "grid": layer.grid,  # 2D list representation
                "placements": layer_placements
            })

        # Calculate Center of Gravity metrics using C++
        # Gather all C++ Placements first.
        cpp_all_placements = []
        for layer in layers:
            for pl in layer.placements:
                cpp_all_placements.append(pl)

        cog_ok, cog_x, cog_y, cog_z, total_packed_weight = self.cpp_engine.calculate_cog(cpp_all_placements)
        cog_score = self.cpp_engine.get_cog_score(cog_x, cog_y, float(carton["length"]), float(carton["width"])) if cog_ok else 100.0

        # Calculate stack compression pressures using C++
        grid_width = int(carton["length"] // cell_size)
        grid_height = int(carton["width"] // cell_size)
        stack_weights = self.cpp_engine.calculate_stack_weights(layers, grid_width, grid_height)

        # Check stack limits and fragile items overload
        stack_limits_violated = False
        limit_violations = []
        
        # Build mapping of sku to product definitions for constraint lookups
        prod_map = {p["sku"]: p for p in products}
        
        for pl_dict in all_placements:
            pl_id = pl_dict["id"]
            sku = pl_dict["sku"]
            w_stacked = stack_weights.get(pl_id, 0.0)
            pl_dict["stacked_weight"] = w_stacked
            
            p_def = prod_map.get(sku)
            if p_def:
                if p_def["fragile"] and w_stacked > 0.0:
                    stack_limits_violated = True
                    limit_violations.append(f"Fragile item '{p_def['name']}' ({sku}) has stacked weight: {w_stacked:.2f} kg.")
                elif not p_def["stackable"] and w_stacked > 0.0:
                    stack_limits_violated = True
                    limit_violations.append(f"Non-stackable item '{p_def['name']}' ({sku}) has stacked weight: {w_stacked:.2f} kg.")
                elif w_stacked > p_def["max_stack_weight"]:
                    stack_limits_violated = True
                    limit_violations.append(f"Item '{p_def['name']}' ({sku}) exceeds max stack weight: {w_stacked:.2f} / {p_def['max_stack_weight']:.2f} kg.")

        # Compute packed volumes
        carton_volume = float(carton["length"]) * float(carton["width"]) * float(carton["height"])
        packed_volume = 0.0
        for pl in all_placements:
            packed_volume += pl["length"] * pl["width"] * pl["height"]

        space_utilization = (packed_volume / carton_volume) * 100.0 if carton_volume > 0 else 0.0

        # Determine unpacked quantities
        packed_counts = {}
        for pl in all_placements:
            packed_counts[pl["sku"]] = packed_counts.get(pl["sku"], 0) + 1

        unpacked = []
        for p, qty in zip(products, quantities):
            p_packed = packed_counts.get(p["sku"], 0)
            p_unpacked = qty - p_packed
            if p_unpacked > 0:
                unpacked.append({
                    "product": p,
                    "quantity": p_unpacked
                })

        # Calculate stability score: ratio of supported boxes
        supported_count = 0
        total_boxes = len(all_placements)
        
        # Calculate support ratios for each placement
        for pl_dict in all_placements:
            # Floor layer is 100% supported
            if pl_dict["z"] == 0.0:
                pl_dict["support_ratio"] = 1.0
                supported_count += 1
            else:
                # Find the layer below
                lower_layer_idx = -1
                for idx, layer_data in enumerate(layers_data):
                    # Find layer whose top boundary corresponds to this placement's bottom
                    if abs((layer_data["z_start"] + layer_data["height"]) - pl_dict["z"]) < 2.0:
                        lower_layer_idx = idx
                        break
                
                if lower_layer_idx != -1:
                    lower_grid = layers_data[lower_layer_idx]["grid"]
                    ratio = self.cpp_engine.calculate_support_ratio(
                        lower_grid, pl_dict["gx"], pl_dict["gy"], pl_dict["gw"], pl_dict["gl"]
                    )
                    pl_dict["support_ratio"] = ratio
                    if ratio >= required_support:
                        supported_count += 1
                else:
                    pl_dict["support_ratio"] = 0.0

        stability_score = (supported_count / total_boxes) * 100.0 if total_boxes > 0 else 100.0

        # Packing efficiency score (weighted average of utilization, balance, and stability)
        packing_efficiency = 0.5 * space_utilization + 0.2 * cog_score + 0.3 * stability_score

        # Estimated packing time (approx. 10s per item, slightly slower for higher layers)
        packing_time_sec = 0.0
        for pl in all_placements:
            base_time = 8.0  # seconds
            height_penalty = (pl["z"] / 100.0) * 0.8  # adds 0.8s for every 10cm higher
            packing_time_sec += base_time + height_penalty

        return {
            "success": len(unpacked) == 0,
            "layers": layers_data,
            "unpacked": unpacked,
            "total_packed_items": total_boxes,
            "statistics": {
                "space_utilization": space_utilization,
                "total_packed_weight": total_packed_weight,
                "center_of_gravity": {
                    "x": cog_x,
                    "y": cog_y,
                    "z": cog_z,
                    "score": cog_score
                },
                "stability_score": stability_score,
                "packing_efficiency_score": packing_efficiency,
                "packing_time_estimate_sec": packing_time_sec,
                "stack_limits_violated": stack_limits_violated,
                "limit_violations": limit_violations
            }
        }
