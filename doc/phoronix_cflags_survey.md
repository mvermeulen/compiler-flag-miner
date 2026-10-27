# Phoronix Test Suite: which tests take compiler flags (survey, 2026-10-26)

Which PTS tests could `cfm` mine through `cfm/workloads/phoronix.py`? That needs a test that builds from source
and lets the trial's flags reach the compiler. This survey scanned the latest version of every profile in
`erie`'s `~/.phoronix-test-suite/test-profiles/pts` (PTS 10.8.6; 564 tests, 1,659 profile versions). It read each
`install.sh`, `test-definition.xml` and `results-definition.xml`. Nothing was downloaded or built, so a test
that leaves flags to its own Makefile is classified "probably", not confirmed. The scan script is not in the repo
(it lives in the session scratchpad); rerunning it is a few seconds of regex over the profiles.

## How PTS passes flags

PTS has no flag mechanism of its own: it exports the user's environment to `install.sh`, and each profile
decides what to do with it. Four patterns show up:

1. **`$CFLAGS`/`$CXXFLAGS` on the compile line or in an export** (45 tests), usually next to hard-coded
   flags: `cc -O3 $CFLAGS ...`, `export CFLAGS="-O3 -march=native $CFLAGS"`. Ours come *after* the profile's,
   so our `-O` level and `-march=` win (GCC takes the last of each), and everything else is additive. The
   profile's other hard-coded flags can't be removed.
2. **The `CFLAGS_OVERRIDE` convention** (12 tests): `crafty`, `ebizzy`, `hint`, `hpcc`, `iperf`, `m-queens`,
   `n-queens`, `netperf`, `npb`, `polybench-c`, `stream`, `tscp`. Without it they build with
   `CFLAGS="$CFLAGS -O3 -march=native"`, so our flags come *first* and lose. With `CFLAGS_OVERRIDE` set, they
   use exactly that string. **The backend must set `CFLAGS_OVERRIDE` to the trial's flags** for these, or every
   trial is silently `-O3 -march=native`.
3. **Implicit, through the build system** (149 tests): autotools `./configure`, CMake and Meson read
   `CFLAGS`/`CXXFLAGS` from the environment on a fresh configure, which the backend always does. One catch:
   with `-DCMAKE_BUILD_TYPE=Release`, CMake appends `-O3 -DNDEBUG` *after* the environment flags, so the `-O`
   level is fixed at `-O3`. Additive flags still work. (`-Ofast` then becomes `-O3`; the no-code-change guard
   would catch that.)
4. **Plain `make` or a direct compiler call with no flag variable** (111 tests): it depends on the Makefile.
   `CFLAGS = ...` in a Makefile overrides the environment; `CFLAGS +=`, `?=` or the implicit rules honor it.

No profile references `FFLAGS`, `FCFLAGS`, `RUSTFLAGS` or `GOFLAGS`. The six tests with Fortran (`npb`,
`laghos`, `remhos`, `dolfyn`, `epoch`, `polyhedron`) get their Fortran flags from hard-coded lines or the
build system. The seven Rust/Go tests (`rav1e`, `rust-mandel`, `rustls`, `build-wasmer`, `go-benchmark`, `etcd`,
`influxdb`) are out of scope for a GCC miner.

The remaining 259 tests don't build C/C++ for the timed program (this includes the seven Rust/Go ones): prebuilt binaries, Python/Java/Node, GPU and game tests, and
system tests that drive installed software. The 21 `build-*` tests (counted in the classes above) compile something and time the *compile*,
so the flags would change what's measured rather than the code being measured. They're excluded too.

| Class | Processor | System | Memory | Other | Total |
|---|---|---|---|---|---|
| Explicit `$CFLAGS`/`$CXXFLAGS` | 28 | 8 | 4 | 5 | 45 |
| Implicit (configure/CMake/Meson) | 80 | 41 | — | 28 | 149 |
| `make`/direct compile, no variable | 58 | 28 | 3 | 22 | 111 |
| Other languages / no build | 61 | 71 | — | 127 | 259 |

## What the backend supports today, and what it would need

The backend accepts only coremark today: one `OutputTemplate`, no options menu, higher-is-better, plus a
per-test output validator. Most of the good candidates need one or more of these:

| Extension | Tests it unlocks | Effort |
|---|---|---|
| Set `CFLAGS_OVERRIDE` alongside `CFLAGS` | the 12 in pattern 2 | trivial; harmless for every other test |
| Lower-is-better scores (`Proportion` LIB): ratio = 1 / time | ~half the candidates (n-queens, c-ray, povray, compression, ...) | small |
| No `ResultsParser` at all: PTS times the whole run script itself | aobench, polybench-c, m-queens, smallpt, encode-*, hmmer, mafft, ... | small: time the run in the backend |
| One fixed choice from an options menu (a `cfm` setting per test) | most media/crypto/HPC tests (scimark2, npb, x264, openssl, ...) | moderate |
| `LineHint`/`LineBeforeHint`/`MultiplyResultBy`, several parsers | scimark2, cpuminer-opt, hpcc, john-the-ripper | moderate |
| A validator per test | every test | per test: easy where the program checks itself, real work otherwise |

The validator is the real per-test cost. Some programs check their own answers: coremark (CRC, confirmed), and from their
upstream documentation `stream` ("Solution Validates"), `npb` ("Verification = SUCCESSFUL") and
`hpl`/`hpcc`/`hpcg` (residual checks); the last four still need confirming in PTS's builds. For
compressors and encoders, a round trip or output hash against a reference build would serve. For chess engines
(`tscp`, `crafty`, `stockfish`), a fixed-depth search's node count works, since a correct build gives a fixed
answer. Each of these still needs confirming against the real output.

