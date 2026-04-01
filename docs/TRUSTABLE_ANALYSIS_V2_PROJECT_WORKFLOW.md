# Trustable Analysis V2 Project Workflow

## Job folder contract
Each project uses `projects/<slug>/` with:
- `inputs/`
- `outputs/`
- `snapshots/`
- `logs/`
- `config/`

## CLI sequence
```bash
sba project init <slug>
sba project ingest --project <slug> --script <script.csv> --budget <budget.csv> [--schedule <schedule.csv>]
sba project analyze --project <slug>
sba project snapshot --project <slug> --label "baseline"
sba project list-snapshots --project <slug>
sba project compare --project <slug> --a <snapshot_a> --b <snapshot_b>
sba project export --project <slug> --format all [--compare <snapshot_a> <snapshot_b>]
```

## Deterministic outputs
Generated into `projects/<slug>/outputs/` with fixed names:
- `ingest_report.json`
- `project_summary.json`
- `risk_register.csv`
- `recommendations.csv`
- `assumptions.csv`
- `producer_memo.md`
- `snapshot_diff.md` (compare)

## Safety/trust
- Heuristics are always labeled and paired with limitations.
- No hidden LLM scoring in deterministic analysis.
- No fake market-rate assertions.
