from __future__ import annotations

import argparse

from .db.init_db import init_db
from .db.session import session_scope
from .services.backup import restore_from_backup, write_backup


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage provider configuration backups")
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore providers from the configured backup file",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export current providers to the configured backup file",
    )
    args = parser.parse_args()

    if not args.restore and not args.export:
        parser.error("No action specified. Use --restore or --export.")

    init_db()

    with session_scope() as session:
        if args.export:
            path = write_backup(session)
            print(f"Backup written to {path}")
        if args.restore:
            count = restore_from_backup(session)
            print(f"Restored {count} providers from backup")


if __name__ == "__main__":
    main()
