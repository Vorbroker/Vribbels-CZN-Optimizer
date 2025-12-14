"""
Memory Fragment set definitions for CZN.
Contains set bonus information and derived lists.
"""

# Set definitions
SETS = {
    6: {"name": "Conqueror's Aspect", "pieces": 4, "bonus": "+35% Crit DMG of 1-cost cards", "type": "conditional"},
    7: {"name": "Tetra's Authority", "pieces": 2, "bonus": "+12% Defense", "type": "stat", "stat": "DEF%", "value": 12},
    8: {"name": "Healer's Journey", "pieces": 2, "bonus": "+12% Max HP", "type": "stat", "stat": "HP%", "value": 12},
    9: {"name": "Black Wing", "pieces": 2, "bonus": "+12% Attack", "type": "stat", "stat": "ATK%", "value": 12},
    10: {"name": "Seth's Scarab", "pieces": 2, "bonus": "+20% Basic Card DMG", "type": "conditional"},
    11: {"name": "Executioner's Tool", "pieces": 2, "bonus": "+25% Crit Damage", "type": "stat", "stat": "Crit DMG", "value": 25},
    12: {"name": "Instinctual Growth", "pieces": 4, "bonus": "+20% Instinct DMG (4+ cards)", "type": "conditional"},
    15: {"name": "Bullet of Order", "pieces": 4, "bonus": "+10% Order DMG after Attack (2 max)", "type": "conditional"},
    16: {"name": "Offering of the Void", "pieces": 4, "bonus": "+20% Void DMG after Exhaust (1 turn)", "type": "conditional"},
    18: {"name": "Spark of Passion", "pieces": 4, "bonus": "+20% Passion DMG after Upgrade (5 times)", "type": "conditional"},
    19: {"name": "Cursed Corpse", "pieces": 2, "bonus": "+10% DMG to Agony Inflicted", "type": "conditional"},
    20: {"name": "Line of Justice", "pieces": 4, "bonus": "+20% Crit Rate for 2+ cost", "type": "conditional"},
    22: {"name": "Orb of Inhibition", "pieces": 4, "bonus": "+10% Void DMG for 1 turn after hitting 2 times with Attack (2 max)", "type": "conditional"},
    23: {"name": "Judgment's Flames", "pieces": 4, "bonus": "+50% Instinct DMG to Ravaged targets", "type": "conditional"},
}

TWO_PIECE_SETS = [sid for sid, s in SETS.items() if s["pieces"] == 2]
FOUR_PIECE_SETS = [sid for sid, s in SETS.items() if s["pieces"] == 4]
