from __future__ import annotations


def suggest_times_from_text(text: str | None) -> tuple[list[str], str]:
    """Return suggested HH:MM times (UTC) and a short rationale.

    Heuristics, minimal MVP:
    - once daily → 08:00
    - twice daily / bid → 08:00, 20:00
    - three times / tid → 08:00, 14:00, 20:00
    - four times / qid → 08:00, 12:00, 16:00, 20:00
    - morning → 08:00; evening/bedtime → 22:00; night → 20:00
    - with meals → defaults to 08:00, 13:00, 19:00, but respects counts:
      - twice daily with meals → 08:00, 19:00
      - once daily with meals → 19:00

    Times are interpreted as UTC for now.
    """
    s = (text or "").lower()
    times: list[str] = []
    reason = ""
    has_with_meals = any(k in s for k in ["with meals", "with food"])
    has_twice = any(k in s for k in ["twice", "bid", "b.i.d", "two times"])
    has_once = any(k in s for k in ["once", "q.d", "qd", "daily", "every day"])
    has_three = any(k in s for k in ["three times", "tid", "t.i.d"])
    has_four = any(k in s for k in ["four times", "qid", "q.i.d"])
    has_night = "night" in s

    if has_with_meals:
        if has_twice:
            times = ["08:00", "19:00"]
            reason = "twice daily with meals"
            return times, reason
        if has_once:
            times = ["19:00"]
            reason = "once daily with meals"
            return times, reason
        if has_three:
            times = ["08:00", "13:00", "19:00"]
            reason = "three times daily with meals"
            return times, reason
        times = ["08:00", "13:00", "19:00"]
        reason = "with meals"
        return times, reason
    if "bedtime" in s or "evening" in s:
        times = ["22:00"]
        reason = "evening/bedtime"
        return times, reason
    if has_night:
        times = ["20:00"]
        reason = "night"
        return times, reason
    if "morning" in s:
        times = ["08:00"]
        reason = "morning"
        return times, reason
    if has_four:
        times = ["08:00", "12:00", "16:00", "20:00"]
        reason = "four times daily"
        return times, reason
    if has_three:
        times = ["08:00", "14:00", "20:00"]
        reason = "three times daily"
        return times, reason
    if has_twice:
        times = ["08:00", "20:00"]
        reason = "twice daily"
        return times, reason
    if has_once:
        times = ["08:00"]
        reason = "once daily"
        return times, reason
    # Fallback
    times = ["08:00"]
    reason = "default once daily"
    return times, reason


def parse_times_user_input(text: str) -> list[str] | None:
    """Parse user-provided times like '08:00, 20:00'. Returns HH:MM list."""
    raw = [t.strip() for t in text.replace(";", ",").split(",")]
    out: list[str] = []
    for t in raw:
        if len(t) == 5 and t[2] == ":" and t[:2].isdigit() and t[3:].isdigit():
            hh = int(t[:2])
            mm = int(t[3:])
            if 0 <= hh <= 23 and 0 <= mm <= 59:
                out.append(f"{hh:02d}:{mm:02d}")
    return out or None
