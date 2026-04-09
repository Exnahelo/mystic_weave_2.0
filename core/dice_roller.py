import random
import re

def roll(
    dice_expression,
    advantage=False,
    disadvantage=False,
    seed=None,
    verbose=False,
    pool_mode=False,
    keep_highest=None,
    keep_lowest=None
):
    if seed is not None:
        random.seed(seed)

    match = re.fullmatch(r"(\d*)d(\d+)([+-]\d+)?", dice_expression.strip())
    if not match:
        raise ValueError(f"Invalid dice expression: {dice_expression}")

    num_dice = int(match.group(1)) if match.group(1) else 1
    die_size = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0

    def single_roll():
        rolls = [random.randint(1, die_size) for _ in range(num_dice)]
        is_crit = (die_size == 20 and num_dice == 1 and rolls[0] == 20)
        if pool_mode:
            if keep_highest:
                rolls.sort(reverse=True)
                used_rolls = rolls[:keep_highest]
            elif keep_lowest:
                rolls.sort()
                used_rolls = rolls[:keep_lowest]
            else:
                used_rolls = rolls
        else:
            used_rolls = rolls
        total = sum(used_rolls) + modifier
        return rolls, used_rolls, total, is_crit

    if advantage or disadvantage:
        rolls_1, used_1, total_1, crit_1 = single_roll()
        rolls_2, used_2, total_2, crit_2 = single_roll()
        if verbose:
            print(f"Roll 1: {rolls_1} (used: {used_1}) -> {total_1}{' (CRIT!)' if crit_1 else ''}")
            print(f"Roll 2: {rolls_2} (used: {used_2}) -> {total_2}{' (CRIT!)' if crit_2 else ''}")
        if advantage:
            return max(total_1, total_2)
        else:
            return min(total_1, total_2)
    else:
        rolls, used, total, is_crit = single_roll()
        if verbose:
            print(f"Rolled: {rolls} (used: {used}) -> Total: {total}{' (CRIT!)' if is_crit else ''}")
        return total

if __name__ == "__main__":
    print("Standard roll (2d6+3):", roll("2d6+3", verbose=True))
    print("Advantage roll (1d20):", roll("1d20", advantage=True, verbose=True))
    print("Disadvantage roll (1d20):", roll("1d20", disadvantage=True, verbose=True))
    print("Critical test (1d20):", roll("1d20", seed=20, verbose=True))
    print("Pool roll, keep highest 2 of 4d6:", roll("4d6", pool_mode=True, keep_highest=2, verbose=True))
