# Skin Directory + Manifest Theming Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Move Hermes WebUI skins out of hardcoded JS/CSS/backend allowlists and into a loadable `static/skins/` directory with non-CSS manifest files as the source of truth.

**Architecture:** Skins should be defined by data files, not raw CSS as the primary authoring format. Use a small JSON manifest format first (`static/skins/<slug>.skin.json`) that can later grow into broader theming options without requiring a new parser or unsafe executable theme code. The backend loads and validates manifests, exposes them via `/api/skins`, and generates CSS variables/client metadata from the manifest. The browser consumes that API for picker entries and uses generated CSS for actual styling.

**Tech Stack:** Python stdlib JSON + validation helpers, vanilla JS, CSS custom properties, pytest source/unit tests.

---

## Design Decisions

1. **Use `.skin.json`, not CSS, as the source format.**
   - JSON is already natural for WebUI settings/API code.
   - It supports future options like `author`, `description`, `preview`, `variants`, `accessibility`, `editorFields`, `messageBubbles`, or `components` without inventing CSS parsing.
   - It avoids accepting arbitrary CSS as a first-class theme package format.

2. **Generate/load CSS from manifests.**
   - The active visual contract stays CSS variables on `<html>`.
   - The manifest becomes a safe data layer; CSS is implementation output.

3. **Keep built-ins working during migration.**
   - Existing built-in skins (`default`, `ares`, `mono`, `slate`, `poseidon`, `sisyphus`, `charizard`, `sienna`, `obryn`) should be converted or mirrored into manifest data.
   - Do not break saved `skin` settings.

4. **First-class endpoint shape:**
   - `GET /api/skins` returns validated skin metadata and CSS variable maps.
   - `POST /api/skins/export` writes a new `.skin.json` manifest, not a `.css` file.

5. **No arbitrary paths from the client.**
   - All file writes stay under `static/skins/`.
   - Filenames derive from sanitized slugs.
   - Reject overwrites unless/until an explicit update flow exists.

---

## Proposed Manifest Shape

Create files like `static/skins/obryn.skin.json`:

```json
{
  "schema": 1,
  "slug": "obryn",
  "name": "Obryn",
  "description": "Black-stone archive dragon palette.",
  "preview": ["#8B5CF6", "#38BDF8", "#D4AF37"],
  "variants": {
    "light": {
      "bg": "#F7F5FF",
      "sidebar": "#ECE8FA",
      "surface": "#F1EEFC",
      "text": "#151126",
      "muted": "#5C5574",
      "border": "#D9D1F0",
      "border2": "rgba(76,43,168,0.20)",
      "accent": "#6D4DDB",
      "accent-hover": "#5738C6",
      "accent-bg": "rgba(109,77,219,0.10)",
      "accent-bg-strong": "rgba(109,77,219,0.20)",
      "accent-text": "#4C2BA8"
    },
    "dark": {
      "bg": "#07070D",
      "sidebar": "#0D0D17",
      "surface": "#12121F",
      "text": "#F8F6FF",
      "muted": "#B8B3CE",
      "border": "#28243A",
      "border2": "rgba(255,255,255,0.14)",
      "accent": "#A78BFA",
      "accent-hover": "#8B5CF6",
      "accent-bg": "rgba(167,139,250,0.12)",
      "accent-bg-strong": "rgba(167,139,250,0.24)",
      "accent-text": "#C4B5FD"
    }
  }
}
```

Future-compatible additions can live beside `variants`, e.g. `components`, `layout`, `syntax`, `editor`, or `accessibility`.

---

## Task 1: Add backend skin manifest loader tests

**Objective:** Define expected manifest loading behavior before implementation.

**Files:**
- Create: `tests/test_skin_manifest_loader.py`
- Modify later: `api/skins.py`

**Step 1: Write failing tests**

Test cases:
- loads all `*.skin.json` files from a provided directory;
- validates slug/name/schema;
- rejects invalid filenames/slugs;
- returns metadata needed by the picker: `slug`, `name`, `preview`, `variants`;
- normalizes token keys to CSS variable names without leading `--`;
- ignores malformed files with a structured warning or raises deterministic `ValueError` in unit helper.

