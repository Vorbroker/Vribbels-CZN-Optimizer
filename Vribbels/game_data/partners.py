"""
Partner card data and related functions for CZN.
Contains partner definitions, stats, passives, and helper functions.
"""

# Default partner data for unknown partners
DEFAULT_PARTNER = {
    "name": "Unknown",
    "grade": 3,
    "class": "Controller",
    "passive_name": "Unknown Passive",
    "passive_desc": "Unknown passive effect.",
    "values": {},
    "stats": {},
    "ego_name": "Unknown Skill",
    "ego_cost": 2,
    "ego_desc": "Unknown effect.",
}

# Unified partner card data: res_id -> all partner information
# Contains: name, grade, class, passive_name, passive_desc, values, stats, ego_name, ego_cost, ego_desc
# Note: Values marked with # EST are estimated (linear interpolation) - update when real data is available
PARTNERS = {
    20001: {
        "name": "Arwen",
        "grade": 4,
        "class": "Controller",
        "passive_name": "Starshine Intellect",
        "passive_desc": "The assigned combatant's HP and healing are increased by {HP%}%.\nAt the start of the turn, gain [Ponopoko's Cheer] equal to the number of enemies with attack intentions.\n[Ponopoko's Cheer]: Incoming Damage is reduced by {DR%}%. Upon activation, remove Ponopoko's Cheer (stacks up to 3 times).",
        "values": {
            "HP%": (8, 9, 10, 11, 12),
            "DR%": (10, 13, 15, 18, 20),
        },
        "stats": {"HP%": (8, 9, 10, 11, 12)},
        "ego_name": "Pokopo Ponpon!",
        "ego_cost": 3,
        "ego_desc": "Heal 200%. Apply 1 Damage Reduction.",
    },
    20003: {
        "name": "Alyssa",
        "grade": 4,
        "class": "Controller",
        "passive_name": "Alchemical Fruits",
        "passive_desc": "The assigned combatant's Defense is increased by {DEF%}%.\nAt the end of battle, recover {heal}% Health.",
        "values": {
            "DEF%": (12, 15, 18, 21, 24),
            "heal": (3, 3.8, 4.5, 5.3, 6),
        },
        "stats": {"DEF%": (12, 15, 18, 21, 24)},
        "ego_name": "Vitality Boosting Potion",
        "ego_cost": 2,
        "ego_desc": "Heal 100%. When in an Injured state, increase Healing Amount by 50%. 1 Morale for 1 turn.",
    },
    20005: {
        "name": "Eishlen",
        "grade": 5,
        "class": "Vanguard",
        "passive_name": "Arcane Wave",
        "passive_desc": "The assigned combatant's Health and shield gain are increased by {HP%}%.\nWhen the assigned Combatant gains Counterattack for the first time, +{Counter%}%.",
        "values": {
            "HP%": (8, 10, 12, 14, 16),
            "Counter%": (15, 19, 23, 27, 30),
        },
        "stats": {},
        "ego_name": "Innos's Guardian",
        "ego_cost": 4,
        "ego_desc": "100% shield. At the end of the turn, retain 50% of Shield.",
    },
    20006: {
        "name": "Nyx",
        "grade": 5,
        "class": "Controller",
        "passive_name": "Resonance",
        "passive_desc": "The assigned combatant's HP and healing are increased by {HP%}%.\nWhen the assigned combatant Draws for the first time each turn using an ability, {DMG%}% Damage dealt by allies for 1 turn.",
        "values": {
            "HP%": (8, 10, 12, 14, 16),
            "DMG%": (8, 10, 12, 14, 16),
        },
        "stats": {"HP%": (8, 10, 12, 14, 16)},
        "ego_name": "Errante Hurricane",
        "ego_cost": 4,
        "ego_desc": "Discard up to 3 cards, then Draw +1 cards equal to the number discarded.",
    },
    20007: {
        "name": "Akad",
        "grade": 4,
        "class": "Hunter",
        "passive_name": "Self Defense",
        "passive_desc": "The damage of the combatant's Bullet cards increases by {BulletDMG%}%.\nWhen the combatant lands their first critical hit, Bullet card damage increases by {BulletDMG2%}% for 1 turn.",
        "values": {
            "BulletDMG%": (10, 13, 15, 18, 20),
            "BulletDMG2%": (12, 15, 18, 21, 24),
        },
        "stats": {},
        "ego_name": "What I Wished to Protect",
        "ego_cost": 2,
        "ego_desc": "For 1 turn, +25% Critical Chance of Designated Combatants's Attack cards.",
    },
    20008: {
        "name": "Anteia",
        "grade": 5,
        "class": "Psionic",
        "passive_name": "Clairvoyance",
        "passive_desc": "The assigned combatant's HP and damage are increased by {HP%}%.\nWhen a card is created for the first time by the assigned Combatant each turn, +{CardDMG%}% Damage Amount to Attack Cards for 1 turn.",
        "values": {
            "HP%": (8, 10, 12, 14, 16),
            "CardDMG%": (8, 10, 12, 14, 16),
        },
        "stats": {"HP%": (8, 10, 12, 14, 16)},
        "ego_name": "Scholarly Measures",
        "ego_cost": 2,
        "ego_desc": "180% Damage to all enemies. 1 Vulnerable.",
    },
    20009: {
        "name": "Zeta",
        "grade": 5,
        "class": "Vanguard",
        "passive_name": "Deadly Poison",
        "passive_desc": "The Defense-Based Damage of the assigned combatant's Instinct cards is increased by {InstDMG%}%.\nThe assigned Combatant's Defense-Based Damage and Shield Amount for the Celestial card becomes +{CelestialBonus%}%.",
        "values": {
            "InstDMG%": (15, 19, 23, 27, 31),
            "CelestialBonus%": (25, 32, 38, 44, 50),
        },
        "stats": {},
        "ego_name": "Undertaking the Mission",
        "ego_cost": 2,
        "ego_desc": "200% Defense-Based Damage. Draws 1 highest-cost card.",
    },
    20010: {
        "name": "Nakia",
        "grade": 3,
        "class": "Ranger",
        "passive_name": "Hot-Blooded Soldier",
        "passive_desc": "The assigned combatant's Attack is increased by {ATK%}%.\nWhen an ally defeats an enemy, gain 1 [Backline Support].\n[Backline Support]: {DMG%}% Damage of 1 attack card. Upon activation, Backline Support is reduced by 1 (up to 3 stacks).",
        "values": {
            "ATK%": (8, 10, 12, 14, 16),
            "DMG%": (10, 13, 15, 18, 20),
        },
        "stats": {
            "ATK%": (8, 10, 12, 14, 16),
        },
        "ego_name": "Powerful Shot",
        "ego_cost": 2,
        "ego_desc": "Deal 200% Damage.",
    },
    20011: {
        "name": "Daisy",
        "grade": 4,
        "class": "Ranger",
        "passive_name": "Dowsing",
        "passive_desc": "The assigned combatant's Extra Attack damage is increased by {Extra DMG%}%.\nWhen the assigned combatant Draws for the first time each turn using an ability, there is a {MChance%}% chance to gain 1 Morale for 1 turn.",
        "values": {
            "Extra DMG%": (10, 13, 15, 18, 20),
            "MChance%": (20, 25, 30, 35, 40),
        },
        "stats": {
            "Extra DMG%": (10, 13, 15, 18, 20),
        },
        "ego_name": "Commencing Detection!",
        "ego_cost": 2,
        "ego_desc": "Gain 180% Shield. Gain 1 Morale for 1 turn.",
    },
    20012: {
        "name": "Zatera",
        "grade": 3,
        "class": "Psionic",
        "passive_name": "Fortune Telling",
        "passive_desc": "The assigned combatant's Attack is increased by {ATK%}%.\nWhen Injured, at the end of battle, recover {skill}% Health.",
        "values": {
            "ATK%": (8, 10, 12, 14, 16),
            "skill": (4, 5, 6, 7, 8),
        },
        "stats": {"ATK%": (8, 10, 12, 14, 16)},
        "ego_name": "Flower of Memory",
        "ego_cost": 2,
        "ego_desc": "Gain 200% Shield.",
    },
    20013: {
        "name": "Raidel",
        "grade": 3,
        "class": "Vanguard",
        "passive_name": "Strategic Analysis",
        "passive_desc": "The combatant's max Health increases by {HP%}%.\nIf the combatant is in Counterattack state, their Defense-Based Damage increases by {DEFDAM%}%.",
        "values": {
            "HP%": (8, 10, 12, 14, 16),
            "DEFDAM%": (8, 10, 12, 14, 16),
        },
        "stats": {"HP%": (8, 10, 12, 14, 16)},
        "ego_name": "Analyze Weakness",
        "ego_cost": 2,
        "ego_desc": "Gain 100% Shield. Gain 1 Counterattack.",
    },
    20014: {
        "name": "Serithea",
        "grade": 5,
        "class": "Hunter",
        "passive_name": "Ensemble",
        "passive_desc": "The Critical Chance of the combatant's attack cards increases by {CRate%}%.\nWhen the assigned combatant's attack results in a Critical Hit, +{CDmg%}% Critical Damage. Stacks up to 5 times.",
        "values": {
            "CRate%": (8, 10, 12, 14, 16),
            "CDmg%": (3, 3.5, 4, 4.5, 5),
        },
        "stats": {},
        "ego_name": "Crimson Romance",
        "ego_cost": 3,
        "ego_desc": "250% Damage. 2 Vulnerable.",
    },
    20015: {
        "name": "Douglas",
        "grade": 3,
        "class": "Striker",
        "passive_name": "Guard",
        "passive_desc": "The assigned combatant's Attack is increased by {ATK%}%.\nAt the start of battle, Damage dealt by the assigned combatant increases by {DMG%}% for 1 turn.",
        "values": {
            "ATK%": (8,10,12,14,16),
            "DMG%": (8,10,12,14,16),
        },
        "stats": {"ATK%": (8,10,12,14,16)
        },
        "ego_name": "Giant Bazooka",
        "ego_cost": 2,
        "ego_desc": "120% Damage to all enemies",
    },
    20016: {
        "name": "Yuri",
        "grade": 3,
        "class": "Hunter",
        "passive_name": "Cantrip",
        "passive_desc": "The assigned combatant's Attack is increased by {ATK%}%.\nUpon the first shuffle, the assigned combtant's damage dealt is increased by {DMG%}%.",
        "values": {
            "ATK%": (8,10,12,14,16),
            "DMG%": (8,10,12,14,16)
        },
        "stats": {"ATK%": (8,10,12,14,16)},
        "ego_name": "Drone Deployment",
        "ego_cost": 3,
        "ego_desc": "Draw 2",
    },
    20019: {
        "name": "Priscilla",
        "grade": 5,
        "class": "Striker",
        "passive_name": "Arachnid Domain",
        "passive_desc": "The assigned combatant's HP and damage are increased by {HP%}%.\n+{RavagedDMG%}% Damage dealt by the assigned Combatant to targets in a Ravaged state.",
        "values": {
            "HP%": (8, 10, 12, 14, 16),
            "RavagedDMG%": (25, 32, 38, 44, 50),
        },
        "stats": {"HP%": (8, 10, 12, 14, 16)},
        "ego_name": "Arachnid Web",
        "ego_cost": 2,
        "ego_desc": "Deal 250% Damage. Apply Weakness Attack to 1 assigned combatant's random Attack cards in hand.",
    },
    20024: {
        "name": "Wilhelmina",
        "grade": 4,
        "class": "Vanguard",
        "passive_name": "Battle Command",
        "passive_desc": "The assigned combatant's Defense is increased by {DEF%}%.\nWhen the assigned combatant targets a Vulnerable enemy, {DEFDAM%}% Defense-based Damage of Attack cards.",
        "values": {
            "DEF%": (12, 15, 18, 21, 24),
            "DEFDAM%": (10, 13, 15, 18, 20),
        },
        "stats": {"DEF%": (12, 15, 18, 21, 24)},
        "ego_name": "Tactical Command",
        "ego_cost": 2,
        "ego_desc": "For 1 turn, gain 2 Morale.\nFor 1 turn, gain 1 Fortitude.",
    },
    20025: {
        "name": "Rosaria",
        "grade": 4,
        "class": "Hunter",
        "passive_name": "Financial Support",
        "passive_desc": "The assigned combatant's Extra Damage is increased by {Extra DMG}%.\nWhen the assigned combatant uses an Upgrade or Skill card, {MChance%}% chance to gain 1 Morale for 1 turn.",
        "values": {
            "Extra DMG": (10, 13, 15, 18, 20),
            "MChance%": (25, 32, 38, 44, 50),
        },
        "stats": {"Extra DMG%": (10, 13, 15, 18, 20)},
        "ego_name": "Security Team, Requesting Support!",
        "ego_cost": 2,
        "ego_desc": "Draw 1 Enhanced Card(s).\nIf there are no Enhance Cards in the Draw Pile, Draw 1 Card.",
    },
    20026: {
        "name": "Yvonne",
        "grade": 3,
        "class": "Controller",
        "passive_name": "Bless",
        "passive_desc": "The assigned combatant's Defense is increased by {DEF%}%.\nIf the combatant ends the turn without using an attack card, Heal {heal%}% at the start of the next turn.",
        "values": {
            "DEF%": (8, 10, 12, 14, 16),
            "heal%": (30, 38, 45, 53, 60),
        },
        "stats": {"DEF%": (8, 10, 12, 14, 16)},
        "ego_name": "Consecration",
        "ego_cost": 2,
        "ego_desc": "Heal 100%. For 1 turn, gain 1 Fortitude.",
    },
    20027: {
        "name": "Eloise",
        "grade": 4,
        "class": "Psionic",
        "passive_name": "Technical Support",
        "passive_desc": "The combatant's attack card damage increases by {atkcard%}%.\nWhen the combatant first Exhausts a card or first gains a Status Ailment card, their attack card damage increases by {atkcard%2}% for 1 turn.",
        "values": {
            "atkcard%": (10, 13, 15, 18, 20),
            "atkcard%2": (12, 15, 18, 21, 24),
        },
        "stats": {},
        "ego_name": "Activate Defense Module",
        "ego_cost": 3,
        "ego_desc": "For 1 turn, when a card is Exhausted, apply 1 Weaken to a random enemy.",
    },
    20030: {
        "name": "Kiara",
        "grade": 5,
        "class": "Hunter",
        "passive_name": "Analyze Weakness",
        "passive_desc": "If there are 10 or more cards in the Graveyard, the assigned combatant's attack card damage is increased by {GraveDMG%}%.\nWhen a card is discarded for the first time by the assigned Combatant each turn, +{DiscardDMG%}% Damage Amount to Attack Cards for 1 turn.",
        "values": {
            "GraveDMG%": (15, 19, 23, 27, 30),
            "DiscardDMG%": (25, 32, 38, 44, 50),
        },
        "stats": {},
        "ego_name": "Lumina Explosion",
        "ego_cost": 3,
        "ego_desc": "200% Damage. +20% Damage by the number of cards in Graveyard.",
    },
    20032: {
        "name": "Rachel",
        "grade": 4,
        "class": "Vanguard",
        "passive_name": "Replenish Energy",
        "passive_desc": "The assigned combatant's skill card shield gain is increased by {shieldgain%}%.\nWhen the assigned combatant gains Shield, {counterchance%}% chance to gain 1 Counterattack.",
        "values": {
            "shieldgain%": (10, 13, 15, 18, 20),
            "counterchance%": (20, 25, 30, 35, 40),
        },
        "stats": {},
        "ego_name": "Colonel Hamburger!",
        "ego_cost": 2,
        "ego_desc": "Gain 100% Shield. Draw 1 Card.",
    },
    20033: {
        "name": "Lillian",
        "grade": 4,
        "class": "Striker",
        "passive_name": "Poltergeist",
        "passive_desc": "The assigned combatant's attack cards with a cost of 1 or less deal {atkDAM%}% damage.\nWhen the assigned combatant uses a Skill card, {atkDAM%2}% attack card damage for 1 turn. Stacks up to 3 times.",
        "values": {
            "atkDAM%": (10, 13, 15, 18, 20),
            "atkDAM%2": (10, 13, 15, 18, 20),
        },
        "stats": {},
        "ego_name": "Light of Judgement",
        "ego_cost": 3,
        "ego_desc": "Deal 100% Damage to all enemies. Draw 1 Attack card(s) from the assigned combatant with cost of less than or equal to 1.",
    },
    20035: {
        "name": "Ritochka",
        "grade": 4,
        "class": "Striker",
        "passive_name": "Construction Support",
        "passive_desc": "The assigned Combatant's attack cards with a cost of 2 or more deal +{Cost2DMG%}% damage.\nAt the start of the turn, 1 of the assigned Combatant's attack cards gains +{CostScaleDMG%}% damage for every point of the total cost of attack cards.",
        "values": {
            "Cost2DMG%": (10, 13, 15, 18, 20),
            "CostScaleDMG%": (5, 7, 8, 9, 10),
        },
        "stats": {},
        "ego_name": "Workplace hazards ahead!",
        "ego_cost": 2,
        "ego_desc": "For 1 turn, 3 Morale.",
    },
    20036: {
        "name": "Carroty",
        "grade": 4,
        "class": "Hunter",
        "passive_name": "Super Carrot Power!",
        "passive_desc": "At the start of the turn, the damage of 1 attack card increases by {cardATK%}% for the combatant.\nWhen the combatant generates a card for the first time, their attack card damage increases by {cardATK%2}% for 1 turn.",
        "values": {
            "cardATK%": (10, 13, 15, 18, 20),
            "cardATK%2": (10, 13, 15, 18, 20),
        },
        "stats": {},
        "ego_name": "Eating Soft Carrots",
        "ego_cost": 2,
        "ego_desc": "Increase Damage Amount of cards created by Designated Combatants's ability by 20% for 1 turn.",
    },
    20039: {
        "name": "Tina",
        "grade": 5,
        "class": "Ranger",
        "passive_name": "Communication Support",
        "passive_desc": "Order attribute's Extra Attack damage increase by {OrderExtra%}%.\n+{TargetExtra%}% Extra Attack damage from Targeting Attack Cards.",
        "values": {
            "OrderExtra%": (15, 19, 23, 27, 31),
            "TargetExtra%": (25, 32, 38, 44, 50),
        },
        "stats": {},
        "ego_name": "Target confirmed, initiating support!",
        "ego_cost": 2,
        "ego_desc": "Draw 1. Increase the combatant's Extra Attack damage by 30% for 1 turn.",
    },
    30044: {
        "name": "Westmacott",
        "grade": 5,
        "class": "Striker",
        "passive_name": "Gleaming Deduction",
        "passive_desc": "Attack Cards of the assigned Combatant drawn gain +{DrawnDMG%}% Damage Amount for 1 turn.\nIncreases Damage Amount of the assigned Combatant's cards that have Inspiration by {InspireDMG%}%.",
        "values": {
            "DrawnDMG%": (25, 32, 38, 44, 50),
            "InspireDMG%": (10, 13, 15, 18, 20),
        },
        "stats": {},
        "ego_name": "Clue Spotted",
        "ego_cost": 3,
        "ego_desc": "Move 1 card from hand to Draw Pile. Draw 1 assigned Combatant cards.",
    },
    30045: {
        "name": "Asteria",
        "grade": 5,
        "class": "Striker",
        "passive_name": "Starshine-piercing Lighthouse",
        "passive_desc": "The assigned combatant's attack cards with a cost of 2 or more deal +{Cost2DMG%}% damage.\nIncrease Damage Amount of Pulverize cards of the assigned Combatant by {PulverizeDMG%}%.",
        "values": {
            "Cost2DMG%": (25, 32, 38, 44, 50),
            "PulverizeDMG%": (10, 13, 15, 18, 20),
        },
        "stats": {},
        "ego_name": "Light of Ark",
        "ego_cost": 2,
        "ego_desc": "+20% Damage of the next Attack card used by the assigned Combatant for the total cost of all cards in the hand (Max 10).",
    },
    30046: {
        "name": "Itsuku",
        "grade": 5,
        "class": "Psionic",
        "passive_name": "Tranquil Marker",
        "passive_desc": "The assigned combatant's Attack is increased by {ATK%}%. Every time the assigned Combatant's cards stack, increases Damage Amount of Attack Cards by {StackDMG%}%. Can stack up to 3 times.\nEvery time 1 Attack Card used by the assigned Combatant deals 3 Hits, inflicts {FixedDMG%}% Fixed Damage to the target.",
        "values": {
            "ATK%": (8, 10, 12, 14, 16),
            "StackDMG%": (5, 7, 8, 9, 10),
            "FixedDMG%": (30, 38, 45, 53, 60),
        },
        "stats": {"ATK%": (8, 10, 12, 14, 16)},
        "ego_name": "Moonlit Leisure",
        "ego_cost": 4,
        "ego_desc": "200% Damage to all enemies.\n 1 Fierce Winds.",
    },
    30051: {
        "name": "Marin",
        "grade": 5,
        "class": "Ranger",
        "passive_name": "Raging Wave",
        "passive_desc": "The Extra Attack damage of cards generated by the assigned combatant's abilities increases by {ExtraDMG%}%.\nWhen a Skill Card is used for the first time by the assigned Combatant each turn, +{SkillExtra%}% Damage Amount to Extra Attacks for 1 turn.",
        "values": {
            "ExtraDMG%": (15, 19, 23, 27, 30),
            "SkillExtra%": (25, 32, 38, 44, 50),
        },
        "stats": {},
        "ego_name": "Azure Fury",
        "ego_cost": 3,
        "ego_desc": "200% Damage to all enemies. Draw 1 skill card.",
    },
    30052: {
        "name": "Noel",
        "grade": 5,
        "class": "Controller",
        "passive_name": "Hymn of Blessing",
        "passive_desc": "Increase Damage, Shield Gain, and Heal Amounts of the assigned Combatants Retain Cards by {RetainBonus%}%.\nAt the end of the turn, deal Fixed Damage to all enemies equal to {FixedDMG%}% for each retained card of the assigned combatant. +5% Damage for enemies with the Instinct attribute.",
        "values": {
            "RetainBonus%": (15, 19, 23, 27, 30),
            "FixedDMG%": (15, 19, 23, 27, 30),
        },
        "stats": {},
        "ego_name": "Legato of Faith",
        "ego_cost": 3,
        "ego_desc": "Heal 100%. Activate the Retain effect of all cards held by the assigned combatant.",
    },
    30054: {
        "name": "Erica",
        "grade": 5,
        "class": "Vanguard",
        "passive_name": "No Speeding!",
        "passive_desc": "The assigned combatant's Counterattack damage increases by {CounterDMG%}%.\nWhen the assigned Combatant uses a Skill or Upgrade Card, there is a {CounterChance%}% chance to gain Counterattack.",
        "values": {
            "CounterDMG%": (15, 19, 23, 27, 30),
            "CounterChance%": (50, 63, 75, 88, 100),
        },
        "stats": {},
        "ego_name": "Crackdown Beam Bombardment",
        "ego_cost": 2,
        "ego_desc": "200% Defense-based Damage to all enemies.\n 1 Counterattack.\n If any enemy's Anticipated Action is attack, 1 Counterattack.",
    },
    30076: {
        "name": "Peko",
        "grade": 5,
        "class": "Hunter",
        "passive_name": "Peko's Multi-Purpose Kit",
        "passive_desc": "Increase the assigned Combatant's Attack by {ATK%}%. When the assigned Combatant's card Moves from the Graveyard to hand, gain 1 Repairs Complete. Repairs Complete: +{RepairsDMG%}% Damage Amount to the assigned Combatant's Attack Cards (Max-3) Increase Damage Amount of the assigned Combatant's Attack Cards that are used against Ravaged targets by {RavagedDMG%}%.",
        "values": {
            "ATK%": (8, 10, 12, 14, 16),
            "RepairsDMG%": (10, 13, 15, 18, 20),
            "RavagedDMG%": (15, 19, 23, 27, 30),
        },
        "stats": {"ATK%": (8, 10, 12, 14, 16)},
        "ego_name": "Overclock Beacon",
        "ego_cost": 3,
        "ego_desc": "When an ally inflicts Ravage, 1 Overclock to the assigned Combatant (1 per turn).",
    },
}

