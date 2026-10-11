from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from database.repository import CartonRepository
from optimizer.python.optimizer import PackageOptimizer
from optimizer.python.weight import calculate_volumetric_weight
from shipping.courier import estimate_shipping_fee

class CartonSelector:
    def __init__(self):
        self.optimizer = PackageOptimizer()

    def recommend_cartons(
        self,
        db: Session,
        products: List[Dict[str, Any]],
        quantities: List[int],
        courier: Dict[str, Any] = None,
        top_clearance: float = 20.0,
        cell_size: float = 10.0
    ) -> List[Dict[str, Any]]:
        """
        Mode B: Evaluate and rank all cartons in the database for the given product mix.
        Returns a list of carton recommendation details, sorted by compatibility.
        """
        cartons = CartonRepository.get_all(db)
        recommendations = []

        total_product_volume = sum(
            float(p["length"]) * float(p["width"]) * float(p["height"]) * qty 
            for p, qty in zip(products, quantities)
        )
        total_product_weight = sum(
            float(p["weight"]) * qty 
            for p, qty in zip(products, quantities)
        )

        for carton in cartons:
            carton_dict = carton.to_dict()
            
            # Fast Pre-filtering
            carton_volume = carton.length * carton.width * carton.height
            if carton_volume < total_product_volume:
                # Volumetrically impossible to fit all
                continue
                
            if carton.max_weight > 0.0 and total_product_weight > carton.max_weight:
                # Exceeds maximum weight capacity of carton
                continue

            # Run solver to check actual fitting capacity
            try:
                result = self.optimizer.optimize(
                    carton=carton_dict,
                    products=products,
                    quantities=quantities,
                    top_clearance=top_clearance,
                    cell_size=cell_size
                )
            except Exception as e:
                # If C++ module is missing or crashes, log and skip
                continue

            packed_count = result["total_packed_items"]
            total_items = sum(quantities)
            fit_ratio = packed_count / total_items if total_items > 0 else 0.0
            
            # Shipping cost estimation
            actual_w = result["statistics"]["total_packed_weight"] + carton.empty_weight
            vol_w = calculate_volumetric_weight(
                carton.length, carton.width, carton.height, 
                courier["volumetric_factor"] if courier else 5000.0
            )
            chargeable_w = max(actual_w, vol_w)
            
            est_shipping = 0.0
            if courier:
                est_shipping = estimate_shipping_fee(
                    chargeable_weight=chargeable_w,
                    rate_per_kg=courier["rate_per_kg"],
                    minimum_charge=courier["minimum_charge"]
                )

            total_cost = carton.cost + est_shipping

            recommendations.append({
                "carton": carton_dict,
                "fit_ratio": fit_ratio,
                "fully_fits": result["success"],
                "utilization": result["statistics"]["space_utilization"],
                "total_packed_items": packed_count,
                "unpacked_count": total_items - packed_count,
                "actual_weight": actual_w,
                "chargeable_weight": chargeable_w,
                "estimated_shipping": est_shipping,
                "total_cost": total_cost,
                "layout_result": result
            })

        # Rank recommendations:
        # 1. Fully fits first (descending)
        # 2. Fit ratio (descending)
        # 3. Space utilization (descending)
        # 4. Total Cost (ascending)
        recommendations.sort(
            key=lambda x: (x["fully_fits"], x["fit_ratio"], x["utilization"], -x["total_cost"]),
            reverse=True
        )

        return recommendations

    def calculate_what_fits(
        self,
        carton: Dict[str, Any],
        product: Dict[str, Any],
        top_clearance: float = 20.0,
        cell_size: float = 10.0
    ) -> Tuple[int, str]:
        """
        Mode C: Calculates the maximum quantity of a SINGLE product type that fits in the carton.
        Returns a tuple of (max_quantity, limiting_factor).
        """
        # Physical dimensional limits checks
        p_len, p_wid, p_hei = product["length"], product["width"], product["height"]
        c_len, c_wid, c_hei = carton["length"], carton["width"], carton["height"]

        # Check if product is too large for the carton in any orientation
        p_dims = sorted([p_len, p_wid, p_hei])
        c_dims = sorted([c_len, c_wid, c_hei - top_clearance])

        if p_dims[0] > c_dims[0] or p_dims[1] > c_dims[1] or p_dims[2] > c_dims[2]:
            return 0, "Dimensions (Product is larger than the carton dimensions)"

        # Binary search for maximum quantity
        low = 1
        high = 1000
        # Fast limit boundary check based on volume and weight
        vol_limit = int((c_len * c_wid * (c_hei - top_clearance)) // (p_len * p_wid * p_hei))
        
        weight_limit = 99999
        if carton["max_weight"] > 0.0 and product["weight"] > 0.0:
            weight_limit = int((carton["max_weight"] - carton["empty_weight"]) // product["weight"])

        high = min(vol_limit, weight_limit)
        if high <= 0:
            high = 1

        best_qty = 0
        limiting_factor = "Optimal fit achieved"

        while low <= high:
            mid = (low + high) // 2
            
            result = self.optimizer.optimize(
                carton=carton,
                products=[product],
                quantities=[mid],
                top_clearance=top_clearance,
                cell_size=cell_size
            )
            
            if result["success"]:
                best_qty = mid
                low = mid + 1
            else:
                high = mid - 1

        # Determine limiting factor
        if best_qty == 0:
            return 0, "Dimensions (Items do not tile mathematically on the grid layout)"

        # Check what stops us from adding 1 more
        next_qty = best_qty + 1
        
        # 1. Weight limit check
        total_weight_next = next_qty * product["weight"]
        if carton["max_weight"] > 0.0 and total_weight_next > (carton["max_weight"] - carton["empty_weight"]):
            limiting_factor = "Carton maximum weight limit"
            return best_qty, limiting_factor

        # 2. Volume check
        total_vol_next = next_qty * (p_len * p_wid * p_hei)
        carton_vol = c_len * c_wid * (c_hei - top_clearance)
        if total_vol_next > carton_vol:
            limiting_factor = "Carton volume limit"
            return best_qty, limiting_factor

        # 3. If volume and weight didn't fail, but solver failed: it is geometry/dimension constraints
        limiting_factor = "Geometric layout constraints (cannot tile more boxes without overlaps)"
        
        return best_qty, limiting_factor
