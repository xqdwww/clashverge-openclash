# Changelog

## Unreleased

### Security

- Preserve owner-only output permissions without a post-finalization path
  operation, closing a local replacement race window.

### Changed

- Update and pin the GitHub Actions checkout and Python setup steps.
- Make the Ruff rule baseline explicit and bound development tooling below the
  next major version so compatible upgrades cannot silently redefine CI.

## [0.1.0] - 2026-07-16

### Added

- Bounded safe YAML loading with duplicate-key rejection.
- Validation for a deliberately limited inline-proxy/select-group subset.
- Local conversion with one manual default group and one final MATCH rule.
- Dry-run, explicit overwrite consent, same-path protection, and atomic 0600
  output.
- Synthetic fixtures, unit tests, CI, security guidance, and provenance record.
