# Opportunity list: `niwot`

Follow-up experiments and pipeline improvements that could add gain on this host
(see [`host_niwot.md`](host_niwot.md)). Each item says what to run and what result would change a verdict.
When an item is done, strike it through and link the write-up, rather than deleting it.

Rough priority: **H** is likely to move a suite geomean or fix a pipeline blind spot, **M** could firm up or
slightly improve an existing result, **L** is a curiosity or diagnostic.

## Per-benchmark experiments

| # | Pri | Benchmark | Opportunity | How | What would change |
|---|---|---|---|---|---|
| 1 | ~~M~~ | `708.sqlite_r` | ~~**Prefetch-distance sweep** on top of the accepted `-fprefetch-loop-arrays`. The catalog's `--param prefetch-latency=N` entry is a template placeholder that every mine skips.~~ | `cfm measure 708.sqlite_r --flags="-O3 -fprefetch-loop-arrays --param prefetch-latency=N"` for N = 200, 300, 400, interleaved with the plain winner as a control. | **Done 2026-10-18:** 100/300/400 all within +0.8% of the default 200 (CIs overlap); default stays ([write-up](mining_results.708.sqlite_r.2026-10-17.md#follow-up-sweep---param-prefetch-latency-2026-10-18)). |
| 2 | **H** | `708.sqlite_r`, `729.abc_r` | **Local-shape cross-check.** Raised to H after vpr (#20): a memory-bound shape hid +14.7% of LTO + PGO there. **sqlite done 2026-10-21:** PGO +9.65% on top of the winner, `-flto` -0.7% ([write-up](mining_results.708.sqlite_r.2026-10-17.md#follow-up-lto-and-pgo-on-top-of-the-winner-2026-10-21)); **abc done 2026-10-21:** `-flto` +3.10%, PGO about -4% ([write-up](mining_results.729.abc_r.2026-10-17.md#follow-up-lto-and-pgo-2026-10-21)). Both used low-confidence corpus shapes (memory-bound 39.7% / 38.2%, frontend-bound close behind), which excluded `-flto` and PGO untried. | One `deep-cpu` characterization each, or a direct interleaved `cfm measure` of `-O3` against `-O3 -flto`. | A frontend-bound local shape, or a real `-flto` gain, means re-mining with the local shape (LTO + PGO in play). |
| 3 | ~~M~~ | `729.abc_r` | ~~**Interleaved re-measure** of `-O3` and `-O3 -march=znver5`, because the mine's calibration baseline looked about 1% low.~~ | 3 rounds alternating the two. | **Done 2026-10-18:** +0.55%, reject stands; mine baseline was ~0.5% low ([write-up](mining_results.729.abc_r.2026-10-17.md#follow-up-re-measure--o3-vs--o3--marchznver5-2026-10-18)). |
| 13 | ~~H~~ | `708.sqlite_r` | ~~**Re-confirm the +1.76% itself.** The sweep's control (24.37-24.55) sat below the mine's winner (24.70), near the mine's `-O3` (24.27).~~ | Interleaved `cfm measure`, `-O3` against `-O3 -fprefetch-loop-arrays`, 3 rounds. | **Done 2026-10-19:** +1.68%, CIs clear, consistent every round. Gain confirmed ([write-up](mining_results.708.sqlite_r.2026-10-17.md#follow-up-re-check--o3-vs--o3--fprefetch-loop-arrays-2026-10-19)). |
| 4 | L | `706.stockfish_r` | **Why does LTO regress -16.6%?** (about -24% on top of `-march=native`). | Compare `-flto` with `-flto-partition=one`, `-fno-inline-functions` or `--param inline-unit-growth`, or `perf` the LTO and non-LTO binaries for a hot-path difference. | An LTO variant that doesn't regress could then stack with `-march=native`. |
| 5 | L | `714.cpython_r` | **Why does `-march=native` regress -4.8%?** It does on both hosts. | Try `-march=native -mno-avx512f` / `-mprefer-vector-width=256`, or the separate `-mtune=znver5` vs `-march=znver5` effects on top of the `-flto -fprofile-use` winner. | A tune-only variant could add a little on top of +36.49%. |
| 17 | L | `723.llvm_r` | **Why is LTO only +1.4% on llvm** (+5.9% on the old host, +13.1% on omnetpp here)? | `-flto -flto-partition=one`, or a different `-flto-partition`, against default `-flto`; slow builds (~16 min per LTO trial). | An LTO variant worth a few more points would stack under PGO. |
| 18 | H | `727.cppcheck_r` | **`-O3 -flto -fprofile-use` was never measured.** `-flto` alone was +0.96% (CI clear of baseline, under the 1% bar), so PGO went on plain `-O3`. LTO and PGO stacked on omnetpp and llvm. | Interleaved `cfm measure`, `-O3 -fprofile-use` against `-O3 -flto -fprofile-use`, 3 rounds (~10 min per PGO trial). | A real gain makes `-O3 -flto -fprofile-use` cppcheck's winner. |
| 6 | M | `714.cpython_r` | **Microarch on the final winner.** The multiplier tried `-mtune=znver5` on top of `-flto -fprofile-use` (+2.17%, CIs overlapped). | 3 more interleaved reps against the winner. | A real +2% would lift intrate by about 0.15 points. |
| 14 | L | `750.sealcrypto_r` | **Why is `-march=native` +20.5% here but +14-16% on the old host?** | `-O3 -march=znver5` with `-mprefer-vector-width=256` vs `=512`, interleaved. | Explains a cross-host difference; may show a vector-width setting that adds on top. |
| 20 | ~~M~~ | `734.vpr_r` | ~~**LTO and PGO never tried** (on either host): the memory-bound shape (45.4%) excluded `-flto` and skipped PGO.~~ | Interleaved `cfm measure` of `-O3 -march=native` against `+ -flto`, `+ -fprofile-use`, and both, 3 rounds. | **Done 2026-10-20:** `-flto` +11.35%, PGO +4.05%, both +14.65% over `-O3 -march=native`, all CIs clear. vpr's best is now +15.77% ([write-up](mining_results.734.vpr_r.2026-10-20.md#follow-up-lto-and-pgo-on-top-of-the-winner-2026-10-20)). |
| 21 | M | `735.gem5_r` | **PGO regresses -10.6% on top of `-flto`** (-6.7% on the old host); `729.abc_r`'s PGO also regresses (about -4%), so the check covers both (queued after gcc). Likely an unrepresentative training run. | Interleaved `cfm measure` of `-O3 -flto` against `-O3 -flto -fprofile-use -fprofile-partial-training`, 3 rounds. `cfm measure` accepts the flag as is; it lands on the shared `OPTIMIZE` line, so pass 1 sees it too, which should be harmless (check the build log). | Removing the regression confirms the training-coverage reading; a gain on top of +11.01% becomes gem5's winner. |
| 12 | M | `707.ntest_r` | **LTO and PGO never tried** (on either host): the narrow-margin compute-bound shape (40.6%) excluded both. | Interleaved `cfm measure` of `-O3 -march=native` against `-O3 -march=native -flto`, then the PGO variant. | A real gain on top of +14.27% means the exclusion rule is too strict for narrow margins (see #8). |

## Pipeline improvements

| # | Pri | Opportunity | Motivation |
|---|---|---|---|
| 7 | H | **End-of-Phase-4 baseline re-check:** one or two extra `-O3` reps after confirmation, flagging a baseline offset beyond some threshold. | `729.abc_r`'s calibration sampled about 0.5% low (confirmed by re-measure), inflating every delta and the knowledge-table means. Cheap (one or two trials per mine). |
| 8 | H | **Don't let a low-confidence corpus shape exclude whole flag families.** When the corpus margin between primary and alternative shape is narrow, union the two shapes' plausible candidates, or fall back to local `deep-cpu`. | sqlite and abc both excluded LTO and PGO on a ~4-5 point corpus margin from another machine. `734.vpr_r` (memory-bound 45.4%) proves the cost: LTO + PGO, excluded by the shape, measured +14.65% on top of the mine's winner (#20), sqlite (39.7%) hid PGO +9.65%, abc (38.2%) hid `-flto` +3.10%, and gcc (45.2%) hid LTO + PGO +10.87%. All four memory-bound benchmarks here gained. The exclusion may be wrong for memory-bound shapes at any margin below a clear majority. |
| 9 | M | **Re-try screening prunes in combination.** A flag pruned at Phase 3 is never tried again with the eventual winner. | Interactions such as `-march=native` with `-fprefetch-loop-arrays` (sqlite: -1.84% for `-march=znver5`) go unexplored in both directions. |
| 10 | M | **Resolve catalog template placeholders** (`--param prefetch-latency=N` and others) into a small, fixed sweep instead of skipping them. | Item 1 is the hand-run version of this. |
| 15 | M | **M4 fast-track needs a stronger prior.** Today any single past accept qualifies, and the mean can be one outlier. Require a majority-accepted record, or rank by median. | `710.omnetpp_r` fast-tracked `-march=native` on a 1-of-2 record (mean +21.8%, really +48% and -4.8%) and rejected it at +0.35%, spending 3 confirmation trials instead of 1 screening trial. `723.llvm_r` repeated it (1-of-3 record, rejected at -0.85%), and so did `727.cppcheck_r` (1-of-4, +0.07%). Memory-bound too: `734.vpr_r` fast-tracked `-fprefetch-loop-arrays` on a 1-of-2 record and rejected it at +0.42%. `721.gcc_r` fast-tracked both `-fprefetch-loop-arrays` and `-march=native` on 1-of-3 records; both rejected (-0.54%, -0.27%). |
| 16 | L | **Why is PGO's gain on top of LTO smaller here than on the old host?** omnetpp +14.9% vs +23.5%, cpython +24.8% vs +31.2%. | Possibly the cache-size difference (64 MB L3 vs 16 + 8 MB) or the hybrid Zen5c cores. A diagnostic, unlikely to add gain directly. |
| 19 | M | **Carry near-miss flags into Phase 6.** A flag whose CI is clear of baseline but whose delta misses the 1% bar is dropped before PGO. Offer it as a second PGO base variant. | `727.cppcheck_r`'s `-flto` (+0.96%, CI-clear) never got to stack with PGO (#18). |
| 11 | L | **Speed-suite (`_s`) support check.** cfm has never mined a speed benchmark (threads, not copies). | Half of the four suites on the host page are speed suites. |

## Done

- `721.gcc_r` LTO/PGO (2026-10-21): `-O3 -flto -fprofile-use`, +10.71% over `-O3` (mine accepted nothing).
- #2 (abc half) `729.abc_r` LTO/PGO (2026-10-21): `-O3 -flto`, +2.49% over `-O3` (mine accepted nothing); PGO regresses.
- #2 (sqlite half) `708.sqlite_r` LTO/PGO (2026-10-21): `-O3 -fprefetch-loop-arrays -fprofile-use`, +10.48% over `-O3` (mine found +1.76%).

- #20 `734.vpr_r` LTO/PGO (2026-10-20): `-O3 -march=native -flto -fprofile-use`, +15.77% over `-O3` (mine found +1.31%).

- #1 `708.sqlite_r` prefetch-latency sweep (2026-10-18): no setting beats the default 200.
- #13 `708.sqlite_r` re-check (2026-10-19): `-fprefetch-loop-arrays` +1.68%, confirmed.
- #3 `729.abc_r` interleaved re-measure (2026-10-18): `-march=znver5` +0.55%, reject stands.
