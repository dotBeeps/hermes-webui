"""Directory-backed skin manifest loading for Hermes WebUI."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SKIN_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}$")
_TOKEN_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_FORBIDDEN_CSS_CHARS = set(";{}")
_FORBIDDEN_NAME_CHARS = set("<>\"'{}")
_FORBIDDEN_PREVIEW_CHARS = set("<>\"'`")
_MAX_MANIFEST_BYTES = 128 * 1024


def skin_slug(value: object) -> str:
    """Return the normalized filesystem-safe skin slug for user input."""
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")[:48]


def _validate_slug(slug: object) -> str:
    value = str(slug or "").strip().lower()
    if not _SKIN_SLUG_RE.fullmatch(value):
        raise ValueError(f"invalid skin slug: {value or '<empty>'}")
    return value


def _validate_name(name: object, slug: str) -> str:
    value = str(name or "").strip()
    if not value:
        return slug.replace("-", " ").title()
    if len(value) > 80:
        raise ValueError(f"skin name is too long: {slug}")
    if "*/" in value or any(ch in value for ch in _FORBIDDEN_NAME_CHARS):
        raise ValueError(f"invalid skin name: {slug}")
    return value


def _validate_preview_value(value: object) -> str:
    text = _validate_token_value(value)
    if any(ch in text for ch in _FORBIDDEN_PREVIEW_CHARS):
        raise ValueError(f"invalid skin preview value: {text}")
    return text


def _validate_preview(preview: object, variants: dict[str, dict[str, str]]) -> list[str]:
    if isinstance(preview, list):
        colors = [str(item).strip() for item in preview[:3] if str(item).strip()]
    else:
        colors = []
    if not colors:
        for variant in (variants.get("dark"), variants.get("light")):
            if variant:
                colors.extend([variant.get("accent", ""), variant.get("accent-hover", ""), variant.get("accent-text", "")])
                break
    colors = [c for c in colors if c][:3]
    while len(colors) < 3:
        colors.append("#888888")
    return [_validate_preview_value(color) for color in colors]


def _validate_token_value(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("invalid skin token value: empty")
    if any(ch in text for ch in _FORBIDDEN_CSS_CHARS):
        raise ValueError(f"invalid skin token value: {text}")
    if len(text) > 160:
        raise ValueError("invalid skin token value: too long")
    return text


def _validate_tokens(tokens: object, slug: str, variant: str) -> dict[str, str]:
    if not isinstance(tokens, dict) or not tokens:
        raise ValueError(f"skin {slug} missing {variant} tokens")
    result: dict[str, str] = {}
    for key, value in tokens.items():
        token = str(key or "").strip().lower()
        if not _TOKEN_NAME_RE.fullmatch(token):
            raise ValueError(f"invalid skin token name: {token}")
        result[token] = _validate_token_value(value)
    return result


def _manifest_from_path(path: Path) -> dict[str, Any]:
    if path.stat().st_size > _MAX_MANIFEST_BYTES:
        raise ValueError(f"skin manifest too large: {path.name}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"skin manifest must be an object: {path.name}")
    if raw.get("schema") != 1:
        raise ValueError(f"unsupported skin schema in {path.name}")
    slug = _validate_slug(raw.get("slug"))
    expected_name = f"{slug}.skin.json"
    if path.name != expected_name:
        raise ValueError(f"skin slug {slug} must live in {expected_name}")
    variants_raw = raw.get("variants")
    if not isinstance(variants_raw, dict):
        raise ValueError(f"skin {slug} missing variants")
    light = _validate_tokens(variants_raw.get("light"), slug, "light")
    dark = _validate_tokens(variants_raw.get("dark"), slug, "dark")
    variants = {"light": light, "dark": dark}
    return {
        "slug": slug,
        "name": _validate_name(raw.get("name"), slug),
        "preview": _validate_preview(raw.get("preview"), variants),
        "variants": variants,
    }


def generate_skin_css(skin: dict[str, Any]) -> str:
    """Generate CSS variable overrides for one validated skin manifest."""
    slug = _validate_slug(skin["slug"])
    light = skin["variants"]["light"]
    dark = skin["variants"]["dark"]

    def block(selector: str, tokens: dict[str, str]) -> str:
        body = "".join(f"--{key}:{value};" for key, value in sorted(tokens.items()))
        return f'{selector}{{{body}}}'

    return "\n".join([
        f"/* Skin: {slug} */",
        block(f':root[data-skin="{slug}"]', light),
        block(f':root.dark[data-skin="{slug}"]', dark),
    ])


def load_skin_registry(static_dir: str | Path) -> dict[str, Any]:
    """Load all static/skins/*.skin.json manifests and return UI metadata + CSS."""
    static_path = Path(static_dir)
    skins_dir = static_path / "skins"
    manifests = sorted(skins_dir.glob("*.skin.json")) if skins_dir.exists() else []
    skins: list[dict[str, Any]] = []
    seen: set[str] = set()
    warnings: list[str] = []
    for path in manifests:
        try:
            skin = _manifest_from_path(path)
        except Exception as exc:
            message = f"skipping invalid skin manifest {path.name}: {exc}"
            warnings.append(message)
            logger.warning(message)
            continue
        slug = skin["slug"]
        if slug in seen:
            message = f"skipping duplicate skin slug {slug}: {path.name}"
            warnings.append(message)
            logger.warning(message)
            continue
        seen.add(slug)
        skins.append(skin)
    return {
        "skins": [{"slug": s["slug"], "name": s["name"], "colors": s["preview"], "preview": s["preview"], "variants": s["variants"]} for s in skins],
        "slugs": seen,
        "css": "\n".join(generate_skin_css(s) for s in skins),
        "warnings": warnings,
    }


def get_valid_skin_slugs(static_dir: str | Path) -> set[str]:
    """Return the known skin slugs, falling back safely to default on loader errors."""
    try:
        slugs = load_skin_registry(static_dir)["slugs"]
    except Exception:
        slugs = set()
    return set(slugs) or {"default"}


def _validate_variants(variants: object, slug: str) -> dict[str, dict[str, str]]:
    if not isinstance(variants, dict) or not variants:
        raise ValueError(f"skin {slug} missing export variants")
    light = _validate_tokens(variants.get("light"), slug, "light")
    dark = _validate_tokens(variants.get("dark"), slug, "dark")
    return {"light": light, "dark": dark}


def build_skin_manifest(name: object, slug: object, variants: object) -> dict[str, Any]:
    """Build a schema-v1 manifest from editor light/dark variant tokens."""
    clean_slug = _validate_slug(slug)
    clean_name = _validate_name(name, clean_slug)
    clean_variants = _validate_variants(variants, clean_slug)
    preview_keys = ("accent", "accent-hover", "accent-text")
    preview = [clean_variants["dark"].get(k) or clean_variants["light"].get(k) for k in preview_keys]
    preview = [item for item in preview if item]
    if not preview:
        preview = list(clean_variants["dark"].values())[:3] or list(clean_variants["light"].values())[:3]
    while len(preview) < 3:
        preview.append(preview[-1] if preview else "#888888")
    preview = _validate_preview(preview[:3], clean_variants)
    return {
        "schema": 1,
        "slug": clean_slug,
        "name": clean_name,
        "preview": preview,
        "variants": clean_variants,
    }
