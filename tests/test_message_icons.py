from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_settings_persists_user_icon():
    src = read("api/config.py")
    assert '"user_icon": ""' in src
    assert '"user_icon"' in src and "_sanitize_message_icon" in src


def test_profile_api_exposes_and_saves_assistant_icon():
    src = read("api/profiles.py")
    assert "assistant_icon" in src
    assert "def update_profile_display_api" in src
    routes = read("api/routes.py")
    assert '"assistant_icon"' in routes
    assert '"/api/profile/display"' in routes


def test_settings_and_profile_panels_have_icon_inputs():
    html = read("static/index.html")
    assert 'id="settingsUserIcon"' in html
    assert 'id="profileAssistantIcon"' in read("static/panels.js")


def test_message_renderer_uses_configured_icons_for_both_roles():
    src = read("static/ui.js")
    assert "_messageIconHtml" in src
    assert "window._userIcon" in src
    assert "window._assistantIcon" in src
    assert "msg-avatar ${role}" in src
    assert "_messageIconHtml('user'" in src
    assert "_messageIconHtml('assistant'" in src
    assert "row.dataset.role='user'" in src or 'row.dataset.role="user"' in src
    assert "<span style=\"font-size:12px\">You</span>${userIconHtml}" in src


def test_boot_and_autosave_keep_icons_live():
    boot = read("static/boot.js")
    panels = read("static/panels.js")
    assert "window._userIcon=s.user_icon||''" in boot
    assert "window._assistantIcon=p.assistant_icon||''" in boot
    assert "payload.user_icon" in panels
    assert "window._userIcon" in panels
    assert "saveProfileAssistantIcon" in panels


def test_icon_css_supports_emoji_and_images():
    css = read("static/style.css")
    assert ".msg-avatar" in css
    assert ".msg-avatar-img" in css
    assert ".msg-avatar-text" in css


def test_user_role_header_is_right_aligned_with_user_bubble():
    css = read("static/style.css")
    assert '.msg-row[data-role="user"] .msg-role' in css
    assert "justify-content:flex-end" in css or "justify-content: flex-end" in css
