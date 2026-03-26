# Trustable Analysis V2 Ingest Formats

## Script CSV
Required columns:
- `scene_id`
- `int_ext`
- `day_night`
- `location_name`

Optional columns:
- `page_length`
- `cast_names` (pipe-separated, e.g. `A|B|C`)
- `tags` (pipe-separated)
- `raw_text_excerpt`

## Budget CSV
Required columns:
- `account_code`
- `account_name`
- `quantity`
- `unit`
- `rate`
- `total`

Optional columns:
- `source_sheet`

## Schedule CSV (optional)
- Parsed and included in ingest provenance/report.
- Current phase does not perform schedule optimization.

## Ingest report
`outputs/ingest_report.json` includes:
- `missing_fields`
- `guessed_fields`
- `parse_confidence`
- `limitations`
- `warnings`
- `provenance`

Rows with missing required fields are not silently dropped: they are warned and excluded.
