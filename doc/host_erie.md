# Mining host: `erie`

Index of `cfm mine` results for this host. `erie` has the same CPU as [`niwot`](host_niwot.md) but is a laptop,
with half the memory. It's where Phoronix Test Suite mining started. `niwot`'s results and `cfm.db` knowledge
priors don't carry over here: this host's `cfm.db` is its own, started empty on 2026-10-26.

## Host

| | |
|---|---|
| CPU | AMD Ryzen AI 7 350 w/ Radeon 860M (family 1a model 60): 4 Zen5 + 4 Zen5c cores, 16 threads, 16 MB L3 |
| Clocks | Zen5 CPUs (0, 2, 4, ... 14) max 5.09 GHz; Zen5c CPUs (1, 3, ... 15) max 3.51 GHz |
| Memory | 30 GB |
| Chassis | laptop: HP OmniBook 5 16-ag1xxx (DMI chassis type 10); mined on AC power |
| OS / compiler | Ubuntu 26.04.1 LTS, Linux 7.0.0-38-generic, GCC 15.2.0 (Ubuntu 15.2.0-16ubuntu1) |
| Phoronix Test Suite | 10.8.6, user directory `~/.phoronix-test-suite`; installed tests: `pts/coremark-1.0.1`, `pts/tscp-1.2.2`, `pts/crafty-1.4.5`, `pts/himeno-1.3.0` (PTS's own install fails under GCC 15; cfm's build override works), `pts/c-ray-2.0.0` |
| SPEC | CPU2026 1.0.1 at `/home/mev/cpu2026`, `gcc_O3.cfg` (label `gcc_O3`, `copies = 16`, `threads = 16`); not mined here yet |
| Power | **profile `performance` since 2026-10-26** (`powerprofilesctl set performance`; ACPI platform profile, EPP and governor all follow to `performance`). amd-pstate `active`. The first coremark mine ran under `balanced` (governor `powersave`, EPP `balance_performance`); the re-mine under `performance` |
| Microarch detection | `-march=znver5` / `-mtune=znver5` (hybrid Zen5/Zen5c, PR #46's fix) |
| Sensors | `k10temp` (CPU temp), `amdgpu` `power1_average` (package power under all-core coremark: 19-24 W in `balanced`, a steady ~29.5 W in `performance`), `hp` and `acpi_fan` hwmons |
| Memory bandwidth | 45-47 GB/s on `cfm/bandwidth.py`'s 16-thread triad; the gate never waited past its first probe |

## Running here

`cfm`'s defaults fit this host: `gcc_O3.cfg` exists, and `CFM_PTS_HOME` defaults to `~/.phoronix-test-suite`.
There's no `.venv`, so run the package from the repo directly:

```
python3 -m cfm.cli mine pts/coremark-1.0.1
python3 -m pytest -q
```

A Phoronix test has to be installed by PTS first (`phoronix-test-suite install pts/<test>`), which downloads the
sources the backend builds from. Only tests with an output validator in `cfm/workloads/phoronix.py`'s
`_VALIDATORS` can be mined.

## Results

| Date | Benchmark | Shape (source) | Winning flags | Gain vs `-O3` | Write-up |
|---|---|---|---|---|---|
| 2026-10-26 | `pts/coremark-1.0.1` | compute-bound 42.3% (local) | `-O3 -fprofile-use` | **+6.65%** | [link](mining_results.pts_coremark-1.0.1.2026-10-26.md) (`balanced`; superseded) |
| 2026-10-27 | `pts/coremark-1.0.1` | compute-bound 42.6% (local) | `-O3 -funroll-loops -fprofile-use` | **+8.86%** | [link](mining_results.pts_coremark-1.0.1.2026-10-26b.md) (`performance`) |
| 2026-10-27 | `pts/tscp-1.2.2` | frontend-bound 54.7% (local) | `-O3 -flto -funroll-loops` | **+6.07%** | [link](mining_results.pts_tscp-1.2.2.2026-10-27.md) |
| 2026-10-27 | `pts/crafty-1.4.5` | frontend-bound 42.6% (local) | `-O3 -fno-pie -no-pie -mtune=znver5` | **+7.23%** | [link](mining_results.pts_crafty-1.4.5.2026-10-27.md) |
| 2026-10-27 | `pts/crafty-1.4.5` (PGO re-mines, exp. 10-11) | frontend-bound 42.4% (local) | `-O3 -fno-pie -no-pie -fprofile-use` | **+7.05%** | [link](mining_results.pts_crafty-1.4.5.2026-10-27b.md) (deterministic PGO) |
| 2026-10-27 | `pts/himeno-1.3.0` (exp. 13, 15) | memory-bound 62.0% (local) | `-O3` | **0%** | [link](mining_results.pts_himeno-1.3.0.2026-10-27.md) (exp. 15 with `--no-shape-filter`, 3 runs per rep) |

Base and best are each test's own score (coremark Iterations/Sec over 16 processes, TSCP and crafty nodes/sec on one
pinned core), not SPEC ratios:

