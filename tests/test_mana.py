import pytest
from mtg_mana_simulator.mana import ManaCost, generate_mana_combinations, calculate_cmc, parse_mana_cost, ManaSymbol

@pytest.fixture
def parser():
    return parse_mana_cost

def test_phyrexian_hybrid_mana(parser):
    result = parse_mana_cost("{1}{B/G/P}")
    assert result.has_hybrid
    assert result.phyrexian > 0
    assert "1B1G1P" in ''.join(sorted(result.possible_combinations))

def test_generic_hybrid_mana(parser):
    result = parse_mana_cost("{H}{G/W}")
    assert result.has_hybrid
    assert len(result.possible_combinations) > 1
    assert any("G" in combo for combo in result.possible_combinations)
    assert any("W" in combo for combo in result.possible_combinations)

def test_multiple_phyrexian_mana(parser):
    result = parse_mana_cost("{C/P}{G/P}{W/U/P}")
    assert result.phyrexian > 0
    assert result.has_hybrid
    assert len(result.possible_combinations) > 1

def test_mixed_hybrid_mana(parser):
    result = parse_mana_cost("{W/G}{B/U}")
    assert result.has_hybrid
    assert len(result.possible_combinations) == 4
    assert all(len(combo) == 2 for combo in result.possible_combinations)

def test_colorless_hybrid_combinations(parser):
    result = parse_mana_cost("{C/W}{C/U}{C/B}{C/R}{C/G}")
    assert result.has_hybrid
    assert result.colorless == 0  # Since all are hybrid
    assert len(result.possible_combinations) > 1

def test_snow_mana(parser):
    result = parse_mana_cost("{S}{S}{R}")
    assert result.snow == 2
    assert result.red == 1

def test_special_mana_symbols(parser):
    result = parse_mana_cost("{D}{½}")
    assert result.land_drop == 1
    assert result.generic == 0.5

def test_x_spell_cost(parser):
    result = parse_mana_cost("{X}{R}")
    assert result.has_any_xyz
    assert result.red == 1
    assert result.cmc == 1  # X counts as 0 for CMC
