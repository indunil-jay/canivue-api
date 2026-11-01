def maintenance_calories(weight_kg: float) -> int:
    """Resting energy requirement (70 x kg^0.75) times 1.6 for a typical neutered adult."""
    return round(70 * weight_kg**0.75 * 1.6) if weight_kg > 0 else 0
