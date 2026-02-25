# Trustable Analysis V2 Claude Code Integration

## Added files
- `CLAUDE.md`
- `.claude/commands/project_init.md`
- `.claude/commands/ingest_project.md`
- `.claude/commands/analyze_project.md`
- `.claude/commands/snapshot_project.md`
- `.claude/commands/compare_snapshots.md`
- `.claude/commands/export_artifacts.md`
- `.claude/agents/verifier.md`

## Command policy
Claude commands must:
- Run actual CLI commands.
- Summarize observed outputs only.
- Surface warnings and limitations prominently.
- Never invent facts or market-rate claims.

## Verifier policy
Verifier checks:
- expected outputs exist
- limitations are visible
- deterministic rerun sanity
- no fake market rates
- audit log has required provenance fields