| Benchmark | Base (`-O3`) | Best | Winning flags | Gain |
|---|---|---|---|---|
| `pts/coremark-1.0.1` | 382,163 | 416,025 | `-O3 -funroll-loops -fprofile-use` | **+8.86%** |
| `pts/tscp-1.2.2` | 2,576,439 | 2,732,788 | `-O3 -flto -funroll-loops` | **+6.07%** |
| `pts/crafty-1.4.5` | 13,456,441 | 14,405,707 | `-O3 -fno-pie -no-pie -fprofile-use` | **+7.05%** (three mines: +7.05% to +8.93%, winners all 14.4-14.5M) |
| `pts/himeno-1.3.0` | 7,800 MFLOPS | — | `-O3` | **0%** (best: `-march=native` +0.25%; streams 29 MB per sweep, memory-bound) |

The first mine (`balanced`, 361,329 → 385,356 with `-O3 -fprofile-use`) is kept for history. Its power sag
made every verdict except PGO's unreliable.

## Standing facts about this host

- **Under `balanced`, package power sags under sustained all-core load.** In the coremark mine it fell from about
  24 W to about 20 W some 14 minutes in, while CPU temperature *fell* too (84 → 76°C), and scores fell with it
  (r = 0.90). That points to a sustained power limit, not heat. It biased every Phase 3-4 delta after the baseline
  by about -3%, and the baseline recheck flagged it (-3.34%).
- **Under `performance`, there's no sag, but there is a 2-minute thermal transient.** A 10.5-minute check
  (2026-10-26: 25 back-to-back `-O3` coremark runs, fixed 9.6M iterations, power/temp/clock sampled every 5 s) held
  package power at 29.1-29.8 W from the second run to the last. In the first ~2 minutes the CPU hit 94-95°C and
  one run dropped to 352k (cpu0 averaging 3.1 GHz) before the fan caught up. From then on it held 84-87°C. Runs
  12-24 averaged **384,079 ± 0.36%** (sd), against about 361k for `-O3` under `balanced` (+6%). Runs 8-11 were
  noisier (374-381k); the test suite and a profile scan ran during that window, so they aren't clean evidence
  either way. Two 25-second warm-up reps wouldn't cover a cold start, which is why warm-up now has a 180 s
  minimum (item 3). In the re-mine the transient never showed up, because the 4.5-minute `deep-cpu`
  characterization run comes first.
- **Under `performance`, package power sits pinned at the platform limit, about 29 W**, and the limit can move.
  In the re-mine it dropped about 1 W (to ~28.0 W) 20 minutes in and stayed there. Scores moved about -0.5%.
- **About one coremark rep in eight reads about 1% low** under `performance`. That is too small for the slow-rep
  rerun, but it widens a 3-rep CI to about ±1.7%.
- **Coremark sized its own runs** (9.6M or 17.6M iterations, 27 or 47 seconds) until the backend pinned
  `COREMARK_ITERATIONS` (600,000 per process, 9.6M total) on 2026-10-26.
- **A single-threaded PTS test runs pinned to CPU 2** (a Zen5 core; its SMT sibling is CPU 10). Pinned and
  repeated 40 times per measurement, TSCP's 3-rep CIs were ±0.1-0.25%. One rep in the tscp mine still ran 5.5%
  slow for its whole duration with no visible cause, and the PGO reps, which keep the core busy several
  minutes with no idle, reached 92-95°C against the usual 75-79°C.
