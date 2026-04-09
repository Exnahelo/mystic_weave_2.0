"""
dice_roller.py — Authoritative dice resolution for Mystic Weave.

Rolls 1d100. Returns the raw result. That's it.

The route layer (routes/roll.py) handles target comparison,
success/failure determination, and degree of success bands.
This module only generates the random number.
"""

import random


def roll(dice_expression: str = "1d100", seed: int | None = None) -> int:
    """
    Roll dice and return the total.

    Supports standard notation: NdS or NdS+M or NdS-M
    Default: 1d100

    In practice this is only ever called with "1d100" but the parser
    is kept general for future extensibility (damage rolls, etc.).
    """
    if seed is not None:
        random.seed(seed)

    import re
    match = re.fullmatch(r"(\d*)d(\d+)([+-]\d+)?", dice_expression.strip())
    if not match:
        raise ValueError(f"Invalid dice expression: {dice_expression}")

    num_dice = int(match.group(1)) if match.group(1) else 1
    die_size = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0

    total = sum(random.randint(1, die_size) for _ in range(num_dice)) + modifier
    return total
