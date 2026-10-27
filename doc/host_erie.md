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
| Phoronix Test Suite | 10.8.6, user directory `~/.phoronix-test-suite`; installed tests: `pts/coremark-1.0.1` only |
| SPEC | CPU2026 1.0.1 at `/home/mev/cpu2026`, `gcc_O3.cfg` (label `gcc_O3`, `copies = 16`, `threads = 16`); not mined here yet |
| Power | **profile `performance` since 2026-10-26** (`powerprofilesctl set performance`; ACPI platform profile, EPP and governor all follow to `performance`). amd-pstate `active`. The coremark mine ran under `balanced` (governor `powersave`, EPP `balance_performance`) |
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
| 2026-10-26 | `pts/coremark-1.0.1` | compute-bound 42.3% (local) | `-O3 -fprofile-use` | **+6.65%** | [link](mining_results.pts_coremark-1.0.1.2026-10-26.md) |

Base and best are coremark Iterations/Sec (16 forked processes), not SPEC ratios:

| Benchmark | Base (`-O3`) | Best | Winning flags | Gain |
|---|---|---|---|---|
| `pts/coremark-1.0.1` | 361,329 | 385,356 | `-O3 -fprofile-use` | **+6.65%** |

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
  either way. **Two 25-second warm-up reps don't cover the transient**; see open item 3.
- **Coremark sized its own runs** (9.6M or 17.6M iterations, 27 or 47 seconds) until the backend pinned
  `COREMARK_ITERATIONS` (600,000 per process, 9.6M total) on 2026-10-26.
- **Coremark builds its flags into the binary** (`FLAGS_STR`), so `cfm`'s no-code-change guard never skips a
  coremark trial (CLAUDE.md's 2026-10-26 trap entry).

## Open items

| # | Pri | Opportunity | How | What would change |
|---|---|---|---|---|
| 1 | **H** | **Is `-funroll-loops` a real coremark win?** It screened +5.07% at matched power, then confirmed flat against the higher-power baseline (+3.3% against the recheck). | Interleaved `cfm measure`: `-O3`, `-O3 -funroll-loops`, `-O3 -march=native`, `-O3 -fprofile-use -funroll-loops`, several rounds. | A real +3-5% would stack with PGO for roughly +10%. |
| 2 | ~~H~~ | ~~**Does the `performance` profile remove the power sag?**~~ | `powerprofilesctl set performance`, then 25 back-to-back coremark runs with power sampled. | **Done 2026-10-26:** power steady at ~29.5 W for 10 minutes, steady-state runs ±0.36%; the host now stays in `performance`. A 2-minute thermal transient remains (item 3). |
| 3 | **H** | **Warm up long enough, and catch a power drop.** The fixed two warm-up reps were sized for SPEC's multi-minute trials; a 25-second coremark rep needs ~2 minutes of load before it settles here. And the baseline recheck caught `balanced`'s sag but by design changes no verdict. | Pipeline changes: warm up by time or until two consecutive reps agree within ~1%, not a fixed count; flag (and rerun) a trial whose package power reads well below the baseline reps' mean, the way slow reps are rerun now; or re-run Phase 4 against a fresh baseline when the recheck flags. | Short PTS benchmarks get trustworthy Phase 3-4 verdicts on hosts like this one. |
| 4 | ~~M~~ | ~~**Fixed-work coremark runs.**~~ | Pass an explicit iteration count to `coremark.exe`. | **Done 2026-10-26:** `_RUN_OVERRIDES` runs `coremark.exe 0x0 0x0 0x66 600000` (same seeds as the no-argument run, so the CRC check still applies). Verified in the power check: 9.6M iterations every run. |
| 5 | M | **More Phoronix tests.** Only coremark is installed and validated. | Install CFLAGS-honoring PTS tests and add a `_VALIDATORS` entry for each; candidates are surveyed in [`phoronix_cflags_survey.md`](phoronix_cflags_survey.md). | Broader coverage outside SPEC. |
| 6 | L | **SPEC CPU2026 on `erie`.** SPEC is installed but unmined here. | Mine a few `intrate` benchmarks already done on `niwot`. | A same-CPU, different-chassis comparison: laptop power limits vs. the mini PC. |
