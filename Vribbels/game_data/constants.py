"""
Game constants for CZN.
Contains experience tables, equipment slots, stats, rarity, and other game-wide constants.
"""

from pathlib import Path

# Experience thresholds for character levels (heroes)
CHARACTER_EXP_TABLE = [
    (0, 1), (100, 2), (500, 5), (2000, 10), (8000, 15),
    (20000, 20), (40000, 25), (70000, 30), (100000, 35),
    (144000, 40), (200000, 45), (300000, 50), (481000, 55), (720000, 60),
]

# Partner card exp table (different from heroes!)
# Based on actual data: Daisy 36300=30, Alyssa 181000=50, Nyx 251000=55
PARTNER_EXP_TABLE = [
    (0, 1), (100, 2), (1000, 5), (4000, 10), (12000, 15),
    (20000, 20), (28000, 25), (36300, 30), (70000, 35),
    (110000, 40), (145000, 45), (181000, 50), (251000, 55), (360000, 60),
]

# Friendship bonus rewards (cumulative)
FRIENDSHIP_BONUSES = [
    (1, 0, 0, 0), (2, 3, 0, 0), (3, 3, 1, 0), (4, 3, 1, 1), (5, 6, 1, 1),
    (6, 6, 2, 1), (7, 6, 2, 4), (8, 9, 2, 4), (9, 9, 3, 4), (10, 9, 3, 7),
    (11, 12, 3, 7), (12, 12, 4, 7), (13, 12, 4, 10), (14, 15, 4, 10), (15, 15, 5, 10),
    (16, 15, 5, 13), (17, 18, 5, 13), (18, 18, 6, 13), (19, 18, 6, 16), (20, 21, 6, 16),
    (21, 21, 7, 16), (22, 21, 7, 19), (23, 24, 7, 19), (24, 24, 8, 19), (25, 24, 8, 22),
    (26, 27, 8, 22), (27, 27, 9, 22), (28, 27, 9, 25), (29, 30, 9, 25), (30, 30, 10, 25),
    (31, 30, 10, 28), (32, 33, 10, 28), (33, 33, 11, 28), (34, 33, 11, 31), (35, 36, 11, 31),
    (36, 36, 12, 31), (37, 36, 12, 34), (38, 39, 12, 34), (39, 39, 13, 34), (40, 39, 13, 37),
]

# Note: Capture-related constants (GAME_HOSTS, GAME_PORT, PROXY_PORT, OUTPUT_DIR, HOSTS_PATH)
# have been moved to the capture module (capture/constants.py)

EQUIPMENT_SLOTS = {
    1: "I Shock",
    2: "II Suppression",
    3: "III Denial",
    4: "IV Ideal",
    5: "V Desire",
    6: "VI Imagination",
}

SLOT_ORDER = [1, 2, 3, 4, 5, 6]

RARITY = {1: "Common", 2: "Uncommon", 3: "Rare", 4: "Legendary"}

# Updated colors: Orange for Legendary, Blue for Rare, Green for Uncommon
RARITY_COLORS = {
    1: "#888888",      # Common - Gray
    2: "#50C878",      # Uncommon - Green
    3: "#00BFFF",      # Rare - Blue
    4: "#FF8C00",      # Legendary - Orange
}

RARITY_BG_COLORS = {
    1: "#1e1e2e",
    2: "#1e2e1e",      # Uncommon - Green tint
    3: "#1e2535",      # Rare - Blue tint
    4: "#2e2518",      # Legendary - Orange tint
}

RARITY_ICONS = {1: "[C]", 2: "[U]", 3: "[R]", 4: "[L]"}

RARITY_STARTING_SUBSTATS = {
    1: 0, 2: 1, 3: 2, 4: 3,
}

# Stat definitions with min/max roll values
STATS = {
    "S_ATK_INC_ADD_OUT": ("Flat ATK", "Flat ATK", False, 8.0, 5.0),
    "S_ATK_INC_RATE_OUT": ("ATK%", "ATK%", True, 1.3, 0.8),
    "S_ADDI_ATK_DMG_RATE_INC_ADD": ("Extra DMG%", "Extra DMG%", True, 3.4, 2.7),
    "S_DEF_INC_ADD_OUT": ("Flat DEF", "Flat DEF", False, 5.0, 3.0),
    "S_DEF_INC_RATE_OUT": ("DEF%", "DEF%", True, 1.3, 0.8),
    "S_HP_INC_ADD_OUT": ("Flat HP", "Flat HP", False, 12.0, 10.0),
    "S_HP_INC_RATE_OUT": ("HP%", "HP%", True, 1.3, 0.8),
    "S_CRI_INC_ADD": ("CRate", "CRate", True, 2.0, 1.2),
    "S_CRI_DMG_RATE_INC_ADD": ("CDmg", "CDmg", True, 4.0, 2.4),
    "S_CHARGING_POWER_INC_ADD": ("Ego", "Ego", False, 5.0, 2.0),
    "S_DOT_ATK_DMG_RATE_INC_ADD": ("DoT%", "DoT%", True, 3.4, 2.7),
    "S_RED_DMG_RATE_INC_ADD": ("Passion DMG%", "Passion", True, 3.5, 2.0),
    "S_GREEN_DMG_RATE_INC_ADD": ("Order DMG%", "Order", True, 3.5, 2.0),
    "S_BLUE_DMG_RATE_INC_ADD": ("Justice DMG%", "Justice", True, 3.5, 2.0),
    "S_PURPLE_DMG_RATE_INC_ADD": ("Void DMG%", "Void", True, 3.5, 2.0),
    "S_ORANGE_DMG_RATE_INC_ADD": ("Instinct DMG%", "Instinct", True, 3.5, 2.0),
}

