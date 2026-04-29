import json
from pathlib import Path

import pytest
from pydantic import ValidationError

import api.game_data as game_data


@pytest.fixture(autouse=True)
def clear_catalog_cache() -> None:
    game_data.load_catalog_items.cache_clear()
    yield
    game_data.load_catalog_items.cache_clear()


def _write_item(root: Path, subdir: str, filename: str, item: dict) -> Path:
    path = root / subdir / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(item), encoding="utf-8")
    return path


def _base_item(item_id: str, *, name: str | None = None) -> dict:
    return {
        "id": item_id,
        "name": name or item_id.replace("-", " ").title(),
        "category": "gear",
        "description": f"Description for {item_id}.",
        "value_cd": 1,
        "tags": ["test"],
        "schema_version": 1,
    }


def _weapon_item(item_id: str, *, magical: bool = False) -> dict:
    item = _base_item(item_id)
    item["category"] = "weapon"
    item["tags"] = ["weapon"]
    item["knowledge_tag"] = "melee"
    item["application_tag"] = "sword"
    item["base_damage"] = 60
    item["weapon_handedness"] = {"hands": "one"}
    if magical:
        item["tier"] = "T1"
        item["magic_field"] = "elemental"
    return item


def _armor_item(item_id: str) -> dict:
    item = _base_item(item_id)
    item["category"] = "armor"
    item["tags"] = ["armor"]
    item["knowledge_tag"] = "armor"
    item["application_tag"] = "light_armor"
    item["armor_floor"] = 10
    item["armor_ceiling"] = 20
    return item


def _ammunition_item(item_id: str) -> dict:
    item = _base_item(item_id)
    item["category"] = "ammunition"
    item["tags"] = ["ammunition"]
    item["knowledge_tag"] = "ranged"
    item["application_tag"] = "shortbow"
    item["ammo_class"] = "standard"
    item["used_with"] = ["shortbow"]
    item["damage_modifier"] = 0
    return item


def _set_catalog_dir(monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
    monkeypatch.setattr(game_data, "_CATALOG_ITEMS_DIR", path)
    game_data.load_catalog_items.cache_clear()


def test_load_catalog_items_returns_empty_list_when_directory_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_catalog_dir(monkeypatch, tmp_path / "missing")

    assert game_data.load_catalog_items() == []


def test_load_catalog_items_loads_recursively_sorted_by_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_catalog_dir(monkeypatch, tmp_path)
    _write_item(tmp_path, "gear", "zeta.json", _base_item("zeta"))
    _write_item(tmp_path, "weapon", "alpha.json", _weapon_item("alpha"))

    items = game_data.load_catalog_items()

    assert [item["id"] for item in items] == ["alpha", "zeta"]


def test_load_catalog_items_skips_files_starting_with_underscore(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_catalog_dir(monkeypatch, tmp_path)
    _write_item(tmp_path, "gear", "torch.json", _base_item("torch"))
    _write_item(tmp_path, "gear", "_template.json", {"invalid": "template"})

    assert [item["id"] for item in game_data.load_catalog_items()] == ["torch"]


def test_load_catalog_items_raises_validation_error_on_malformed_item(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_catalog_dir(monkeypatch, tmp_path)
    _write_item(tmp_path, "gear", "bad.json", {"id": "bad"})

    with pytest.raises(ValidationError):
        game_data.load_catalog_items()


def test_load_catalog_items_adds_subdir_from_immediate_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_catalog_dir(monkeypatch, tmp_path)
    _write_item(tmp_path, "weapon", "sword.json", _weapon_item("sword"))

    assert game_data.load_catalog_items()[0]["_subdir"] == "weapon"


def test_project_catalog_to_item_option_for_weapon_subdir() -> None:
    item = _weapon_item("longsword")
    item["_subdir"] = "weapon"

    assert game_data.project_catalog_to_item_option(item) == {
        "id": "longsword",
        "name": "Longsword",
        "category": "weapon",
        "description": "Description for longsword.",
        "tags": ["weapon"],
        "roll_tag": None,
        "consumable": False,
        "charges": None,
        "rarity": "common",
        "value_cd": 1,
        "effects": [],
    }


def test_project_catalog_to_item_option_maps_unknown_subdir_to_gear() -> None:
    item = _base_item("mystery")
    item["_subdir"] = "unknown"

    assert game_data.project_catalog_to_item_option(item)["category"] == "gear"


def test_filter_catalog_by_kind_apparel_returns_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_catalog_dir(monkeypatch, tmp_path)
    _write_item(tmp_path, "gear", "cloak.json", _base_item("cloak"))

    assert game_data.filter_catalog_by_kind("apparel") == []


def test_filter_catalog_by_kind_weapon_includes_non_magical_excludes_magical(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_catalog_dir(monkeypatch, tmp_path)
    _write_item(tmp_path, "weapon", "longsword.json", _weapon_item("longsword"))
    _write_item(
        tmp_path,
        "weapon",
        "flame_tongue.json",
        _weapon_item("flame-tongue", magical=True),
    )

    assert [item["id"] for item in game_data.filter_catalog_by_kind("weapon")] == [
        "longsword"
    ]


def test_filter_catalog_by_kind_magical_includes_magical_excludes_non_magical(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_catalog_dir(monkeypatch, tmp_path)
    _write_item(tmp_path, "weapon", "longsword.json", _weapon_item("longsword"))
    _write_item(
        tmp_path,
        "weapon",
        "flame_tongue.json",
        _weapon_item("flame-tongue", magical=True),
    )

    assert [item["id"] for item in game_data.filter_catalog_by_kind("magical")] == [
        "flame-tongue"
    ]


def test_filter_catalog_by_kind_mundane_excludes_typed_and_magical_items(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_catalog_dir(monkeypatch, tmp_path)
    _write_item(tmp_path, "gear", "rope.json", _base_item("rope"))
    _write_item(tmp_path, "weapon", "longsword.json", _weapon_item("longsword"))
    _write_item(tmp_path, "armor", "leather.json", _armor_item("leather"))
    _write_item(tmp_path, "ammunition", "arrows.json", _ammunition_item("arrows"))
    _write_item(
        tmp_path,
        "weapon",
        "flame_tongue.json",
        _weapon_item("flame-tongue", magical=True),
    )

    assert [item["id"] for item in game_data.filter_catalog_by_kind("mundane")] == [
        "rope"
    ]


def test_filter_catalog_by_kind_unknown_kind_returns_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_catalog_dir(monkeypatch, tmp_path)
    _write_item(tmp_path, "gear", "rope.json", _base_item("rope"))

    assert game_data.filter_catalog_by_kind("unknown_kind") == []