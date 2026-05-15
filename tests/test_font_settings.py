from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FONT = '-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,system-ui,sans-serif'
OBRYN_FONT = 'RecMonoLinear Nerd Font,-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,system-ui,sans-serif'


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_global_custom_font_family_setting_is_removed_from_ui_layers():
    sources = {
        "static/index.html": read("static/index.html"),
        "static/boot.js": read("static/boot.js"),
        "static/panels.js": read("static/panels.js"),
    }
    removed_tokens = [
        "settingsFontFamily",
        "settingsFontFamilyPresets",
        "font_family:",
        "_applyFontFamily",
        "window._fontFamily",
    ]
    for path, src in sources.items():
        for token in removed_tokens:
            assert token not in src, f"{token} should not remain in {path}"


def test_font_family_is_a_skin_config_token_with_obryn_recmono_default():
    boot = read("static/boot.js")
    assert "{var:'font-ui',label:'UI font stack',section:'Typography'}" in boot

    for manifest_path in (ROOT / "static" / "skins").glob("*.skin.json"):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = OBRYN_FONT if manifest["slug"] == "obryn" else DEFAULT_FONT
        assert manifest["variants"]["light"]["font-ui"] == expected
        assert manifest["variants"]["dark"]["font-ui"] == expected


def test_font_family_setting_is_legacy_dropped_and_ignored(tmp_path, monkeypatch):
    import api.config as cfg

    monkeypatch.setattr(cfg, "SETTINGS_FILE", tmp_path / "settings.json")
    cfg.SETTINGS_FILE.write_text(
        json.dumps({"font_size": "large", "font_family": "RecMonoLinear Nerd Font"})
    )

    loaded = cfg.load_settings()
    assert loaded["font_size"] == "large"
    assert "font_family" not in loaded

    saved = cfg.save_settings({"font_family": "Inter"})
    assert "font_family" not in saved


def test_font_size_presets_include_tiny_and_huge_options():
    html = read("static/index.html")
    cfg = read("api/config.py")
    css = read("static/style.css")
    assert 'data-font-size-val="xs"' in html
    assert 'data-font-size-val="xlarge"' in html
    assert '"xs"' in cfg and '"xlarge"' in cfg
    assert ':root[data-font-size="xs"]' in css
    assert ':root[data-font-size="xlarge"]' in css


def test_font_size_xl_alias_normalizes_to_xlarge(tmp_path, monkeypatch):
    import api.config as cfg

    monkeypatch.setattr(cfg, "SETTINGS_FILE", tmp_path / "settings.json")
    cfg.SETTINGS_FILE.write_text(json.dumps({"font_size": "xl"}), encoding="utf-8")

    loaded = cfg.load_settings()
    assert loaded["font_size"] == "xlarge"

    saved = cfg.save_settings({"font_size": "xl"})
    assert saved["font_size"] == "xlarge"
    persisted = json.loads(cfg.SETTINGS_FILE.read_text(encoding="utf-8"))
    assert persisted["font_size"] == "xlarge"


def test_font_size_by_category_feature_is_removed_from_ui_layers():
    sources = {
        "static/index.html": read("static/index.html"),
        "static/boot.js": read("static/boot.js"),
        "static/panels.js": read("static/panels.js"),
        "static/style.css": read("static/style.css"),
    }
    removed_tokens = [
        "Text size by category",
        "settingsFontScaleStep",
        "settingsFontSizeChat",
        "font_scale_step",
        "font_size_chat",
        "font_size_sidebar",
        "font_size_composer",
        "font_size_code",
        "_applyTextScaleSettings",
        "font-category-grid",
        "--font-size-chat",
        "--font-size-sidebar",
        "--font-size-composer",
        "--font-size-code",
    ]
    for path, src in sources.items():
        for token in removed_tokens:
            assert token not in src, f"{token} should not remain in {path}"


def test_removed_font_category_settings_are_legacy_dropped(tmp_path, monkeypatch):
    import api.config as cfg

    monkeypatch.setattr(cfg, "SETTINGS_FILE", tmp_path / "settings.json")
    cfg.SETTINGS_FILE.write_text(
        json.dumps(
            {
                "font_size": "large",
                "font_scale_step": "1.20",
                "font_size_chat": "xlarge",
                "font_size_sidebar": "small",
                "font_size_composer": "large",
                "font_size_code": "xs",
            }
        )
    )

    loaded = cfg.load_settings()
    assert loaded["font_size"] == "large"
    for key in (
        "font_scale_step",
        "font_size_chat",
        "font_size_sidebar",
        "font_size_composer",
        "font_size_code",
    ):
        assert key not in loaded
