# research_archive/

Frozen, git-tracked snapshots of completed research validation runs —
the evidence behind a research close-out, preserved so it can never be
silently overwritten by a later run of the same tooling.

This directory exists because `experiments/` scripts write their
machine-readable output (e.g.
`reference_v1_significance_report.json`) to a fixed path at the repo
root, and that path is gitignored by design — every rerun regenerates
it, which is correct for day-to-day iteration but means the *specific*
result a conclusion was drawn from has no durable copy once a later run
overwrites it. A snapshot copied in here, under a dated filename, is
never touched by future runs.

One subdirectory per frozen reference profile:

```
research_archive/
  reference_v1/
    reference_v1_significance_report_2026-07-18.json   # dated, frozen copy of the completed run's output
    COMMIT.txt                                          # the exact commit the result was produced against
    README.md                                           # what this is, links to the close-out doc
```

## Conventions

- **Snapshot, never regenerate in place.** Files here are copies, made
  once, at the point a research cycle is closed out. Nothing in this
  directory is produced by running a script against it — scripts still
  write to their own gitignored working paths as before; a snapshot is
  a manual, deliberate copy taken afterward.
- **Every snapshot pairs with a `COMMIT.txt`** recording the exact
  commit hash the result was produced against, so the snapshot can
  always be tied back to the exact source code (scoring profile
  definition, statistical methodology, ETF universe, script versions)
  that produced it.
- **Every snapshot pairs with a short `README.md`** stating what the
  snapshot is and pointing at the full close-out document in `docs/`
  (e.g. `docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md`) — this directory
  holds evidence, not narrative; the narrative lives in `docs/`.
- **One subdirectory per reference profile**, named after the profile
  it archives (`reference_v1/`, and `reference_v2/` etc. if and when a
  future profile reaches its own close-out). Each subdirectory is
  self-contained and never overwritten once written.
- Nothing here is consumed by `core/`, `adapters/`, or any
  `experiments/` script at runtime — this is a documentation/evidence
  archive only, with the same "not part of the production platform"
  boundary the rest of `experiments/` and `docs/` already have.
