# Mystic Weave — The Oath Calendar

Version 2.1 — May 2026
Status: Canonical. Upload to GPT builder as a knowledge file.

---

## Overview

The Oath Calendar marks time from the day the Oath of the Fallen was sworn — the moment Drakenvale was founded. Years are reckoned in **Years of the Oath (YO)**. Year 1 begins on the day the Oath was sworn. The current campaign year is set at session start.

**Structure:** 12 months × 30 days = 360 days per year.

Festivals fall on specific days within months — they mark solstices, equinoxes, and significant remembrances. Festival days are observed across Drakenvale as rest days: no commerce, no petitions, ceremonies only. Each festival sits on a named (month, day), not between months.

---

## Months

| # | Name | Season | Character |
|---|---|---|---|
| 1 | **Ashwake** | Winter | Deep cold. Volcanic vents most active. Forge-work begins. |
| 2 | **Embertide** | Winter | Season of indoor craft and long forge hours. |
| 3 | **Mistbreak** | Winter → Spring | Mists thin. First thaw. Travel cautiously resumes. |
| 4 | **Verdantrise** | Spring | Valley floor blooms. Grasslands brighten. |
| 5 | **Clearwater** | Spring | Crystalline rivers run highest. Trade routes open fully. |
| 6 | **Goldmere** | Spring → Summer | Long days. Dragon social season begins. |
| 7 | **Scaletide** | Summer | Peak heat. Trial of Wings season. Dragon gatherings. |
| 8 | **Amberveil** | Summer | Harvest of magical flora. Forge Guild stock assessments. |
| 9 | **Ashenfall** | Summer → Autumn | First ash from volcanic activity. Air turns sharp. |
| 10 | **Ironmoor** | Autumn | Cooling. Forge production increases for winter stock. |
| 11 | **Dimlight** | Autumn | Days shorten. Shadowed Hollows most active. Cult watch heightened. |
| 12 | **Deepwarden** | Autumn → Winter | Year's end. Cold returns. Final harvests secured. |

---

## Festival Days

Festival days fall on specific named days within months. They mark solstices, equinoxes, and significant remembrances. Each festival is observed across Drakenvale as a rest day.

| Name | Calendar Day | Season Boundary | Observance |
|---|---|---|---|
| **The Day of Founding** | Deepwarden 30 | Winter Solstice — Year's End | Honors the swearing of the Oath of the Fallen. Formal ceremonies at the Platinum Heart. The Platinum Flame burns at full intensity. Solemn. The most significant day in the Drakenvale calendar. |
| **New Year's Dawn** | Ashwake 1 | Winter Solstice — Year's Start | Community gatherings. Oaths renewed. New ventures announced publicly. Warm and informal counterpart to the solemn Founding Day. The two together form the winter solstice observance. |
| **The Verdant Gate** | Verdantrise 1 | Spring Equinox | Marks the valley's renewal. Platinum Acolytes bless the Sacred Pools. The Draconic Grasslands ceremonially opened for dragon gatherings. The Trial of Wings season is announced. |
| **Highscale** | Scaletide 1 | Summer Solstice | Festival of Wings — aerial displays across all alignments. Trial of Wings season opens formally. The most festive day of the year. Commerce, competition, celebration. |
| **Highharvestide** | Ashenfall 1 | Autumn Equinox | Harvest of magical flora and forge materials assessed. The SSTC's primary coordination day for external trade. Gifts exchanged. |
| **The Day of Remembrance** | Ironmoor 1 | Mid-Autumn | Honors the Platinum Warden's sacrifice and all who fell in the Discordant War. Completely solemn. No commerce. No petitions. Warden vigils at the Rift of Discord and Temple of Mordrax perimeter. The Platinum Flame dims to a single point of light at dusk and is relit at dawn. |

---

## Season Summary

| Season | Months | Festival at Boundary |
|---|---|---|
| Winter | Ashwake, Embertide, Mistbreak | Day of Founding + New Year's Dawn (solstice pair) |
| Spring | Verdantrise, Clearwater, Goldmere | The Verdant Gate |
| Summer | Scaletide, Amberveil, Ashenfall | Highscale |
| Autumn | Ironmoor, Dimlight, Deepwarden | Highharvestide (equinox) + Day of Remembrance (mid-autumn) |

---

## Vaelthor — The Moon

Drakenvale's moon. Named from ancient Draconic — "the wandering eye." Its cycle runs 30 days, aligned to the calendar month. Phase is always derivable from the current `day` — no separate state field needed.

### Phase Table