STAT_SHORT_NAMES = {info[0]: info[1] for info in STATS.values()}
ALL_STAT_NAMES = [s[0] for s in STATS.values()]

# Main stats for each slot (using updated names)
SLOT_MAIN_STATS = {
    1: ["Flat ATK"],
    2: ["Flat DEF"],
    3: ["Flat HP"],
    4: ["ATK%", "DEF%", "HP%", "CRate", "CDmg"],
    5: ["ATK%", "DEF%", "HP%", "Passion DMG%", "Order DMG%", "Justice DMG%", "Void DMG%", "Instinct DMG%"],
    6: ["ATK%", "DEF%", "HP%", "Ego"],
}

MAX_LEVEL = 5
UPGRADES_PER_RARITY = {3: 3, 4: 4}

# Growth Stone items - maps res_id to (attribute, quality, icon_filename)
GROWTH_STONES = {
    # Passion stones
    3120001: ("Passion", "Common", "growth_stone_passion_common.png"),
    3120002: ("Passion", "Great", "growth_stone_passion_great.png"),
    3120003: ("Passion", "Premium", "growth_stone_passion_premium.png"),
    # Instinct stones
    3120011: ("Instinct", "Common", "growth_stone_instinct_common.png"),
    3120012: ("Instinct", "Great", "growth_stone_instinct_great.png"),
    3120013: ("Instinct", "Premium", "growth_stone_instinct_premium.png"),
    # Void stones
    3120021: ("Void", "Common", "growth_stone_void_common.png"),
    3120022: ("Void", "Great", "growth_stone_void_great.png"),
    3120023: ("Void", "Premium", "growth_stone_void_premium.png"),
    # Order stones
    3120031: ("Order", "Common", "growth_stone_order_common.png"),
    3120032: ("Order", "Great", "growth_stone_order_great.png"),
    3120033: ("Order", "Premium", "growth_stone_order_premium.png"),
    # Justice stones
    3120051: ("Justice", "Common", "growth_stone_justice_common.png"),
    3120052: ("Justice", "Great", "growth_stone_justice_great.png"),
    3120053: ("Justice", "Premium", "growth_stone_justice_premium.png"),
}


def get_level_from_exp(exp: int, exp_table: list = None) -> int:
    """Convert experience points to level with interpolation"""
    if exp_table is None:
        exp_table = CHARACTER_EXP_TABLE

    if exp <= 0:
        return 1

    prev_exp, prev_level = 0, 1
    for min_exp, lvl in exp_table:
        if exp < min_exp:
            if min_exp > prev_exp:
                progress = (exp - prev_exp) / (min_exp - prev_exp)
                return prev_level + int(progress * (lvl - prev_level))
            return prev_level
        prev_exp, prev_level = min_exp, lvl

    return 60  # Max level


def get_partner_level_from_exp(exp: int) -> int:
    """Convert partner card experience to level.
    Partners use a simpler linear formula at low levels: ~180 exp per level.
    At higher levels, the exp requirement increases."""
    if exp <= 0:
        return 1

    # For low exp (levels 1-10), use linear formula: 180 exp per level
    if exp < 4000:
        return min(60, max(1, exp // 180 + 1))

    # For higher levels, use the exp table with interpolation
    return get_level_from_exp(exp, PARTNER_EXP_TABLE)


def get_friendship_bonus(index: int) -> tuple[int, int, int]:
    """Get cumulative friendship bonus (ATK, DEF, HP) for given index"""
    if index <= 1:
        return (0, 0, 0)
    for bonus in FRIENDSHIP_BONUSES:
        if bonus[0] == index:
            return (bonus[1], bonus[2], bonus[3])
    if index > 40:
        cycles = (index - 4) // 3
        remainder = (index - 4) % 3
        atk = 3 + (cycles + 1) * 3 + (3 if remainder >= 1 else 0)
        def_b = 1 + cycles + 1 + (1 if remainder >= 2 else 0)
        hp = 1 + cycles * 3 + (3 if remainder >= 0 else 0)
        return (atk, def_b, hp)
    return (0, 0, 0)