**Step 2: Run RED**

```bash
uv run --with pytest pytest -q tests/test_skin_manifest_loader.py
```

Expected: FAIL because `api.skins` does not exist yet.

---

## Task 2: Implement `api/skins.py`

**Objective:** Centralize skin manifest validation, loading, CSS generation, and export writing.

**Files:**
- Create: `api/skins.py`

**Implementation outline:**

- Constants:
  - `SKIN_SCHEMA_VERSION = 1`
  - `SKIN_FILE_SUFFIX = ".skin.json"`
  - `DEFAULT_SKINS_DIR = REPO_ROOT / "static" / "skins"`
  - `ALLOWED_TOKEN_RE = re.compile(r"^[a-z][a-z0-9-]*$")`
- Functions:
  - `skin_slug(value: object) -> str`
  - `validate_skin_manifest(data: dict, *, source: str = "") -> dict`
  - `load_skin_manifests(directory: Path = DEFAULT_SKINS_DIR) -> list[dict]`
  - `skin_manifest_to_css(manifest: dict) -> str`
  - `write_skin_manifest(body: dict, directory: Path = DEFAULT_SKINS_DIR) -> dict`

**Verification:**

```bash
uv run --with pytest pytest -q tests/test_skin_manifest_loader.py
python3 -m py_compile api/skins.py
```

---

## Task 3: Add built-in manifest files

**Objective:** Make the current built-in skins load from `static/skins/`.

**Files:**
- Create: `static/skins/default.skin.json`
- Create: `static/skins/ares.skin.json`
- Create: `static/skins/mono.skin.json`
- Create: `static/skins/slate.skin.json`
- Create: `static/skins/poseidon.skin.json`
- Create: `static/skins/sisyphus.skin.json`
- Create: `static/skins/charizard.skin.json`
- Create: `static/skins/sienna.skin.json`
- Create: `static/skins/obryn.skin.json`

**Notes:**
- Start with token values already present in `static/style.css` and `_SKINS` preview colors.
- Default can either contain base light/dark token values or be a special manifest with empty overrides; prefer full data so the editor has concrete fields.

**Verification:**

```bash
uv run --with pytest pytest -q tests/test_skin_manifest_loader.py
```

---

## Task 4: Add `/api/skins` route

**Objective:** Expose loaded manifests to the browser.

**Files:**
- Modify: `api/routes.py`
- Test: `tests/test_skin_manifest_loader.py` or new route-focused test

**Behavior:**

`GET /api/skins` returns:

```json
{
  "skins": [
    {
      "slug": "obryn",
      "name": "Obryn",
      "description": "...",
      "preview": ["#8B5CF6", "#38BDF8", "#D4AF37"],
      "variants": {"light": {}, "dark": {}}
    }
  ],
  "css": "...optional generated css..."
}
```

Two viable choices:
- Return CSS in JSON and inject a `<style id="skinManifestStyle">` client-side.
- Serve `/api/skins.css` as generated CSS and fetch metadata separately.

Recommendation: use `/api/skins` for metadata and `/api/skins.css` for generated CSS if this becomes large. For first pass, JSON with both is acceptable and simple.

**Verification:**

```bash
python3 -m py_compile api/routes.py api/skins.py
uv run --with pytest pytest -q tests/test_skin_manifest_loader.py
```

---

## Task 5: Make frontend picker consume skin API

**Objective:** Replace hardcoded `_SKINS` as the authoritative source for the picker.

**Files:**
- Modify: `static/boot.js`
- Modify: `static/commands.js` if `/theme` should use loaded skins
- Test: `tests/test_skin_editor.py` or new source assertions

**Implementation outline:**

- Keep a minimal boot fallback list for no-flash/default safety.
- Add async `loadSkinCatalog()` during boot/settings hydration:
  - fetch `/api/skins`;
  - update `window._skinCatalog` or `_SKINS`;
  - inject generated CSS if provided;
  - rebuild picker;
  - update `_VALID_SKINS`.