| Days of Month | Phase |
|---|---|
| 1–2 | New Moon |
| 3–6 | Waxing Crescent |
| 7–9 | First Quarter |
| 10–13 | Waxing Gibbous |
| 14–16 | Full Moon |
| 17–20 | Waning Gibbous |
| 21–23 | Last Quarter |
| 24–30 | Waning Crescent |

### Mechanical Effects by Location

Vaelthor's phase has mechanical weight only in specific locations. Everywhere else it is atmospheric — describe it, do not apply modifiers.

**Shadowed Hollows / Temple of Mordrax perimeter**
- Full Moon (days 14–16): Cult activity and wraith presence increase. Apply −10 to difficulty modifier on stealth, avoidance, and detection rolls in this zone.
- New Moon (days 1–2): Suppressed activity. Apply +5 to the same rolls.
- All other phases: no modifier.

**Mystic Wetlands**
- Full Moon: Restorative and divination magic enhanced. Any roll involving healing or information-seeking gains +5.
- New Moon: Navigation harder, disorientation more likely. Apply −5 to navigation and perception rolls.
- All other phases: no modifier.

**Sacred Pools / Platinum Heart rituals**
- Certain Platinum Acolyte rituals are only performed on full moon or new moon. If a player attempts a ritual at the wrong phase, the Acolytes will delay or redirect. Narrative gating only — no roll modifier.

**Vaelthor on festival days**
- The Day of Remembrance falling on a full moon is considered a grave omen. Warden patrols are doubled. Note this in narration if it occurs.
- Highscale falling on a full moon is considered auspicious for the Trial of Wings. Note it in narration.

---

## Weather

Valley weather reflects the collective emotional state of the resident dragons — a natural magical phenomenon tied to Drakenvale's founding wards. It is not purely meteorological.

### Weather States

| State | Description | Typical Cause |
|---|---|---|
| `clear` | Calm skies, good visibility, mild conditions. | Council in harmony, no active tensions. |
| `mist` | Soft fog, reduced visibility, contemplative atmosphere. | Varethyn's influence dominant; periods of reflection or mediation underway. |
| `storm` | Thunder, lightning, high winds. | Active conflict or tension between Council members or factions. |
| `ash-haze` | Volcanic particulate in the air, reduced light quality, acrid smell. | Zarkeros active, forge production at peak, or volcanic event in the Highlands. |
| `unnatural` | Weather that defies season or logic — snow in summer, silence during a storm, light with no source. | Temple seal weakening, significant magical disruption, or Rift of Discord instability. |

### Weather Rules

- Update `weather` only when something in the world causes it to change. Do not change it arbitrarily between turns.
- Narrate transitions gradually — weather shifts over hours, not instantly.
- Storm weather in open terrain (Draconic Grasslands, Alpine Peaks approaches) adds 1–2 time steps to travel.
- `unnatural` weather is always a signal to the player that something significant is wrong. Use it sparingly and intentionally.

Seasonal defaults if no other cause is active:

| Season | Default Weather |
|---|---|
| Winter | `mist` or `clear` |
| Spring | `clear` |
| Summer | `clear` or `ash-haze` (Scaletide peak) |
| Autumn | `mist` (Dimlight especially) |

The Day of Remembrance defaults to `mist` regardless of other factors.

---

## World State Fields

The `world.time` block is server-computed from prior state plus the duration sent on each save. Do not write derived fields directly.

```json
"time": {
  "day": 1,
  "month": "Verdantrise",
  "year": 847,
  "time_of_day": "morning",
  "season": "spring",
  "festival": null,
  "weather": "clear",
  "weather_note": ""
}
```

**Server-computed (do not write):**

- `day` — integer 1–30. Resets to 1 on month change.
- `month` — month name from the months table.
- `year` — integer YO. Increments after Day of Founding.
- `time_of_day` — band: `dawn / morning / midday / afternoon / dusk / night`.
- `season` — derived from `month`.
- `festival` — auto-set on festival days, cleared otherwise.

**Writable through `world.time`:**

- `weather` — enum: `clear / mist / storm / ash-haze / unnatural`. Update only when world events warrant a change.
- `weather_note` — freeform string. Optional context for current weather. Leave empty if no specific cause.

**To advance time, send `time_elapsed` on the save:**

- `{steps: N}` — N band advances (1 step ≈ 2–3 hours; bounds 0–12)
- `{days: N}` — N full days (bounds 0–30)
- `{until: "dawn"}` — skip to the next dawn (mutually exclusive with steps/days)
- `{}` — no time passes (default; valid for fast scenes such as combat exchanges or dialogue beats)

**Moon phase is not stored.** Derive Vaelthor's phase from `day` using the phase table whenever needed.

