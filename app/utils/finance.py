def calculate_pct_change(start_value: float, end_value: float) -> float:
    if start_value == 0:
        raise ValueError("start_value cannot be zero for percentage change")
    return ((end_value - start_value) / start_value) * 100