- **Coremark builds its flags into the binary** (`FLAGS_STR`), so `cfm`'s no-code-change guard never skips a
  coremark trial (CLAUDE.md's 2026-10-26 trap entry).

## Open items

| # | Pri | Opportunity | How | What would change |
|---|---|---|---|---|
| 1 | ~~H~~ | ~~**Is `-funroll-loops` a real coremark win?**~~ | Re-mine under `performance`. | **Done 2026-10-27:** yes, +5.86% (Phase 4), and PGO adds +3.10% on top, for +8.86% overall. `-march=native` is +2.58% alone but doesn't stack with unrolling. |
| 2 | ~~H~~ | ~~**Does the `performance` profile remove the power sag?**~~ | `powerprofilesctl set performance`, then 25 back-to-back coremark runs with power sampled. | **Done 2026-10-26:** power steady at ~29.5 W for 10 minutes, steady-state runs ±0.36%; the host now stays in `performance`. A 2-minute thermal transient remains (item 3). |
| 3 | ~~H~~ | ~~**Warm up long enough, and catch a power drop.**~~ The fixed two warm-up reps were sized for SPEC's multi-minute trials; a 25-second coremark rep needs ~2 minutes of load before it settles here. And the baseline recheck caught `balanced`'s sag but by design changes no verdict. | Pipeline changes: warm up by time or until two consecutive reps agree within ~1%, not a fixed count; flag (and rerun) a trial whose package power reads well below the baseline reps' mean, the way slow reps are rerun now; or re-run Phase 4 against a fresh baseline when the recheck flags. | **Done 2026-10-26** (commit `1853b3d`): settle-based warm-up (two reps within 1% and at least `--warmup-min-seconds`, default 180, at most 8 reps), package power sampled every 2 s during each run, and a rep more than 8% below the baseline's power rerun after 30 s idle (`--no-power-check`). In the re-mine neither guard had to act. |
| 4 | ~~M~~ | ~~**Fixed-work coremark runs.**~~ | Pass an explicit iteration count to `coremark.exe`. | **Done 2026-10-26:** `_RUN_OVERRIDES` runs `coremark.exe 0x0 0x0 0x66 600000` (same seeds as the no-argument run, so the CRC check still applies). Verified in the power check: 9.6M iterations every run. |
| 5 | M | **More Phoronix tests.** coremark, tscp, crafty and himeno are mined; c-ray is set up (2026-10-27: 1080p render about 77 s at `-O3 -ffast-math` on 16 threads, ~29-30 W, 83-90°C). Next on the survey's list: `n-queens`. Do a marker-flag build first: crafty's install.sh looked fine and silently dropped every flag. | Install CFLAGS-honoring PTS tests and add a `_VALIDATORS` entry for each; candidates are surveyed in [`phoronix_cflags_survey.md`](phoronix_cflags_survey.md). | Broader coverage outside SPEC. |
| 6 | L | **SPEC CPU2026 on `erie`.** SPEC is installed but unmined here. | Mine a few `intrate` benchmarks already done on `niwot`. | A same-CPU, different-chassis comparison: laptop power limits vs. the mini PC. |
| 7 | L | **Five calibration reps for short benchmarks.** The occasional 1%-low rep widens a 3-rep baseline CI to ±1.7%. The opposite happens too: himeno's 3 calibration reps landed together at the top of a 2% range (CI ±0.2%), and the recheck flagged -1.13%. | More reps when a rep is under a minute, or a tighter rerun threshold. | Tighter accept/reject on ~1-2% effects. |
| 8 | ~~H~~ | ~~**Catch a moderate slow rep in a tight set.**~~ tscp's trial 215 was 5.5% low against siblings agreeing to 0.1%, under the 10% rerun threshold. | A rerun rule relative to the flagset's own spread. | **Done 2026-10-27:** with 3+ reps, a rep more than 4x its siblings' spread (and at least 2%) below the slowest sibling is rerun (`SPREAD_RERUN_FACTOR`/`SPREAD_RERUN_MIN_PCT`). On erie's history it flags only trial 215. |
| 9 | M | **Trustworthy PGO on single-threaded tests.** tscp's PGO reps ran 13-16°C hotter than any other trial. | Idle after the training run, or a temperature check per rep. | A clean PGO verdict for tscp (probably still a reject, about -1.4%). |
| 10 | ~~M~~ | ~~**Deterministic PGO training for crafty.**~~ | Serial-only training isn't possible without patching crafty; instead one profile per flagset per mine. | **Done 2026-10-27:** experiment 11's PGO reps share one code fingerprint; PGO accepted at +2.54%. |
| 11 | M | **Quiet host for single-threaded mines.** crafty's experiment 11 had several 2-3%-low reps at flat power and temperature, with other Claude Code sessions running (load ~1.7). | Keep CPU 2's sibling (10) and one more core free of other work during a pinned mine, or check load before each rep. | Tighter CIs on tscp/crafty-style tests; `-mtune`/`-march` on top of PGO resolved. |
