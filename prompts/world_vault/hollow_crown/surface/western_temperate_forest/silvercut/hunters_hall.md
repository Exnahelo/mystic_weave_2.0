---
id: hunters-hall
name: Hunter's Hall
type: location
region_id: hollow-crown
settlement_id: silvercut
parent_location_id: silvercut
description: The Hunts-Master's seat and the village's hunting coordination post, set a short walk into the western temperate forest from Silvercut proper. The hall handles licensing, training, game population tracking, and stocks the crafting resources and raw materials hunters draw on to fletch, repair, and maintain their own gear.
connections:
- silvercut
tags:
- drakenvale
- silvercut
- hunters-hall
- western-forest
- hunting
- crafting-materials
known_npcs:
- Tova Kerrin
threat_level: 1
discovered: true
---

# Hunter's Hall

The Hunts-Master's seat and the village's hunting coordination post, set a short walk into the western temperate forest from Silvercut proper. The hall handles licensing, training, game population tracking, and stocks the crafting resources and raw materials hunters draw on to fletch, repair, and maintain their own gear.

## Scene Texture

The Hunter's Hall sits along one of the managed paths leading north from Silvercut's central clearing, where the forest thickens but has not yet closed over the trail. The building is a long low structure of silverwood beams and dark-stained plank walls, with a broad covered porch across its front and a deep overhang behind to shield the skinning frames and drying racks clustered at its rear from weather. A simple post-and-rail hitch line stands at the porch's edge; the hall sees enough daily traffic that horses, pack mules, and the occasional deer sled are regular visitors.

Inside, the hall's main room is working space — a long central table where hunting licenses are issued and game logs are entered, a map wall with the current season's quota marks and population notes, a rack of spare bows and crossbows kept for training use, and benches along the walls where hunters returning from a day's work can sit and catch their wind before the debrief. The hall's east room holds the workbench: arrow stock by length and wood type, fletch feathers sorted by bird, sinew, bowstrings, glue pots, pitch, wax, and the hand tools that turn raw materials into finished arrows, bolts, snares, and field repairs. Hunters fletch and repair their own gear at this bench. Raw stock is drawn through the Hunts-Master's office against the hunter's license and tallied at resupply, rather than purchased separately. Specialty orders from Dracélune are filled by whichever hunter has the hand for it that season, with the hall's resources and the Hunts-Master's approval.

The hall's back room is the Hunts-Master's office — smaller, quieter, with a desk and a pair of chairs for difficult conversations. It holds the village's formal hunting records, the seasonal population surveys, and the correspondence trail to the Silver Scale Trading Company's game buyers and to Dracélune's civic offices.

Outside, the rear yard handles processing work that does not need to go all the way to the village's central smokehouses — quick cleaning, hide stretching, and the first stages of the work that larger operations finish elsewhere.

## Functions

- **Hunting licenses and coordination.** All hunting in the Silvercut range is licensed through the Hunts-Master's office here. The seasonal quotas are set, adjusted, and enforced from this hall.
- **Training.** New hunters — village-born and occasional outside apprentices — train at the Hunter's Hall under the Hunts-Master's direction and through assignments with senior hunters.
- **Game population monitoring.** The map wall holds the current season's working model of the surrounding forest's game populations. Returning hunters contribute sightings, kills, and observed sign; the model is updated continuously.
- **Crafting and repair materials.** The workbench stocks shafts, fletch feathers, sinew, bowstrings, glue, pitch, wax, and related raw materials for the hunters to fletch arrows, string bows, build snares, and repair field gear. Material draw is against license and tracked through the Hunts-Master's office. Silvercut's hunters do their own craft work; there is no dedicated fletcher.

## Character

The Hunter's Hall is quieter than the village proper and keeps its own rhythm. Hunters pass through early — before dawn on most days, collecting tags and gear before moving out — and return late, bringing game, hides, and the day's intelligence back through the hall before heading home. Midday is the hall's slowest stretch, and the Hunts-Master's most useful working time.

The hall's ethos mirrors the village's Forest Principle: restraint, observation, and deference to the forest as a living system. A hunter who kills carelessly, takes beyond quota, or disrespects the forest's patterns will find themselves in a quiet back-room conversation that leaves no room for misunderstanding.

## Tags

- drakenvale
- silvercut
- hunters-hall
- western-forest
- hunting
- crafting-materials

## Connected Nodes

- `silvercut`

## Authoring Notes

The **Hunts-Master** is anchored here as named Tier-1 NPC **Tova Kerrin**. Personality, voice, and specific temperament are intentionally left loose so they can vary from session to session within the role's constraints (forest expertise, careful adherence to the Forest Principle, direct manner with apprentices and outsiders).

**No Fletcher role.** Silvercut's hunters fletch and repair their own gear. The hall stocks raw crafting materials (shafts, feathers, sinew, bowstrings, glue, pitch, wax, hand tools) drawn against the hunter's license and tallied through the Hunts-Master's office. Specialty orders from Dracélune are filled by whichever hunter has the skill and hand for it that season. This is a deliberate scope decision — the village does not support a full professional fletcher and the existing license-and-quota system is the material-draw mechanism.

The Hunter's Hall is a sibling child of Silvercut, not a district or quarter. Separate node because it sits outside the main village clearing, generates its own scenes, and anchors a named NPC.

Threat level 1 reflects the managed forest edge around the hall. The hall itself is civically safe; the risk is the forest that begins at its back door.

Connections are intentionally limited to `silvercut`. Deeper forest movement routes through Silvercut's regional hookup to `western-temperate-forest`, not through this hall.

Crafting material draw through the Hunts-Master's office is narration-only at this stage. If gameplay eventually requires licensed hunters to draw against a mechanical resource budget, that system should be authored through `data/economy/` or a future crafting module. For now, the draw is a narrative texture that reinforces the village's licensed-and-tracked approach to forest work. Raw crafting materials themselves have baseline prices in `data/economy/prices.json` under `basic_gear` for any case where a non-licensed character or visitor buys them outright.