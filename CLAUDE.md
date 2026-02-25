# CLAUDE Code Operating Conventions

## Project workflow contract
- Each job lives at `projects/<slug>/`.
- Required folders:
  - `inputs/`
  - `outputs/`
  - `snapshots/`
  - `logs/`
  - `config/`

## Trust and safety rules
- Never invent market rates or represent mock inputs as factual rates.
- Never hide heuristic behavior; surface `is_heuristic` and limitations in summaries.
- Never perform destructive operations on project folders unless explicitly instructed.
- Never claim a command succeeded without checking output artifacts.

## Verification checklist
1. Confirm required outputs exist in `projects/<slug>/outputs/`.
2. Confirm `producer_memo.md` includes heuristic and limitation notices.
3. Run deterministic sanity check by re-running analysis on unchanged inputs and confirming stable summary values.
4. Confirm `logs/audit.log` has JSONL entries for each action.
5. Confirm no fake market-rate references are introduced.
