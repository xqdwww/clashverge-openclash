"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .converter import convert_document
from .model import validate_document
from .yamlio import ConfigError, atomic_write_yaml, load_yaml, paths_overlap


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clashverge-openclash",
        description="Convert a documented Clash YAML subset into OpenClash-ready YAML locally.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    convert = commands.add_parser("convert", help="validate and convert a local YAML file")
    convert.add_argument("--input", "-i", required=True, type=Path)
    convert.add_argument("--output", "-o", required=True, type=Path)
    convert.add_argument("--default-target", help="target for an added final MATCH rule")
    convert.add_argument("--dry-run", "-n", action="store_true", help="validate without writing")
    convert.add_argument("--force", "-f", action="store_true", help="replace an existing output")

    validate = commands.add_parser("validate", help="validate a source or generated target")
    validate.add_argument("config_file", type=Path)
    validate.add_argument("--type", choices=("source", "target"), default="source")
    return parser


def _convert(args: argparse.Namespace) -> int:
    if paths_overlap(args.input, args.output):
        raise ConfigError("Input and output paths must be different")
    source = load_yaml(args.input)
    target = convert_document(source, default_target=args.default_target)
    print(
        "Validated conversion: "
        f"{len(target['proxies'])} proxies, "
        f"{len(target['proxy-groups'])} groups, "
        f"{len(target['rules'])} rules"
    )
    if args.dry_run:
        print("Dry run: no file written")
        return 0
    atomic_write_yaml(args.output, target, force=args.force)
    print(f"Wrote: {args.output}")
    return 0


def _validate(args: argparse.Namespace) -> int:
    document = load_yaml(args.config_file)
    validate_document(document, require_target_shape=args.type == "target")
    print(f"Valid {args.type} configuration")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "convert":
            return _convert(args)
        return _validate(args)
    except ConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
