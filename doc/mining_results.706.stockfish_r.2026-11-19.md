# `cfm mine` results: 706.stockfish_r on `chicago`, 2026-11-19

This is the first intrate benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `706.stockfish_r`
is the Stockfish chess engine (C++), whose evaluation is an NNUE neural network. niwot mined it on 2026-10-17
(`-O3 -march=native`, +48.42%, [write-up](mining_results.706.stockfish_r.2026-10-17.md)). Its corpus shape is
memory-bound at 45.3%, under the 55% gate, so the shape filter excluded nothing.

## Headline result

**`-O3 -march=native -fno-pie -no-pie`, +54.65% over plain `-O3`** (ratio 112.742 → 174.353).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 112.742 | — |
| `-O3 -march=native` | 172.227 | +52.76% |
| `+ -fno-pie -no-pie` | 174.353 | +1.23% |

- **`-march=native` gave +52.76%**, against +48.42% on niwot and +48.75% on this machine in August. Its three reps
  span 172.212-172.242 (0.02%).
- **`-fno-pie -no-pie` gave +2.46% alone and +1.23% on top of `-march=native`**, the first accept for that flag in the
  memory-bound cluster here (0 of 7 before). It wasn't in the catalog when niwot mined stockfish. A guess at why:
  without PIE, an access like `table[i]` to a global array can use the array's absolute address as the
  displacement in a single instruction, where PIE needs a separate `lea` first, and stockfish's search and
  evaluation index many global tables. The run doesn't show that directly.
- **`-funroll-loops` gave +2.27% alone but -2.76% on top of `-march=native -fno-pie -no-pie`**, so it isn't in the
  winning set.
- **`-flto` lost 18.1% at screening** (92.25, against the last calibration rep), as on niwot (-16.6%, confirmed by re-measurement; niwot open item 4).
  **`-fipa-pta` lost 40.7%** (66.86), the largest single-flag loss mined on any host so far. Both were pruned there.
