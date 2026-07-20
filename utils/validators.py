"""Input validation utilities for TRAVAS system."""

from datetime import date, datetime
from typing import Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)


def validate_hotel_preferences(
    budget: float,
    destination: str,
    checkin_date: str,
    checkout_date: str,
    num_travelers: int = 1
) -> Tuple[bool, Optional[str]]:
    """Validate hotel preferences.

    Args:
        budget: Budget per night in INR
        destination: Destination city
        checkin_date: Check-in date (YYYY-MM-DD format)
        checkout_date: Check-out date (YYYY-MM-DD format)
        num_travelers: Number of travelers

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate budget
    if not isinstance(budget, (int, float)) or budget <= 0:
        return False, "Budget must be a positive number"

    if budget < 500:
        return False, "Budget should be at least ₹500 per night"

    if budget > 500000:
        return False, "Budget seems unusually high. Please confirm."

    # Validate destination
    valid_destinations = ["Delhi", "Mumbai", "Goa", "Bangalore", "Kolkata", "Jaipur"]
    if destination not in valid_destinations:
        return False, f"We currently support: {', '.join(valid_destinations)}"

    # Validate dates
    try:
        checkin = datetime.strptime(checkin_date, "%Y-%m-%d").date()
        checkout = datetime.strptime(checkout_date, "%Y-%m-%d").date()
    except ValueError:
        return False, "Dates must be in YYYY-MM-DD format"

    today = date.today()
    if checkin < today:
        return False, "Check-in date cannot be in the past"

    if checkout <= checkin:
        return False, "Check-out date must be after check-in date"

    duration = (checkout - checkin).days
    if duration > 90:
        return False, "We support bookings up to 90 days"

    if duration == 0:
        return False, "Minimum stay is 1 night"

    # Validate travelers
    if not isinstance(num_travelers, int) or num_travelers <= 0:
        return False, "Number of travelers must be a positive integer"

    if num_travelers > 10:
        return False, "We support up to 10 travelers per booking"

    return True, None


def validate_city(city: str) -> Tuple[bool, Optional[str]]:
    """Validate if city is supported."""
    valid_cities = ["Delhi", "Mumbai", "Goa", "Bangalore", "Kolkata", "Jaipur"]
    if city not in valid_cities:
        return False, f"Currently supporting: {', '.join(valid_cities)}"
    return True, None


def validate_price_range(
    min_price: float,
    max_price: float
) -> Tuple[bool, Optional[str]]:
    """Validate price range."""
    if min_price < 0 or max_price < 0:
        return False, "Prices cannot be negative"

    if min_price > max_price:
        return False, "Minimum price cannot exceed maximum price"

    if max_price > 500000:
        return False, "Maximum price seems unusually high"

    return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validate email format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    return True, None


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """Validate phone number format."""
    import re
    # Support Indian phone numbers
    pattern = r'^(?:\+91|0)?[6-9]\d{9}$'
    cleaned = phone.replace(" ", "").replace("-", "")
    if not re.match(pattern, cleaned):
        return False, "Invalid phone number format"
    return True, None


def parse_date(date_str: str) -> Optional[date]:
    """Parse date string to date object.

    Supports multiple formats:
    - YYYY-MM-DD
    - DD/MM/YYYY
    - DD-MM-YYYY
    """
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    return None


def extract_budget_from_text(text: str) -> Optional[float]:
    """Extract budget amount from natural language text.

    Examples:
    - "5000" -> 5000
    - "₹5000" -> 5000
    - "5000 per night" -> 5000
    - "budget is 5000" -> 5000
    """
    import re

    # Remove common words
    text = text.lower()

    # Try to find numbers with rupee symbol or explicit price indicators
    patterns = [
        r'₹[\s]*(\d+(?:,\d{3})*)',  # ₹5000
        r'(?:budget|price|cost)[\s]*(?:is|of)?[\s]*₹?[\s]*(\d+(?:,\d{3})*)',  # budget is 5000
        r'(\d+(?:,\d{3})*)\s*(?:per night|night)',  # 5000 per night
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                amount = int(match.group(1).replace(",", ""))
                if 500 <= amount <= 500000:
                    return float(amount)
            except (ValueError, IndexError):
                continue

    return None


def format_price(price: float) -> str:
    """Format price in Indian currency format."""
    if price >= 100000:
        return f"₹{price/100000:.1f}L"
    elif price >= 1000:
        return f"₹{price/1000:.0f}K"
    else:
        return f"₹{price:.0f}"
