# Trustable Analysis V2 Changelog

## Follow-up run (Phase A-G)
- Added assumptions registry model, validation, JSON persistence, and CRUD repository.
- Extended risks and recommendations to include `assumptions_used`.
- Added snapshot persistence (`create`, `list`, `load`) with provenance and assumptions frozen at analysis time.
- Added deterministic snapshot diff engine and human-readable diff summary.
- Added export generators for JSON reports, CSV risk register, and Markdown producer memo.
- Added CLI wiring for assumptions, snapshots, compare, and exports.
- Added tests for assumptions, snapshots, compare, and exports.
