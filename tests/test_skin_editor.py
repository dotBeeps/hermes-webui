"""Appearance skin editor: live CSS-variable fields and export flow."""

from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
INDEX_HTML = (REPO / "static" / "index.html").read_text(encoding="utf-8")
BOOT_JS = (REPO / "static" / "boot.js").read_text(encoding="utf-8")
STYLE_CSS = (REPO / "static" / "style.css").read_text(encoding="utf-8")
ROUTES_PY = (REPO / "api" / "routes.py").read_text(encoding="utf-8")


def test_skin_editor_markup_lives_below_skin_picker():
    skin_idx = INDEX_HTML.index('id="skinPickerGrid"')
    editor_idx = INDEX_HTML.index('id="skinEditorPanel"')
    text_size_idx = INDEX_HTML.index('id="settingsFontSize"')

    assert skin_idx < editor_idx < text_size_idx
    assert 'id="skinEditorFields"' in INDEX_HTML
    assert 'id="skinEditorTabs"' in INDEX_HTML
    assert 'data-skin-editor-variant="light"' in INDEX_HTML
    assert 'data-skin-editor-variant="dark"' in INDEX_HTML
    assert 'onclick="_exportEditedSkin()"' in INDEX_HTML
    assert 'data-i18n="settings_export_skin"' in INDEX_HTML


def test_skin_editor_builds_config_fields_from_css_variables():
    for name in (
        "_SKIN_EDITOR_FIELDS",
        "_renderSkinEditor",
        "_readEditableSkinVars",
        "_applyEditedSkinVars",
        "_switchSkinEditorVariant",
        "_readEditableSkinVariants",
        "_skinEditorVariantMatchesCurrentTheme",
        "_syncEditedSkinVarsForCurrentTab",
    ):
        assert f"{name}" in BOOT_JS

    for css_var in ("accent", "accent-hover", "accent-bg", "accent-bg-strong", "bg", "sidebar", "surface", "text", "muted"):
        assert f"var:'{css_var}'" in BOOT_JS

    for section in ("Base palette", "Accent", "Typography"):
        assert f"section:'{section}'" in BOOT_JS
    for section in ("Code", "Chrome", "Interaction"):
        assert f"section:'{section}'" not in BOOT_JS
    for css_var in ("code-bg", "code-text", "topbar-bg", "main-bg", "input-bg", "hover-bg", "focus-ring", "focus-glow"):
        assert f"var:'{css_var}'" not in BOOT_JS
    assert "_skinEditorSections" in BOOT_JS
    assert "document.createElement('details')" in BOOT_JS
    assert "document.createElement('summary')" in BOOT_JS
    assert "variants:(s.variants&&typeof s.variants==='object')?s.variants:null" in BOOT_JS
    assert "const manifestValues=manifest&&manifest.variants&&manifest.variants[cleanVariant]" in BOOT_JS
    assert "if(manifestValues) return {...manifestValues}" in BOOT_JS

    assert 'input.type=field.type||\'text\'' in BOOT_JS
    assert "document.documentElement.style.setProperty(`--${field.var}`,value)" in BOOT_JS
    assert "if(!_skinEditorVariantMatchesCurrentTheme())" in BOOT_JS
    assert "_clearEditedSkinInlineVars()" in BOOT_JS
    assert "_syncEditedSkinVarsForCurrentTab()" in BOOT_JS
    assert "_renderSkinEditor(appearance.skin)" in BOOT_JS


def _boot_function_body(name: str) -> str:
    start = BOOT_JS.index(f"function {name}(")
    next_function = BOOT_JS.find("\nfunction ", start + 1)
    if next_function == -1:
        return BOOT_JS[start:]
    return BOOT_JS[start:next_function]


