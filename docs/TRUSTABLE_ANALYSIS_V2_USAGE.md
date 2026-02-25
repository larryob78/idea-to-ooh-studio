# Trustable Analysis V2 Usage

## Overview
This prototype provides deterministic analysis, assumptions registry persistence, snapshoting, diffing, and exports.

Persistence uses atomic JSON writes at `.data/trustable_analysis_v2.json` by default.

## CLI
Use module form:

```bash
python -m producer_amplifier.cli --store .data/trustable_analysis_v2.json <command>
```

### Assumptions
```bash
python -m producer_amplifier.cli assumptions add --title "Night permits stable" --description "City permit office indicates normal windows" --source-type quote --confidence 0.8
python -m producer_amplifier.cli assumptions list
python -m producer_amplifier.cli assumptions update <assumption_id> --confidence 0.7
python -m producer_amplifier.cli assumptions delete <assumption_id>
python -m producer_amplifier.cli assumptions export
```

Validation:
- `confidence` must be in `[0,1]`
- `source_type` must be one of: `user_input`, `heuristic`, `quote`, `rule`, `mock`

### Snapshots
Snapshot persistence API (Python):

```python
from producer_amplifier.analysis import analyze_project, AssumptionsRepository, SnapshotsRepository

risks, recs, summary = analyze_project(project)
assumptions = AssumptionsRepository().list()
snapshot_id = SnapshotsRepository().create_snapshot(
    project_id=project.project_id,
    risk_flags=risks,
    recommendations=recs,
    summary_metrics=summary,
    assumptions=assumptions,
    inputs_metadata={"run": "manual"},
    source_files=["script.csv", "budget.csv"],
)
```

CLI:
```bash
python -m producer_amplifier.cli snapshots list <project_id>
python -m producer_amplifier.cli snapshots load <snapshot_id>
python -m producer_amplifier.cli snapshots compare <snapshot_a> <snapshot_b>
```

### Exports
```bash
python -m producer_amplifier.cli export json <snapshot_id> --out-dir exports
python -m producer_amplifier.cli export risks-csv <snapshot_id> --out-dir exports
python -m producer_amplifier.cli export memo-md <snapshot_id> --out-dir exports
python -m producer_amplifier.cli export all <snapshot_id> --out-dir exports --compare-with <prior_snapshot_id>
```

Outputs:
- JSON analysis snapshot report
- CSV risk register
- Markdown producer memo with visible heuristic/limitation notice
