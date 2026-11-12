# `cfm mine` results: 865.roms_s on `chicago`, 2026-11-12

This is the tenth fpspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first
`865.roms_s` mine on any host. `865.roms_s` is the SPECspeed version of ROMS, the Regional Ocean Modeling System, a
Fortran ocean-circulation code parallelized with OpenMP; its rate counterpart was
[mined here on 2026-11-05](mining_results.765.roms_r.2026-11-05.md) (+7.19%, `-O3 -march=native`). Its corpus shape is
memory-bound at 95.1%, the strongest memory-bound read mined here.

## Headline result

**`-O3 -march=native`, +1.95% over plain `-O3`** (ratio 2.6194 → 2.6705). It's the same winning flag set as roms_r,
with about a quarter of the gain.

- **`-march=native` gave +1.95%.** All three of its reps (2.667-2.674) sat above every `-O3` calibration rep
  (2.616-2.626), and its CI [2.6623, 2.6787] is clear of baseline's [2.6058, 2.6330]. It was fast-tracked on the
  memory-bound prior (accepted 15 of 21).
- **Nothing added to it.** PGO read -0.35% and `-mprefer-vector-width=256` -0.52% on top of `-march=native`, both
  rejected. On roms_r the vector-width flag cost 4.04%, so 512-bit vectors still help roms here, just less.
- **`-fprefetch-loop-arrays` -0.55%, `-fgraphite-identity` -0.15%, `-fstack-arrays` +0.10%, `-flto` +0.06%**, all
  rejected. `-frecursive` built the same code as `-O3` and was skipped.
- **The shape filter dropped 8 candidates** on the 95.1% memory-bound read, `-Ofast` and `-ffast-math` among them.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 865.roms_s` (uncapped, defaults) |
| Code | `main` at `84bf0e4` (no code changes since `c933ee2`, PR #71) |
| SPEC config | `threads = 32`; `-ftree-parallelize-loops=32` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 25 |
| Started / finished | 2026-11-12T05:56:38Z / 2026-11-12T10:09:05Z (4h12m) |
| Final status | `converged` |
| Trials | 32 (1142-1173), 1 skipped as unchanged code, no reruns |
| Candidates screened / confirmed | 5 / 4 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | 8 (`-flto` kept, exempt) |
| Fast-tracked (M4) | `-march=native` (accepted 15 of 21, mean +15.56%) |
| Skipped as unchanged code | `-frecursive` (same code as `-O3`) |
| Winning flags | `["-O3", "-march=native"]`, +1.95% |
| Guards | bandwidth gate waited 30 s before 29 of 31 timed runs; no reruns; baseline recheck not flagged (+0.14%) |
| Power | package power median 84.97-85.06 W on every trial; CPU temperature 87.9-90.8°C |

A non-PGO trial took about 8 minutes and a PGO trial about 10. Every trial's `.rsf` reads `valid: S` for roms.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 95.1%, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 1142 | warm-up | 2.62052 |
| 1143 | warm-up | 2.60014 |
| 1144 | calibration | 2.62571 |
| 1145 | calibration | 2.61595 |
| 1146 | calibration | 2.61653 |
| 1167 | recheck | 2.62306 (+0.14%) |

The calibration mean is 2.619396, with a 95% CI of [2.60578, 2.63301] (±0.52%). Warm-up settled after the minimum
two reps (922 s). Every `-O3` build had the same code fingerprint (`6a711420`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 1147-1151 | screening | 5 candidates | 2.609-2.622 | | all survived (`-frecursive` skipped as unchanged code) |
| 1152-1154 | confirmation | `-fprefetch-loop-arrays` | 2.6049 | -0.55% | reject |
| 1155-1157 | confirmation | `-fgraphite-identity` | 2.6154 | -0.15% | reject |
| 1158-1160 | confirmation | `-fstack-arrays` | 2.6219 | +0.10% | reject |
| 1161-1163 | confirmation | `-flto` | 2.6209 | +0.06% | reject |
| 1164-1166 | confirmation (fast-tracked) | `-march=native` | 2.6705 | +1.95% | **accept** |
| 1168-1170 | PGO | `-march=native -fprofile-use` | 2.661 | -0.35% | reject |
| 1171-1173 | vector width | `-march=native -mprefer-vector-width=256` | 2.656 | -0.52% | reject |

Phase 6 deltas are against `-O3 -march=native`. With one accepted flag, Phase 5 had nothing to combine and ran no
trials. The microarch multiplier was skipped because the winning set already had `-march=native`. No candidate came
within the 1% bar, so PGO had no near-miss variant to try.

## Observations

- **roms gains less as a speed benchmark than as a rate one here**: `-march=native` +1.95% on 32 threads against
  +7.19% on 32 copies. fotonik3d went the same way (+5.43% rate, -0.71% speed), and palm the other way (+4.1% rate,
  +19.2% speed). The two that shrank are the two most memory-bound reads mined here (92.7%, 95.1%); one large grid
  shared by 32 threads may simply be more bandwidth-limited than 32 small private ones. That's a guess, not something
  this run measured.
- **The PGO builds had three different code fingerprints** and agreed within 0.1% (2.660-2.662), so retraining per
  build (CLAUDE.md's 2026-10-28 trap) didn't matter here.
- **The bandwidth gate waited before 29 of 31 timed runs**, and the recorded probes read 98.8-106.1 GB/s, near the
  session best, so it was catching the tail of the previous run, as on cloverleaf_s. The reps stayed tight.
- **niwot hasn't mined roms_s yet.**
