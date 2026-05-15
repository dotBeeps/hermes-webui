"""Directory-driven Hermes WebUI skin manifests."""

import json
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
BOOT_JS = (REPO / "static" / "boot.js").read_text(encoding="utf-8")
ROUTES_PY = (REPO / "api" / "routes.py").read_text(encoding="utf-8")
CONFIG_PY = (REPO / "api" / "config.py").read_text(encoding="utf-8")


def _manifest(slug="blueberry", name="Blueberry"):
    return {
        "schema": 1,
        "slug": slug,
        "name": name,
        "preview": ["#123456", "#abcdef", "#fedcba"],
        "variants": {
            "light": {"accent": "#123456", "bg": "#ffffff", "text": "#111111"},
            "dark": {"accent": "#abcdef", "bg": "#000000", "text": "#eeeeee"},
        },
    }


def test_manifest_loader_discovers_skin_json_files_and_generates_css(tmp_path, monkeypatch):
    from api import skins

    skins_dir = tmp_path / "static" / "skins"
    skins_dir.mkdir(parents=True)
    (skins_dir / "blueberry.skin.json").write_text(json.dumps(_manifest()), encoding="utf-8")

    loaded = skins.load_skin_registry(tmp_path / "static")

    assert [skin["slug"] for skin in loaded["skins"]] == ["blueberry"]
    assert loaded["slugs"] == {"blueberry"}
    assert ':root[data-skin="blueberry"]' in loaded["css"]
    assert ':root.dark[data-skin="blueberry"]' in loaded["css"]
    assert "--accent:#123456;" in loaded["css"]
    assert "--accent:#abcdef;" in loaded["css"]


def test_manifest_loader_skips_bad_slug_and_css_injection_without_hiding_good_skins(tmp_path, caplog):
    from api import skins

    skins_dir = tmp_path / "static" / "skins"
    skins_dir.mkdir(parents=True)
    (skins_dir / "blueberry.skin.json").write_text(json.dumps(_manifest()), encoding="utf-8")
    (skins_dir / "bad.skin.json").write_text(json.dumps(_manifest(slug="../bad")), encoding="utf-8")
    data = _manifest(slug="evil", name="Evil")
    data["variants"]["light"]["accent"] = "#fff; color:red"
    (skins_dir / "evil.skin.json").write_text(json.dumps(data), encoding="utf-8")

    loaded = skins.load_skin_registry(tmp_path / "static")

    assert [skin["slug"] for skin in loaded["skins"]] == ["blueberry"]
    assert loaded["slugs"] == {"blueberry"}
    assert skins.get_valid_skin_slugs(tmp_path / "static") == {"blueberry"}
    assert ':root[data-skin="blueberry"]' in loaded["css"]
    assert ':root[data-skin="evil"]' not in loaded["css"]
    assert len(loaded["warnings"]) == 2
    assert any("bad.skin.json" in warning for warning in loaded["warnings"])
    assert any("evil.skin.json" in warning for warning in loaded["warnings"])
    assert "skipping invalid skin manifest" in caplog.text


def test_manifest_loader_skips_malformed_json_manifest(tmp_path):
    from api import skins

    skins_dir = tmp_path / "static" / "skins"
    skins_dir.mkdir(parents=True)
    (skins_dir / "blueberry.skin.json").write_text(json.dumps(_manifest()), encoding="utf-8")
    (skins_dir / "broken.skin.json").write_text("{not json", encoding="utf-8")

    loaded = skins.load_skin_registry(tmp_path / "static")

    assert loaded["slugs"] == {"blueberry"}
    assert skins.get_valid_skin_slugs(tmp_path / "static") == {"blueberry"}
    assert len(loaded["warnings"]) == 1
    assert "broken.skin.json" in loaded["warnings"][0]


