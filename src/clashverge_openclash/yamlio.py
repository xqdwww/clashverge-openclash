"""Bounded YAML input and atomic private output helpers."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import yaml
from yaml.tokens import AliasToken


MAX_INPUT_BYTES = 5 * 1024 * 1024
MAX_ALIASES = 50


class ConfigError(ValueError):
    """A configuration cannot be safely processed."""


class StrictSafeLoader(yaml.SafeLoader):
    """SafeLoader variant that rejects duplicate mapping keys."""

    def construct_mapping(self, node: yaml.nodes.MappingNode, deep: bool = False) -> dict[Any, Any]:
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in mapping
            except TypeError as exc:
                raise ConfigError("YAML mapping keys must be scalar values") from exc
            if duplicate:
                raise ConfigError(f"Duplicate YAML mapping key: {key!r}")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a UTF-8 YAML mapping with size, alias, and duplicate-key limits."""
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ConfigError(f"Cannot access input file: {exc}") from exc
    if not path.is_file():
        raise ConfigError("Input path is not a regular file")
    if size > MAX_INPUT_BYTES:
        raise ConfigError(f"Input exceeds the {MAX_INPUT_BYTES}-byte limit")

    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ConfigError(f"Cannot read UTF-8 input: {exc}") from exc
    if len(raw) > MAX_INPUT_BYTES:
        raise ConfigError(f"Input exceeds the {MAX_INPUT_BYTES}-byte limit")

    try:
        alias_count = sum(isinstance(token, AliasToken) for token in yaml.scan(text))
        if alias_count > MAX_ALIASES:
            raise ConfigError(f"Input contains more than {MAX_ALIASES} YAML aliases")
        document = yaml.load(text, Loader=StrictSafeLoader)
    except ConfigError:
        raise
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML: {exc}") from exc

    if not isinstance(document, dict):
        raise ConfigError("YAML document root must be a mapping")
    return document


def paths_overlap(input_path: Path, output_path: Path) -> bool:
    """Return whether input and output resolve to the same filesystem location."""
    try:
        if input_path.exists() and output_path.exists():
            return os.path.samefile(input_path, output_path)
    except OSError:
        pass
    return input_path.resolve(strict=False) == output_path.resolve(strict=False)


def atomic_write_yaml(path: Path, document: dict[str, Any], *, force: bool) -> None:
    """Atomically write YAML with mode 0600 and explicit overwrite consent."""
    if path.is_symlink():
        raise ConfigError("Refusing to write through or replace an output symlink")
    if path.exists() and not force:
        raise ConfigError("Output exists; pass --force to replace it")
    parent = path.parent
    if not parent.is_dir():
        raise ConfigError("Output parent directory does not exist")

    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=parent,
            delete=False,
        ) as handle:
            temporary_name = handle.name
            os.chmod(temporary_name, 0o600)
            yaml.safe_dump(document, handle, allow_unicode=True, sort_keys=False)
            handle.flush()
            os.fsync(handle.fileno())
        if force:
            os.replace(temporary_name, path)
        else:
            try:
                os.link(temporary_name, path)
            except FileExistsError as exc:
                raise ConfigError("Output appeared during write; pass --force to replace it") from exc
            Path(temporary_name).unlink()
    except OSError as exc:
        raise ConfigError(f"Cannot write output: {exc}") from exc
    finally:
        if temporary_name:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            except OSError:
                pass
