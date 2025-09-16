from typing import Literal


def add(a: float, b: float = 5.0) -> float:
    """Add a + b."""
    return a + b


def format_bytes(size: int) -> str:
    """Format bytes into either: bytes, kilobytes, megabytes, gigabytes, or terabytes."""
    power = 1024
    n = 0

    labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    
    return f"{size:.2f}{labels[n]}b"


def convert(number: float, current_format: Literal['bytes', 'kb', 'mb', 'gb', 'tb'], desired_format: Literal['bytes', 'kb', 'mb', 'gb', 'tb']) -> float:
    """Converts a given number between storage units: 'bytes', 'kb', 'mb', 'gb', or 'tb'."""
    # Normalize input to bytes first
    units = {'bytes': 0, 'kb': 1, 'mb': 2, 'gb': 3, 'tb': 4}
    if current_format not in units or desired_format not in units:
        raise ValueError("Invalid format. Use 'bytes', 'kb', 'mb', 'gb', or 'tb'.")
    
    # Convert input to bytes
    bytes_value = number * (1024 ** units[current_format])
    
    # Convert from bytes to desired format
    result = bytes_value / (1024 ** units[desired_format])
    return float(result)