def test_skin_picker_builds_manifest_labels_and_swatches_without_html_interpolation():
    body = _boot_function_body("_buildSkinPicker")

    assert "grid.innerHTML=''" in body  # clearing existing trusted UI remains okay.
    assert "btn.innerHTML" not in body
    assert "${skin.name}" not in body
    assert "background:${c}" not in body
    assert "skin.colors.map" not in body

    assert "const dots=document.createElement('div')" in body
    assert "const dot=document.createElement('span')" in body
    assert "dot.style.background=c" in body
    assert "const label=document.createElement('span')" in body
    assert "label.textContent=skin.name" in body
    assert "btn.appendChild(dots)" in body
    assert "btn.appendChild(label)" in body


def test_skin_editor_color_bubble_opens_native_color_picker():
    assert "function _skinEditorFieldSupportsColor(field)" in BOOT_JS
    assert "function _skinEditorColorInputValue(value)" in BOOT_JS
    assert "function _syncSkinEditorColorBubble(input,bubble,colorInput)" in BOOT_JS
    assert "bubble.className='skin-editor-color-bubble'" in BOOT_JS
    assert "colorInput.type='color'" in BOOT_JS
    assert "colorInput.className='skin-editor-color-input'" in BOOT_JS
    assert "if(typeof colorInput.showPicker==='function') colorInput.showPicker()" in BOOT_JS
    assert "else colorInput.click()" in BOOT_JS
    assert "input.value=colorInput.value" in BOOT_JS
    assert "return field && field.var!=='font-ui'" in BOOT_JS


def test_skin_export_prompts_for_name_and_writes_manifest_file():
    assert "async function _exportEditedSkin()" in BOOT_JS
    assert "showPromptDialog" in BOOT_JS
    assert "title:'Export skin'" in BOOT_JS
    assert "confirmLabel:'Export'" in BOOT_JS
    assert "_skinNameToSlug(name)" in BOOT_JS
    assert "api('/api/skins/export'" in BOOT_JS
    assert "_copyText(css)" not in BOOT_JS
    assert "variants=_readEditableSkinVariants()" in BOOT_JS
    assert "JSON.stringify({name:safeName,slug,variants})" in BOOT_JS
    assert "await _loadSkins()" in BOOT_JS
    assert "_buildSkinPicker(saved.slug||slug)" in BOOT_JS


def test_skin_export_endpoint_and_writer_are_present():
    assert 'parsed.path == "/api/skins/export"' in ROUTES_PY
    assert "def _write_exported_skin_file(" in ROUTES_PY
    assert "static" in ROUTES_PY and "skins" in ROUTES_PY
    assert ".skin.json" in ROUTES_PY
    assert "skin file already exists" in ROUTES_PY


def test_write_exported_skin_file_sanitizes_slug_and_writes(tmp_path, monkeypatch):
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
    written_text = written.read_text(encoding="utf-8")
    assert '"schema": 1' in written_text
    assert '"light": {' in written_text and '"dark": {' in written_text
    assert '"#abcdef"' in written_text
    assert result["slug"] == "my-skin"
    assert result["path"].endswith("static/skins/my-skin.skin.json")


def test_write_exported_skin_file_rejects_overwrite_and_bad_tokens(tmp_path, monkeypatch):
    from api import routes

    monkeypatch.setattr(routes, "STATIC_DIR", tmp_path / "static")
    routes._write_exported_skin_file({
        "name": "Same",
        "variants": {"light": {"accent": "#123456"}, "dark": {"accent": "#654321"}},
    })
    with pytest.raises(FileExistsError, match="already exists"):
        routes._write_exported_skin_file({
            "name": "Same",
            "variants": {"light": {"accent": "#123456"}, "dark": {"accent": "#654321"}},
        })
    with pytest.raises(ValueError, match="missing export variants"):
        routes._write_exported_skin_file({"name": "No Tokens", "variants": {}})


def test_skin_editor_has_styling_hooks():
    for selector in (
        ".skin-editor-panel",
        ".skin-editor-tabs",
        ".skin-editor-tab",
        ".skin-editor-section",
        ".skin-editor-section-summary",
        ".skin-editor-section-fields",
        ".skin-editor-input-row",
        ".skin-editor-color-bubble",
        ".skin-editor-color-input",
        ".skin-editor-actions",
    ):
        assert selector in STYLE_CSS
