"""Clean-room transformation of the documented supported subset."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .model import BUILTIN_TARGETS, validate_document
from .yamlio import ConfigError


DEFAULT_GROUP_NAME = "OPENCLASH"


def convert_document(
    source: dict[str, Any], *, default_target: str | None = None
) -> dict[str, Any]:
    """Create a rule-mode target without adding remote-management features."""
    validate_document(source, require_target_shape=False)
    target = deepcopy(source)
    proxy_names = [proxy["name"].strip() for proxy in target["proxies"]]

    groups = target.get("proxy-groups", [])
    if not groups:
        if DEFAULT_GROUP_NAME in proxy_names:
            raise ConfigError(f"Proxy name {DEFAULT_GROUP_NAME!r} is reserved for the default group")
        groups = [
            {
                "name": DEFAULT_GROUP_NAME,
                "type": "select",
                "proxies": ["DIRECT", *proxy_names],
            }
        ]
        target["proxy-groups"] = groups

    available_targets = {group["name"] for group in groups} | set(proxy_names) | BUILTIN_TARGETS
    chosen_target = default_target or groups[0]["name"]
    if chosen_target not in available_targets:
        raise ConfigError(f"Default target {chosen_target!r} is not a proxy, group, or builtin")

    rules = list(target.get("rules", []))
    if not rules or rules[-1].split(",", 1)[0].strip().upper() != "MATCH":
        rules.append(f"MATCH,{chosen_target}")
    target["rules"] = rules
    target["mode"] = "rule"
    validate_document(target, require_target_shape=True)
    return target
