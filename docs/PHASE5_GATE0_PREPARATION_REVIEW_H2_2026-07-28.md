# Phase 5 — Gate 0 Preparation Review: H2 (Long-Term Momentum, 12-1 Month)

**Status.** Preparation review only — not a governance decision, not an ADR, not a Hypothesis-phase registration. Nothing in this document opens `core/research/lifecycle.py`'s Phase 1, and no code, dataset, archive, or governance file was modified to produce it. **Date.** 2026-07-28. **Author basis.** Level 1 — one reader with repository access, compiled from `docs/REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md`, `docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md`, `docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md`, `docs/REFERENCE_H3_DATA_SUFFICIENCY_REPORT.md`, `docs/REFERENCE_H3_RESEARCH_CLOSEOUT.md`, and a direct, read-only inspection of `experiments_etf_universe.db` performed for this review.

**Material finding up front.** This review's read-only database inspection surfaces a fact not reflected in either previously accepted document: the historical-depth question Gate 2 below addresses is **substantially more resolved than `REFERENCE_RESEARCH_ROADMAP_NEXT_V2.md` and `PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` state.** Both describe H2's data feasibility as requiring an extension ("needs deeper history than currently backfilled," "exceeds what the platform's current backfilled history supports"). That was accurate for the ~2-year window `reference_v1`/H1 used, but `reference_h3`'s own Gate 2 (`docs/REFERENCE_H3_DATA_SUFFICIENCY_REPORT.md`) already executed and verified a backfill extension to 2016-09-13 for the full 25-ETF universe, and that extended data is **currently present in the live database** (confirmed directly: `PriceBar` spans 2016-09-13 to 2026-07-17 uniformly across all 25 ETFs, 2,474 rows each). No new backfill work is required for H2's raw-data depth. This does not resolve Gate 2 outright — see below — but it changes what Gate 2 actually requires. If this proposal is accepted, the two prior documents' data-feasibility language should be corrected accordingly, not left standing uncorrected alongside it.

---

## 1. H2 Novelty Gate

**Construction comparison, exact.**

| | `reference_v1` MOMENTUM | H2 (candidate) |
|---|---|---|
| Quantity measured | `SMA(20)`, the 20-day simple moving average of **close price**, used **unnormalized** as the score itself | Trailing 12-month cumulative **return**, formation ending 1 month before the ranking date (literature convention) |
| Units | Dollars (raw price level) | Dimensionless (a ratio / percentage) |
| Scale behavior | Explicitly flagged in `reference_v1`'s own close-out as an unresolved architectural risk: "REFERENCE v1's unnormalized-MOMENTUM... scale mismatch was a real, previously confirmed architectural risk" — a $400 ETF and a $20 ETF are not comparably scored by this construction regardless of trend | Scale-free by construction; a return ratio needs no separate normalization step |
| Formation window | 20 trading days (~1 month) | ~252 trading days (~12 months), with a 1-month skip |

**Is the distinction strong enough?** Stronger than the framing in `PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md` §3 credited it with. That document characterized the two as sharing "the same underlying mechanism label — trend continuation via underreaction," differing mainly in window length. Re-reading `reference_v1`'s literal construction shows a sharper distinction: `SMA(20)` **unnormalized** is not a return, rate-of-change, or trend-strength measure at all — it is an absolute price level — this review's own reading of the construction, not a claim `reference_v1`'s close-out makes directly. What the close-out itself documents is narrower: a scale-dominance risk specifically in *combining* unnormalized MOMENTUM with bounded VALUE ("normalize each dimension's scale before combining, never after") — a blend-level concern, not a standalone critique of `SMA(20)`'s validity as a trend measure. H2, by contrast, is a genuine return-based, scale-free construct. This is a real, citable, constructional difference, not merely a parameter change — a materially stronger novelty basis than either prior Phase 5 document currently states.

**This does not fully close the question.** Two residual risks remain, both empirical rather than definitional:
- Price level and cumulative past return are not independent in practice — an ETF whose price has drifted up over years will tend to have both a higher `SMA(20)` and a higher trailing 12-month return. The two constructs could still be correlated in this specific 25-ETF universe for reasons unrelated to either's own economic story.
- "Momentum" is used as a colloquial label for both in ordinary usage, which is a communication risk for any reviewer or reader who does not read past the label.

