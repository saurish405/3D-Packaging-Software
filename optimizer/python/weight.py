from shipping.volumetric import calculate_volumetric_weight

def get_package_volumetric_weight(length: float, width: float, height: float, factor: float = 5000.0) -> float:
    return calculate_volumetric_weight(length, width, height, factor)
