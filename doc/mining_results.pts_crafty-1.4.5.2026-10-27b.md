# `cfm mine` results: pts/crafty-1.4.5 on `erie`, 2026-10-27 (PGO re-mines)

Two re-mines of [crafty](mining_results.pts_crafty-1.4.5.2026-10-27.md), for `host_erie.md` item 10. In the
first mine (experiment 9), each PGO rep built different code, and PGO's +1.8% was rejected on CI overlap.

## The fix, and the first attempt that didn't take

Item 10 asked for training on crafty's serial pass only. That isn't possible without patching crafty.
`bench` runs its nondeterministic 2-thread pass whenever threads are off (`mt=0`). Setting `mt=2` makes the
serial pass itself parallel, and `mt=1` is rejected (`option.c`).

Instead, the Phoronix backend now trains **one profile per flagset per `cfm mine`**. The profile is trained on
first use and reused by every later build of the same flags, so a PGO flagset's reps all measure one binary.
That is also how PGO is used in practice: one training run, one build.

- **Experiment 10 ran with the first version of this, which didn't work.** The record of trained profiles
  lived on the `PhoronixWorkload` instance. `run_one_trial()` asks `workload_for()` for a fresh backend on
  every trial, so the record was empty each time and every PGO rep retrained. The unit test built twice on one
  instance, so it shared the code's wrong assumption.
- **Fixed in `83c3e88`.** `workload_for()` keeps one Phoronix backend per process, and the new test goes
  through `workload_for()` as trials do.
- **Experiment 11 confirms the fix.** Each PGO flagset's three reps have one code fingerprint (`87c07f5a`,
  `f9e440ff`, `7253bbe9`). In experiments 9 and 10, every PGO rep had its own.

## Results across the three crafty mines

| | Exp. 9 (first mine) | Exp. 10 (retrained per rep) | Exp. 11 (one profile per flagset) |
|---|---|---|---|
| `-O3` baseline | 13,440,532 | 13,311,135 | 13,456,441 |
| `-fno-pie -no-pie`, Phase 4 | +4.66% | +5.70% | +4.28% |
| PGO on `-fno-pie -no-pie` | +1.80%, reject | +2.10%, **accept** | +2.54%, **accept** |
| `-march=znver5` on the incoming set | -0.73% | +2.20%, reject (CI) | +1.58%, reject (CI) |
| `-mtune=znver5` on the incoming set | +2.26%, **accept** | +1.01%, **accept** | +0.48%, reject |
| Winner | `-fno-pie -no-pie -mtune=znver5` | `-fno-pie -no-pie -fprofile-use -mtune=znver5` | `-fno-pie -no-pie -fprofile-use` |
| Winner's score | 14,412,893 | 14,500,272 | 14,405,707 |
| Gain vs. own `-O3` | +7.23% | +8.93% | **+7.05%** |

The microarch rows were measured on top of PGO in experiments 10 and 11, but not in experiment 9.

**What holds across all three:**

- **`-fno-pie -no-pie` is crafty's real win: +4.3% to +5.7%,** every time.
- **PGO is worth about +2% to +2.5%.** It was accepted twice, and the third run's rejection came from
  per-rep retraining.
- **Everything else in Phase 4 rejects** each time. That includes TSCP's two wins, `-funroll-loops` and
  `-flto`.

**What doesn't hold:**

- **`-mtune=znver5`** was accepted twice and rejected once. Its effect shrinks once PGO is in: +2.26% without
  PGO, +1.01% and +0.48% with it.
- **`-march=znver5` with PGO** read +2.2% and +1.6%, but its CI overlapped both times. Without PGO it was a
  loss (-0.73%).

**The winners' absolute scores are nearly identical:** 14.41M, 14.50M and 14.41M nodes/sec. The gains differ
mostly through the baseline. Experiment 10's baseline was the lowest, because one calibration rep read
13,126,876, which inflates its +8.93%.

The fair summary for crafty on erie is **about +7% to +8% from `-fno-pie -no-pie` plus PGO**, with
Zen5 tuning on top worth 0-2% and not reliably resolved.

## Measurement notes (experiment 11)

| | |
|---|---|
| Started / finished | 2026-10-27T17:05:36Z / 17:43:37Z (38 min) |
| Code | `feature/crafty-pgo-train` at `83c3e88` |
| Power / temp | 18.0 W throughout; 78-85°C |
| Reruns | one, by the spread rule (trial 455, 3.3% below siblings that agreed exactly) |
| Baseline recheck | -0.12% |

- **PGO trials are faster now.** Only the first PGO build of a flagset trains. The rest compile once, so the
  9 Phase 6 trials took about the same time as 9 ordinary trials would plus three training builds.
- **This run was noisier than experiment 9.** Baseline warm-up hit its 8-rep cap *without* settling: its last
  two reps differed by 2%. Several Phase 4 sets had one rep 2-3% low, with CIs up to ±5%:
  `-fno-stack-protector` 13.00M against 13.16M and 13.46M, and `-fno-math-errno` 13.04M against 13.43M and
  13.55M. Power and temperature were flat, so this isn't the laptop's power limit. The spread rule caught the
  one case where the siblings agreed tightly. In the others the siblings themselves differed by 1-2%, so the
  rule left them alone, by design. Other Claude Code sessions were running on the host (load average about 1.7)
  during this mine. That is a likely contributor on a single-threaded test pinned to one core.

## Follow-ups

1. **Keep the host quieter for single-threaded PTS mines**, or keep the pinned core's SMT sibling (CPU 10) and
   a second core free of other work, since a pinned single-core benchmark feels any neighbor.
2. **Two crafty runs per rep** (the first write-up's follow-up 2) would halve the effect of one bad run on a rep.
3. **`-march=znver5` vs. `-mtune=znver5` on top of PGO** is unresolved. An interleaved `cfm measure` of the two
   against `-fno-pie -no-pie -fprofile-use` would settle it, now that PGO builds are deterministic.
