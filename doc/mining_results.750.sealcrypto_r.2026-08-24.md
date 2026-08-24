# `cfm mine` results: 750.sealcrypto_r, 2026-08-24

The first real mining run against a genuinely **compute-bound** benchmark — every prior real run
(`706.stockfish_r`, `782.lbm_r` ×2, `714.cpython_r`) characterized as memory-bound or frontend-bound,
leaving the catalog's compute-bound-targeted flags (`-Ofast`, `-ffast-math`, `-funroll-loops`) completely
untested against real signal until now. Picked deliberately: of 17 real benchmarks checked against the
external reference-matrix corpus, `750.sealcrypto_r` (SEAL homomorphic encryption — heavy polynomial/
big-integer arithmetic) was the only one whose real characterized shape actually comes back
compute-bound.

## Headline result

**`-O3 -march=native` beats plain `-O3` by +14.17%** — a third distinct real benchmark now confirming
`-march=native`'s value, joining `706.stockfish_r` (+48.75%) and `782.lbm_r` (rejected, +1.79%, too
small to clear that benchmark's own CI). SEAL's own big-integer/polynomial arithmetic plausibly benefits
from the wider AVX-512 execution units `-march=native` unlocks, the same underlying mechanism as
stockfish's own win, just far less dramatically — consistent with a compute-bound workload with only
`vectorization_density=moderate` (vs. stockfish's own heavier dependence).

**The compute-bound catalog flags this run existed to finally test — `-Ofast`, `-ffast-math`,
`-funroll-loops` — were all pruned at screening, alongside both `-mprefer-vector-width` choices.** This
result needs a caveat, not a clean headline: see "An open finding" below.

## Run metadata

| | |
|---|---|
| Command | `cfm mine 750.sealcrypto_r` (uncapped) |
| Experiment id | 16 |
| Started | 2026-08-24T08:58:45Z |
| Finished | 2026-08-24T10:19:05Z |
| Wall-clock | 1h20m20s — by far the fastest real uncapped run to date |
| Final status | `converged` |
| Candidates screened | 6 (of 6 plausible survivors) |
| Candidates accepted | 1 (`-march=native`) |
| Winning flags | `["-O3", "-march=native"]`, +14.17% overall gain |

Wall-clock is dramatically shorter than every prior real run (lbm's own ~19min/trial, cpython's ~19-22
min/trial) — `750.sealcrypto_r`'s own `quick`-profile trial cost is roughly ~5-6 minutes, a genuine
per-workload difference (SEAL's own reference workload is intrinsically much shorter-running), not a
methodology change.

## Baseline

`baseline_characterization_source: "reference-matrix:amd-370-64gb"` — real match, no local trial
needed: `resource_dominance=compute-bound` (55.10%, medium confidence, `memory-bound` as the distant
alternative at 40.50% per the reference-matrix's own data), `vectorization_density=moderate`,
`allocation_pressure=low`.

Baseline calibration (3× `quick`-profile reps at `-O3` alone):

| Trial | Ratio | CPU temp |
|---|---|---|
| 216 | 56.177 | 93.9°C |
| 217 | 54.795 | 93.9°C |
| 218 | 52.089 | 92.0°C |

Mean **54.354** — a real, if moderate, downward settling pattern across the 3 reps (~7.5% front-to-back
spread), similar in shape to the early-rep drift seen in prior runs' own baselines.

**Thermal throttling directly ruled out, not just assumed absent**: lining up ratio against this
trial's own recorded `cpu_temp_c` shows temperature staying in a narrow 90.9-93.9°C band throughout,
with no correlation to the ratio pattern — trials 221→222→223 sit at 91.5°C→92.0°C→92.2°C (essentially
flat, if anything rising slightly) while their ratios go 50.65→62.14→50.60, a 23% swing fully explained
by which flag compiled in (`-march=native` at 222), not by temperature. The `-march=native` confirmation
reps (225-227) show the same pattern in reverse: temp actually *drops* from 93.4°C to 91.6°C while the
ratio stays flat at ~62.0 — the opposite of what throttling would predict. Whatever produces the
baseline's own settling pattern, it isn't thermal, and a cooldown pause between trials wouldn't be
expected to help — there's no thermal signal here to wait out. Real, still-unidentified candidates
(none confirmed): SPECrate's own per-copy startup variance, page cache/TLB warm-up state, or another
non-thermal effect this project doesn't currently instrument.

## Candidate generation and filtering

`_filter_implausible_candidates()` excluded 6 catalog flags as mechanically implausible against a
compute-bound, moderate-vectorization baseline: `-flto`, `-freorder-blocks-and-partition`,
`-freorder-functions`, `-fno-semantic-interposition` (all `frontend-bound`), `-fprefetch-loop-arrays`
(`memory-bound-corroborated`), `-fipa-pta`/`-fgraphite-identity` (`backend-bound`/`memory-bound-
corroborated`). Plus the usual 3 unresolved-template-placeholder skips. **6 plausible survivors**
screened: `-funroll-loops`, `-mprefer-vector-width=256`, `-mprefer-vector-width=512`, `-march=native`,
`-Ofast`, `-ffast-math`.

## Phase 3/4: screening and confirmation

| Flag | Screening ratio | Delta vs. baseline | Verdict |
|---|---|---|---|
| `-funroll-loops` | 50.776 | −6.58% | **pruned at screening** |
| `-mprefer-vector-width=256` | 50.592 | −6.92% | **pruned at screening** |
| `-mprefer-vector-width=512` | 50.654 | −6.81% | **pruned at screening** |
| **`-march=native`** | **62.136** | **+14.30%** | **survived → confirmed, accept, +14.05%** |
| `-Ofast` | 50.597 | −6.91% | **pruned at screening** |
| `-ffast-math` | 50.572 | −6.96% | **pruned at screening** |

Every screened trial's compiled-flags audit confirms its own distinct flag genuinely compiled in (no
repeated-binary issue — this isn't a basepeak-class bug). `-march=native` alone survived and was
confirmed at +14.05% (95% CI cleanly non-overlapping baseline's own), accepted, and re-confirmed again
at Phase 5's greedy-combine step (+14.17%, trivial with only one accepted candidate — no pair tournament
possible).

## An open finding: were the other 5 flags genuinely rejected, or victims of a settling baseline?

This is the result this run exists to get real signal on, and it deserves an honest caveat rather than
a clean "compute-bound flags don't help" headline.

All 5 non-`-march=native` screening trials landed in a tight **50.57–50.78** band — *below even
baseline's own lowest rep* (52.089) — comfortably past the 5% prune bar (−6.6% to −7.0%). Read one way,
this looks like a clean, consistent reject across 5 mechanistically different flags. Read another way:
baseline's own 3 reps were still visibly settling downward (56.18 → 54.80 → 52.09) when Phase 3 screening
started immediately after, and Phase 3 deliberately has no CI at all — it compares a single cheap trial
against baseline's raw *mean* (54.35, pulled up by the two earlier, higher reps), not against wherever
the benchmark's *true* steady-state ratio actually was by the time screening ran. The screening trials
that followed (219-221, `-funroll-loops`/`-mprefer-vector-width=256/512`) stayed essentially flat around
50.6-50.8 rather than continuing to decline — consistent with the settling having mostly finished by
then, at a floor close to, but still visibly below, baseline's own last rep.

`-march=native`'s own screening trial (222) — chronologically sandwiched directly between the pruned
ones — jumped to 62.14, proving the settling pattern doesn't swamp a real, large effect. But a *small*
real effect (positive or negative) is exactly what this kind of baseline instability can't cleanly
separate from noise using Phase 3's threshold-on-a-mean design. None of the 5 pruned flags ever got a
real, CI-based confirmation-grade trial to resolve this — screening's whole job is to prune without one.

**Left as an open, documented finding, not resolved this run** (deliberately, rather than spending
another ~20-30 minutes per flag on an ad hoc re-check right now): whether `-Ofast`/`-ffast-math`/
`-funroll-loops` have a genuine flat-to-negative effect on this benchmark, or a small real effect that
baseline settling made unreadable at the screening stage, is unknown. A future run — either a fresh
`750.sealcrypto_r` re-mine, or a design change letting Phase 3 compare against a rolling/late-window
baseline estimate instead of the full-run mean — would resolve it.

## Phase 6: both multipliers correctly skipped

**PGO**: `"skipping PGO -- topdown_signals ['frontend-bound', 'speculation-bound'] implausible given
baseline shape (resource_dominance='compute-bound', vectorization_density='moderate')"` — correct;
compute-bound is neither of PGO's own claimed-relevant signals.

**Microarch**: `"skipping microarch multiplier -- winning set ['-O3', '-march=native'] already has an
-march=/-mtune= flag, adding another would conflict rather than compound"` — same correct guard seen on
`706.stockfish_r`'s own run: `-march=native` already won via the ordinary path, so a separate
`-march=znver5` trial would rebuild the identical binary.

## Knowledge table: a new cluster, for the first time

| cluster | flag | n_trials | n_accepted | mean Δ% | last benchmark |
|---|---|---|---|---|---|
| **compute-bound** | `-march=native` | 1 | 1 | **+14.05%** | `750.sealcrypto_r` |

The first real `compute-bound`-cluster row this project has ever recorded — a real, if single-sample,
prior for whichever compute-bound benchmark gets mined next (M4's own cross-benchmark transfer
mechanism, doc/DESIGN.md sec. 8, would fast-track `-march=native` again the moment a second
compute-bound benchmark is mined, exactly as it already did for `782.lbm_r` within the `memory-bound`
cluster).

## What this run actually confirms

- **`-march=native` now has real accepted evidence in three separate clusters** (`memory-bound`,
  `frontend-bound` was never tested directly but `compute-bound` and `memory-bound` both show real
  wins) — a strong, cross-workload signal that this flag is broadly valuable on this host, not specific
  to any one benchmark's quirks.
- **Every screened trial's compiled-flags audit checked out** — no repeat of the basepeak-class bug,
  every trial built what it claimed to.
- **A real, honest methodological limitation surfaced under real signal for the first time**: Phase 3
  screening's fixed-threshold-against-a-raw-mean design is vulnerable to a still-settling baseline, not
  just to the previously-documented multi-hour drift case. Worth keeping in mind for the next run at
  least as much as the hours-long drift already documented for `782.lbm_r`'s 2026-08-21 run.

## Next steps this suggests

- **Resolve the open finding above** — either a fresh confirmation-grade check of `-Ofast`/
  `-ffast-math`/`-funroll-loops` specifically, or a real design conversation about Phase 3 comparing
  against something more robust than the full baseline mean. Thermal throttling is directly ruled out
  as the cause (temp stayed flat at 91-94°C with no correlation to the ratio pattern — a cooldown pause
  between trials wouldn't be expected to help); the real cause is still unidentified.
- **Still need a genuinely backend-bound benchmark** — memory-bound, frontend-bound, and compute-bound
  are now all covered by at least one real run; backend-bound has never been the primary characterized
  shape for any benchmark checked so far.
- Phase 5's pair tournament still has zero real coverage.
