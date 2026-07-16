# Clean-room Blocker Resolution

Date: 2026-07-16

| finding_id | severity | affected_file | affected_lines_or_history | category | evidence | required_resolution | resolution_status |
|---|---|---|---|---|---|---|---|
| CL-PRIV-001 | P0 | Prior candidate audit output | Two prior reachable commits | Git history privacy | Prior Codex audit found private local identifiers in tracked reports | Publish from a new root with no inherited Git objects and rescan all objects | RESOLVED_BY_NEW_ROOT_AND_FULL_SCAN |
| CL-LIC-001 | P1 | Prior formal source and candidate core | Project-specific group/rule design | Unknown source authorization | Formal source had no explicit grant and prior candidate materially derived its design | Copy no old implementation; independently implement only a public documented subset | RESOLVED_BY_CLEAN_ROOM_REIMPLEMENTATION |
| CL-SCOPE-001 | P1 | Prior feature design | Health checks, router/deployment context | Product/security scope | Publication task excludes network, SSH, router, subscription, and remote-control features | Omit all excluded features and enforce scope in docs/tests | RESOLVED |
| CL-SRC-001 | P1 | All clean-room source files | Current tree | Code provenance | Public release requires file-level authorship and dependency record | Record source, evidence, license, and final handling in `code_provenance.md` | RESOLVED |
| CL-PRIV-002 | P1 | Fixtures and documentation | Current tree | Current-tree privacy | Public repository must not include real proxy or private path data | Use TEST-NET fixtures and synthetic credentials; run current/history scans | RESOLVED |
| CL-REL-001 | P1 | Entire clean-room | Pre-release state | Release validation | Tests, install, CLI, CI, license, provenance, Git cleanliness, and no-remote gates required | Complete independent audit before any repository, tag, or release action | RESOLVED_WITH_EXTERNAL_RELEASE_AUDIT |