def test_skin_names_reject_comment_and_markup_injection(tmp_path):
    from api import skins

    variants = {
        "light": {"accent": "#123456", "bg": "#ffffff", "text": "#111111"},
        "dark": {"accent": "#abcdef", "bg": "#000000", "text": "#eeeeee"},
    }
    for bad_name in ('Evil */ body{color:red} /*', '<img src=x>', '" onclick="alert(1)', "Dog's {bad}"):
        with pytest.raises(ValueError, match="invalid skin name"):
            skins.build_skin_manifest(bad_name, "evil", variants)

    skins_dir = tmp_path / "static" / "skins"
    skins_dir.mkdir(parents=True)
    (skins_dir / "evil.skin.json").write_text(
        json.dumps(_manifest(slug="evil", name="Evil */ body{color:red} /*")),
        encoding="utf-8",
    )
    loaded = skins.load_skin_registry(tmp_path / "static")
    assert loaded["skins"] == []
    assert any("invalid skin name" in warning for warning in loaded["warnings"])


def test_generate_skin_css_uses_validated_slug_not_untrusted_name():
    from api import skins

    css = skins.generate_skin_css({
        "slug": "safe-skin",
        "name": "Evil */ body{color:red} /*",
        "variants": {
            "light": {"accent": "#123456", "bg": "#ffffff", "text": "#111111"},
            "dark": {"accent": "#abcdef", "bg": "#000000", "text": "#eeeeee"},
        },
    })

    assert "Evil" not in css
    assert "body{color:red}" not in css
    assert "/* Skin: safe-skin */" in css


def test_preview_values_reject_attribute_breakout_characters(tmp_path):
    from api import skins

    data = _manifest(slug="evil", name="Evil")
    data["preview"] = ['#fff" onmouseover="alert(1)', "<red>", "#000000"]
    skins_dir = tmp_path / "static" / "skins"
    skins_dir.mkdir(parents=True)
    (skins_dir / "evil.skin.json").write_text(json.dumps(data), encoding="utf-8")

    loaded = skins.load_skin_registry(tmp_path / "static")
    assert loaded["skins"] == []
    assert any("invalid skin preview value" in warning for warning in loaded["warnings"])

    variants = data["variants"]
    variants["dark"]["accent"] = '#fff" onmouseover="alert(1)'
    with pytest.raises(ValueError, match="invalid skin preview value"):
        skins.build_skin_manifest("Evil", "evil", variants)


def test_builtin_skins_are_manifest_files():
    skins_dir = REPO / "static" / "skins"
    expected = {"default", "ares", "mono", "slate", "poseidon", "sisyphus", "charizard", "sienna", "obryn"}
    found = {p.name.removesuffix(".skin.json") for p in skins_dir.glob("*.skin.json")}
    assert expected <= found

    from api import skins
    registry = skins.load_skin_registry(REPO / "static")
    assert expected <= registry["slugs"]


def test_export_writes_skin_manifest_not_css(tmp_path, monkeypatch):
    from api import routes

    monkeypatch.setattr(routes, "STATIC_DIR", tmp_path / "static")
    result = routes._write_exported_skin_file({
        "name": "My Skin!!",
        "variants": {
            "light": {"accent": "#123456", "bg": "#ffffff", "text": "#111111"},
            "dark": {"accent": "#abcdef", "bg": "#000000", "text": "#eeeeee"},
        },
    })

    written = tmp_path / "static" / "skins" / "my-skin.skin.json"
    assert written.exists()
    data = json.loads(written.read_text(encoding="utf-8"))
    assert data["schema"] == 1
    assert data["slug"] == "my-skin"
    assert data["name"] == "My Skin!!"
    assert data["variants"]["light"]["accent"] == "#123456"
    assert data["variants"]["dark"]["accent"] == "#abcdef"
    assert result["path"] == "static/skins/my-skin.skin.json"


def test_backend_and_frontend_use_dynamic_skin_registry():
    assert 'parsed.path == "/api/skins"' in ROUTES_PY
    assert "load_skin_registry" in ROUTES_PY
    assert "get_valid_skin_slugs" in CONFIG_PY
    assert "async function _loadSkins" in BOOT_JS
    assert "api('/api/skins')" in BOOT_JS
    assert "_SKINS=[" not in BOOT_JS
    assert "new Set((_SKINS||[]).map" not in BOOT_JS
