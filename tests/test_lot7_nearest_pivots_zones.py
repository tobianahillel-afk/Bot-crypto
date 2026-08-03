from crypto_quant_bot.market_state.nearest import nearest_pivots, nearest_zones


def test_nearest_pivots_respects_usable_from_and_limit():
    pivots = [
        {"pivot_id": "future", "price": 100.0, "usable_from": "2026-05-25T01:00:00Z"},
        {"pivot_id": "a", "price": 99.0, "usable_from": "2026-05-25T00:00:00Z"},
        {"pivot_id": "b", "price": 101.0, "usable_from": "2026-05-25T00:00:00Z"},
        {"pivot_id": "c", "price": 103.0, "usable_from": "2026-05-25T00:00:00Z"},
        {"pivot_id": "d", "price": 104.0, "usable_from": "2026-05-25T00:00:00Z"},
    ]
    result = nearest_pivots(pivots, 100.0, "2026-05-25T00:30:00Z")
    assert len(result) == 3
    assert {row["pivot_id"] for row in result} <= {"a", "b", "c", "d"}
    assert "future" not in {row["pivot_id"] for row in result}


def test_nearest_zones_respects_usable_from_and_limit():
    zones = [
        {"zone_id": "future", "center_price": 100.0, "usable_from": "2026-05-25T01:00:00Z"},
        {"zone_id": "a", "center_price": 99.0, "usable_from": "2026-05-25T00:00:00Z"},
        {"zone_id": "b", "center_price": 101.0, "usable_from": "2026-05-25T00:00:00Z"},
        {"zone_id": "c", "center_price": 103.0, "usable_from": "2026-05-25T00:00:00Z"},
        {"zone_id": "d", "center_price": 104.0, "usable_from": "2026-05-25T00:00:00Z"},
    ]
    result = nearest_zones(zones, 100.0, "2026-05-25T00:30:00Z")
    assert len(result) == 3
    assert "future" not in {row["zone_id"] for row in result}
