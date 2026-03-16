"""Publish service — slug generation."""
from __future__ import annotations

import re
import unicodedata

from sqlalchemy import select


def slugify(text: str) -> str:
    """Convert a string to a URL-safe slug."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")


async def generate_unique_slug(name: str, db) -> str:  # noqa: ANN001
    """Return a slug derived from name, suffixed if a collision exists."""
    from app.models import ToolApp  # local import to avoid circular

    base = slugify(name)[:80]
    slug = base
    counter = 2
    while True:
        existing = await db.scalar(select(ToolApp).where(ToolApp.slug == slug))
        if not existing:
            return slug
        slug = f"{base}-{counter}"
        counter += 1
