---
id: herbalists-cabin
name: Herbalist's Cabin
type: location
region_id: hollow-crown
settlement_id: silvercut
parent_location_id: silvercut
description: The village healer's workspace and residence, set on a small managed clearing at Silvercut's southern edge. The cabin holds the medicinal gardens, drying shed, tincture workroom, and a modest patient room for injury care and short convalescence.
connections:
- silvercut
tags:
- drakenvale
- silvercut
- herbalists-cabin
- western-forest
- healer
- medicine
- herbalism
known_npcs:
- Marren Oake
threat_level: 0
discovered: true
---

# Herbalist's Cabin

The village healer's workspace and residence, set on a small managed clearing at Silvercut's southern edge. The cabin holds the medicinal gardens, drying shed, tincture workroom, and a modest patient room for injury care and short convalescence.

## Scene Texture

The cabin stands in a small clearing a short walk south of Silvercut along its own path, close enough that an injured hunter can be carried in on a sling in a reasonable time and far enough that the village's usual noise does not reach it. The clearing is tidy without being groomed — beds of medicinal herbs laid out in long parallel rows, a low stone wall marking the garden's edge, a few older silverwood trees left standing where the original clearing was cut, and the cabin itself set at the back of the open ground with its door facing north toward the village.

The cabin is small, built in the local idiom — silverwood beams, plank walls, a steep roof with deep eaves. A covered porch holds drying racks in use during most of the growing season, and a smaller covered shed beside the cabin handles the longer-term drying of bulk herb harvests and the preparation of the rougher preserved materials.

Inside, the cabin is divided into three functional spaces. The front room is the workroom: a long bench along one wall with the tools of tincture-making (mortars, pestles, glass and ceramic vessels, a small distillation setup, scales, notebooks, the careful record-keeping of a practitioner who has been at this work for a long time), a wall of shelved jars and labeled bundles, and a small fire for low-heat preparations. The middle room is the patient room: two narrow beds, a washing basin, clean linens, and the sparse efficient fittings of a space that sees regular use but does not hold patients long. The back room is the healer's own — sleeping quarters, a reading chair, a small personal garden bed visible through the back window.

The garden itself is the cabin's working heart. Silvercut's forest ecology supplies a substantial pharmacopeia, and Marren Oake's beds hold the cultivated varieties of the species the forest provides in less concentrated form: common herbs for simple infusions, the more demanding species that require careful soil and attention, and a few rare varieties that have taken years to establish. Beekeeping is incidental but real; two small hives at the garden's edge provide honey for preparations and, by coincidence, a minor tie-in to the village's apiary economy.

## Functions

- **Village medicine.** The cabin is the village's primary care point for injuries and illness arising from the working life — axe cuts, fall injuries, hunting wounds, infections, seasonal fevers, exposure. Treatment follows what the cabin's pharmacopeia and skill can handle.
- **Medicinal gardens.** The cultivated beds supply herbs, roots, and preparations used in the cabin's treatments and in the modest remedies the village keeps on hand. Surplus occasionally moves to Dracélune but the cabin is not production-scale.
- **Tincture, salve, and remedy preparation.** The workroom produces the village's working stock of preserved medicines — tinctures, salves, teas, and the simpler compounded remedies.
- **Short convalescence.** Patients not severe enough to require Dracélune's larger facilities but too hurt or sick to recover well at home can use the cabin's patient room for a few days. The arrangement is informal; payment is usually in work or kind rather than coin.
- **Stabilization and referral.** Serious cases — severe trauma, injuries beyond the cabin's capacity, illnesses requiring deeper care — are stabilized here and sent on to Dracélune by wagon or cart, usually with a messenger running ahead.

## Character

The cabin is a quiet place. The Healer works alone most of the time, with an occasional apprentice or temporarily assigned villager when the caseload demands it. Days in the garden alternate with days in the workroom and days with patients; the rhythm is seasonal as much as weekly.

The cabin's ethos mirrors the village's broader restraint. The Healer treats what can be treated, refers what cannot, and does not oversell the pharmacopeia's range. Villagers trust the cabin specifically because it does not promise what it cannot deliver.

## Tags

- drakenvale
- silvercut
- herbalists-cabin
- western-forest
- healer
- medicine
- herbalism

## Connected Nodes

- `silvercut`

## Authoring Notes

The **Healer** is anchored here as named Tier-1 NPC **Marren Oake**. Personality, voice, and specific temperament are intentionally left loose so they can vary from session to session within the role's constraints (careful practitioner, long experience with forest-ecology medicine, direct about what the cabin can and cannot treat, quiet authority).

The Herbalist's Cabin is a sibling child of Silvercut, not a part of the village proper. Separate node because it sits outside the main village clearing, generates its own scenes, and anchors a named NPC.

Threat level 0 reflects the cabin's placement within the village's safe perimeter and its intrinsic civic safety. Injured or sick patients arrive here; danger happens elsewhere.

The cabin is **not a full infirmary**. Serious cases escalate narratively to Dracélune. This is a deliberate scope limit: the cabin handles village-scale medicine, not realm-scale medical infrastructure.

Any structured mechanics around healing (potion pricing, treatment cost, recovery time, what the pharmacopeia can resolve) should be authored into `data/economy/` or a future medical-system module if gameplay routes characters through the cabin for mechanical effect. Prose-texture healing is narration-only.

The apiary detail is soft-authored — two garden hives at the cabin, not a full village-economy hook. If a later storyline needs cabin-honey to be distinct from Silvercut's main apiary output, that can be committed then.