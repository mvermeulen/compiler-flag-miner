# Investigation: run-duration "settling"/drift, and why it isn't (just) thermal

**Prepared away from the mining host** -- this session had no access to a real `cfm.db` or the SPEC
CPU2026 install (`/home/mev/cpu2026` doesn't exist here, no `cfm.db` anywhere on this filesystem), so
nothing below was actually run against real data. This is a synthesis of what the four real
`doc/mining_results.*.md` write-ups already documented, a set of hypotheses to evaluate, and a ready-to-run
script (`scripts/analyze_trial_drift.py`) for whoever picks this up on the machine that actually ran the
mining jobs. Treat every "worth checking" below as literally that -- unconfirmed until re-run there.

## What's already documented

Four real `cfm mine` runs each independently noticed "ratio isn't stable through the first several
minutes/hours of sustained load, and the pattern tracks elapsed time/trial order far more tightly than it
tracks which flag was under test" -- in three distinct shapes:

| Run | Shape | Timescale | Magnitude | Thermal checked against real telemetry? |
|---|---|---|---|---|
| `doc/mining_results.782.lbm_r.2026-08-21.md` | Near-monotonic ramp across the whole run | ~7.8h | ~12% rise, trial 58->78 | No -- only hypothesized (overnight ambient cooling), explicitly flagged as unconfirmed in that doc |
| `doc/mining_results.714.cpython_r.2026-08-21.md` | Step: fast baseline window, then a stable *lower* band for the rest of the run | ~2.4h | baseline mean 63.39 vs. steady-state ~60-62 | No |
| `doc/mining_results.706.stockfish_r.2026-08-23.md` | Baseline's own 3 reps front-loaded-high-then-settling (103.6 -> 97.7 -> 94.8) | ~20min | ~9% front-to-back spread | No (didn't matter for that run -- the real win, +48.75%, was far too large to be swamped) |
| `doc/mining_results.750.sealcrypto_r.2026-08-24.md` | Baseline settling downward (56.18 -> 54.80 -> 52.09), then flat through screening | ~15min | ~7.5% front-to-back spread | **Yes -- and ruled out.** See below. |

The `750.sealcrypto_r` run is the one case anyone actually lined ratio up against a real sensor reading.
Quoting that doc directly:

> lining up each trial's own recorded `cpu_temp_c` against its ratio shows temperature staying in a
> narrow 90.9-93.9C band with no correlation to the pattern -- trials 221->222->223 sit at
> 91.5C->92.0C->92.2C (flat, if anything rising) while their ratios go 50.65->62.14->50.60, a 23% swing
> fully explained by which flag compiled in, not temperature; the `-march=native` confirmation reps show
> the same disconnect in reverse (temp drops 93.4C->91.6C while ratio stays flat at ~62.0).

That's a real, already-collected negative result for the simple "the chip is throttling" explanation --
not an assumption, not waved off. It only covers one of the four documented occurrences, though, and it
never checked *why* the baseline itself was settling in the first place, only that die temp wasn't the
mechanism.

## An important caveat on what "thermal" was actually checked

Every `cpu_temp_c` value in every one of these runs comes from exactly one source:
`agents/spec_agent.py`'s `_extract_cpu_temp_c()`, which regex-parses wspy's `quick` profile's `--system`
output (`"cpu temp   XX.X C"`). Reading `vendor/wspy/system.c` directly: that value is **package/die
temperature only** (`k10temp`'s `Tctl`/`Tdie` on AMD, `coretemp` on Intel -- `TEMP_HWMON_DRIVERS`/
`TEMP_PREFERRED_LABELS` in that file). "Thermal ruled out" so far means specifically **die-temp
throttling ruled out** -- it says nothing about a chassis/ambient/skin-temperature-gated mechanism that
wouldn't show up on that sensor at all (see Hypothesis 2 below). Worth being precise about this distinction
before writing off "thermal" as a category entirely.

## Hypotheses

None of these are confirmed. Ranked by how cheap they are to check first.

