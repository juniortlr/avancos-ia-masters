---
name: data-provenance-and-contracts
description: "Use when: first opening a new dataset or extract, joining two data sources, writing an ETL or extraction script, checking whether a column means what its name says, sealing data for reproducibility, hashing or versioning inputs, handling sentinel and missing values, resampling or regridding a time series, anonymising identifiers, or debugging a join that returns zero rows or duplicated rows"
---

# Data Provenance and Contracts

Before an analysis can be wrong, the data has to be misunderstood. This step is where that gets
caught — and it is almost always cheaper here than three weeks later.

## 1. Seal before you analyse

Reproducibility means someone can prove they have the same bytes you had. Build a manifest:

- per file: **SHA-256**, byte size, row count, column list, source system, extraction date,
  and the script or query that produced it
- a **single digest over the whole manifest**, so one comparison proves the whole set
- a `--check` mode that recomputes and exits non-zero on drift

**Keep `generated_at` and any other timestamp *outside* the hashed payload.** A manifest that
hashes its own creation time can never reproduce, and the check can never pass.

Prefer file footers/metadata over full reads for row counts where the format supports it — a
seal you can afford to re-run is a seal you will re-run.

Raw data usually should not be committed. The manifest is the reproducibility artifact; the data
is an input you can re-fetch.

## 2. Ask what one row *is*

The most damaging class of error, because nothing about it looks wrong.

- **Is this a measurement series, or a resampled grid?** A source that emits every few minutes,
  forward-filled onto a fixed grid, looks like a high-rate series and is not. Inspect source timestamps, quality flags and update counters; constant runs and distinct-value counts are diagnostics, not proof of the source sampling rate. A hundred-fold inflation of the sample count is common,
  and every per-unit n in every spec downstream is then wrong.
- **Does the resampling invent values?** A mean over a grid cell that spans a transition emits a
  value that lies strictly between its neighbours — a value the instrument never produced.
  Compare against source records and aggregation semantics. A value strictly between neighbors can be genuine; flag it and preserve raw data. Exclude only under a documented measurement rule, with sensitivity checks.
- **What is the grain?** One row per unit per event, or per unit per field? An index column that
  is a *field selector* rather than a unit identifier will silently average incompatible units into one meaningless mean.
- **Does the same column name mean the same thing in two sources?** Frequently not.

Write the answers down. This is the data contract.

## 3. Sentinels are column-scoped, never value-global

A global "these values are missing" list will delete real data. The same number is a sentinel in
one column and a genuine reading in another — a documented reserved code may be a sentinel in one channel and a valid measurement in another; never infer sentinel status solely from a value.

Scope every sentinel to its column, test the scoping, and record which columns are **entirely
null** rather than sentinel-filled — those are a different failure and have a different fix.

Watch for **zero as a sentinel**. A device that reports 0 for "not fitted" or "not initialised"
puts a value on no standard missing-data list, and in a percentage target a 0 is an artifact
step of one hundred points.

## 4. Verify the field exists — in the authoritative catalogue

Helper tools and convenience lookups lie by omission: they check one naming pattern and miss
suffixed, split or versioned variants of the same object, then report "does not exist".

- Check the **system catalogue** (`sys.objects`, `INFORMATION_SCHEMA`, the data dictionary),
  not a wrapper's existence check.
- Before referencing a derived or joined view in a query, confirm **that specific object**
  exists. Assuming a naming convention holds across a family is how a pipeline breaks at refresh
  rather than at authoring time.
- Never extrapolate an identifier sequence. Codes that look contiguous routinely are not, and
  the neighbouring code often belongs to a completely unrelated family. Resolve each one.

## 5. Joins

- **Prefer a verified event key.** Two extracts of the same event can carry
  clocks that differ by a fixed offset, or a DST-aware offset, or a timezone. Joining on
  timestamp then silently returns near-zero matches while looking like a legitimate low-overlap
  result. Test it: take a shared key, difference the timestamps, and look at the distribution.
- **Check keys before designing around them.** Without a shared key, record linkage or calibrated temporal alignment may be necessary. Quantify linkage uncertainty and do not assume records match. If reliable linkage is unavailable, restrict paired validation claims.
- If no shared event key exists, a temporal/as-of join can be valid after timezone/clock calibration, tolerance and direction checks. Enforce no-future matching for prediction. Aggregating first still requires compatible coverage windows and a compatible estimand.
- After any join, report **rows in, rows out, and unmatched on both sides.** Declare expected cardinality (1:1, m:1 or deliberate 1:m). Unexpected multiplication is a bug; intended expansion is not.

## 6. Identifiers and confidentiality

If identifiers are sensitive, alias them (`CH001`) with the linkage kept out of version control,
and make the rule **executable** — a test that fails when a raw identifier appears in the
committed surface. Note that such a test reads the live file surface, so an ignore-file change
can move it; re-baseline only when the exposed set **shrinks**.

## 7. Coverage before conclusions

Build a coverage matrix: per unit, per signal, first and last timestamp, count, null fraction.
Then check the thing everyone assumes:

- Is the history you need actually **in the extract**, or only in the source table? Catalogue
  coverage and extract coverage are different numbers, and the gap means a re-extraction, not a
  recomputation.
- Is missingness **conditional on the thing you are studying**? Compute
  P(target present | covariates present) inside each unit's own window. A high conditional availability is a coverage diagnostic, not proof that dropout is noninformative. Examine observation timing, outcomes, selection and plausible unobserved drivers.
- Do any units continue under a **different identifier**? Check for adjacent windows plus a
  continuous monotone counter (sequence or cumulative observation counter) across the seam.
  Merging two ids that are one unit changes every per-unit n.

## Output

A short data-contract note plus a test file that asserts it. Several assertions should encode
defects that **currently exist** — a test that fails when a known problem is fixed is how you
find out that it was.

## Anti-patterns

- Analysing an extract without knowing which system produced it or when.
- Treating a resampled grid as the measurement rate.
- One global sentinel list.
- Trusting a wrapper's "not found" over the system catalogue.
- Joining on timestamps across systems without clock, tolerance and direction validation.
- Quoting a missing-data fraction without conditioning it on the analysis window.
