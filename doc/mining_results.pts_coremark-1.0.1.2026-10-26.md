# `cfm mine` results: pts/coremark-1.0.1 on `erie`, 2026-10-26

The first benchmark mined outside SPEC CPU2026, and the first `cfm mine` on `erie` (see
[`host_erie.md`](host_erie.md)). It ran through the new Phoronix Test Suite backend
(`cfm/workloads/phoronix.py`, branch `feature/phoronix-workload`). That backend replays the PTS profile's own
`install.sh` with the trial's flags as `CFLAGS`, runs coremark's test script directly under wspy, and reads the
score (Iterations/Sec) from coremark's own log. A trial counts only when coremark's CRC self-check prints
`Correct operation validated`.

## Headline result

**`-O3 -fprofile-use`, +6.65% over plain `-O3`** (385,356 vs. 361,329 iterations/sec).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 361,329 | — |
| `+ -fprofile-use` | 385,356 | +6.65% |

- **The win is real, but this run's other verdicts aren't trustworthy.** The host's package power fell from
  about 24 W to about 20 W during screening, and the score fell with it (r = 0.90 over trials 11-23). Every
  later trial was measured against a baseline taken at the higher power. The baseline recheck after Phase 4
  read **-3.34%** and was flagged. See "Power sag" below.
- **PGO won despite that bias, not because of it.** It measured at 22 W, against a baseline taken at 24 W.
  Against the 22 W recheck (349,269) it reads +10.3%.
- **`-funroll-loops` probably has a real gain the mine rejected.** It screened at +5.07% at matched power
  (24 W, trial 10). It confirmed at about flat (-0.16%) against the 24 W baseline. That is +3.3% against the
  22 W recheck.
- **The seven screening prunes are an artifact.** They are exactly the seven flags screened last (trials
  17-23), after power had dropped to 20-21 W. Each read -6% to -7.3%.

## Run metadata

