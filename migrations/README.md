# Migration policy

`run_migrations` (see `core/market_data/persistence/migrations.py`) applies every
`*.sql` file in this directory exactly once, tracked by filename in
`schema_migrations`. That mechanism only works if migration files are stable
once applied. This directory follows one rule:

- **`0001_initial_schema.sql` is pre-release and may still be edited in place.**
  It has been amended during Phase 0 development because no real database has
  ever existed — every application of it so far has been against an ephemeral
  test database created and discarded within a single test run.
- **The moment a real (non-test) database is created from it, `0001` is frozen.**
  From that point on it must never be edited again, for any reason, including
  bug fixes.
- **Every schema change after that point ships as a new, additive migration**
  (`0002_*.sql`, `0003_*.sql`, ...). Additive means: new tables, new nullable/
  defaulted columns, new indexes, new triggers. It does not rewrite or delete
  the contents of a migration that has already been released.
- If a released migration turns out to be wrong, the fix is a new forward
  migration that corrects the effect (e.g. a follow-up `ALTER TABLE` or a
  corrective backfill) — never an edit to the original file's history.

This rule is what makes `schema_migrations` a trustworthy audit log instead of
just a cache: once real data exists, the filename-to-SQL mapping it tracks
must stay honest forever.
