# Code Provenance

Date: 2026-07-16

Status: `CLEAN_ROOM_PROVENANCE_RECORDED`

This is an engineering provenance record, not legal advice.

## Clean-room boundary

- The prior candidate repository was used only as an audit record identifying
  what must not be published.
- No prior `.git` directory, commit, source file, fixture, report, patch,
  project-specific 12-group design, service rules, candidate lists, health
  checks, SSH logic, router paths, or private-environment integration was copied,
  cherry-picked, grafted, merged, or imported.
- The implementation was newly authored for this clean-room repository from the
  product boundary in the publication task and public configuration-format
  documentation.

## Public interoperability evidence

| Reference | Evidence pinned during review | Use |
|---|---|---|
| MetaCubeX Meta-Docs | commit `824be43699b2b6dcb0c0bf4d7a0412884c7b17c7` | Public YAML, proxy-group, and rule shapes only |
| OpenClash | commit `1c8e8cb8eaad0edaae11928c9b802b7d613c0f97`, repository reports MIT | Project identity and interoperability context only |
| PyYAML | commit `34a9bf82357f4952d8f194a5a31f1c39743652d0`, MIT | Runtime dependency through package management |

At review time the public `MetaCubeX/mihomo` repository metadata appeared
unrelated to the documented proxy core, so no code or license conclusion was
taken from that repository. The separate Meta-Docs pages were used as the
functional format reference.

## File-level record

| File or area | Function | Source and author | Third-party adaptation | MIT release status | Final handling |
|---|---|---|---|---|---|
| `src/clashverge_openclash/yamlio.py` | Bounded safe YAML and atomic file I/O | Newly authored in this clean-room task for project contributors | None; calls public PyYAML API | Eligible under repository MIT grant | Retain |
| `src/clashverge_openclash/model.py` | Supported-subset validation | Newly authored from task requirements and public format shapes | None | Eligible under repository MIT grant | Retain |
| `src/clashverge_openclash/converter.py` | Minimal group/MATCH transformation | Newly authored from task requirements and public format shapes | None | Eligible under repository MIT grant | Retain |
| `src/clashverge_openclash/cli.py` | Local argparse CLI | Newly authored in this clean-room task | None | Eligible under repository MIT grant | Retain |
| `tests/` and fixtures | Synthetic regression evidence | Newly authored in this clean-room task | None | Eligible under repository MIT grant | Retain |
| Documentation and CI | Scope, maintenance, and verification policy | Newly authored in this clean-room task; public links are citations only | No copied upstream text or workflow | Eligible under repository MIT grant | Retain |

## Third-party handling

PyYAML is referenced as a normal MIT-licensed dependency and is not vendored.
No upstream Clash, Mihomo, OpenClash, or Clash Verge source, binary, asset,
copyright header, or NOTICE file is included. Compatibility names are used only
to describe the local file format and intended output context, with explicit
non-affiliation language.

## Conclusion

All publishable implementation and test files have a documented clean-room
origin. No source with unknown permission remains. The repository publisher
applies the repository's MIT license to the newly authored contents.
