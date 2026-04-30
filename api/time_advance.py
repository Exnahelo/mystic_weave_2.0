"""Pure time advancement helpers for the Ptarian calendar."""

from __future__ import annotations

from api.models import TimeElapsed, TimeState


MONTHS = (
    "Ashwake", "Embertide", "Mistbreak", "Verdantrise",
    "Clearwater", "Goldmere", "Scaletide", "Amberveil",
    "Ashenfall", "Ironmoor", "Dimlight", "Deepwarden",
)

BANDS = ("dawn", "morning", "midday", "afternoon", "dusk", "night")

SEASON_BY_MONTH = {
    "Ashwake": "winter", "Embertide": "winter", "Mistbreak": "winter",
    "Verdantrise": "spring", "Clearwater": "spring", "Goldmere": "spring",
    "Scaletide": "summer", "Amberveil": "summer", "Ashenfall": "summer",
    "Ironmoor": "autumn", "Dimlight": "autumn", "Deepwarden": "autumn",
}

# (month, day) → festival name
FESTIVALS = {
    ("Deepwarden", 30): "The Day of Founding",
    ("Ashwake", 1): "New Year's Dawn",
    ("Verdantrise", 1): "The Verdant Gate",
    ("Scaletide", 1): "Highscale",
    ("Ashenfall", 1): "Highharvestide",
    ("Ironmoor", 1): "The Day of Remembrance",
}


def advance_time(current: TimeState, elapsed: TimeElapsed) -> TimeState:
    """Pure function. Compute new TimeState from current + elapsed duration.

    Owns: band rollover, day rollover, month rollover, year rollover,
    festival detection, season lookup. Preserves weather and weather_note
    from `current` unchanged.

    Year structure: 12 months × 30 days = 360 days/year. Festivals fall on
    specific (month, day) tuples; no intercalary days.
    """
    current_band = current.time_of_day.value if hasattr(current.time_of_day, "value") else str(current.time_of_day)
    current_band_index = BANDS.index(current_band)

    if elapsed.until == "dawn":
        effective_steps = 6 if current_band == "dawn" else (6 - current_band_index) % 6
        effective_days = 0
    else:
        effective_steps = elapsed.steps
        effective_days = elapsed.days

    total_bands = effective_steps + effective_days * len(BANDS)
    band_total = current_band_index + total_bands
    new_band = BANDS[band_total % len(BANDS)]
    day_overflow = band_total // len(BANDS)

    day_total_zero_based = (current.day - 1) + day_overflow
    extra_months = day_total_zero_based // 30
    new_day = (day_total_zero_based % 30) + 1

    current_month_index = MONTHS.index(current.month)
    month_total = current_month_index + extra_months
    new_month = MONTHS[month_total % len(MONTHS)]
    new_year = current.year + (month_total // len(MONTHS))

    return TimeState.model_validate(
        {
            "day": new_day,
            "month": new_month,
            "year": new_year,
            "time_of_day": new_band,
            "season": SEASON_BY_MONTH[new_month],
            "festival": FESTIVALS.get((new_month, new_day)),
            "weather": current.weather,
            "weather_note": current.weather_note,
        }
    )