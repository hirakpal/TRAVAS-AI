"""Input Validation Utilities"""

import re
from typing import Dict, Any, List


def validate_email(email: str) -> bool:
    """
    Validate email address.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_hotel_data(hotel_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate hotel information.

    Args:
        hotel_data: Hotel information dictionary

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Required fields
    required_fields = ['name', 'address', 'city']
    for field in required_fields:
        if field not in hotel_data or not hotel_data[field]:
            errors.append(f"Missing required field: {field}")

    # Validate price range
    if 'price_range_low' in hotel_data and 'price_range_high' in hotel_data:
        if hotel_data['price_range_low'] > hotel_data['price_range_high']:
            errors.append("Price range invalid: low > high")

    # Validate rating
    if 'star_rating' in hotel_data:
        rating = hotel_data['star_rating']
        if rating and (rating < 0 or rating > 5):
            errors.append("Star rating must be between 0 and 5")

    # Verify data is not fabricated
    if hotel_data.get('verified') is False:
        errors.append("Hotel data not verified")

    return len(errors) == 0, errors


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input.

    Args:
        text: Input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Trim whitespace
    text = text.strip()

    # Limit length
    if len(text) > max_length:
        text = text[:max_length]

    return text


def validate_date_range(check_in: str, check_out: str) -> tuple[bool, str]:
    """
    Validate check-in and check-out dates.

    Args:
        check_in: Check-in date (ISO format)
        check_out: Check-out date (ISO format)

    Returns:
        Tuple of (is_valid, error_message)
    """
    from datetime import datetime

    try:
        check_in_dt = datetime.fromisoformat(check_in)
        check_out_dt = datetime.fromisoformat(check_out)

        if check_in_dt >= check_out_dt:
            return False, "Check-in date must be before check-out date"

        if check_in_dt < datetime.now():
            return False, "Check-in date cannot be in the past"

        return True, ""
    except ValueError:
        return False, "Invalid date format"