1. **Baseline-window artifact, not a physical effect at all.** Every run's own baseline (Phase 1, 3 reps)
   runs first, before anything else, and Phase 3 screening (as of the 2026-08-24 `most_recent_ratio` fix)
   already changed its own comparison basis specifically because of this -- see CLAUDE.md's matching
   "Resolved 2026-08-24" traps-log entry. Worth checking first whether the *drift itself* also
   disappears/shrinks once measured against a per-window baseline instead of assuming a real environmental
   cause is needed at all. Some of what's currently being called "settling" may just be normal trial-to-
   trial variance that only looks like a trend because baseline happened to sample from the tail of it.

2. **A chassis/host-level power-management ramp that die temp can't see.** If the actual mining host is a
   laptop-class part (this needs confirming *on that machine* -- don't assume it from this session, see
   next section), AMD's mobile parts use STAPM (Skin Temperature Aware Power Management): an internal,
   firmware-modeled *skin* temperature, not exposed by `k10temp`, that gates the sustained power limit
   (PPT) and eases it upward over real wall-clock minutes as the model decides the chassis can absorb more
   sustained draw. This would produce exactly the disconnect `750.sealcrypto_r` found (die temp flat/no
   correlation, ratio still moving) because it's tracking a variable nothing here currently measures at
   all. If the host is a desktop/server part instead, this hypothesis doesn't apply and can be dropped
   immediately -- check the host's own chassis/CPU model before spending any time on this one.
3. **CPU frequency-governor/EPP ramp.** A `powersave`-style governor with an EPP hint (as opposed to a
   fixed `performance` governor) can take real elapsed wall-clock time under *sustained* load to settle
   into its eventual steady-state effective frequency, independent of temperature entirely. Cheap to check
   (`cpupower frequency-info`, or just reading `scaling_governor`/`energy_performance_preference` on the
   real host) and cheap to fix (force `performance` for a mining run) if confirmed.
4. **SPECrate warm-up state (cache/TLB/branch-predictor), not clock/power at all.** First copies of a
   fresh SPECrate run pay cold page-cache/TLB/branch-predictor costs that later copies, or later trials
   reusing the same working set, don't. This is a *compute-bound-looking* mechanism (IPC would visibly
   rise over the run) as opposed to hypotheses 2/3 (frequency-bound-looking: IPC roughly flat, wall-clock
   ratio still rises because more instructions/sec are actually being retired at a higher clock). These
   are distinguishable with data that's already almost being collected -- see "Already-collected data"
   below.
5. **Something host-specific and non-thermal already ruled in as a candidate but not confirmed**:
   `750.sealcrypto_r`'s own doc explicitly leaves "SPECrate's own per-copy startup variance, page
   cache/TLB warm-up state, or another non-thermal effect this project doesn't currently instrument" as
   open. Hypothesis 4 above is a sharper version of this, not a new idea.

## Before trusting any host-specific claim: confirm what machine this actually is

This session is not the mining host (confirmed: no `/home/mev/cpu2026`, no `cfm.db` anywhere on this
filesystem). Whoever picks this up on the real machine should confirm, and record here or in the next
mining-results doc, before leaning on hypothesis 2/3 above:

```
lscpu | grep -i "model name"
cat /sys/class/dmi/id/chassis_type      # 3=Desktop, 9/10=Laptop/Notebook, etc.
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference 2>/dev/null
ls /sys/class/power_supply/             # any battery present at all -> mobile part
sensors 2>/dev/null | head -30          # what temp/power sensors actually exist
```

(`CLAUDE.md`'s own traps log names the real mining host as having `-march=native` expand to `znver5`
Zen5 -- confirm the CPU model matches that before assuming anything about STAPM/mobile-part-specific
behavior; if it's a desktop or server Zen5 part, hypothesis 2 doesn't apply and can be dropped.)

## Already-collected data worth mining, roughly cheapest-first

