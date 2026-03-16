"""Schemas for the publish module."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PublishResponse(BaseModel):
    public_url: str
    slug: str
    published_at: datetime


class PublicAppSnapshot(BaseModel):
    id: str
    name: str
    pages: list[dict]