## Candidates

### Tier 1: flags reach the compiler cleanly, CPU-bound, no options menu

| Test | Lang | Score | How flags get in | Self-check | Backend needs |
|---|---|---|---|---|---|
| `coremark` | C | HIB | `XCFLAGS="$CFLAGS"` after its `-O2` | CRC | **done** |
| `tscp` | C | HIB | `CFLAGS_OVERRIDE` | node count (to confirm) | `CFLAGS_OVERRIDE` |
| `crafty` | C | HIB | `CFLAGS_OVERRIDE`, plus `CXXFLAGS`/`LDFLAGS` | node count (to confirm) | `CFLAGS_OVERRIDE` |
| `ebizzy` | C | HIB | `CFLAGS_OVERRIDE` | none known | `CFLAGS_OVERRIDE`, validator |
| `n-queens` | C, OpenMP | LIB | `CFLAGS_OVERRIDE` | solution count (to confirm) | `CFLAGS_OVERRIDE`, LIB |
| `himeno` | C | HIB | `cc ... -O3 $CFLAGS` | none known | validator |
| `clomp` | C, OpenMP | HIB | `cc -fopenmp -O3 $CFLAGS` | none known | validator |
| `aircrack-ng` | C | HIB | `CFLAGS="-O3 -fcommon $CFLAGS"` (its `CXXFLAGS` line has a `$CXFLAGS` typo, so C++ flags are dropped) | none known | validator |
| `aobench` | C | LIB, no parser | `cc ao.c -O3 $CFLAGS` | output image hash (to confirm it's deterministic) | LIB, wall-clock timing |
| `smallpt` | C++, OpenMP | LIB, no parser | `c++ -fopenmp -O3 $CXXFLAGS` | none: OpenMP + random sampling makes the image nondeterministic (to confirm) | LIB, timing |
| `m-queens` | C++, OpenMP | LIB, no parser | `CFLAGS_OVERRIDE` (default `-O2 -march=native`) | solution count (to confirm) | all three |
| `polybench-c` | C | LIB, no parser | `CFLAGS_OVERRIDE` | none (timing kernel) | all three, plus one option |
| `fhourstones` | C | HIB | Makefile (pattern 4) | known game value (to confirm) | confirm flags reach it |
| `lulesh`, `amg`, `ffte` | C++/C | HIB | Makefile (pattern 4) | possibly built-in residual/error output (to confirm) | confirm flags reach it |
| `gmpbench` | C | HIB | `cc -O3 $CFLAGS` for the driver; GMP itself builds via `./configure` | none known | validator |

### Tier 2: good benchmarks that need an option fixed

`scimark2` (C, a 6-result suite; pick one kernel or the composite), `npb` (C + Fortran, `CFLAGS_OVERRIDE`; the
option picks the kernel; self-verifying), `stream` (Memory, `CFLAGS_OVERRIDE`; self-validating, but it measures
bandwidth, which flags barely move and erie's bandwidth gate already watches), `compress-7zip` (its built-in
benchmark; it hard-codes `-march=native` *before* ours), `john-the-ripper`, `c-ray` (Makefile; LIB),
`compress-zstd`, `compress-lz4`, `lzbench`, `x264`, `x265`, `svt-vp9`, `dav1d`, `libgav1`, `kvazaar`,
`vpxenc`, `webp`, `openssl`, `botan`, `nettle`, `cryptopp`, `simdjson`, `primesieve`, `povray` (LIB),
`fftw`, `hpl`, `hpcg`, `minife`, `quicksilver`, `luajit`, `stockfish` (Makefile with its own `ARCH`; SPEC's
`706.stockfish_r` already covers it).

### Avoid or deprioritize

- **`quantlib`, `mkl-dnn`**: set `CMAKE_C_FLAGS`/`CFLAGS` to fixed strings, ignoring ours.
- **`onednn`, `mt-dgemm`, `liquid-dsp`, `cpuminer-opt`**: the timed work is mostly a library built separately, or
  hand-vectorized kernels the flags barely touch.
- **`rocksdb`, `speedb`, `nginx`, `iperf`, `netperf`**: system and network tests; I/O dominates.
- **`build-*`**: they time compilation (see above).

## Suggested order

1. **`CFLAGS_OVERRIDE` + LIB + wall-clock timing** in the backend: small changes that together open most of
   tier 1.
2. **`tscp` and `crafty`** next: classic integer workloads, both `CFLAGS_OVERRIDE`. Their fixed-depth node count
   makes a clean validator. They're also a useful contrast to SPEC's `706.stockfish_r`.
3. **`himeno`** and **`n-queens`**: one floating-point stencil and one branchy search, both trivial to build.
4. **`npb`** with a fixed kernel: the one self-verifying test that also exercises Fortran.

Before mining any test, install it (`phoronix-test-suite install pts/<test>`) and build it once through the
backend with a marker flag (e.g. `-DCFM_MARKER`). The compiled-flags audit then shows whether the flags reached
the binary that is actually timed. This settles pattern 4's "probably" for that test.

PTS also ships a `pgo` module (`pts-core/modules/pgo.php`) that builds, trains and rebuilds with
`-fprofile-generate`/`-fprofile-use` through these same flag variables. `cfm`'s backend does its own two-pass
build instead, but the module's existence suggests PTS profiles are generally expected to honor `CFLAGS`.
