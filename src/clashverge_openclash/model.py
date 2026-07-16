"""Validation for the deliberately small supported configuration subset."""

from __future__ import annotations

from typing import Any

from .yamlio import ConfigError


SUPPORTED_TOP_LEVEL = {
    "port",
    "socks-port",
    "mixed-port",
    "allow-lan",
    "mode",
    "log-level",
    "ipv6",
    "dns",
    "proxies",
    "proxy-groups",
    "rules",
}
BUILTIN_TARGETS = {"DIRECT", "REJECT"}
GROUP_FIELDS = {"name", "type", "proxies"}
SUPPORTED_RULE_TYPES = {
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "GEOIP",
    "IP-CIDR",
    "IP-CIDR6",
    "MATCH",
}


def _required_name(item: Any, label: str) -> str:
    if not isinstance(item, dict):
        raise ConfigError(f"Each {label} must be a mapping")
    name = item.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ConfigError(f"Each {label} must have a non-empty string name")
    name = name.strip()
    if "," in name:
        raise ConfigError(f"{label.title()} names must not contain commas")
    return name


def _proxy_names(document: dict[str, Any]) -> list[str]:
    proxies = document.get("proxies")
    if not isinstance(proxies, list) or not proxies:
        raise ConfigError("proxies must be a non-empty list of inline proxy mappings")
    names = []
    for proxy in proxies:
        name = _required_name(proxy, "proxy")
        for field in ("type", "server"):
            if not isinstance(proxy.get(field), str) or not proxy[field].strip():
                raise ConfigError(f"Proxy {name!r} must have a non-empty string {field}")
        port = proxy.get("port")
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            raise ConfigError(f"Proxy {name!r} must have an integer port from 1 to 65535")
        names.append(name)
    if len(names) != len(set(names)):
        raise ConfigError("Proxy names must be unique")
    collisions = set(names) & BUILTIN_TARGETS
    if collisions:
        raise ConfigError(f"Proxy names must not use builtin targets: {sorted(collisions)}")
    return names


def _group_map(document: dict[str, Any]) -> dict[str, list[str]]:
    groups = document.get("proxy-groups", [])
    if not isinstance(groups, list):
        raise ConfigError("proxy-groups must be a list")
    result: dict[str, list[str]] = {}
    for group in groups:
        name = _required_name(group, "proxy group")
        if name in BUILTIN_TARGETS:
            raise ConfigError(f"Proxy group name {name!r} is a reserved builtin target")
        if name in result:
            raise ConfigError("Proxy group names must be unique")
        unknown = set(group) - GROUP_FIELDS
        if unknown:
            raise ConfigError(f"Unsupported fields in select group {name!r}: {sorted(unknown)}")
        if group.get("type") != "select":
            raise ConfigError("Only type: select proxy groups are supported in v0.1.0")
        members = group.get("proxies")
        if not isinstance(members, list) or not members:
            raise ConfigError(f"Proxy group {name!r} must contain a non-empty proxies list")
        if not all(isinstance(member, str) and member.strip() for member in members):
            raise ConfigError(f"Proxy group {name!r} members must be non-empty strings")
        normalized = [member.strip() for member in members]
        if len(normalized) != len(set(normalized)):
            raise ConfigError(f"Proxy group {name!r} members must be unique")
        result[name] = normalized
    return result


def _check_group_references(proxy_names: list[str], groups: dict[str, list[str]]) -> None:
    collisions = set(proxy_names) & set(groups)
    if collisions:
        raise ConfigError(f"Proxy and group names must not collide: {sorted(collisions)}")
    allowed = set(proxy_names) | set(groups) | BUILTIN_TARGETS
    for name, members in groups.items():
        unknown = [member for member in members if member not in allowed]
        if unknown:
            raise ConfigError(f"Proxy group {name!r} references unknown targets: {unknown}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visiting:
            raise ConfigError(f"Proxy group cycle detected at {name!r}")
        if name in visited:
            return
        visiting.add(name)
        for member in groups[name]:
            if member in groups:
                visit(member)
        visiting.remove(name)
        visited.add(name)

    for group_name in groups:
        visit(group_name)


def rule_target(rule: str) -> str:
    """Extract the target from a documented comma-separated rule."""
    if not isinstance(rule, str):
        raise ConfigError("Each rule must be a string")
    parts = [part.strip() for part in rule.split(",")]
    if len(parts) < 2 or any(not part for part in parts):
        raise ConfigError(f"Invalid rule syntax: {rule!r}")
    kind = parts[0].upper()
    if kind not in SUPPORTED_RULE_TYPES:
        raise ConfigError(f"Unsupported rule type: {kind!r}")
    if kind == "MATCH":
        if len(parts) != 2:
            raise ConfigError(f"MATCH requires exactly one target: {rule!r}")
        return parts[1]
    if len(parts) not in (3, 4):
        raise ConfigError(f"Rule requires value and target: {rule!r}")
    if len(parts) == 4:
        if parts[-1].lower() != "no-resolve":
            raise ConfigError(f"Unsupported fourth rule field: {rule!r}")
        return parts[-2]
    return parts[-1]


def _validate_common_fields(document: dict[str, Any]) -> None:
    for key in ("port", "socks-port", "mixed-port"):
        if key in document:
            value = document[key]
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 65535:
                raise ConfigError(f"{key} must be an integer from 1 to 65535")
    for key in ("allow-lan", "ipv6"):
        if key in document and not isinstance(document[key], bool):
            raise ConfigError(f"{key} must be a boolean")
    if "dns" in document and not isinstance(document["dns"], dict):
        raise ConfigError("dns must be a mapping")


def validate_document(document: dict[str, Any], *, require_target_shape: bool) -> None:
    """Validate a source subset or a complete generated target."""
    unknown = set(document) - SUPPORTED_TOP_LEVEL
    if unknown:
        raise ConfigError(f"Unsupported top-level keys: {sorted(unknown)}")
    _validate_common_fields(document)
    proxy_names = _proxy_names(document)
    groups = _group_map(document)
    _check_group_references(proxy_names, groups)

    rules = document.get("rules", [])
    if not isinstance(rules, list):
        raise ConfigError("rules must be a list")
    allowed_targets = set(proxy_names) | set(groups) | BUILTIN_TARGETS
    match_positions: list[int] = []
    for index, rule in enumerate(rules):
        target = rule_target(rule)
        kind = rule.split(",", 1)[0].strip().upper()
        if target not in allowed_targets:
            raise ConfigError(f"Rule references unknown target {target!r}")
        if kind == "MATCH":
            match_positions.append(index)

    if len(match_positions) > 1:
        raise ConfigError("At most one MATCH rule is allowed")
    if match_positions and match_positions[0] != len(rules) - 1:
        raise ConfigError("MATCH must be the final rule")
    if require_target_shape:
        if document.get("mode") != "rule":
            raise ConfigError("Generated target must set mode: rule")
        if not groups:
            raise ConfigError("Generated target must contain a proxy group")
        if match_positions != [len(rules) - 1]:
            raise ConfigError("Generated target must end with exactly one MATCH rule")
