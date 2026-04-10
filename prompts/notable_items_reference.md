# Mystic Weave — Notable Items Reference

This reference defines reusable, canonical item patterns for runtime narration and state updates. Use these entries as templates for generated loot, rewards, and faction gear.

## Item Authoring Rules

- Every durable item should map to at most one `roll_tag`.
- `roll_tag` provides contextual fit, not extra numeric bonus.
- Keep effects concrete and state-compatible (HP, status, access, positioning, information).
- If an item creates a persistent world fact, save it to state/location.

## Canonical Notable Items

| ID | Item | Category | Suggested `roll_tag` | Mechanical Effect |
|---|---|---|---|---|
| item_radiant_blade_01 | Radiant Blade | weapon | `heavy_weapons` | On strong success or critical success, may convert minor collateral harm to controlled impact in scene narration. |
| item_wardbreaker_spear_01 | Wardbreaker Spear | weapon | `heavy_weapons` | Grants narrative justification to contest reinforced barriers or shield lines. |
| item_quicksilver_knife_01 | Quicksilver Knife | weapon | `light_weapons` | Supports stealth takedown narration when action already succeeds. |
| item_skystring_bow_01 | Skystring Bow | weapon | `ranged_weapons` | Enables long-range precision shots in high-wind scenes without contradiction. |
| item_bastion_mail_01 | Bastion Mail | armor | `shields_armor` | On partial failure in direct combat, reduce severity by one narrative step when plausible. |
| item_aegis_kite_01 | Aegis Kite Shield | armor | `shields_armor` | Supports ally-protection framing and line-holding outcomes. |
| item_monksteel_wraps_01 | Monksteel Handwraps | weapon | `unarmed_combat` | Enables meaningful unarmed engagement against armored foes. |
| item_veilcloak_01 | Veilcloak | utility | `disguise_forgery` | Supports identity concealment checks in formal spaces. |
| item_ghoststep_boots_01 | Ghoststep Boots | utility | `light_weapons` | Supports silent movement framing in infiltration scenes. |
| item_lockwhisper_set_01 | Lockwhisper Picks | utility | `lockpicking_traps` | Supports rapid bypass attempts under time pressure. |
| item_hawkeye_lens_01 | Hawkeye Lens | utility | `ranged_weapons` | Improves fictional positioning for long-sight reconnaissance. |
| item_wayfarer_reins_01 | Wayfarer Reins | utility | `mounts_vehicles` | Supports difficult mount/vehicle control in hazardous terrain. |
| item_aether_staff_01 | Aether Staff | arcane | `arcane_implements` | Supports stable channeling for multi-step arcane actions. |
| item_rune_compass_01 | Rune Compass | arcane | `arcane_implements` | Supports magical orientation and pathfinding in distorted zones. |
| item_sunvial_elixir_01 | Sunvial Elixir | consumable | `herbalism_alchemy` | Restore moderate HP once per scene where immediate treatment is plausible. |
| item_emberseal_paste_01 | Emberseal Paste | consumable | `herbalism_alchemy` | Temporarily suppresses environmental burn exposure in volcanic scenes. |
| item_sanctum_oil_01 | Sanctum Oil | sacred | `sacred_rites` | Supports purification or consecration attempts at tainted sites. |
| item_oathbell_01 | Oathbell of Accord | sacred | `sacred_rites` | Supports negotiation scenes where formal vows are binding. |
| item_resonance_lyre_01 | Resonance Lyre | utility | `musical_instruments` | Supports crowd-calming or ritual synchronization actions. |
| item_vault_tome_01 | Vault Cognition Tome | special | `arcane_implements` | Grants temporary narrative access to specialized lore in-scene; not a permanent encyclopedic bypass. |

## Balance & Consistency Notes

- Items should not replace domain/tag selection; they contextualize an attempt.
- Avoid unconditional immunity or guaranteed success items.
- Rare/legendary items should introduce obligations, visibility, or political attention.
- For campaign continuity, prefer "advantage in specific context" over global bonuses.