- **PGO lost 1.14%** on top of the winner, and its near-miss variant (with `-fno-math-errno`) lost 1.19%.
  **`-mprefer-vector-width=256` lost 8.25%**: stockfish wants the 512-bit vectors.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 706.stockfish_r` (uncapped, defaults) |
| Code | `main` at `8cfe190` (includes PR #72's throttle stop; the kernel note `6da67bc` landed during the run) |
| SPEC config | `gcc_O3.cfg`, `copies = 32` |
| Experiment id | 29 |
| Started / finished | 2026-11-19T04:25:25Z / 2026-11-19T14:37:59Z (10h13m) |
| Final status | `converged` |
| Trials | 83 (1290-1372), none skipped, no reruns |
| Candidates screened / confirmed | 14 / 12 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | none (45.3% is under the 55% gate) |
| Fast-tracked (M4) | `-march=native` (accepted 18 of 25, mean +15.63%) |
| Accepted in Phase 4 | `-march=native` +52.76%, `-fno-pie -no-pie` +2.46%, `-funroll-loops` +2.27% |
| Winning flags | `["-O3", "-march=native", "-fno-pie -no-pie"]`, +54.65% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 60 of 83 timed runs; no reruns; **baseline recheck flagged (-1.94%)** |
| Power | package power median 84.99 W on every trial (PGO included); CPU temperature 87.5-95.2°C |

A non-PGO trial took about 6.5 minutes (the `-fipa-pta` one about 10), a PGO trial about 23. The last run's
`.rsf` reads `valid: S`.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 45.3%, `vectorization_density=moderate`,
`allocation_pressure=high`. niwot's local characterization read it frontend-bound 40.6%; it sits near that boundary.

| Trial | Role | Ratio |
|---|---|---|
| 1290 | warm-up | 112.587 |
| 1291 | warm-up | 112.919 |
| 1292 | calibration | 112.701 |
| 1293 | calibration | 112.821 |
| 1294 | calibration | 112.704 |
| 1348 | recheck | 110.556 (**-1.94%, flagged**) |

The calibration mean is 112.742, with a 95% CI of [112.572, 112.912] (±0.15%). Warm-up settled after the minimum two
reps (775 s). Every `-O3` build, the recheck included, had the same code fingerprint (`333eb238`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 1295-1308 | screening | 14 candidates | 66.86-115.71 | | 12 survived; `-flto` (92.25, -18.1%) and `-fipa-pta` (66.86, -40.7%) pruned |
| 1309-1311 | confirmation | `-fprefetch-loop-arrays` | 111.869 | -0.77% | reject |
| 1312-1314 | confirmation | `-fgraphite-identity` | 112.834 | +0.08% | reject |
| 1315-1317 | confirmation | `-fno-pie -no-pie` | 115.516 | +2.46% | **accept** |
| 1318-1320 | confirmation | `-fno-stack-protector` | 112.668 | -0.07% | reject |
| 1321-1323 | confirmation | `-fcf-protection=none` | 112.870 | +0.11% | reject |
| 1324-1326 | confirmation | `-U_FORTIFY_SOURCE` | 113.073 | +0.29% | reject (CI-clear, under the 1% bar) |
| 1327-1329 | confirmation | `-funroll-loops` | 115.301 | +2.27% | **accept** |
| 1330-1332 | confirmation | `-Ofast` | 112.899 | +0.14% | reject |
| 1333-1335 | confirmation | `-ffast-math` | 112.824 | +0.07% | reject |
| 1336-1338 | confirmation | `-fno-math-errno` | 113.126 | +0.34% | reject (CI-clear, under the 1% bar) |
| 1339-1341 | confirmation | `-fno-ipa-cp-clone` | 112.741 | 0.00% | reject |
| 1342-1344 | confirmation | `-fno-unswitch-loops` | 112.816 | +0.07% | reject |
| 1345-1347 | confirmation (fast-tracked) | `-march=native` | 172.227 | +52.76% | **accept** (the greedy start) |
| 1348 | baseline recheck | `-O3` | 110.556 | -1.94% | flagged |
| 1349-1351 | combination (greedy) | `-march=native -fno-pie -no-pie` | 174.353 | +1.23% | **accept** |
| 1352-1354 | combination (greedy) | `+ -funroll-loops` | 169.539 | -2.76% | reject |
| 1355-1357 | combination (pair) | `-funroll-loops -march=native` | 167.724 | +48.77% | accept, below the greedy winner |
| 1358-1360 | combination (pair) | `-fno-pie -no-pie -funroll-loops` | 117.274 | +4.02% | accept, below the greedy winner |
| 1361-1363 | combination (pair) | `-fno-pie -no-pie -march=native` | 174.543 | +54.82% | accept, same code as the winner |
| 1364-1366 | PGO | winner `+ -fprofile-use` | 172.362 | -1.14% | reject |
| 1367-1369 | PGO (near-miss variant) | winner `+ -fno-math-errno -fprofile-use` | 172.279 | -1.19% | reject |
| 1370-1372 | vector width | winner `+ -mprefer-vector-width=256` | 159.976 | -8.25% | reject |

Phase 4 deltas are against `-O3`, greedy-step deltas against the step before, pair deltas against `-O3`, and Phase 6
deltas against the winner. The greedy walk started from the Phase 4 `-march=native` result rather than re-measuring
it. The microarch multiplier was skipped because the winning set already had `-march=native`.

## Observations

- **The baseline recheck read 1.94% low on identical code.** Trial 1348 had the `-O3` fingerprint, a normal
  bandwidth probe (105.1 GB/s), 84.99 W and 93.5°C, so nothing recorded explains it, and it's one rep. It doesn't
  change a verdict: the +52.8% win is far outside it, and `-fno-pie -no-pie`'s +2.46% held up in the pair trials
  (`-fno-pie -no-pie -funroll-loops` at +4.02%, `-march=native -fno-pie -no-pie` at +54.82%). It's the first flagged
  recheck on this host.
- **The winning code (`57921615`) measured 174.11-174.76 over six runs**, three as the greedy step and three as the
  pair.
- **Unrolling and `-march=native` don't stack**: `-funroll-loops -march=native` (167.72) is 2.6% below
  `-march=native` alone (172.23). Unrolling probably adds little to loops already vectorized with AVX-512, and the
  bigger code costs instruction-cache space.
- **PGO drew full power (84.99 W)** and lost a tight 1.1%, unlike neutron_s's low-power PGO loss. On niwot PGO read
  -0.10% on top of `-march=native`.
- **`-fipa-pta` is worth a look.** A 41% loss from a points-to analysis flag is surprising; it may have blocked
  vectorization or inlining in the NNUE code. It was one screening trial, so it isn't confirmed.
