from __future__ import annotations


def infer_timezone_from_phone(phone: str) -> str | None:
    """Very rough mapping from E.164 country code to a primary timezone.

    Prefer users to pick explicitly or share location; this is a fallback.
    """
    p = phone.strip().replace(" ", "")
    if p.startswith("+65"):
        return "Asia/Singapore"
    if p.startswith("+60"):
        return "Asia/Kuala_Lumpur"
    if p.startswith("+62"):
        return "Asia/Jakarta"
    if p.startswith("+63"):
        return "Asia/Manila"
    if p.startswith("+66"):
        return "Asia/Bangkok"
    if p.startswith("+84"):
        return "Asia/Ho_Chi_Minh"
    if p.startswith("+852"):
        return "Asia/Hong_Kong"
    if p.startswith("+886"):
        return "Asia/Taipei"
    if p.startswith("+81"):
        return "Asia/Tokyo"
    if p.startswith("+82"):
        return "Asia/Seoul"
    if p.startswith("+91"):
        return "Asia/Kolkata"
    return None


def infer_timezone_from_coords(lat: float, lon: float) -> str | None:
    """Coarse bounding-box based timezone guess for SEA cities (MVP).

    This is intentionally simple and should be replaced by a proper library
    like timezonefinder for global coverage.
    """
    # Singapore approx
    if 1.15 <= lat <= 1.50 and 103.6 <= lon <= 104.1:
        return "Asia/Singapore"
    # Kuala Lumpur area
    if 3.0 <= lat <= 3.5 and 101.0 <= lon <= 101.9:
        return "Asia/Kuala_Lumpur"
    # Jakarta area
    if -6.4 <= lat <= -6.0 and 106.6 <= lon <= 107.1:
        return "Asia/Jakarta"
    # Bangkok area
    if 13.5 <= lat <= 13.9 and 100.3 <= lon <= 100.7:
        return "Asia/Bangkok"
    # Manila area
    if 14.4 <= lat <= 14.8 and 120.9 <= lon <= 121.2:
        return "Asia/Manila"
    # Ho Chi Minh City
    if 10.6 <= lat <= 10.9 and 106.6 <= lon <= 106.9:
        return "Asia/Ho_Chi_Minh"
    return None
