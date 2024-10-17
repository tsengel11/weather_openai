import random
def get_current_temperature(**kwargs) -> str:
    location = kwargs.get("location", "Unknown Location")
    unit = kwargs.get("unit", "Celsius")  # Default to Celsius if not provided

    if unit not in ["Celsius", "Fahrenheit"]:
        raise ValueError("Invalid unit. Must be 'Celsius' or 'Fahrenheit'.")

    temperature = random.randint(30, 50)
    return f"{temperature} {unit}"