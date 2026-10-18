# Opportunity list: `niwot`

Follow-up experiments and pipeline improvements that could add gain on this host
(see [`host_niwot.md`](host_niwot.md)). Each item says what to run and what result would change a verdict.
When an item is done, strike it through and link the write-up, rather than deleting it.

Rough priority: **H** is likely to move a suite geomean or fix a pipeline blind spot, **M** could firm up or
slightly improve an existing result, **L** is a curiosity or diagnostic.

## Per-benchmark experiments

| # | Pri | Benchmark | Opportunity | How | What would change |
|---|---|---|---|---|---|
| 1 | M | `708.sqlite_r` | **Prefetch-distance sweep** on top of the accepted `-fprefetch-loop-arrays`. The catalog's `--param prefetch-latency=N` entry is a template placeholder that every mine skips. | `cfm measure 708.sqlite_r --flags="-O3 -fprefetch-loop-arrays --param prefetch-latency=N"` for N = 200, 300, 400, interleaved with the plain winner as a control. | A setting clearly above 24.70 becomes the new sqlite best. |
| 2 | M | `708.sqlite_r`, `729.abc_r` | **Local-shape cross-check.** Both used low-confidence corpus shapes (memory-bound 39.7% / 38.2%, frontend-bound close behind), which excluded `-flto` and PGO untried. | One `deep-cpu` characterization each, or a direct interleaved `cfm measure` of `-O3` against `-O3 -flto`. | A frontend-bound local shape, or a real `-flto` gain, means re-mining with the local shape (LTO + PGO in play). |
| 3 | ~~M~~ | `729.abc_r` | ~~**Interleaved re-measure** of `-O3` and `-O3 -march=znver5`, because the mine's calibration baseline looked about 1% low.~~ | 3 rounds alternating the two. | **Done 2026-10-18:** +0.55%, reject stands; mine baseline was ~0.5% low ([write-up](mining_results.729.abc_r.2026-10-17.md#follow-up-re-measure--o3-vs--o3--marchznver5-2026-10-18)). |
| 4 | L | `706.stockfish_r` | **Why does LTO regress -16.6%?** (about -24% on top of `-march=native`). | Compare `-flto` with `-flto-partition=one`, `-fno-inline-functions` or `--param inline-unit-growth`, or `perf` the LTO and non-LTO binaries for a hot-path difference. | An LTO variant that doesn't regress could then stack with `-march=native`. |
| 5 | L | `714.cpython_r` | **Why does `-march=native` regress -4.8%?** It does on both hosts. | Try `-march=native -mno-avx512f` / `-mprefer-vector-width=256`, or the separate `-mtune=znver5` vs `-march=znver5` effects on top of the `-flto -fprofile-use` winner. | A tune-only variant could add a little on top of +36.49%. |
| 6 | M | `714.cpython_r` | **Microarch on the final winner.** The multiplier tried `-mtune=znver5` on top of `-flto -fprofile-use` (+2.17%, CIs overlapped). | 3 more interleaved reps against the winner. | A real +2% would lift intrate by about 0.15 points. |

## Pipeline improvements

| # | Pri | Opportunity | Motivation |
|---|---|---|---|
| 7 | H | **End-of-Phase-4 baseline re-check:** one or two extra `-O3` reps after confirmation, flagging a baseline offset beyond some threshold. | `729.abc_r`'s calibration appears to have sampled about 1% low, inflating every delta and the knowledge-table means. Cheap (one or two trials per mine). |
| 8 | H | **Don't let a low-confidence corpus shape exclude whole flag families.** When the corpus margin between primary and alternative shape is narrow, union the two shapes' plausible candidates, or fall back to local `deep-cpu`. | sqlite and abc both excluded LTO and PGO on a ~4-5 point corpus margin from another machine. |
| 9 | M | **Re-try screening prunes in combination.** A flag pruned at Phase 3 is never tried again with the eventual winner. | Interactions such as `-march=native` with `-fprefetch-loop-arrays` (sqlite: -1.84% for `-march=znver5`) go unexplored in both directions. |
| 10 | M | **Resolve catalog template placeholders** (`--param prefetch-latency=N` and others) into a small, fixed sweep instead of skipping them. | Item 1 is the hand-run version of this. |
| 11 | L | **Speed-suite (`_s`) support check.** cfm has never mined a speed benchmark (threads, not copies). | Half of the four suites on the host page are speed suites. |

## Done

- #3 `729.abc_r` interleaved re-measure (2026-10-18): `-march=znver5` +0.55%, reject stands.
