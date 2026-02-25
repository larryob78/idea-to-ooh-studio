# Command: export_artifacts

Export producer-ready artifacts:

```bash
sba project export --project <slug> --format all [--compare <snapshot_id_a> <snapshot_id_b>]
```

Expected output files in `projects/<slug>/outputs/`:
- `project_summary.json`
- `risk_register.csv`
- `recommendations.csv`
- `assumptions.csv`
- `producer_memo.md`
- `snapshot_diff.md` (when compare provided)
