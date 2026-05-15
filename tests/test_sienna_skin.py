"""Sienna skin: warm clay/sand earth palette, opt-in via Settings → Skin."""

from pathlib import Path

REPO = Path(__file__).parent.parent
CSS = (REPO / "static" / "style.css").read_text(encoding="utf-8")
BOOT_JS = (REPO / "static" / "boot.js").read_text(encoding="utf-8")
INDEX_HTML = (REPO / "static" / "index.html").read_text(encoding="utf-8")
MANIFEST = (REPO / "static" / "skins" / "sienna.skin.json").read_text(encoding="utf-8")


def test_sienna_skin_present_in_skins_manifest():
    """The Sienna skin must be exposed in the directory-backed skin registry."""
    assert '"slug": "sienna"' in MANIFEST, "Sienna manifest missing"
    assert '"#D97757"' in MANIFEST and '"#C06A49"' in MANIFEST and '"#9A523A"' in MANIFEST, (
        "Sienna preview swatches missing"
    )


def test_sienna_skin_in_early_init_allowlist():
    """The early-init script must preserve directory-backed saved skin slugs."""
    assert "skins={" not in INDEX_HTML
    assert "^[a-z0-9][a-z0-9-]{0,47}$" in INDEX_HTML, (
        "early-init should preserve saved skin slugs until the API registry loads"
    )


def test_sienna_skin_palette_has_full_light_and_dark():
    """Sienna defines both light and dark scoped palettes."""
    assert '"light"' in MANIFEST, "Sienna light-mode palette block missing"
    assert '"dark"' in MANIFEST, "Sienna dark-mode palette block missing"
    # Spot-check that the palette is a full rewrite (not just accent)
    for token in ('"bg": "#FAF9F5"', '"sidebar": "#F0EEE6"', '"accent": "#D97757"'):
        assert token in MANIFEST, f"Sienna light palette token missing: {token}"
    for token in ('"bg": "#1F1E1C"', '"sidebar": "#262522"', '"accent": "#D97757"'):
        assert token in MANIFEST, f"Sienna dark palette token missing: {token}"


def test_sienna_skin_does_not_force_migration():
    """Sienna must not be silently migrated onto existing users.

    The early-init script in index.html must NOT contain logic that flips an
    existing 'default' skin to 'sienna' on first load. New users keep the gold
    default; users opt in via Settings → Skin.
    """
    # The skin allowlist line should NOT contain a sienna-migration flag.
    init_script_idx = INDEX_HTML.find("var themes=")
    end_idx = INDEX_HTML.find("</script>", init_script_idx)
    init_block = INDEX_HTML[init_script_idx:end_idx]
    forbidden = ["sienna-migrated", "skin-sienna-migrated", "skin='sienna'", 'skin="sienna"']
    for marker in forbidden:
        assert marker not in init_block, (
            f"Sienna skin must be opt-in, not force-migrated. Found '{marker}' "
            f"in early-init script."
        )


def test_default_theme_is_still_dark():
    """Adding a new skin must not change the default theme."""
    # The early-init script defaults to 'dark' when no saved theme exists.
    init_script_idx = INDEX_HTML.find("var themes=")
    end_idx = INDEX_HTML.find("</script>", init_script_idx)
    init_block = INDEX_HTML[init_script_idx:end_idx]
    assert "||'dark'" in init_block, (
        "Default theme must remain 'dark' (the existing baseline)"
    )


def test_sienna_new_chat_button_specificity_guards_against_clay_on_clay():
    """The new-chat button needs higher specificity than the base
    :root:not(.dark) .new-chat-btn rule, otherwise the inherited
    color:var(--accent-text) collides with the solid-accent background and
    produces invisible clay-on-clay text in light mode."""
    assert ':root[data-skin="sienna"]:not(.dark) .new-chat-btn' in CSS, (
        "Sienna light-mode .new-chat-btn override missing — clay-on-clay risk"
    )
