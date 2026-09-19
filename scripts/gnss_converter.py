"""
GNSS Coordinate Converter

Converts GNSS coordinates from DMS (Degrees, Minutes, Seconds) or 
DDMS (Degrees, Decimal Minutes) format to DD (Decimal Degrees) format.

Supported input formats:
- DMS: "40 26 46" or "40° 26' 46\"" with direction (N/S/E/W)
- DDMS: "40 26.767" or "40° 26.767'" with direction (N/S/E/W)
- Numeric with direction: 40, 26, 46, 'N'
"""

import re
from typing import Union, Tuple


def dms_to_dd(degrees: float, minutes: float, seconds: float = 0, direction: str = 'N') -> float:
    """
    Convert DMS (Degrees, Minutes, Seconds) to DD (Decimal Degrees).
    
    Args:
        degrees: Degrees component (0-360)
        minutes: Minutes component (0-60)
        seconds: Seconds component (0-60), optional
        direction: Cardinal direction ('N', 'S', 'E', 'W')
    
    Returns:
        Decimal degrees as float
    
    Examples:
        >>> dms_to_dd(40, 26, 46, 'N')
        40.446111111111114
        >>> dms_to_dd(73, 58, 26.5, 'W')
        -73.97402777777778
    """
    dd = degrees + minutes / 60 + seconds / 3600
    
    # Apply direction (negative for S and W)
    if direction.upper() in ('S', 'W'):
        dd = -dd
    
    return dd


def ddms_to_dd(degrees: float, decimal_minutes: float, direction: str = 'N') -> float:
    """
    Convert DDMS (Degrees, Decimal Minutes) to DD (Decimal Degrees).
    
    Args:
        degrees: Degrees component (0-360)
        decimal_minutes: Decimal minutes component (0-60)
        direction: Cardinal direction ('N', 'S', 'E', 'W')
    
    Returns:
        Decimal degrees as float
    
    Examples:
        >>> ddms_to_dd(40, 26.767, 'N')
        40.446116666666665
        >>> ddms_to_dd(73, 58.4408, 'W')
        -73.97400666666667
    """
    dd = degrees + decimal_minutes / 60
    
    # Apply direction (negative for S and W)
    if direction.upper() in ('S', 'W'):
        dd = -dd
    
    return dd


def parse_coordinate_string(coord_string: str) -> Tuple[float, float, float, str]:
    """
    Parse a coordinate string in various DMS/DDMS formats.
    
    Supports formats like:
    - "40 26 46 N"
    - "40° 26' 46\" N"
    - "40 26.767 N"
    - "40° 26.767' N"
    
    Args:
        coord_string: Coordinate string to parse
    
    Returns:
        Tuple of (degrees, minutes, seconds, direction)
    
    Raises:
        ValueError: If the string cannot be parsed
    """
    # Remove common symbols and clean up
    cleaned = re.sub(r'[°′″\'"°]', ' ', coord_string.strip())
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
    
    # Split by spaces
    parts = cleaned.split()
    
    if len(parts) < 2:
        raise ValueError(f"Invalid coordinate format: {coord_string}")
    
    try:
        degrees = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2]) if len(parts) >= 3 and parts[2] not in ('N', 'S', 'E', 'W') else 0
        
        # Extract direction (last part if it's a letter)
        direction = 'N'
        for part in parts:
            if part.upper() in ('N', 'S', 'E', 'W'):
                direction = part.upper()
                break
        
        return degrees, minutes, seconds, direction
    
    except ValueError as e:
        raise ValueError(f"Could not parse coordinate string: {coord_string}") from e


def convert_coordinate(coord_input: Union[str, Tuple]) -> float:
    """
    Convert a coordinate from DMS/DDMS format to DD format.
    
    Args:
        coord_input: Either a coordinate string or tuple of (degrees, minutes, [seconds], direction)
    
    Returns:
        Decimal degrees as float
    
    Examples:
        >>> convert_coordinate("40 26 46 N")
        40.446111111111114
        >>> convert_coordinate((40, 26, 46, 'N'))
        40.446111111111114
        >>> convert_coordinate("40 26.767 N")
        40.446116666666665
    """
    if isinstance(coord_input, str):
        degrees, minutes, seconds, direction = parse_coordinate_string(coord_input)
    else:
        # Assume tuple format
        if len(coord_input) == 3:
            degrees, minutes, direction = coord_input
            seconds = 0
        elif len(coord_input) == 4:
            degrees, minutes, seconds, direction = coord_input
        else:
            raise ValueError(f"Invalid tuple format: {coord_input}")
    
    # Determine if it's DMS or DDMS based on whether minutes is a whole number
    # Actually, we should check if seconds is 0 and minutes has decimals = DDMS, otherwise DMS
    if seconds == 0 and '.' in str(coord_input[1]) if isinstance(coord_input, tuple) else minutes % 1 != 0:
        return ddms_to_dd(degrees, minutes, direction)
    else:
        return dms_to_dd(degrees, minutes, seconds, direction)


def format_output(dd_value: float, precision: int = 6) -> str:
    """
    Format decimal degrees for display.
    
    Args:
        dd_value: Decimal degrees value
        precision: Number of decimal places to display
    
    Returns:
        Formatted string representation
    """
    return f"{dd_value:.{precision}f}°"


# Example usage and tests
if __name__ == "__main__":
    # print("=" * 60)
    # print("GNSS Coordinate Converter - DMS/DDMS to DD")
    # print("=" * 60)
    
    # # Example 1: DMS format
    # print("\n[Example 1] DMS Format: 40° 26' 46\" N")
    # result1 = convert_coordinate("40 26 46 N")
    # print(f"Result: {format_output(result1)}")
    
    # # Example 2: DDMS format
    # print("\n[Example 2] DDMS Format: 40° 26.767' N")
    # result2 = convert_coordinate("40 26.767 N")
    # print(f"Result: {format_output(result2)}")
    
    # # Example 3: DMS with tuple input
    # print("\n[Example 3] DMS Tuple: (73, 58, 26.5, 'W')")
    # result3 = dms_to_dd(73, 58, 26.5, 'W')
    # print(f"Result: {format_output(result3)}")
    
    # # Example 4: String with symbols
    # print("\n[Example 4] String with symbols: 40° 26' 46\" N")
    # result4 = convert_coordinate("40° 26' 46\" N")
    # print(f"Result: {format_output(result4)}")
    
    # # Example 5: South latitude
    # print("\n[Example 5] South Latitude: 33 52 48 S")
    # result5 = convert_coordinate("33 52 48 S")
    # print(f"Result: {format_output(result5)}")
    
    # # Example 6: East longitude
    # print("\n[Example 6] East Longitude: 151 12 30.5 E")
    # result6 = convert_coordinate("151 12 30.5 E")
    # print(f"Result: {format_output(result6)}")
    
    # print("\n" + "=" * 60)

    lat = "38 59.38332 N"
    lon = "110 7.85832 W"

    print(f"Latitude: {format_output(convert_coordinate(lat))}")
    print(f"Longitude: {format_output(convert_coordinate(lon))}")
