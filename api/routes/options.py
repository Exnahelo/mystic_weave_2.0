"""
routes/options.py — GET /options

Returns all supported classes, species, subspecies, backgrounds, subclasses, and languages
from the local unified SRD JSON snapshots.

The GPT calls this once at the start of character creation to enumerate
valid options. This prevents the GPT from guessing or confabulating
unsupported choices.
"""

from __future__ import annotations

from fastapi import APIRouter

from api.models import (
    BackgroundOption,
    ClassOption,
    LanguageOption,
    OptionsResponse,
    SpeciesOption,
    SubclassOption,
    SubclassRef,
    SubspeciesOption,
)
from api.srd5e import (
    list_backgrounds,
    list_classes,
    list_languages,
    list_species,
    list_subclasses,
    list_subspecies,
)

router = APIRouter()


@router.get("/options", response_model=OptionsResponse, tags=["options"])
async def get_options() -> OptionsResponse:
    """
    Return all supported classes, species, subspecies, backgrounds, subclasses, and languages
    from the local unified SRD data.

    Call this before asking the player to choose a class, species, subspecies,
    background, subclass, or language. Only present options returned by this endpoint — do not
    offer any options not listed here. Never enumerate from memory.

    Each class entry includes a 'subclasses' list of available subclasses.
    The top-level 'subclasses' list contains all subclasses with their class_index.
    Subclass selection is optional at character creation (typically chosen at level 3).
    """
    # Build subclass lookup by class index for embedding in ClassOption
    all_subclasses_raw = list_subclasses()
    subclasses_by_class: dict[str, list[dict]] = {}
    for sc in all_subclasses_raw:
        cls_idx = sc["class_index"]
        subclasses_by_class.setdefault(cls_idx, []).append(sc)

    # Build ClassOption list with embedded subclass refs
    classes = []
    for c in list_classes():
        cls_subs = subclasses_by_class.get(c["index"], [])
        classes.append(ClassOption(
            index=c["index"],
            name=c["name"],
            hit_die=c["hit_die"],
            subclasses=[SubclassRef(index=s["index"], name=s["name"]) for s in cls_subs],
        ))

    species = [SpeciesOption(**s) for s in list_species()]
    subspecies = [SubspeciesOption(**s) for s in list_subspecies()]
    backgrounds = [BackgroundOption(**b) for b in list_backgrounds()]
    subclasses = [SubclassOption(**sc) for sc in all_subclasses_raw]
    languages = [LanguageOption(**lang) for lang in list_languages()]

    return OptionsResponse(
        classes=classes,
        species=species,
        subspecies=subspecies,
        backgrounds=backgrounds,
        subclasses=subclasses,
        languages=languages,
    )