# Base stats by grade and class at level 60
# Offensive classes (Hunter, Psionic, Ranger, Striker): High ATK, low DEF
# Defensive classes (Controller, Vanguard): Low ATK, high DEF
PARTNER_CLASS_STATS = {
    # 3-star classes
    (3, "Hunter"):     {"atk": 89, "def": 5, "hp": 85},
    (3, "Psionic"):    {"atk": 89, "def": 5, "hp": 85},
    (3, "Ranger"):     {"atk": 89, "def": 5, "hp": 85},
    (3, "Striker"):    {"atk": 89, "def": 5, "hp": 85},
    (3, "Controller"): {"atk": 5, "def": 36, "hp": 85},
    (3, "Vanguard"):   {"atk": 5, "def": 36, "hp": 85},
    # 4-star classes
    (4, "Hunter"):     {"atk": 101, "def": 5, "hp": 95},
    (4, "Psionic"):    {"atk": 101, "def": 5, "hp": 95},
    (4, "Ranger"):     {"atk": 101, "def": 5, "hp": 95},
    (4, "Striker"):    {"atk": 101, "def": 5, "hp": 95},
    (4, "Controller"): {"atk": 5, "def": 40, "hp": 95},
    (4, "Vanguard"):   {"atk": 5, "def": 40, "hp": 95},
    # 5-star classes
    (5, "Hunter"):     {"atk": 111, "def": 5, "hp": 105},
    (5, "Psionic"):    {"atk": 111, "def": 5, "hp": 105},
    (5, "Ranger"):     {"atk": 111, "def": 5, "hp": 105},
    (5, "Striker"):    {"atk": 111, "def": 5, "hp": 105},
    (5, "Controller"): {"atk": 5, "def": 44, "hp": 105},
    (5, "Vanguard"):   {"atk": 5, "def": 44, "hp": 105},
}


