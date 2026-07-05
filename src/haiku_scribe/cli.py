from __future__ import annotations

import argparse
import sys
from pathlib import Path

from haiku_scribe.doctor import doctor_user
from haiku_scribe.settings import SettingsError
from haiku_scribe.setup import setup_user
from haiku_scribe.uninstall import uninstall_user


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="haiku-scribe")
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup = subparsers.add_parser("setup", help="Install Haiku Scribe for one user")
    setup.add_argument("--dry-run", action="store_true", help="Print planned changes without writing files")
    setup.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)

    doctor = subparsers.add_parser("doctor", help="Validate the personal Haiku Scribe installation")
    doctor.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)

    uninstall = subparsers.add_parser("uninstall", help="Remove Haiku Scribe-owned personal configuration")
    uninstall.add_argument("--dry-run", action="store_true", help="Print planned removals without writing files")
    uninstall.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "setup":
        try:
            result = setup_user(args.home, dry_run=args.dry_run)
        except SettingsError as exc:
            print(f"setup failed: {exc}", file=sys.stderr)
            return 1
        if args.dry_run:
            print("Dry run: no files written")
            for item in result.planned:
                print(item)
        else:
            for path in result.written:
                print(f"Wrote {path}")
        return 0

    if args.command == "doctor":
        result = doctor_user(args.home)
        if result.ok:
            print("Haiku Scribe doctor: ok")
            return 0
        print("Haiku Scribe doctor: failed")
        for failure in result.failures:
            print(f"- {failure}")
        return 1

    if args.command == "uninstall":
        result = uninstall_user(args.home, dry_run=args.dry_run)
        if args.dry_run:
            print("Dry run: no files removed")
            for item in result.planned:
                print(item)
            if not result.planned:
                print("Nothing to remove")
            return 0
        if not result.removed:
            print("Nothing to remove")
            return 0
        for path in result.removed:
            print(f"Removed {path}")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2
