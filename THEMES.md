# Hermes Web UI — Themes

Hermes Web UI splits **appearance** into two independent pickers:

- **Theme** — the mode: `System`, `Dark`, or `Light`. Drives the background,
  text, surface, and chrome colors.
- **Skin** — the accent/palette layer loaded from `static/skins/*.skin.json`.
  Drives accent variables today and can carry broader theme tokens over time.

You pick one of each and they combine, so the look adapts to your environment
without losing your favorite accent — pure CSS, no Python changes needed.

---

## Switching Appearance

**Settings panel:** Click the gear icon → **Appearance**. The **Theme** card
toggles Light/Dark/System; the **Skin** grid is populated from the manifest
registry. Preview is instant — the UI updates as you click.

**Slash command:** Type `/theme <name>` in the composer. The command accepts
both theme names (`system`, `dark`, `light`) and any manifest skin slug (for
example `default`, `ares`, `sienna`, or `obryn`). It updates the matching axis
and leaves the other one alone.

**Persistence:** Both choices are stored in `localStorage` for flicker-free
loading, and saved server-side via `POST /api/settings` (under `theme` and
`skin` keys in `settings.json`).

---

## Built-in Themes

| Theme | Description |
|-------|-------------|
| **System** (default) | Follows the OS `prefers-color-scheme` preference and updates live. |
| **Dark** | Deep dark surfaces, low-glare for long sessions. |
| **Light** | Bright surfaces with dark text, high contrast for daylight environments. |

The theme is applied as a class on `<html>`: `.dark` is present for dark mode,
absent for light. System mode tracks the OS preference at runtime.

---

## Built-in Skins

| Skin | Description |
|------|-------------|
| **Default** | The original Hermes gold accent. Warm and understated. |
| **Ares** | Fiery red. High-energy and assertive. |
| **Mono** | Neutral gray. Distraction-free, for deep focus. |
| **Slate** | Slate blue-gray. Subtle and grown-up. |
| **Poseidon** | Ocean blue. Calm and focused for long sessions. |
| **Sisyphus** | Vivid purple. Distinctive without being loud. |
| **Charizard** | Warm orange. Energetic and easy on the eyes. |
| **Sienna** | Warm clay and sand earth palette. Soft and natural. |

Each skin defines paired light + dark variants so it reads cleanly on either
theme. The skin is applied as `data-skin="<name>"` on `<html>` (the default
skin clears the attribute).

---

## Creating a Custom Skin

Skins are loaded from manifest files in `static/skins/*.skin.json`. The manifest
is the source of truth; the backend validates it, generates the CSS variable
blocks, exposes the picker metadata through `GET /api/skins`, and uses the same
registry when normalizing saved settings.

```json
{
  "schema": 1,
  "slug": "my-skin",
  "name": "My Skin",
  "preview": ["#66BB6A", "#43A047", "#1B5E20"],
  "variants": {
    "light": {
      "accent": "#2E7D32",
      "accent-hover": "#1B5E20",
      "accent-bg": "rgba(46,125,50,0.08)",
      "accent-bg-strong": "rgba(46,125,50,0.15)",
      "accent-text": "#1B5E20"
    },
    "dark": {
      "accent": "#66BB6A",
      "accent-hover": "#43A047",
      "accent-bg": "rgba(102,187,106,0.08)",
      "accent-bg-strong": "rgba(102,187,106,0.15)",
      "accent-text": "#66BB6A"
    }
  }
}
```

The filename must match the slug exactly: `static/skins/my-skin.skin.json`.
Token names become CSS custom properties (`accent` → `--accent`). Token values
must be plain CSS values without `;`, `{`, or `}`.

You can also create a skin from the browser: **Settings → Appearance → Skin config**
lets you switch between **Light** and **Dark** variant tabs, edit each variant's
CSS variables grouped in collapsible sections, then **Export skin** prompts for
a name and writes `static/skins/<slug>.skin.json` with distinct `light` and
`dark` token maps.

### Tips

- **Test both themes.** A skin that pops on Dark can be illegible on Light.
  Always check `:root[data-skin]` (light) *and* `:root.dark[data-skin]` (dark).
- **Pick contrasting `--accent-text` on `--accent-bg`.** The strong variant
  appears behind small labels and chips; weak contrast there reads as blur.
- **The logo gradient uses `--accent` automatically**, so it adapts to your
  skin without any extra work.
- **No server changes needed.** The `skin` setting in `settings.json` accepts
  any string, so your custom skin name persists without code changes once you
  load the CSS.

---

## Creating a Custom Theme

A full custom *theme* (a different overall mood, not just an accent change) is
a larger task than a skin: it has to redefine the core palette variables
(`--bg`, `--surface`, `--text`, `--border`, `--code-bg`, and friends) for one
or both modes. The contract is defined in the top `:root` and `:root.dark`
blocks of `static/style.css` — start there.

Most of the time, a custom **skin** is what you actually want. Reach for a
custom theme only when the existing Light/Dark modes don't fit (for example,
a high-contrast accessibility theme or an OLED black variant).

---

## Font Size

Right under Theme/Skin in **Settings → Appearance**: `Small`, `Default`,
`Large`. Applied as `data-font-size` on `<html>` and scales the WebUI's root
font size. Persists alongside theme and skin.

---

## How It Works Internally

1. **Theme:** `document.documentElement.classList.toggle('dark', isDark)` —
   light mode removes the class. System mode tracks
   `matchMedia('(prefers-color-scheme: dark)')`.
2. **Skin:** `boot.js` fetches `GET /api/skins`, injects the generated manifest
   CSS, and sets `document.documentElement.dataset.skin = slug` (or removes the
   attribute for `default`).
3. **Font size:** `document.documentElement.dataset.fontSize = size` (or
   remove for `default`).
4. **No flash on load:** a tiny inline `<script>` in `<head>` reads
   `localStorage` before the stylesheet does, so the right look is applied
   before paint.
5. **Server sync:** preferences are saved via `POST /api/settings` and
   rehydrated on boot via `GET /api/settings`.

---

## Contributing a Skin

Skins are the easiest extension point — validated JSON manifests under
`static/skins/`, with CSS generated at runtime. To contribute one upstream:

1. Add `static/skins/<slug>.skin.json` with `schema`, `slug`, `name`, `preview`,
   and paired `variants.light` / `variants.dark` token maps.
2. Run the skin manifest tests and check the picker plus `/theme <slug>` in the
   browser.
3. Test on desktop and mobile across both Light and Dark themes.
4. Open a PR — no picker allowlist or slash-command allowlist edits should be
   needed for ordinary skin additions.

For a custom *theme* (overriding the base palette), prefer opening an issue
first to discuss scope, since it touches many selectors.
