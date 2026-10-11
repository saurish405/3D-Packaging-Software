def calculate_volumetric_weight(length: float, width: float, height: float, factor: float = 5000.0) -> float:
    """
    Calculates the volumetric (dimensional) weight of a container.
    Formula: Volumetric Weight (kg) = (Length (mm) * Width (mm) * Height (mm)) / (factor * 1000)
    Note: Length, Width, Height are in millimeters. Divisor 'factor' is typically 5000, 4000, etc.
    """
    if factor <= 0.0:
        factor = 5000.0
    # Length * Width * Height in cubic cm = (mm / 10) * (mm / 10) * (mm / 10) = mm^3 / 1000
    # Volumetric Weight = (L_cm * W_cm * H_cm) / factor = (L_mm * W_mm * H_mm) / (factor * 1000)
    volume_cc = (length * width * height) / 1000.0
    return volume_cc / factor
