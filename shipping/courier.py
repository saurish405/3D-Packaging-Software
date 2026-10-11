def estimate_shipping_fee(chargeable_weight: float, rate_per_kg: float, minimum_charge: float = 0.0) -> float:
    """
    Estimates the courier shipping cost.
    Fee = max(chargeable_weight * rate_per_kg, minimum_charge)
    """
    raw_cost = chargeable_weight * rate_per_kg
    return max(raw_cost, minimum_charge)
