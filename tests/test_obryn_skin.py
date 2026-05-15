"""Obryn skin: black-stone archive dragon palette, opt-in via Settings → Skin."""

from pathlib import Path
import sys

REPO = Path(__file__).parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from api import config

CSS = (REPO / "static" / "style.css").read_text(encoding="utf-8")
BOOT_JS = (REPO / "static" / "boot.js").read_text(encoding="utf-8")
INDEX_HTML = (REPO / "static" / "index.html").read_text(encoding="utf-8")
CONFIG_PY = (REPO / "api" / "config.py").read_text(encoding="utf-8")
MANIFEST = (REPO / "static" / "skins" / "obryn.skin.json").read_text(encoding="utf-8")


def test_obryn_skin_present_in_manifest_registry_and_boot_allowlist():
    """The Obryn skin must be selectable and must survive the early boot script."""
    assert '"slug": "obryn"' in MANIFEST, "Obryn manifest missing"
    assert '"#8B5CF6"' in MANIFEST and '"#38BDF8"' in MANIFEST and '"#D4AF37"' in MANIFEST, (
        "Obryn preview swatches missing"
    )
    assert "skins={" not in INDEX_HTML
    assert "^[a-z0-9][a-z0-9-]{0,47}$" in INDEX_HTML, (
        "early-init should preserve directory-backed saved skin slugs until the API registry loads"
    )


def test_obryn_skin_accepted_by_settings_normalizer():
    """The backend settings registry must persist 'obryn' instead of dropping it."""
    assert 'get_valid_skin_slugs' in CONFIG_PY, "settings skin registry must load manifests"
    assert config._normalize_appearance("dark", "obryn") == ("dark", "obryn")


def test_obryn_skin_palette_has_full_light_and_dark():
    """Obryn defines a full palette rewrite in both resolved theme modes."""
    assert '"light"' in MANIFEST, "Obryn light palette block missing"
    assert '"dark"' in MANIFEST, "Obryn dark palette block missing"
    for token in ('"bg": "#F7F5FF"', '"sidebar": "#ECE8FA"', '"accent": "#6D4DDB"', '"blue": "#38BDF8"'):
        assert token in MANIFEST, f"Obryn light palette token missing: {token}"
    for token in ('"bg": "#07070D"', '"sidebar": "#0D0D17"', '"accent": "#A78BFA"', '"blue": "#38BDF8"'):
        assert token in MANIFEST, f"Obryn dark palette token missing: {token}"


def test_obryn_skin_does_not_force_migration():
    """Obryn is opt-in; existing users keep their saved/default skin."""
    init_script_idx = INDEX_HTML.find("var themes=")
    end_idx = INDEX_HTML.find("</script>", init_script_idx)
    init_block = INDEX_HTML[init_script_idx:end_idx]
    forbidden = ["obryn-migrated", "skin-obryn-migrated", "skin='obryn'", 'skin="obryn"']
    for marker in forbidden:
        assert marker not in init_block, (
            f"Obryn skin must be opt-in, not force-migrated. Found '{marker}' "
            f"in early-init script."
        )


def test_obryn_new_chat_button_specificity_guards_gradient_text():
    """The gradient new-chat button must beat base light-mode accent-text styling."""
    assert ':root[data-skin="obryn"]:not(.dark) .new-chat-btn' in CSS, (
        "Obryn light-mode .new-chat-btn override missing — gradient text contrast risk"
    )
