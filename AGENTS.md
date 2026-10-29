## Agent skills

### Issue tracker

Issues and specs live as GitHub issues. See `docs/agents/issue-tracker.md`.

### Triage labels

Canonical roles use same-named labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `GLOSSARY.md` and `docs/adr/`. See `docs/agents/domain.md`.

### Python

Before writing or editing Python, read `CODING_STANDARD.md`.

### Checks

`make lint` is local. `make test` continues into live Aurora Data API calls and needs `AURORA_CLUSTER_ARN` (the Cluster) and `AURORA_SECRET_ARN` (the Secret).

### Coding standard

When writing or editing Python, read `CODING_STANDARDS.md`.
