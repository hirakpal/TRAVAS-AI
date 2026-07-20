"""Live Google Places API (New) client.

Replaces the old static mock datasets: specialists now ground on real, current
Google Places data (real names, ratings, addresses, price level, hours, reviews)
for ANY destination - so coverage is no longer limited to Delhi/Mumbai/Goa.

Auth: set GOOGLE_PLACES_API_KEY (or GOOGLE_MAPS_API_KEY) in the environment, with
billing enabled on the Google Cloud project. Text Search (New):
    POST https://places.googleapis.com/v1/places:searchText
    headers: X-Goog-Api-Key, X-Goog-FieldMask, Content-Type: application/json
    body:    {"textQuery": "...", "includedType": "...", "maxResultCount": N}

Everything here degrades gracefully: a missing key, network error, or non-200
response returns {"ok": False, "reason": "..."} rather than raising, so a live
failure surfaces as an honest "couldn't fetch verified data" to the traveler
instead of crashing a specialist turn.

Docs:
  https://developers.google.com/maps/documentation/places/web-service/text-search
  https://developers.google.com/maps/documentation/places/web-service/choose-fields
  https://developers.google.com/maps/documentation/places/web-service/place-details
"""

import os
import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
_DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"

# Field mask for Text Search - every path is prefixed with "places." Keep this
# tight: you're billed by the most expensive field requested, and reviews/hours
# push into higher SKUs. (Adjust if you want to trim cost.)
_SEARCH_FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.rating",
    "places.userRatingCount",
    "places.priceLevel",
    "places.types",
    "places.currentOpeningHours.openNow",
    "places.regularOpeningHours.weekdayDescriptions",
    "places.websiteUri",
    "places.nationalPhoneNumber",
    "places.googleMapsUri",
    "places.editorialSummary",
    "places.reviews",
])

# Place Details field mask - same paths WITHOUT the "places." prefix.
_DETAILS_FIELD_MASK = ",".join([
    "id", "displayName", "formattedAddress", "location", "rating",
    "userRatingCount", "priceLevel", "types", "currentOpeningHours.openNow",
    "regularOpeningHours.weekdayDescriptions", "websiteUri",
    "nationalPhoneNumber", "googleMapsUri", "editorialSummary", "reviews",
])

_PRICE_LEVEL_LABELS = {
    "PRICE_LEVEL_FREE": "Free",
    "PRICE_LEVEL_INEXPENSIVE": "Budget ($)",
    "PRICE_LEVEL_MODERATE": "Mid-range ($$)",
    "PRICE_LEVEL_EXPENSIVE": "Upscale ($$$)",
    "PRICE_LEVEL_VERY_EXPENSIVE": "Luxury ($$$$)",
}


def api_key() -> Optional[str]:
    """The configured Google Places key, or None if not set."""
    return os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")


def is_configured() -> bool:
    """True if a Google Places API key is available."""
    return bool(api_key())


def _normalize_place(p: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten one raw Places result into the compact shape specialists use."""
    name = (p.get("displayName") or {}).get("text", "")
    price_level_raw = p.get("priceLevel")
    reviews = []
    for r in (p.get("reviews") or [])[:3]:
        reviews.append({
            "author": ((r.get("authorAttribution") or {}).get("displayName")) or "Google user",
            "rating": r.get("rating"),
            "text": ((r.get("text") or {}).get("text") or "")[:300],
        })
    hours = (p.get("regularOpeningHours") or {}).get("weekdayDescriptions") or []
    return {
        "id": p.get("id"),
        "name": name,
        "address": p.get("formattedAddress"),
        "rating": p.get("rating"),
        "num_ratings": p.get("userRatingCount"),
        "price_level": _PRICE_LEVEL_LABELS.get(price_level_raw, price_level_raw),
        "types": p.get("types") or [],
        "open_now": (p.get("currentOpeningHours") or {}).get("openNow"),
        "hours": hours,
        "website": p.get("websiteUri"),
        "phone": p.get("nationalPhoneNumber"),
        "maps_uri": p.get("googleMapsUri"),
        "summary": (p.get("editorialSummary") or {}).get("text"),
        "reviews": reviews,
    }


def text_search(
    text_query: str,
    included_type: Optional[str] = None,
    max_results: int = 10,
    language_code: str = "en",
) -> Dict[str, Any]:
    """Run a Text Search (New). Returns:
        {"ok": True, "places": [normalized, ...]}
      or
        {"ok": False, "reason": "human-readable why", "places": []}
    Never raises.
    """
    key = api_key()
    if not key:
        return {"ok": False, "reason": "GOOGLE_PLACES_API_KEY is not set", "places": []}
    if not text_query or not text_query.strip():
        return {"ok": False, "reason": "empty query", "places": []}

    body: Dict[str, Any] = {
        "textQuery": text_query.strip(),
        "maxResultCount": max(1, min(int(max_results or 10), 20)),
        "languageCode": language_code,
    }
    if included_type:
        body["includedType"] = included_type

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": _SEARCH_FIELD_MASK,
    }
    try:
        resp = requests.post(_SEARCH_URL, json=body, headers=headers, timeout=15)
    except requests.RequestException as e:
        logger.warning(f"Places text_search network error: {e}")
        return {"ok": False, "reason": f"network error contacting Google Places: {e}", "places": []}

    if resp.status_code != 200:
        # Surface Google's error message (bad key, billing disabled, quota, etc.)
        detail = ""
        try:
            detail = resp.json().get("error", {}).get("message", "")
        except Exception:
            detail = resp.text[:200]
        logger.warning(f"Places text_search HTTP {resp.status_code}: {detail}")
        return {"ok": False, "reason": f"Google Places returned {resp.status_code}: {detail}", "places": []}

    try:
        places = [_normalize_place(p) for p in (resp.json().get("places") or [])]
    except Exception as e:
        return {"ok": False, "reason": f"could not parse Google Places response: {e}", "places": []}

    return {"ok": True, "places": places}


def place_details(place_id: str) -> Dict[str, Any]:
    """Fetch full details for one place id. Returns {"ok":bool, "place":..., "reason":...}."""
    key = api_key()
    if not key:
        return {"ok": False, "reason": "GOOGLE_PLACES_API_KEY is not set", "place": None}
    if not place_id:
        return {"ok": False, "reason": "empty place_id", "place": None}
    headers = {
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": _DETAILS_FIELD_MASK,
    }
    url = _DETAILS_URL.format(place_id=place_id)
    try:
        resp = requests.get(url, headers=headers, timeout=15)
    except requests.RequestException as e:
        return {"ok": False, "reason": f"network error: {e}", "place": None}
    if resp.status_code != 200:
        detail = ""
        try:
            detail = resp.json().get("error", {}).get("message", "")
        except Exception:
            detail = resp.text[:200]
        return {"ok": False, "reason": f"Google Places returned {resp.status_code}: {detail}", "place": None}
    try:
        return {"ok": True, "place": _normalize_place(resp.json())}
    except Exception as e:
        return {"ok": False, "reason": f"parse error: {e}", "place": None}
