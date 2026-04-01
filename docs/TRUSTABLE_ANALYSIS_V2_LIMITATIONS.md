# Trustable Analysis V2 Limitations

## Current limitations
- Heuristic indicators (`overtime`, `cast concentration`, `night concentration`) are deterministic proxies and not schedule-engine outputs.
- No full scheduling engine, union-rule calculator, or market-rate database is included.
- Assumptions persistence is local JSON file storage (atomic file replacement), not multi-user transactional DB.
- Snapshot compare is structural and deterministic but does not include semantic NLP explainers.
- Exports are JSON/CSV/Markdown only in this phase.

## Data confidence boundaries
- Parsed evidence comes from provided project scene/budget inputs.
- User assumptions and quote/mock assumptions are persisted explicitly and surfaced in outputs.
- Mock placeholders are never presented as real market data.

## Safety notes
- Deterministic scoring contains no hidden LLM scoring calls.
- Heuristic outputs are marked with `is_heuristic` and `limitations`.