| | |
|---|---|
| Host | `erie`: HP OmniBook 5 laptop, AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 30 GB RAM, on AC |
| Command | `cfm mine pts/coremark-1.0.1` (uncapped, default `-O3` base) |
| Code | `feature/phoronix-workload` at `52ae6c6` |
| Experiment id | 3 (`cfm.db` new on this host: 1 and 2 were the backend's smoke tests) |
| Started / finished | 2026-10-26T23:08:11Z / 2026-10-26T23:56:19Z (48 min) |
| Final status | `converged` |
| Trials | 55 (3-57) |
| Candidates screened / confirmed | 15 / 8 |
| Fast-tracked (M4) | none (empty knowledge table) |
| Winning flags | `["-O3", "-fprofile-use"]`, +6.65% |
| Workload | coremark 1.0 (PTS `pts/coremark-1.0.1`), `MULTITHREAD=16 USE_FORK=1`: 16 forked processes, one per logical CPU |
| Guards | bandwidth gate 45.1-47.2 GB/s before every run, waited only before the first (30 s); no slow-rep reruns; no audit warnings; **baseline recheck flagged (-3.34%)** |
| Power | platform profile `balanced`, governor `powersave`, EPP `balance_performance`; CPU temp 75.4-87.1°C, package power 19.0-24.1 W |

Trials came 33-35 seconds apart for short runs and about 55 seconds apart for long ones (see "Run length
varies" below). PGO trials came 81 seconds apart: each one builds instrumented, trains with a full coremark
run, rebuilds, then times.

## Baseline

| Trial | Role | Ratio | Power |
|---|---|---|---|
| 3 | `deep-cpu` characterization | 357,920 | 22.06 W |
| 4 | warm-up (excluded from CI) | 361,691 | 24.04 W |
| 5 | warm-up (excluded from CI) | 361,923 | 23.10 W |
| 6 | calibration | 360,604 | 23.06 W |
| 7 | calibration | 361,964 | 24.05 W |
| 8 | calibration | 361,419 | 24.02 W |
| 48 | recheck after Phase 4 | 349,269 (**-3.34%, flagged**) | 22.09 W |

Calibration mean **361,329**, 95% CI **[359,629, 363,029]** (±0.47%).

**Shape: `compute-bound`, 42.3%**, `vectorization_density=low`, `allocation_pressure=low`, from a local
`deep-cpu` trial (the reference-matrix corpus only covers SPEC). 42.3% is under the 55% gate, so nothing was
excluded on `resource_dominance`. The low vectorization density excluded `-mprefer-vector-width=256`.

## Phase 2 and M4

Sixteen C-applicable catalog flags, less the vector-width one: fifteen candidates. `cfm.db` was new on this host,
so there were no priors and nothing was fast-tracked. The language came from the extracted sources (all `.c`).

## Phase 3 screening (vs. most recent calibration rep, 361,419)

Prune threshold -5%. Listed in run order.

| Trial | Flags | Ratio | Delta | Power | Result |
|---|---|---|---|---|---|
| 9 | `-march=native` | 368,178 | +1.87% | 23.02 W | survive |
| 10 | `-funroll-loops` | 379,736 | **+5.07%** | 24.02 W | survive |
| 11 | `-Ofast` | 359,847 | -0.43% | 24.02 W | survive |
| 12 | `-ffast-math` | 359,053 | -0.65% | 24.02 W | survive |
| 13 | `-fno-math-errno` | 353,435 | -2.21% | 23.02 W | survive |
| 14 | `-flto` | 353,136 | -2.29% | 23.05 W | survive |
| 15 | `-fno-pie -no-pie` | 353,930 | -2.07% | 21.06 W | survive |
| 16 | `-fno-stack-protector` | 346,595 | -4.10% | 22.06 W | survive |
| 17 | `-fcf-protection=none` | 339,709 | -6.01% | 21.05 W | pruned |
| 18 | `-U_FORTIFY_SOURCE` | 338,457 | -6.35% | 21.02 W | pruned |
| 19 | `-fprefetch-loop-arrays` | 336,193 | -6.98% | 20.10 W | pruned |
| 20 | `-fno-ipa-cp-clone` | 335,160 | -7.27% | 20.08 W | pruned |
| 21 | `-fno-unswitch-loops` | 334,915 | -7.33% | 20.09 W | pruned |
| 22 | `-fipa-pta` | 338,660 | -6.30% | 20.09 W | pruned |
| 23 | `-fgraphite-identity` | 336,170 | -6.99% | 21.01 W | pruned |

Eight survived. The scores fall almost monotonically in run order, and none of the pruned flags plausibly
costs 6-7% on coremark (`-U_FORTIFY_SOURCE` and `-fcf-protection=none` remove checks; they can't slow it down).

## Phase 4 confirmation (3 reps each, vs. baseline CI [359,629, 363,029])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-funroll-loops` | 359,668, 360,353, 362,244 | 360,755 | [357,440, 364,070] | -0.16% | reject |
| `-fno-pie -no-pie` | 350,298, 354,467, 354,754 | 353,173 | [346,976, 359,369] | -2.26% | reject |
| `-fno-stack-protector` | 348,407, 348,167, 347,298 | 347,957 | [346,507, 349,407] | -3.70% | reject |
| `-flto` | 347,235, 346,408, 349,078 | 347,574 | [344,177, 350,970] | -3.81% | reject |
| `-march=native` | 342,506, 345,647, 346,558 | 344,904 | [339,622, 350,185] | -4.55% | reject |
| `-fno-math-errno` | 344,617, 344,246, 341,491 | 343,452 | [339,209, 347,694] | -4.95% | reject |
| `-ffast-math` | 341,467, 342,027, 343,078 | 342,190 | [340,159, 344,222] | -5.30% | reject |
| `-Ofast` | 340,619, 340,293, 341,832 | 340,914 | [338,900, 342,929] | -5.65% | reject |

All eight rejected, and none was CI-clear above baseline, so Phase 6 had no near-miss variant to try. Phase 4
ran at 19-22 W against a 23-24 W baseline. Read against the 22 W recheck (349,269) instead, `-funroll-loops`
is +3.3%, `-fno-pie -no-pie` +1.1%, and the rest are within -2.4% to -0.4%.

## Phase 5 combination

Nothing was accepted, so the winning set stayed `-O3` and no combination trials ran.

## Phase 6 multipliers (on `-O3`)

| Stage | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `-O3 -fprofile-use` | 384,573, 386,584, 384,910 | 385,356 | [382,680, 388,031] | **+6.65%** vs baseline | **accept** |
| Microarch | `+ -march=znver5` | 381,522, 378,918, 380,064 | 380,168 | [376,926, 383,410] | -1.35% vs PGO | reject |
| Microarch | `+ -mtune=znver5` | 378,674, 378,226, 378,072 | 378,324 | [377,547, 379,101] | -1.82% vs PGO | reject |
| Vector width | — | | | | | skipped (no deferred candidates) |

PGO trained on one full coremark run of the instrumented build, the same workload it then measured. PTS has no
separate training input, unlike SPEC's train workload, so this flatters PGO somewhat compared with a SPEC
result. The audit confirmed `-O3 -fprofile-use=<profile dir>` in the binary and no `-fprofile-generate`.

## Power sag

Package power and CPU temperature both fell during the first half of the run, then settled:

| Trials | Phase | Package power | CPU temp | `-O3`-like scores |
|---|---|---|---|---|
| 4-12 | baseline, early screening | 23-24 W | 83-87°C | ~360k |
| 16-23 | late screening | 20-22 W | 75-80°C | ~335-347k |
| 24-48 | Phase 4, recheck | 19-22 W | 77-87°C | ~341-355k (recheck 349k) |

Falling temperature with falling score rules out thermal throttling as the cause. A sustained package-power limit
stepping down after a few minutes of all-core load (a laptop STAPM-style limit) fits. The same hypothesis was
raised for the old Strix Halo host ([note](settling_baseline_drift_investigation.2026-08-24.md)). Across all 46
non-PGO trials, score and the power reading correlate at r = 0.73. Over trials 11-23, where nothing but the
flag and the power changed, it is r = 0.90.

The two warm-up reps didn't help: the sag started about 14 minutes into the run (around trial 15, 23:22Z),
some 5 minutes after the last calibration rep. On SPEC each
trial runs for many minutes, so a sag like this would land inside the warm-up. Coremark trials last 27-50 seconds,
so the whole baseline finished before it.

## Run length varies

The PTS profile runs `coremark.exe` with no arguments, so coremark sizes its own run (`ITERATIONS=0`: it times a
short run and scales up until the run lasts at least 10 seconds). Here it settled on one of two counts:

| Iterations | Run time | Trials |
|---|---|---|
| 9,600,000 | 26.5-28.7 s | the baseline, most screening and confirmation |
| 17,600,000 | 45.5-51.8 s | the characterization trial, `-march=native` and `-funroll-loops` screening, all three `-funroll-loops` confirmations, 2 of 3 `-fno-pie` ones, one `-march=native` one, `-fcf-protection=none` screening, and every Phase 6 trial |

The score is iterations per second, so the two are comparable in principle. Under a power limit, though, a longer
run spends more of its time at the lower sustained level. Within one power period the long runs read no higher
than the short ones (trial 24 at 17.6M: 342,506; trials 25-26 at 9.6M: 345,647 and 346,558), so the
`-funroll-loops` and PGO results don't look like a run-length effect. A fixed iteration count would remove the
question.

## Knowledge table after this run (`compute-bound`, `erie`)

Every confirmed flag got a knowledge row, including the eight power-biased rejects. `-fprofile-use` is the only
accept. The reject rows carry deltas biased by about -3%, so they make a weak prior for the next compute-bound
mine here.

## Follow-ups

1. **Interleaved re-measure at stable power**: `cfm measure` alternating `-O3`, `-O3 -funroll-loops`,
   `-O3 -march=native` and `-O3 -fprofile-use -funroll-loops`, several rounds. This settles whether
   `-funroll-loops` is really +3-5% and whether it stacks with PGO. Answered by the re-mine instead
   ([re-mine](mining_results.pts_coremark-1.0.1.2026-10-26b.md)): +5.86%, and PGO adds +3.10% on top.
2. **Re-mine under the `performance` profile.** Done in part on 2026-10-26: `erie` is now in `performance`,
   and a 10.5-minute power check showed no sag (package power steady at ~29.5 W, steady-state `-O3` 384,079 ±
   0.36%, about +6% over this mine's `balanced` baseline). A ~2-minute thermal transient at the start remains
   ([`host_erie.md`](host_erie.md)). Re-mined 2026-10-27:
   [`mining_results.pts_coremark-1.0.1.2026-10-26b.md`](mining_results.pts_coremark-1.0.1.2026-10-26b.md),
   `-O3 -funroll-loops -fprofile-use` at +8.86%.
3. **Fix coremark's run length.** Done 2026-10-26: the backend now runs `coremark.exe 0x0 0x0 0x66 600000`
   (`COREMARK_ITERATIONS`), 9.6M iterations total. The bimodal length came from coremark's own sizing rule: it
   multiplies the count by `1 + 10/int(seconds)` after a timing run, and that run sat right at 2 seconds here,
   so it flipped between ×11 and ×6.
4. **A baseline recheck that re-baselines**: the recheck caught this run's offset but, by design, changed no
   verdict. On a host that sags like this, short benchmarks need interleaved baseline reps, or a recheck that
   re-runs Phase 4 against a fresh baseline when it flags.
