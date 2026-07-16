from __future__ import annotations

from copy import deepcopy

import pytest

from clashverge_openclash.converter import convert_document
from clashverge_openclash.model import rule_target, validate_document
from clashverge_openclash.yamlio import ConfigError


def source_document() -> dict:
    return {
        "proxies": [
            {"name": "Alpha", "type": "ss", "server": "192.0.2.10", "port": 443},
            {"name": "Beta", "type": "socks5", "server": "192.0.2.20", "port": 1080},
        ],
        "rules": ["DOMAIN-SUFFIX,example.test,DIRECT"],
    }


def test_conversion_adds_one_select_group_and_final_match():
    result = convert_document(source_document())

    assert result["mode"] == "rule"
    assert result["proxy-groups"] == [
        {"name": "OPENCLASH", "type": "select", "proxies": ["DIRECT", "Alpha", "Beta"]}
    ]
    assert result["rules"][-1] == "MATCH,OPENCLASH"


def test_conversion_does_not_mutate_source():
    source = source_document()
    before = deepcopy(source)

    convert_document(source)

    assert source == before


def test_existing_select_group_and_match_are_preserved():
    source = source_document()
    source["proxy-groups"] = [{"name": "Manual", "type": "select", "proxies": ["Alpha", "DIRECT"]}]
    source["rules"].append("MATCH,Manual")

    result = convert_document(source)

    assert result["proxy-groups"] == source["proxy-groups"]
    assert result["rules"].count("MATCH,Manual") == 1


def test_explicit_default_target_is_used():
    result = convert_document(source_document(), default_target="DIRECT")
    assert result["rules"][-1] == "MATCH,DIRECT"


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda doc: doc.update({"external-controller": "disabled"}), "Unsupported top-level"),
        (lambda doc: doc.update({"proxies": []}), "non-empty list"),
        (lambda doc: doc["proxies"].append(deepcopy(doc["proxies"][0])), "unique"),
        (
            lambda doc: doc.update(
                {"proxy-groups": [{"name": "Auto", "type": "url-test", "proxies": ["Alpha"]}]}
            ),
            "Only type: select",
        ),
        (
            lambda doc: doc.update(
                {"proxy-groups": [{"name": "Manual", "type": "select", "proxies": ["Missing"]}]}
            ),
            "unknown targets",
        ),
        (lambda doc: doc["rules"].append("MATCH,Missing"), "unknown target"),
        (lambda doc: doc["rules"].append("BOGUS,value,DIRECT"), "Unsupported rule type"),
        (lambda doc: doc.update({"mixed-port": 70000}), "mixed-port"),
        (lambda doc: doc.update({"allow-lan": "no"}), "allow-lan"),
        (lambda doc: doc.update({"dns": []}), "dns must be a mapping"),
        (
            lambda doc: doc.update({"rules": ["MATCH,DIRECT", "DOMAIN,example.test,DIRECT"]}),
            "MATCH must be the final",
        ),
        (
            lambda doc: doc.update({"rules": ["MATCH,DIRECT", "MATCH,REJECT"]}),
            "At most one MATCH",
        ),
    ],
)
def test_invalid_source_shapes_are_rejected(change, message):
    source = source_document()
    change(source)
    with pytest.raises(ConfigError, match=message):
        validate_document(source, require_target_shape=False)


def test_group_cycle_is_rejected():
    source = source_document()
    source["proxy-groups"] = [
        {"name": "A", "type": "select", "proxies": ["B"]},
        {"name": "B", "type": "select", "proxies": ["A"]},
    ]
    with pytest.raises(ConfigError, match="cycle"):
        validate_document(source, require_target_shape=False)


def test_proxy_group_name_collision_is_rejected():
    source = source_document()
    source["proxy-groups"] = [{"name": "Alpha", "type": "select", "proxies": ["Beta"]}]
    with pytest.raises(ConfigError, match="must not collide"):
        validate_document(source, require_target_shape=False)


def test_reserved_default_group_proxy_name_is_rejected():
    source = source_document()
    source["proxies"][0]["name"] = "OPENCLASH"
    with pytest.raises(ConfigError, match="reserved"):
        convert_document(source)


def test_proxy_requires_type_server_and_valid_port():
    source = source_document()
    del source["proxies"][0]["server"]
    with pytest.raises(ConfigError, match="server"):
        validate_document(source, require_target_shape=False)


def test_unknown_explicit_default_is_rejected():
    with pytest.raises(ConfigError, match="Default target"):
        convert_document(source_document(), default_target="Unknown")


def test_target_requires_rule_mode_group_and_final_match():
    with pytest.raises(ConfigError, match="mode: rule"):
        validate_document(source_document(), require_target_shape=True)


def test_no_resolve_target_parsing():
    assert rule_target("IP-CIDR,192.0.2.0/24,DIRECT,no-resolve") == "DIRECT"
