"""rotate_key — re-encrypt all DataSource auth_config records with a new key.

Usage
-----
    python -m app.tools.rotate_key --old-key=<OLD_FERNET_KEY> --new-key=<NEW_FERNET_KEY>

Flags
-----
--old-key   Current DATASOURCE_ENCRYPTION_KEY (Fernet base64 URL-safe 32-byte key).
            If omitted, the script reads OLD_KEY env var or falls back to the
            development key derived from JWT_SECRET_KEY.
--new-key   The replacement key.  Must be a valid Fernet key
            (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())").
--dry-run   Print what would be changed without writing to the database.
--batch     How many records to process per transaction (default: 100).

The script is idempotent: records that were already re-encrypted with the new
key will fail decryption with the old key and are skipped with a warning.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import logging
import sys

from cryptography.fernet import InvalidToken
from sqlalchemy import select, update

from app.config import settings
from app.datasources.secrets import rotate_auth_config
from app.db import SessionLocal
from app.models import DataSource

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
)
log = logging.getLogger(__name__)


def _derive_dev_key() -> str:
    digest = hashlib.sha256(settings.jwt_secret_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8")


async def _rotate(old_key: str, new_key: str, dry_run: bool, batch: int) -> None:
    rotated = 0
    skipped = 0
    errors = 0
    offset = 0

    async with SessionLocal() as session:
        while True:
            result = await session.execute(
                select(DataSource).order_by(DataSource.id).offset(offset).limit(batch)
            )
            rows = result.scalars().all()
            if not rows:
                break

            for ds in rows:
                stored = ds.auth_config or {}
                if not stored.get("_encrypted") and not stored:
                    # No credentials at all — nothing to rotate.
                    skipped += 1
                    continue
                try:
                    new_blob = rotate_auth_config(stored, old_key, new_key)
                except InvalidToken:
                    log.warning(
                        "datasource %s: could not decrypt with old key — "
                        "already rotated or encrypted with a different key, skipping.",
                        ds.id,
                    )
                    skipped += 1
                    continue
                except Exception as exc:
                    log.error("datasource %s: unexpected error — %s", ds.id, exc)
                    errors += 1
                    continue

                if dry_run:
                    log.info("DRY-RUN datasource %s: would rotate auth_config", ds.id)
                    rotated += 1
                    continue

                await session.execute(
                    update(DataSource)
                    .where(DataSource.id == ds.id)
                    .values(auth_config=new_blob)
                )
                rotated += 1
                log.info("datasource %s: rotated", ds.id)

            if not dry_run:
                await session.commit()

            offset += batch

    log.info(
        "Done. rotated=%d  skipped=%d  errors=%d%s",
        rotated,
        skipped,
        errors,
        "  (DRY-RUN — no changes written)" if dry_run else "",
    )
    if errors:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Rotate DATASOURCE_ENCRYPTION_KEY")
    parser.add_argument(
        "--old-key",
        default=None,
        help="Current Fernet key (reads OLD_KEY env var if omitted; falls back to dev key).",
    )
    parser.add_argument(
        "--new-key",
        required=True,
        help="Replacement Fernet key.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to the database.",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=100,
        help="Records per transaction (default: 100).",
    )
    args = parser.parse_args()

    import os

    old_key: str = args.old_key or os.environ.get("OLD_KEY") or _derive_dev_key()

    if old_key == args.new_key:
        log.error("--old-key and --new-key are identical; nothing to do.")
        sys.exit(1)

    log.info(
        "Starting key rotation  dry_run=%s  batch=%d",
        args.dry_run,
        args.batch,
    )
    asyncio.run(_rotate(old_key, args.new_key, args.dry_run, args.batch))


if __name__ == "__main__":
    main()