- Ensure commands use the loaded catalog when available.

**Important invariant:** Early boot script cannot await an API. Keep a conservative fallback allowlist or accept that custom saved skins apply after boot hydration.

**Verification:**

```bash
node --check static/boot.js static/commands.js
uv run --with pytest pytest -q tests/test_skin_editor.py
```

---

## Task 6: Move backend skin allowlist to manifest loader

**Objective:** Stop duplicating skin keys in `api/config.py`.

**Files:**
- Modify: `api/config.py`
- Test: update `tests/test_obryn_skin.py`, `tests/test_sienna_skin.py`, and/or add manifest-specific assertions

**Implementation outline:**

- Replace `_SETTINGS_SKIN_VALUES` static set with a helper that includes:
  - built-in fallback values for safety;
  - loaded manifest slugs from `api.skins` when available.
- Keep legacy theme mapping unchanged.
- Preserve behavior for unknown skins if self-hosted extension flow still relies on arbitrary strings; decide explicitly.

**Open decision:** Should unknown skins still persist? Current docs say custom skin name persists once CSS is loaded. A manifest-only future might reject unknown skins. I recommend: accept manifest slugs plus existing built-ins; for now still tolerate unknown strings only if a `custom_skin_passthrough` compatibility flag is desired. Otherwise we make skins safer and predictable.

---

## Task 7: Change export to write `.skin.json`

**Objective:** Align the in-browser editor export with the new source-of-truth format.

**Files:**
- Modify: `static/boot.js`
- Modify: `api/skins.py`
- Modify: `api/routes.py`
- Test: `tests/test_skin_editor.py`, `tests/test_skin_manifest_loader.py`

**Behavior:**

- `_exportEditedSkin()` gathers current edited variables.
- It sends `{ name, slug, preview, variants: { light, dark } }` to `POST /api/skins/export`.
- Backend writes `static/skins/<slug>.skin.json`.
- On success, browser reloads skin catalog and selects the new skin.

**Caveat:** The current editor reads only the resolved current mode. To export both `light` and `dark` cleanly, either:
1. store separate light/dark edit maps in the editor UI, or
2. export the same values to both variants for now, then improve editor UX later.

Recommendation: implement separate Light/Dark tabs in a follow-up. First pass can export current values to both variants if the UI says so clearly.

---

## Task 8: Update documentation

**Objective:** Make `THEMES.md` match the new source-of-truth.

**Files:**
- Modify: `THEMES.md`

**Update sections:**
- Explain `static/skins/*.skin.json`.
- Include manifest example.
- Remove stale “no Python changes needed” / static hardcode language.
- Explain export flow writes a manifest.
- Explain promotion/selection behavior.

---

## Verification Matrix

Run after implementation:

```bash
python3 -m py_compile api/config.py api/routes.py api/skins.py
for f in static/boot.js static/commands.js static/panels.js static/ui.js static/i18n.js; do node --check "$f" || exit 1; done
uv run --with pytest --with pyyaml pytest -q \
  tests/test_skin_manifest_loader.py \
  tests/test_skin_editor.py \
  tests/test_obryn_skin.py \
  tests/test_sienna_skin.py \
  tests/test_theme_color_meta_bridge.py
git diff --check
```

Manual browser check:

1. Open Settings → Appearance.
2. Confirm built-in skins render from manifest catalog.
3. Edit a variable in the skin config fields; confirm live preview.
4. Export as `test skin`; confirm `static/skins/test-skin.skin.json` exists.
5. Reload WebUI; confirm new skin appears in picker.
6. Select it; confirm persistence via `/api/settings` and refresh.

---

## Acceptance Checklist

- [ ] Built-in skins are represented as manifest files.
- [ ] Skin picker is populated from loaded manifests.
- [ ] Backend settings accepts manifest skin slugs.
- [ ] Export writes `.skin.json`, not `.css`.
- [ ] Exported skin appears in the picker after reload/catalog refresh.
- [ ] No path traversal or overwrite behavior in export.
- [ ] `THEMES.md` documents the manifest format.
