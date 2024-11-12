import os
from typing import Optional, List, Any
import requests
import json
from pydantic import BaseModel
import itertools
from mtg_mana_simulator.logger import logger

symbology_url = "https://api.scryfall.com/symbology" # GET - Get the mana and color symbols that Scryfall uses

class ManaSymbol(BaseModel):
    # As in https://scryfall.com/docs/api/colors, minus the "object" field
    symbol: str
    svg_uri: str
    loose_variant: Optional[str]
    english: str
    transposable: bool
    represents_mana: bool
    appears_in_mana_costs: bool
    mana_value: Optional[float]
    hybrid: bool
    phyrexian: bool
    cmc: Optional[float]
    funny: bool
    colors: List[str]
    gatherer_alternates: Optional[List[str]]

class ManaCost(BaseModel):
    # These 5+1+1 fields are only used for non-hybrid mana costs.
    white: float = 0    # W
    blue: float = 0     # U
    black: float = 0    # B
    red: float = 0      # R
    green: float = 0    # G
    colorless: float = 0# C  Colorless is a separate category from generic
    generic: float = 0  # Generic - digits in the mana cost, not including X/Y/Z

    cmc: float = 0      # Converted Mana Cost
    monocolored: bool
    multicolored: bool = False
    phyrexian: float = 0
    has_hybrid: bool = False
    has_any_xyz: bool = False
    land_drop: float = 0
    snow: float = 0
    hybrids: Optional[List[str]]
    possible_combinations: Optional[List[str]] = None


def generate_mana_combinations(mana_cost: str) -> List[str]:
    """Generate all possible combinations for a mana cost"""

    def parse_mana_symbol(symbol):
        if symbol in ['X', 'Y', 'Z', 'S', 'D']:
            return (symbol,)  # Keep special symbols as-is
        if 'H' in symbol:
            return ('P', 'W', 'U', 'B', 'R', 'G')
        elif '/' in symbol:
            if '2' in symbol:
                return ('2', symbol.split('/')[-1])
            options = symbol.split('/')
            return tuple(options)
        return (symbol,)

    cleaned = mana_cost.replace('}{', ' ').strip('{}')
    symbols = cleaned.split()
    symbol_options = [parse_mana_symbol(symbol) for symbol in symbols]
    combinations = list(itertools.product(*symbol_options))
    raw_combos = [''.join(combo) for combo in combinations]
    # Sum all the numbers in each combination
    # 22RC and 2R2C are essentially the same cost, one combination: 4RC
    # Deduplicate the combinations
    unique_combos = set()
    for i, combo in enumerate(raw_combos):
        # If there is a number in the combination, sum all the numbers, remove the numbers and add the sum
        if any(char.isdigit() for char in combo):
            sum_numbers = sum(int(char) for char in combo if char.isdigit())
            combo = ''.join(char for char in combo if not char.isdigit())
            sum_numbers = str(sum_numbers)
            combo = combo + sum_numbers if sum_numbers != '0' else combo
        combo = ''.join(sorted(combo))
        unique_combos.add(combo)
    return list(unique_combos)


def calculate_cmc(mana_cost: str) -> float:
    """Calculate the converted mana cost"""
    total_cmc = 0.0
    cleaned = mana_cost.replace('}{', ' ').strip('{}')
    symbols = cleaned.split()

    for symbol in symbols:
        if symbol.isdigit():
            total_cmc += float(symbol)
        elif symbol in ['X', 'Y', 'Z']:
            total_cmc += 0.0  # X, Y, Z count as 0 for CMC calculation
        elif '2/' in symbol:
            total_cmc += 2.0
        elif '/' in symbol:
            total_cmc += 1.0
        elif symbol == '½':
            total_cmc += 0.5
        else:
            total_cmc += 1.0

    return total_cmc