def get_partner(res_id: int) -> dict:
    """Get partner data by res_id, returning DEFAULT_PARTNER if not found."""
    return PARTNERS.get(res_id, DEFAULT_PARTNER)


def get_value_for_ego_level(values_tuple: tuple, limit_break: int) -> float:
    """Get the value from a 5-element tuple based on limit_break (0-4)."""
    if not values_tuple or len(values_tuple) < 5:
        return 0
    index = max(0, min(4, limit_break))  # Clamp to 0-4
    return values_tuple[index]


def get_partner_base_stats(res_id: int) -> dict:
    """Get base stats for a partner card based on its grade and class."""
    partner = get_partner(res_id)
    grade = partner.get("grade", 3)
    partner_class = partner.get("class", "Controller")
    base = PARTNER_CLASS_STATS.get((grade, partner_class), {"atk": 85, "def": 5, "hp": 90})
    return base


def get_partner_stats(res_id: int, level: int) -> dict:
    """Calculate partner card stats based on level.
    Stats scale linearly from base values to max at level 60."""
    base = get_partner_base_stats(res_id)
    scale = level / 60.0
    return {
        "atk": int(base["atk"] * scale),
        "def": int(base["def"] * scale),
        "hp": int(base["hp"] * scale),
    }


def get_partner_passive_stats(res_id: int, limit_break: int) -> dict:
    """Get unconditional passive stat bonuses for a partner card.
    Returns stat bonuses based on limit_break (0=E0 through 4=E4)."""
    partner = get_partner(res_id)
    stats = {}
    for stat_name, values_tuple in partner.get("stats", {}).items():
        stats[stat_name] = get_value_for_ego_level(values_tuple, limit_break)
    return stats


def format_passive_description(res_id: int, limit_break: int) -> str:
    """Format the passive description with values based on limit_break."""
    partner = get_partner(res_id)

    desc = partner.get("passive_desc", "Unknown passive effect.")
    values = partner.get("values", {})

    # Replace each placeholder with the value for this ego level
    for placeholder, values_tuple in values.items():
        current_val = get_value_for_ego_level(values_tuple, limit_break)
        # Format as integer if whole number, otherwise one decimal
        if current_val == int(current_val):
            val_str = str(int(current_val))
        else:
            val_str = f"{current_val:.1f}"
        desc = desc.replace("{" + placeholder + "}", val_str)

    return desc


def get_partner_passive_info(res_id: int, limit_break: int) -> dict:
    """Get full passive information for display.
    Returns dict with passive_name, formatted description, ego_name, ego_cost, ego_desc."""
    partner = get_partner(res_id)

    return {
        "passive_name": partner.get("passive_name", "Unknown"),
        "passive_desc": format_passive_description(res_id, limit_break),
        "ego_name": partner.get("ego_name", "Unknown"),
        "ego_cost": partner.get("ego_cost", 0),
        "ego_desc": partner.get("ego_desc", "Unknown effect."),
    }
