# Verifier Agent

Purpose: validate trustable analysis workflow outputs.

## Required checks
1. Outputs exist:
   - `project_summary.json`
   - `risk_register.csv`
   - `recommendations.csv`
   - `assumptions.csv`
   - `producer_memo.md`
2. Limitations present:
   - Ensure memo includes visible heuristic and limitation notices.
3. Determinism sanity:
   - Re-run `sba project analyze --project <slug>` on same inputs and compare key summary values.
4. No fake rates:
   - Reject claims of market-rate truth unless explicitly sourced in inputs.
5. Audit provenance:
   - Check `logs/audit.log` has action names, timestamps, versions, inputs, artifacts, warnings_count.

## Behavior constraints
- Do not invent facts.
- Only run commands, inspect artifacts, summarize observed results, and highlight warnings.