---

## Time of Day Progression

Time advances in steps. Each step represents roughly 2–3 hours of in-world time.

```
dawn → morning → midday → afternoon → dusk → night → dawn (next day)
```

Advancing past `night` increments `day` by 1 and returns to `dawn`. The backend handles this rollover, including month, year, season, and festival transitions, when you send `time_elapsed`.

---

## Travel Time Reference

Use this table to choose the `time_elapsed` value for a journey. Source: `geography.md`.

| Journey | time_elapsed |
|---|---|
| Within same location (short scene, no travel) | `{steps: 0}` or `{steps: 1}` |
| Short errand within same biome | `{steps: 1}` |
| Stronghold to Grasslands border (20–40km) | `{steps: 2}` (half day each way) |
| Stronghold to Platinum Heart (~60km) | `{steps: 4}` or `{steps: 5}` (full day) |
| Stronghold to Temperate Forest edge (~80km) | full day, e.g. `{steps: 5}` |
| Stronghold to Volcanic Highlands (~100km) | `{days: 1, steps: 3}` |
| Stronghold to Shadowed Hollows (~150km) | `{days: 3, steps: 3}` (3.5–4 days) |
| Stronghold to Mystic Wetlands (~180km) | `{days: 4}` or `{days: 5}` |
| Stronghold to Alpine Peaks (~200km) | `{days: 4}` or `{days: 5}` |
| Overnight travel | `{until: "dawn"}` |
| Rest / full sleep | `{until: "dawn"}` |

Off-path, night travel, or transition zones: add 50–100% to travel time.
Storm weather in open terrain: add 1–2 steps.

---

## GPT Time Rules (Non-Negotiable)

1. **Send `time_elapsed` on every state-write save.** Use `{steps: N}`, `{days: N}`, `{until: "dawn"}`, or `{}` for no advance. Combinations of steps and days are valid; `until` is mutually exclusive with steps/days.

2. **Choose the duration based on what happened in the scene.** Use the Travel Time Reference for journeys. For non-travel scenes: a brief beat is `{}` or `{steps: 0}`; a meaningful conversation, training, or rest scene is typically `{steps: 1}` or `{steps: 2}`; a long activity is more.

3. **Do not write `world.time.day`, `month`, `year`, `time_of_day`, `season`, or `festival`.** The backend computes these from prior state + `time_elapsed`. Sending them has no effect now and will be rejected in a future update.

4. **`weather` and `weather_note` remain writable** through `world.time`. Update them only when something in the world causes weather to change. Do not change weather arbitrarily. Narrate transitions gradually.

5. **Never offer time-gated content that contradicts current `time_of_day`.** Read the returned `world.time` after each save — the new state is authoritative. A morning mission cannot be offered at dusk. A nocturnal encounter cannot be presented at midday.

6. **Derive Vaelthor's phase from `day`.** Apply mechanical modifiers only in the specified locations. Reference the phase in narration everywhere else.

7. **Narrate time and weather naturally.** Do not announce state field values. Instead: *"By the time you return to the Stronghold, the valley is settling into dusk, the last light catching the platinum walls in orange and gold. A low mist is beginning to roll in from the grasslands — Vaelthor barely visible through it, a waxing crescent low on the horizon."*

---

## In-World Time Telling

Characters do not have access to mechanical clocks. Time of day is determined by:

- Position and quality of light (sun angle, shadow length, sky color)
- Natural cues (birdsong at dawn, crickets at dusk, temperature drop at night)
- Valley weather, which reflects the emotional state of resident dragons
- Vaelthor's position and phase for night scenes
- A timepiece or magical device if carried in equipment — note this in narration if relevant

Precision timing requires a carried device. Without one, time is approximate and the GPT narrates it as such.

---

## Seasonal and Lunar Notes for the GPT

- The Day of Founding and New Year's Dawn always fall together — two days side by side at the winter solstice. The most significant transition of the year.
- The Day of Remembrance is the only mid-season festival day. Its placement in the darkest part of autumn is intentional.
- The Draconic Conclave, when called, is typically scheduled around Highscale or The Day of Founding — never during the Day of Remembrance.
- Dragon social activity peaks during Scaletide and Goldmere. Shadowed Hollows and cult activity spike during Dimlight.
- Forge Guild production is highest during Embertide, Ironmoor, and Ashwake.
- Vaelthor is full during days 14–16 of every month. Dimlight days 14–16 are the highest-risk window for Hollows activity in any given month.
- If The Day of Remembrance falls on a full moon, treat the entire observance as a heightened-tension event. This is rare and significant.