**What a Level 2 reviewer would require before freeze:**
1. The written constructional-distinction argument above, formalized as its own reviewed artifact (already flagged as Gate 1 in the prior selection review — this section sharpens what that artifact should contain).
2. **A specific empirical check, not previously proposed in either prior document:** the cross-sectional correlation between `reference_v1`'s `SMA(20)` rank and a trailing-12-1-month-return rank, computed across the same 25-ETF universe and a shared date range. This is a data-suitability check in the same class as H1's GO-checkpoint dispersion check (`docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` §5) — it uses score-side data only, computes no forward return, and carries no look-ahead risk — so it does not itself constitute an experiment or a Hypothesis-phase commitment. A high correlation would not disqualify H2 outright, but would require the novelty argument to address it directly rather than rely on construction differences alone.
3. Confirmation that no version of H2's construction reduces to a renormalized or rescaled `SMA(20)` — i.e., that the distinction survives being expressed in comparable units, not only in its as-implemented form.

## 2. Data Sufficiency Gate

**Required historical depth.** H2's literature convention (12-month formation, 1-month skip) requires at least ~13 months of trailing price history before the first ranking date, plus the forecast horizon's length after the last ranking date (not yet frozen — see Section 3).

**Is current history sufficient?** Yes, at the raw-data level, without further backfill:
- `PriceBar` covers 2016-09-13 to 2026-07-17 for all 25 ETFs identically (verified directly this review, 2,474 rows per ETF, no gaps observed at the per-ETF row-count level).
- This is the same extension `reference_h3`'s Gate 2 executed and archived (`research_archive/reference_h3/data_inventory_2026-07-19_post_extension.json`), reported there as a "~5x increase in effective independent windows" (~25 → ~123) at a 20-day reference horizon — that figure is explicitly a structural estimate ("approx. trading days ÷ 20-day reference horizon... not a commitment to any H3-specific horizon"), reused here only as a scale indicator, not a claim about H2's own effective sample size.
- ~13 months of trailing buffer is trivially available from a start date of 2016-09-13 — the binding constraint historically (`reference_v1`/H1's ~20-23 independent windows, `reference_h3`'s ~7-8) was the **ranking-date panel's span** (all three cycles' panels sat inside the 2024-2026 window), not the underlying price data's depth.

**What remains genuinely open (this is not a "Poor" data-availability problem, but it is not a zero-effort item either):**
- **The extension was executed for H3's purposes and dated 2026-07-19.** The database is caller-supplied and mutable (`README.md`, "Reproducibility limitations"); nothing prevents a subsequent update run from having altered rows since that date. A fresh, dated inventory check — not a citation of H3's snapshot — is required before Methodology Freeze, following the same "not assumed, a checked figure" discipline `reference_h3`'s own report used.
- **H3's extension was verified adequate for H3's own 60-day trailing construction; it has not been separately verified for a 12-month trailing return calculation.** A 12-month window crosses far more dividend and corporate-action events per ETF than a 60-day window does. The dividend-adjustment concern already disclosed elsewhere in this project's record (`research_archive/reference_h4/decision_log.md`: "the dividend-adjustment component remains genuinely unconfirmed") is more consequential for a 12-month return than for a 60-day volatility measure, and has not been checked for this data at all.
- **The ranking-date panel span is a specification decision, not a data question, and is currently undecided.** `reference_v2_h1`'s own spec explicitly chose to reuse `reference_v1`'s narrow 2024-2026 window "for infrastructure comparability only," not because deeper data was unavailable — the same choice is available to H2 but is not automatic, and needs its own stated justification either way, per `docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md` §D item 6 ("explicit, deliberate choice of dataset window... never an implicit inheritance").

**What a defensible extension requirement looks like, given the above:** not a new backfill request. A defensible Gate 2 for H2 consists of (a) a fresh, dated data-inventory re-check of the existing 2016-2026 range specifically for 12-month-window integrity (gap count, corporate-action/dividend-adjustment consistency), and (b) a written, pre-registered decision on how much of the available 2016-2026 span the ranking-date panel will actually use — analogous in form to `reference_h3`'s own Data Sufficiency Report, not a repeat of its backfill work.

## 3. Freeze Preparation — Pre-Registration Checklist (Draft)

The following mirrors the structure `docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` used for H1, adapted to what H2 would need to fix in writing before Phase 1 (Hypothesis) closes. **No item below is answered by this document — each is listed as an open decision to be resolved at freeze, not a proposed default.**

