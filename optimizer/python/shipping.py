from shipping.courier import estimate_shipping_fee

def calculate_shipping_cost(chargeable_weight: float, rate_per_kg: float, minimum_charge: float = 0.0) -> float:
    return estimate_shipping_fee(chargeable_weight, rate_per_kg, minimum_charge)
