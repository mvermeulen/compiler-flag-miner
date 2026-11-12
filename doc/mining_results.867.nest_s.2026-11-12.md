# `cfm mine` results: 867.nest_s on `chicago`, 2026-11-12

This is the eleventh fpspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first
`867.nest_s` mine on any host. `867.nest_s` is the SPECspeed version of NEST, a C++ simulator for large networks of
spiking neurons, parallelized with OpenMP; its rate counterpart was
[mined here on 2026-11-08](mining_results.767.nest_r.2026-11-08.md) (+1.34%, `-O3 -fno-stack-protector`). Its corpus
shape is memory-bound at 65.6%.

## Headline result

**No flag beat plain `-O3`** (ratio 4.3744), but this reject is weaker than the other flat fpspeed results here.
`-O3`'s own runs varied by 4.2%, which made the baseline CI ±3.65%, so a gain of 2-3% couldn't be resolved.

- **`-march=native` read +3.67% and was rejected on CI overlap.** Its reps were 4.456, 4.560 and 4.588. The microarch
  multiplier's `-march=znver5` built the same code (`df29754b`) and read +1.71% (4.426-4.464). Pooled, the six runs of
  that code average 4.492, +2.69% over the `-O3` calibration mean. That's probably a real gain of a few percent, but
  this run can't show it.
- **`-fgraphite-identity` read +1.44%**, with tight reps (4.426-4.446, after one slow rep was re-run). It was also
  rejected on CI overlap with the wide baseline.
- **PGO read -0.05%, `-mtune=znver5` +0.65%, `-flto` +0.96%, `-fno-math-errno` +0.59%**, all rejected.
  `-fprefetch-loop-arrays` read -0.89%.
- **The shape filter dropped 10 candidates** on the 65.6% memory-bound read, `-fno-stack-protector` (nest_r's winner),
  `-Ofast` and `-ffast-math` among them. `-flto` and `-fno-math-errno` were kept as exempt.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 867.nest_s` (uncapped, defaults) |
| Code | `main` at `f71ff79` (no code changes since `c933ee2`, PR #71) |
| SPEC config | `threads = 32`; `-ftree-parallelize-loops=32` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 26 |
| Started / finished | 2026-11-12T10:09:19Z / 2026-11-12T16:20:36Z (6h11m) |
| Final status | `converged` |
| Trials | 36 (1174-1209), none skipped, 1 slow-rep rerun |
| Candidates screened / confirmed | 4 / 4 (plus `-march=native` fast-tracked, rejected) |
| Excluded on shape (Phase 2) | 10 (`-flto` and `-fno-math-errno` kept, exempt) |
| Fast-tracked (M4) | `-march=native` (accepted 16 of 22, mean +14.94%) |
| Winning flags | `["-O3"]`, +0.00% |
| Guards | bandwidth gate waited 30 s before 10 of 36 timed runs; 1 slow-rep rerun (trial 1189); baseline recheck +2.48%, inside the CI so not flagged |
| Power | package power median 84.99-85.02 W on every trial; CPU temperature 87.6-92.4°C |

A non-PGO trial took about 9.5 minutes and a PGO trial about 19. Every timed run's `.rsf` reads `valid: S` for nest.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 65.6%, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 1174 | warm-up | 4.37888 |
| 1175 | warm-up | 4.45305 |
| 1176 | warm-up | 4.45577 |
| 1177 | calibration | 4.39784 |
| 1178 | calibration | 4.30169 |
| 1179 | calibration | 4.42357 |
| 1200 | recheck | 4.48268 (+2.48%) |

The calibration mean is 4.374363, with a 95% CI of [4.21476, 4.53396] (±3.65%), the widest on this host so far
(palm_s, the next widest fpspeed baseline, was ±0.77%). Warm-up needed a third rep to settle (1,697 s). Every `-O3`
build had the same code fingerprint (`23d24cd2`), and its seven runs span 4.302-4.483.

Trial 1178 read 2.2% below its slowest sibling. The spread rule needs more than 4× the siblings' own spread (0.59%,
so 2.4%), so it wasn't re-run, and it alone accounts for most of the CI's width.

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 1180-1183 | screening | 4 candidates | 4.396-4.495 | | all survived |
| 1184-1186 | confirmation | `-fprefetch-loop-arrays` | 4.3355 | -0.89% | reject |
| 1187-1190 | confirmation | `-fgraphite-identity` | 4.4373 | +1.44% | reject (CI overlap); slow rep 1189 (4.032) re-run as 1190 |
| 1191-1193 | confirmation | `-flto` | 4.4162 | +0.96% | reject |
| 1194-1196 | confirmation | `-fno-math-errno` | 4.4000 | +0.59% | reject |
| 1197-1199 | confirmation (fast-tracked) | `-march=native` | 4.5347 | +3.67% | reject (CI overlap) |
| 1201-1203 | PGO | `-fprofile-use` | 4.372 | -0.05% | reject |
| 1204-1206 | microarch | `-march=znver5` | 4.449 | +1.71% | reject (same code as `-march=native`) |
| 1207-1209 | microarch | `-mtune=znver5` | 4.403 | +0.65% | reject |

With nothing accepted, Phase 5 ran no trials and Phase 6 layered on plain `-O3`. The vector-width multiplier was
skipped because the winning set has no `-march=`. No reject was CI-clear of baseline, so PGO had no near-miss variant.

## Observations

- **nest_s is the noisiest benchmark mined here.** The same `-O3` code ran between 4.302 and 4.483, and the same
  `-march=native` code between 4.426 and 4.588. Package power held at 85.0 W and temperature in a 5°C band throughout,
  and the bandwidth probe readings (90-106 GB/s) don't line up with the slow runs, so nothing recorded explains it.
  It might come from the simulation itself: NEST distributes neurons and spike delivery across threads, and the
  load balance may vary from run to run.
- **`-march=native` is likely worth 2-3% on nest_s.** Six runs of its code averaged +2.69% over the calibration mean,
  and every one of them beat 4.302, the low baseline rep. With this much noise, three reps a side can't clear the CI
  test. Open item 16 proposes a longer interleaved measurement.
- **nest_r's winner was never tried.** `-fno-stack-protector` (+1.34% on nest_r) was excluded on shape here.
- **PGO took about 19 minutes a trial and read flat**, where on nest_r it lost 6.1%.
- **niwot hasn't mined nest_s yet.**
