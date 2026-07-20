"""Live flight data for Safar - closes the flights gap Google Places can't cover.

Two real sources, tried in order:
  1. SearchApi.io Google Flights (SEARCHAPI_KEY) - PRIMARY. Real priced
     itineraries between two airports on a date (airlines, times, duration,
     stops, price). Best for trip planning.
     GET https://www.searchapi.io/api/v1/search?engine=google_flights
         &departure_id=BLR&arrival_id=SIN&outbound_date=YYYY-MM-DD
         &flight_type=one_way&api_key=...
  2. Aviationstack (AVIATIONSTACK_API_KEY) - FALLBACK. Which airlines/flights
     operate the route + scheduled times (NO prices). Used when SearchApi has no
     key / fails / returns nothing, so Safar can still say something verified.
     GET https://api.aviationstack.com/v1/flights?access_key=...&dep_iata=BLR&arr_iata=SIN

Both need IATA airport codes, but the app carries city names, so we resolve via
a small built-in map (extend CITY_IATA as needed). Everything degrades
gracefully: if neither source can answer, we return success=False with a plain
reason so Safar reports honestly instead of inventing flights.

Docs:
  https://www.searchapi.io/docs/google-flights-api
  https://aviationstack.com/documentation
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

_SEARCHAPI_URL = "https://www.searchapi.io/api/v1/search"
# NOTE: aviationstack's FREE plan only allows http (not https). If you're on the
# free tier and https 403s, change this to "http".
_AVIATIONSTACK_URL = "https://api.aviationstack.com/v1/flights"

# City -> primary IATA airport code. Extend as needed; unknown cities fall back
# to trying the raw name on SearchApi (which can sometimes resolve it) and are
# skipped for Aviationstack (which strictly needs IATA).
CITY_IATA = {
    "bangalore": "BLR", "bengaluru": "BLR", "mumbai": "BOM", "delhi": "DEL",
    "new delhi": "DEL", "goa": "GOI", "chennai": "MAA", "kolkata": "CCU",
    "hyderabad": "HYD", "pune": "PNQ", "ahmedabad": "AMD", "kochi": "COK",
    "cochin": "COK", "jaipur": "JAI", "lucknow": "LKO", "guwahati": "GAU",
    "singapore": "SIN", "dubai": "DXB", "abu dhabi": "AUH", "doha": "DOH",
    "bangkok": "BKK", "phuket": "HKT", "kuala lumpur": "KUL", "bali": "DPS",
    "denpasar": "DPS", "male": "MLE", "maldives": "MLE", "colombo": "CMB",
    "kathmandu": "KTM", "london": "LHR", "paris": "CDG", "new york": "JFK",
    "tokyo": "NRT", "hong kong": "HKG", "sydney": "SYD", "istanbul": "IST",
}


def searchapi_key() -> Optional[str]:
    return os.getenv("SEARCHAPI_KEY") or os.getenv("SEARCH_API_KEY")


def aviationstack_key() -> Optional[str]:
    return os.getenv("AVIATIONSTACK_API_KEY")


def city_to_iata(city: str) -> Optional[str]:
    """Resolve a city name (or an already-IATA 3-letter code) to an IATA code."""
    if not city:
        return None
    c = city.strip().lower()
    if len(c) == 3 and c.isalpha():
        return c.upper()  # already looks like an IATA code
    return CITY_IATA.get(c)


def _default_date() -> str:
    """A near-future placeholder date when none is supplied (indicative only)."""
    return (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")


def _search_searchapi(dep_iata: str, arr_iata: str, outbound_date: str) -> Dict[str, Any]:
    key = searchapi_key()
    if not key:
        return {"ok": False, "reason": "SEARCHAPI_KEY not set", "results": []}
    params = {
        "engine": "google_flights",
        "departure_id": dep_iata,
        "arrival_id": arr_iata,
        "outbound_date": outbound_date,
        "flight_type": "one_way",
        "api_key": key,
    }
    try:
        resp = requests.get(_SEARCHAPI_URL, params=params, timeout=20)
    except requests.RequestException as e:
        return {"ok": False, "reason": f"network error: {e}", "results": []}
    if resp.status_code != 200:
        return {"ok": False, "reason": f"SearchApi returned {resp.status_code}: {resp.text[:200]}", "results": []}
    try:
        data = resp.json()
    except Exception as e:
        return {"ok": False, "reason": f"parse error: {e}", "results": []}

    itineraries = (data.get("best_flights") or []) + (data.get("other_flights") or [])
    if not itineraries and data.get("flights"):
        itineraries = data.get("flights")
    results = []
    for it in itineraries[:8]:
        legs = it.get("flights") or []
        airlines = sorted({leg.get("airline") for leg in legs if leg.get("airline")})
        first = legs[0] if legs else {}
        last = legs[-1] if legs else {}
        results.append({
            "airlines": airlines,
            "departure": (first.get("departure_airport") or {}).get("time"),
            "arrival": (last.get("arrival_airport") or {}).get("time"),
            "duration_minutes": it.get("total_duration"),
            "stops": max(len(legs) - 1, 0),
            "price": it.get("price"),
            "type": it.get("type"),
        })
    return {"ok": bool(results), "reason": "" if results else "no itineraries returned", "results": results}


def _search_aviationstack(dep_iata: str, arr_iata: str) -> Dict[str, Any]:
    key = aviationstack_key()
    if not key:
        return {"ok": False, "reason": "AVIATIONSTACK_API_KEY not set", "results": []}
    params = {"access_key": key, "dep_iata": dep_iata, "arr_iata": arr_iata, "limit": 20}
    try:
        resp = requests.get(_AVIATIONSTACK_URL, params=params, timeout=20)
    except requests.RequestException as e:
        return {"ok": False, "reason": f"network error: {e}", "results": []}
    if resp.status_code != 200:
        return {"ok": False, "reason": f"Aviationstack returned {resp.status_code}: {resp.text[:200]}", "results": []}
    try:
        data = resp.json()
    except Exception as e:
        return {"ok": False, "reason": f"parse error: {e}", "results": []}
    if isinstance(data, dict) and data.get("error"):
        return {"ok": False, "reason": f"Aviationstack error: {data['error']}", "results": []}

    seen = set()
    results = []
    for f in (data.get("data") or []):
        airline = (f.get("airline") or {}).get("name")
        flight_no = (f.get("flight") or {}).get("iata")
        dep = f.get("departure") or {}
        arr = f.get("arrival") or {}
        key_t = (airline, flight_no)
        if key_t in seen:
            continue
        seen.add(key_t)
        results.append({
            "airline": airline,
            "flight_number": flight_no,
            "departure": dep.get("scheduled"),
            "arrival": arr.get("scheduled"),
            "departure_terminal": dep.get("terminal"),
            "status": f.get("flight_status"),
            "price": None,
        })
    return {"ok": bool(results), "reason": "" if results else "no flights returned", "results": results}


def search_flights(
    origin_city: str, destination_city: str, outbound_date: Optional[str] = None
) -> Dict[str, Any]:
    """Find flights between two cities. Returns
    {"success": bool, "message": str, "results": [...], "source": str}.
    Never raises.
    """
    dep = city_to_iata(origin_city)
    arr = city_to_iata(destination_city)
    date = (outbound_date or "").strip() or _default_date()
    date_note = "" if outbound_date else f" (using an indicative date {date}; ask the traveler to confirm their date)"

    if not dep or not arr:
        missing = origin_city if not dep else destination_city
        return {
            "success": False,
            "source": "none",
            "message": (
                f"I couldn't map '{missing}' to an airport code, so I can't pull verified "
                f"flights. Ask the traveler for the nearest major airport/city, or add it to "
                f"the airport map. Do NOT invent flight details."
            ),
            "results": [],
        }

    # 1) SearchApi Google Flights (priced options)
    primary = _search_searchapi(dep, arr, date)
    if primary.get("ok"):
        return {
            "success": True,
            "source": "SearchApi Google Flights",
            "message": (
                f"Found {len(primary['results'])} verified flight option(s) {dep}->{arr}"
                f"{date_note}."
            ),
            "results": primary["results"],
        }

    # 2) Aviationstack (route airlines/schedule, no prices)
    fallback = _search_aviationstack(dep, arr)
    if fallback.get("ok"):
        return {
            "success": True,
            "source": "Aviationstack (schedule only, no prices)",
            "message": (
                f"Found {len(fallback['results'])} verified flight(s) operating {dep}->{arr} "
                f"(airlines/schedule only - no live prices from this source). "
                f"Present these as available airlines/times, not quotes."
            ),
            "results": fallback["results"],
        }

    return {
        "success": False,
        "source": "none",
        "message": (
            f"I couldn't fetch verified flights for {dep}->{arr} right now "
            f"(SearchApi: {primary.get('reason')}; Aviationstack: {fallback.get('reason')}). "
            f"Tell the traveler plainly and suggest checking Google Flights / airline sites. "
            f"Do NOT invent flight details."
        ),
        "results": [],
    }