- [ ] **Hypothesis statement.** Exact, falsifiable form (e.g., "ETFs ranked higher by trailing 12-month return, skipping the most recent month, will show higher forward returns at horizon H than ETFs ranked lower"), stated before any code is written.
- [ ] **Economic rationale.** Written mechanism (underreaction / slow information diffusion, per the literature basis in Section 1), including the explicit novelty argument against `reference_v1` MOMENTUM required by Gate 1.
- [ ] **Signal definition.** Exact formation window (12 months — confirm trading-day count, not calendar-day count), exact skip length (1 month, confirm trading-day count), return calculation basis (close-to-close, log or simple — must match or explicitly deviate from prior cycles' log-return convention), and treatment of dividends/distributions in the return calculation (the open item flagged in Gate 2).
- [ ] **Ranking method.** Cross-sectional rank basis (raw return value vs. rank order), tie-handling convention (reuse the existing average-rank convention per prior cycles, or justify a deviation), and minimum-panel-size rule for any ranking date (prior cycles used ≥10 valid ETFs — confirm reuse or justify a different threshold).
- [ ] **Forecast horizon.** Fixed before any outcome data is examined — reuse the pipeline's 20-day default (for statistical-machinery compatibility, as H1 did) or adopt a literature-typical longer horizon with its own written justification. This is Gate 3 of the prior selection review and remains unresolved.
- [ ] **Evaluation metrics.** Statistic(s) to be tested (daily cross-sectional Spearman IC, consistent with all three prior cycles), significance test (within-date permutation, 10,000+ iterations), multiple-comparison correction if more than one statistic is tested jointly (Holm-Bonferroni, per established convention), and bootstrap-robustness protocol (block bootstrap at 20/40/60-day blocks, matching prior cycles unless a different block structure is separately justified for a 12-month-formation signal).
- [ ] **Rejection criteria.** The exact promotion/non-promotion rule, fixed before results are seen: Holm-Bonferroni-adjusted significance **and** bootstrap-CI-excludes-zero across all frozen block lengths, per the bar all three prior cycles were held to — or an explicit, pre-registered justification for any deviation from that bar.
- [ ] **Ranking-date panel span.** Not part of H1's own checklist (H1 inherited v1's window without a live alternative to weigh), but live for H2 given Section 2's finding: an explicit, written choice of how much of the 2016-2026 range to use, with its own stated rationale.

## 4. Governance Boundary

**What this review, and preparation like it, may do under Phase 5 research-preparation activity — no lifecycle phase opened, no code written:**
- Compare existing frozen constructions from closed close-out documents (Section 1).
- Inspect existing repository data read-only to check factual premises (Section 2) — this review's database query was a read, not a write; no row was inserted, updated, or deleted.
- Draft a pre-registration checklist identifying what must be decided (Section 3) without deciding it.
- Identify open questions and next-step evidence needs for a future Level 2 reviewer.

**What would cross into implementation work, requiring Phase 1 (Hypothesis) to actually open first:**
- Writing or running the Gate 1 correlation check (Section 1, item 2) or the Gate 2 data-inventory re-check (Section 2) — both require new code in `experiments/`, even though they are data-suitability checks rather than full experiments in this project's own convention (per H1's GO-checkpoint precedent). Producing them is Pre-validation-phase evidence, not Gate-0 preparation.
- Any answer to the Section 3 checklist becoming binding — that requires Phase 2 (Research Proposal) and Phase 4 (Methodology Freeze) under `docs/RESEARCH_GOVERNANCE_STANDARD.md`, with the AD-072 Level 2 floor applying at each transition into those phases.

**What would require a new governance decision (an AD), which nothing in this review proposes:** none identified for H2 specifically. The extended 2016-2026 dataset already fits within `dataset_manifest.py`'s existing per-source-table hash/row-count schema (`MANIFEST_SCHEMA_VERSION = 3`) — using a longer date range at Methodology Freeze is a larger manifest, not a schema change, and does not touch AD-072's floor table, AD-073/074's archive-seal mechanism, or AD-077's engine-neutrality boundary.

**What would require archive or reproduction-tooling changes:** none until Methodology Freeze. At that point, `core/governance/dataset_manifest.py` and `reconstruction_loader.py` would need to hash and pin whatever `PriceBar`/`TradingSession` range H2's frozen specification actually selects (Section 3's last checklist item) — existing machinery, exercised with new parameters, not new machinery. No archive-seal or reproduction-runner code change is implied by anything in this review.

---

**Net effect of this proposal, if accepted:** Gate 2 (data sufficiency) is materially easier than the two prior accepted documents currently state, and should be corrected there rather than left inconsistent. Gate 1 (novelty) has a stronger, more specific argument available than previously articulated, but gains one new required evidence item (the correlation check) that neither prior document named. Gates remain open; nothing here authorizes Phase 1 to begin.
