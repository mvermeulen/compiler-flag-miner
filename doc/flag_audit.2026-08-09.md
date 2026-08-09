# SPEC CPU2017 GCC flag audit

## Correction (same day, after the original run below)

The first version of this report was wrong in both directions, due to two real bugs in
`scripts/audit_flags_from_spec_results.py`'s `looks_like_gnu_compiler()` (fixed the same session,
confirmed live against this exact 494-config corpus — see the script's own docstring/comments for
the full detail):

1. **The "463 configs used" bucket was 100% AOCC (AMD's compiler), not GCC at all.** AOCC sets
   `CC=clang`/`CXX=clang++` but `FC=gfortran` (a real gfortran binary, running AOCC's own "Fortran
   Plugin" to give it AOCC/LLVM-backed codegen — the config's own words). The compiler check used
   `any()` across CC/CXX/FC, so `FC=gfortran` alone passed the *whole config* as "GNU," incorrectly
   attributing every clang-driven flag — including raw `-mllvm <opt>` LLVM-internal option
   passthroughs like `-unroll-threshold`, `-inline-threshold`, `-enable-gvn-hoist`, and the
   `-fplugin=dragonegg.so`/`-fplugin-arg-dragonegg-llvm-option=...` GCC-plugin-bridges-to-LLVM flags
   below — to "real-world GCC usage." Fixed by requiring **all** declared CC/CXX/FC roles to
   independently be GNU, plus a defense-in-depth scan for known non-GNU vendor banners (`AOCC`
   confirmed; see `_KNOWN_NON_GNU_VENDOR_MARKERS`).
2. **The "31 configs skipped" bucket was 100% real GCC (9.1.0 through 13.2.0, plus "Ampere GCC"),
   wrongly excluded.** Every one uses SPEC's own common config-template idiom
   (`SPECLANG = %{gcc_dir}/bin/` + `CC = $(SPECLANG)gcc`) — the compiler check never resolved
   `$(VAR)` references in CC/CXX/FC before checking them (it already did this for flag *values*, just
   not for the compiler-identity lines themselves), so `"$(SPECLANG)gcc"` never matched. Fixed by
   running CC/CXX/FC through the same `$(VAR)` resolution as everything else, plus a more robust
   word-boundary name match (`_gnu_name_if_any()`) that also correctly handles a real, common
   invocation style (target-triple-prefixed cross-compilers like `aarch64-linux-gnu-gcc`) while still
   correctly rejecting `clang++` (which literally ends in the three characters `"g++"`).

**Net effect**: re-running against the identical 494-config corpus (cached locally, zero new network
requests) now reports **31 configs used, 463 skipped** — the exact reverse of the original 463/31,
and the corrected numbers are the real ones (spot-checked several of each bucket's `sw_compiler000`/
`notes_comp_*` self-identification banners directly against the cached `.cfg` files). Everything below
this point is the corrected re-run, not the original.

The script's ignore-list also grew a few entries this session (diagnostic-suppression `-Wno-*`/`-w`,
build-speed-only `-pipe`, and legacy-buildability shims like `-fallow-argument-mismatch`/`-fcommon`
that are real but never performance-relevant) so a future re-run doesn't have to re-triage the same
non-candidates by hand — see the script's own comment above `_IGNORE_EXACT` for the full list and why
each one qualifies.

---

Catalog checked: `config/gcc_flag_catalog.seed.json`

- Configs used (GNU-compiler, successfully parsed): 31
- Configs skipped (compiler wasn't gcc/g++/gfortran): 463
- Configs with at least one unresolved `$(VAR)` reference: 0
- Fetch failures: 0

## Already known (catalog coverage confirmed against real GCC usage)

`-flto` (43), `-Ofast` (27), `-fprofile-generate` (24), `-fprofile-use` (24), `-funroll-loops` (23),
`-fstack-arrays` (17), `-march` (9)

## New candidates, grouped and annotated

Every one of these is a genuine GCC/GFortran flag (not a false positive from the bug above) worth a
human decision about whether to add to `config/gcc_flag_catalog.seed.json` — grouped by theme, with
a one-line verdict, rather than a flat table to re-analyze from scratch next time.

**Inlining/IPA `--param` family** (all from the same benchmark's peak config, 1-34 configs each) —
directly extends the existing `-finline-limit=N`/`--param prefetch-latency=N` entries' idea:
`--param:early-inlining-insns`, `--param:max-inline-insns-auto`, `--param:inline-unit-growth`,
`--param:ipa-cp-max-recursive-depth`, `--param:ipa-cp-eval-threshold`, `--param:ipa-cp-unit-growth`,
`--param:inline-min-speedup`. **Verdict: strong candidates**, same category/risk shape as the
existing `--param` entry.

**`-ffast-math` sub-component toggles** — `-fno-finite-math-only` (25), `-fno-unsafe-math-optimizations`
(25), `-fno-fast-math` (2). **Verdict: validates an existing catalog note directly**: the `-ffast-math`
entry already says "consider trying the sub-flags individually before the bundle" — real submissions
do exactly that, backing off one component rather than the whole bundle.

**Reverse-hypothesis toggles** — `-fno-stack-arrays` (17, the direct negation of the catalog's own
`-fstack-arrays` entry), `-fno-inline-functions-called-once` (16), `-fno-tree-vectorize` (1).
**Verdict: matches the existing `-funroll-loops` entry's own "worth trying OFF if currently on"
framing** — a real submitter turning a normally-beneficial optimization off is exactly the kind of
prior this catalog wants to capture.

**Target-tuning gap: AArch64.** `-mcpu` (26 configs, from an Ampere/AArch64 submission) and
`-ffinite-loops` (17). **Verdict: `-mcpu` is a real gap** — the catalog's `-march=<detected-uarch>`
entry is x86-specific; `-mcpu` is AArch64's analogous "detected microarch" lever and should get its
own entry once cfm's target detection covers non-x86 hosts.

**LTO/whole-program family** — `-flto-partition` (15), `-fwhole-program` (2). **Verdict: real
companions to the existing `-flto` entry**, worth adding alongside it.

**PGO refinement** — `-fprofile-partial-training` (1). **Verdict: minor but real** — directly extends
the existing `-fprofile-generate`/`-fprofile-use` PGO entries for the case of a non-representative
training run (which those entries already flag as a caveat-worthy scenario).

**Surprising catalog gap** — `-fomit-frame-pointer` (6). **Verdict: add it.** One of the most
well-known, common real-world GCC optimization flags; not previously in the catalog at all.

**Codegen-layout companion** — `-freorder-blocks-algorithm` (2, `simple`/`stc` variants).
**Verdict: real companion** to the existing `-freorder-blocks-and-partition`/`-freorder-functions`
entries.

**Borderline, needs a judgment call, not auto-added here** — `-fno-PIE` (6): real, can have a
measurable performance effect (removes PIE codegen overhead), but is more an environment/deployment
choice than a "try this for peak" lever; `-fopenmp` (31): real and impactful for the specific
benchmarks that support OpenMP parallelism, but scoping it correctly (which benchmarks, what thread
count) is a bigger design question than a one-line catalog entry.

## Ignored (confirmed non-performance: diagnostics, build-speed, ABI/buildability compatibility)

`-std` (58), `-DSPEC_LP64` (31), `-funsigned-char` (31), `-fgnu89-inline` (31), `-DSPEC_LINUX` (31),
`-DSPEC_CASE_FLAG` (31), `-DSPEC_OPENMP` (31), `-D_FILE_OFFSET_BITS` (29), `-g` (29), `-O3` (25),
`-fcommon` (25), `-fallow-argument-mismatch` (25), `-DSPEC_LINUX_%{suffix}` (23),
`-L%{gcc_dir}/lib` (17), `-L%{jemalloc_dir}/lib` (17), `-L%{gcc_dir}/lib64` (17), `-Wno-error` (16),
`-w` (15), `-z` (7, linker passthrough — see the script's own comment for what it's actually for),
`-DSPEC_%{os}_%{suffix}` (6), `-no-pie` (6), `-DSPEC_%{os}` (6), `-pipe` (4), `-fpermissive` (2),
`-static` (2), `-Wno-implicit-int` (2), `-DSPEC_LINUX_AARCH64` (1), `-DSPEC_LINUX_X64` (1)

## Configs skipped as non-GNU, by identity

| CC \| CXX \| FC (resolved) | Configs |
|---|---|
| `clang \| clang++ \| gfortran [vendor marker: AOCC]` | 463 |

## Next step

None of the "strong candidate" flags above have been added to `config/gcc_flag_catalog.seed.json`
yet — that's a real behavior change to a file M1's search loop reads from directly (CLAUDE.md's
branch/PR discipline treats catalog entries the same as code, not a doc-only tweak), left for a
deliberate follow-up PR rather than folded into this audit-tooling session.