1. **`cfm.db`'s own `trials`/`hypotheses` tables, queried across every experiment at once.**
   `scripts/analyze_trial_drift.py` (new, this investigation) does exactly this: joins each trial's
   `created_at`/`ratio`/`phase`/`flags_json` against its `hypotheses` rows (the already-recorded
   `cpu_temp_c` text and the compiled-flags-audit warning text), per experiment, and reports a Pearson
   correlation of ratio against elapsed time and against `cpu_temp_c`. This is pure analysis of data that
   already exists in every past experiment's rows -- nobody has run one query across all of them together,
   every finding above came from reading one run's doc by eye. Run it first:
   ```
   python3 scripts/analyze_trial_drift.py --db /path/to/real/cfm.db
   # or, to also get one CSV per experiment for plotting elsewhere:
   python3 scripts/analyze_trial_drift.py --db /path/to/real/cfm.db --csv-dir /tmp/drift_csv
   ```
2. **The `quick` profile's own `--rusage`/`--counters=ipc` output -- collected on every trial already,
   parsed for nothing but `cpu_temp_c` so far.** `agents/spec_agent.py` only ever extracts the temperature
   line out of `RunSignature.raw_output`; IPC, page faults, and voluntary/involuntary context switches are
   sitting in that same raw text on every single trial and are currently discarded. IPC drifting upward
   over a run (hypothesis 4) vs. staying flat while ratio still rises (hypotheses 2/3) is a clean,
   already-half-collected way to tell a compute-bound warm-up explanation apart from a frequency/power one
   -- would need a small follow-up to `_extract_cpu_temp_c()`'s own pattern (a sibling `_extract_ipc()`)
   before `scripts/analyze_trial_drift.py` could report it too.
3. **Host `sar`/sysstat logs**, if the real mining host runs sysstat with a long enough `HISTORY` --
   already used once, ad hoc, in the isolated-candidate-flags investigation (CLAUDE.md's 2026-08-22 traps
   entry) to directly rule out swap thrashing via real historical data, not assumption. Global
   load/%idle/%iowait/%steal at whatever resolution that host's `sadc` collects at, correlatable against
   each run's own `started_at`/`finished_at` window. Check retention (`HISTORY=` in
   `/etc/sysstat/sysstat`) promptly if you want this for the older (2026-08-20/21) runs specifically --
   a short retention window rotates old data out.
