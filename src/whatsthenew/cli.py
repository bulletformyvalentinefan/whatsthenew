"""Punto de entrada del CLI: `python -m whatsthenew run`."""

from __future__ import annotations

import argparse
import logging
import sys

from . import __version__
from .config import Settings, load_sources


def _cmd_run(_args: argparse.Namespace) -> int:
    from .pipeline import run

    return run(Settings.from_env())


def _cmd_sources(_args: argparse.Namespace) -> int:
    sources = load_sources()
    for group in ("jobs_global", "jobs_chile", "news", "company_blogs", "roadmaps"):
        print(f"\n[{group}]")
        for s in sources.get(group, []):
            flag = "on " if s.get("enabled") else "off"
            print(f"  {flag} {s['id']:<16} {s.get('url', s.get('repo', ''))}")
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="whatsthenew", description="Vigilancia de mercado tech.")
    parser.add_argument("--version", action="version", version=f"whatsthenew {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="Ejecuta el pipeline completo")
    sub.add_parser("sources", help="Lista las fuentes configuradas")

    args = parser.parse_args(argv)
    if args.command == "run":
        return _cmd_run(args)
    if args.command == "sources":
        return _cmd_sources(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