def get_symbology() -> dict:
    """Get the mana and color symbols that Scryfall uses"""
    if os.path.exists('symbology.json'):
        with open('symbology.json', 'r') as f:
            return json.load(f)
    response = requests.get(symbology_url)
    if response.status_code != 200:
        logger.error(f"Failed to get Scryfall symbology: {response.status_code}")
        return {}
    logger.debug(f"Scryfall symbology retrieved: {len(response.json()['data'])} symbols")
    return response.json()


def parse_mana_cost(mana_cost: str) -> ManaCost:
    """Parse a mana cost string into a ManaCost object with all possible combinations"""
    #logger.debug(f"Parsing mana cost: {mana_cost}")

    # Initialize counters
    white = blue = black = red = green = colorless = generic = phyrexian = snow = 0.0
    has_hybrid = False
    hybrid_symbols = []
    land_drop = 0.0
    has_any_xyz = False

    # Remove braces and split into individual symbols
    cleaned = mana_cost.replace('}{', ' ').strip('{}')
    symbols = cleaned.split()

    # Generate all possible combinations
    possible_combinations = generate_mana_combinations(mana_cost)

    # Process each symbol
    for symbol in symbols:
        if symbol.isdigit():
            generic += float(symbol)
        elif symbol in ['X', 'Y', 'Z']:
            generic += 0.0  # X, Y, Z count as 0 for CMC calculation
            has_any_xyz = True
        elif '/' in symbol:
            has_hybrid = True
            hybrid_symbols.append(symbol)
            if 'P' in symbol:
                phyrexian += 1.0
        elif symbol == 'W':
            white += 1.0
        elif symbol == 'U':
            blue += 1.0
        elif symbol == 'B':
            black += 1.0
        elif symbol == 'R':
            red += 1.0
        elif symbol == 'G':
            green += 1.0
        elif symbol == 'C':
            colorless += 1.0
        elif symbol == '½':
            generic += 0.5
        elif symbol == 'H':
            phyrexian += 1.0
            has_hybrid = True
            hybrid_symbols.append(symbol)
        elif symbol == 'S':
            snow += 1.0
        elif symbol == 'D':
            land_drop = 1.0

    # Calculate CMC
    cmc = calculate_cmc(mana_cost)

    # Determine if monocolored or multicolored
    color_count = sum(1 for x in [white, blue, black, red, green] if x > 0)

    # Check possible combinations for additional colors
    if has_hybrid:
        all_colors_in_combinations = set()
        for combo in possible_combinations:
            all_colors_in_combinations.update(c for c in combo if c in 'WUBRG')
        color_count = len(all_colors_in_combinations)

    monocolored = color_count == 1
    multicolored = color_count > 1

    return ManaCost(
        white=white,
        blue=blue,
        black=black,
        red=red,
        green=green,
        colorless=colorless,
        generic=generic,
        cmc=cmc,
        monocolored=monocolored,
        multicolored=multicolored,
        phyrexian=phyrexian,
        has_hybrid=has_hybrid,
        land_drop=land_drop,
        snow=snow,
        has_any_xyz=has_any_xyz,
        hybrids=hybrid_symbols if has_hybrid else None,
        possible_combinations=possible_combinations if has_hybrid else None
    )


def parse_symbology(symbology_json) -> {str: ManaSymbol}:
    """Parse the Scryfall symbology into ManaSymbol objects"""
    mana_symbols = {}
    for symbol in symbology_json['data']:
        if symbol['object'] == 'card_symbol':
            mana_symbols[symbol['symbol']] = ManaSymbol(**symbol)


def parse_mana_symbol(symbol):
    if 'H' in symbol:
        # Generic Phyrexian can be paid by any color or life
        return ('P', 'W', 'U', 'B', 'R', 'G')
    elif '2' in symbol:
        # Handle two generic mana option with one color
        color = symbol[-1]  # extract the last character to get the color
        return ('2', color)
    elif '/' in symbol:
        options = symbol.split('/')
        if 'P' in options:
            # Keep P as an option for Phyrexian mana
            return tuple(options)
        return tuple(options)
    return (symbol,)