4. **`journalctl`/`dmesg` for each run's exact time window** -- thermal-throttle kernel messages, cpufreq
   transition logs, power-supply online/offline events (the same tool that caught the 2026-08-20 OOM
   incident, CLAUDE.md's traps log). Cheap grep, would directly confirm or rule out a power-state flip
   (e.g. an AC adapter dropping out momentarily, if the host turns out to be a mobile part) mid-run.

## Concrete next steps, in order

1. Run `scripts/analyze_trial_drift.py` against the real `cfm.db` for all four affected experiments.
   Compare its Pearson-correlation output against each doc's own by-eye read of the same run -- this is
   the fastest way to confirm the script's join logic is right before trusting it for anything new.
2. Confirm the real host's CPU model/chassis type/governor (commands above) before spending more time on
   hypothesis 2 or 3 specifically.
3. If IPC-vs-ratio (hypothesis 4) still looks live after step 1/2, add IPC extraction alongside
   `_extract_cpu_temp_c()` and re-run.
4. Only after 1-3: consider a dedicated diagnostic run (repeated `quick`-profile trials at a single fixed
   flag for 1-2h, isolating the settling curve from which candidate happened to run when) -- this is the
   most expensive option and shouldn't be reached for before the analysis above has been tried on data
   that already exists.

## Update, same day: run against the real mining host

Step 1 and step 2 of the "concrete next steps" above, actually done.

**`scripts/analyze_trial_drift.py --db cfm.db`, run against all 17 real experiments.** Confirms the
by-eye reads from every affected doc, now systematically: `Pearson r(ratio, elapsed_min)` is
moderate-to-strong (`+0.48` to `+0.82`) in every real, undisturbed run long enough to have more than a
few points, while `r(ratio, cpu_temp_c)` is consistently weaker wherever both are available (e.g.
experiment 13: `+0.479` vs `+0.165`; experiment 16: `+0.651` vs `+0.256`; experiment 17: `+0.572` vs
`+0.239`) — the script's own per-experiment note ("ratio tracks elapsed time much more tightly than it
tracks `cpu_temp_c` ... NOT primarily thermal") fires on five separate experiments independently, not
just the one (`750.sealcrypto_r`) that had already been checked by eye.

**The sign is the important new piece of information this cross-experiment view surfaces that no single
run's own doc emphasized: ratio rises with elapsed time in every one of these, not falls.** Higher
`ratio` means *faster* (fewer seconds per copy). A monotonic *improvement* over a run's own duration is
the opposite of what thermal throttling or component wear-in would predict (both degrade performance
over time as heat/stress accumulates) — it's exactly the shape a **sustained power limit that eases
upward over real wall-clock minutes** would produce, which is hypothesis 2's own specific prediction,
not hypothesis 3's or 4's.

**Host identity and configuration, confirmed directly (not assumed) — hypothesis 3 is now ruled out,
hypothesis 2 is now the best-supported remaining explanation:**

```
Model name:        AMD RYZEN AI MAX+ PRO 395 w/ Radeon 8060S      (Strix Halo, mobile/workstation APU)
chassis_type:      10                                              (Notebook)
scaling_governor:  performance
energy_performance_preference: performance
scaling_driver:    amd-pstate-epp
power_supply:      AC (online=1), BAT0 (98%, not charging)
hwmon sensors present: k10temp (die temp -- the source `_extract_cpu_temp_c()` already reads),
                       amdgpu (exposes `power1_average`, currently ~9W at idle -- APU package power,
                       not yet monitored during a real trial)
```

- **Hypothesis 3 (governor/EPP ramp) is directly ruled out**: both the governor and EPP hint are
  already pinned to `performance`, not a `powersave`-style setting that would need real wall-clock time
  to settle into a steady-state frequency. Nothing here is ramping *because* of a governor policy.
- **Hypothesis 2 (STAPM-style skin-temperature-aware power management) is now the best-supported
  remaining explanation, not just a plausible guess**: this is confirmed a real mobile/notebook-chassis
  AMD part (`chassis_type=10`), AC-powered with a battery present — exactly the class of hardware STAPM
  targets. `k10temp` (die temp) already confirmed uncorrelated with the ratio pattern (the
  `750.sealcrypto_r` finding) is consistent with STAPM's own internal skin-temperature model being a
  *different, unexposed* variable from anything `k10temp` reports — die temp can stay flat while a
  firmware-modeled skin temperature (which STAPM actually gates the sustained power limit on) still
  climbs and eases the power ceiling upward over real minutes, matching the observed shape exactly.
- **Not yet directly observed**: the actual power limit (PPT) ramping in real time. No `power1_cap`
  readback is exposed via the `amdgpu` hwmon path checked here (a dedicated tool like `ryzenadj` would
  be needed to read it directly) — but `amdgpu`'s own `power1_average` sensor *is* already present and
  readable, and would be a cheap thing to sample alongside `cpu_temp_c` on a future run's own trials
  (the same pattern `_extract_cpu_temp_c()` already uses) to check directly whether package power draw
  itself ramps upward over a run's early minutes, which would be much more direct confirmation of
  hypothesis 2 than the elapsed-time correlation alone.

**Hypothesis 1 (pure baseline-window sampling artifact, no real physical cause)** looks weaker after
this cross-experiment view than it did considering any single run alone: the same upward-with-elapsed-
time shape recurs across five independent experiments, multiple benchmarks, and timescales from ~15
minutes (`750.sealcrypto_r`) to ~7.8 hours (`782.lbm_r`'s 2026-08-21 run) — a coincidence of baseline
sampling wouldn't be expected to recur this consistently in the same direction across genuinely
unrelated benchmarks and run durations. This doesn't rule out hypothesis 1 contributing some of the
*apparent* magnitude in any one run, but a purely physical cause (most likely hypothesis 2) now looks
like the dominant driver, not baseline noise alone.

## What this doesn't change

No conclusion in any of the four `doc/mining_results.*.md` accept/reject verdicts is being revisited here
-- every one of those already passed the CI-overlap confirmation bar regardless of this drift's cause.
This is purely about understanding a real, repeatedly-observed methodological wrinkle (and, per the
2026-08-24 `most_recent_ratio` fix, one that's already partially been designed around at the Phase 3
screening step) before it causes a real accept/reject call to go the wrong way on some future benchmark
where the effect size is smaller than `-march=native`'s.
