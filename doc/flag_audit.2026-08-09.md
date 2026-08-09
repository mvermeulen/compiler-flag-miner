# SPEC CPU2017 GCC flag audit

Catalog checked: `/home/mev/source/compiler-flag-miner/config/gcc_flag_catalog.seed.json`

- Configs used (GNU-compiler, successfully parsed): 463
- Configs skipped (compiler wasn't gcc/g++/gfortran): 31
- Configs with at least one unresolved `$(VAR)` reference: 0 (best-effort scanner -- see script docstring)
- Fetch failures: 0

## New candidates (flags seen in the wild, not in the catalog)

| Flag | Seen in N configs | Example source |
|---|---|---|
| `-Wl,-plugin-opt` | 1353 | https://www.spec.org/cpu2017/results/res2019q3/cpu2017-20190723-16402.cfg |
| `-fplugin-arg-dragonegg-llvm-option` | 1140 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-fstruct-layout` | 926 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-unroll-threshold` | 570 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-fprofile-instr-generate` | 463 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-mno-avx2` | 463 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-fremap-arrays` | 463 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-fconvert` | 463 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-mllvm` | 463 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-z` | 463 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-fprofile-instr-use` | 463 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-vectorize-memory-aggressively` | 463 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-fplugin` | 463 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-inline-threshold` | 463 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-finline-aggressive` | 451 | https://www.spec.org/cpu2017/results/res2019q3/cpu2017-20190723-16402.cfg |
| `-madx` | 451 | https://www.spec.org/cpu2017/results/res2019q3/cpu2017-20190723-16402.cfg |
| `-inline-threshold:1000` | 451 | https://www.spec.org/cpu2017/results/res2019q3/cpu2017-20190723-16402.cfg |
| `-mavx` | 451 | https://www.spec.org/cpu2017/results/res2019q3/cpu2017-20190723-16402.cfg |
| `-unroll-count` | 451 | https://www.spec.org/cpu2017/results/res2019q3/cpu2017-20190723-16402.cfg |
| `-mavx2` | 451 | https://www.spec.org/cpu2017/results/res2019q3/cpu2017-20190723-16402.cfg |
| `-fgnu89-inline` | 407 | https://www.spec.org/cpu2017/results/res2019q1/cpu2017-20190221-11093.cfg |
| `-funsigned-char` | 407 | https://www.spec.org/cpu2017/results/res2019q1/cpu2017-20190221-11093.cfg |
| `-fdefault-integer-8` | 356 | https://www.spec.org/cpu2017/results/res2019q1/cpu2017-20190221-11093.cfg |
| `-enable-iv-split` | 356 | https://www.spec.org/cpu2017/results/res2019q1/cpu2017-20190221-11093.cfg |
| `-disable-vect-cmp` | 356 | https://www.spec.org/cpu2017/results/res2019q1/cpu2017-20190221-11093.cfg |
| `-merge-constant` | 356 | https://www.spec.org/cpu2017/results/res2019q1/cpu2017-20190221-11093.cfg |
| `-Wl,-enable-iv-split` | 107 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-enable-gvn-hoist` | 107 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-Wl,-merge-constant` | 107 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-Wl,-inline-recursion` | 107 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-Wl,-unroll-threshold` | 107 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-function-specialize` | 107 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-Wl,-function-specialize` | 107 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-flv-function-specialization` | 107 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-Wl,-lsr-in-nested-loop` | 107 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-Wl,-mllvm` | 107 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-enable-vectorize-compares` | 107 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-Wl,-unroll-aggressive` | 107 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-specs` | 107 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-frepack-arrays` | 95 | https://www.spec.org/cpu2017/results/res2019q3/cpu2017-20190723-16402.cfg |
| `-Wl,-enable-vectorize-compares` | 95 | https://www.spec.org/cpu2017/results/res2019q3/cpu2017-20190723-16402.cfg |
| `-enable-vectorize-compares:false` | 95 | https://www.spec.org/cpu2017/results/res2019q3/cpu2017-20190723-16402.cfg |
| `-Wno-return-type` | 56 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-fopenmp` | 56 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-enable-partial-unswitch` | 12 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-fuse-ld` | 12 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-Wl,-x86-use-vzeroupper` | 12 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |
| `-mno-sse4a` | 12 | https://www.spec.org/cpu2017/results/res2018q4/cpu2017-20181126-09837.cfg |

## Already known (catalog coverage confirmed against real usage)

`-march` (463), `-fprofile-generate` (463), `-flto` (463), `-fprofile-use` (463), `-ffast-math` (463), `-Ofast` (463), `-funroll-loops` (463)

## Ignored (language/ABI/linker plumbing, not tuning knobs)

`-m32` (463), `-DSPEC_LINUX` (463), `-D_FILE_OFFSET_BITS` (463), `-DSPEC_CASE_FLAG` (463), `-DSPEC_LP64` (463), `-DSPEC_LINUX_X64` (463), `-O3` (463), `-D__BOOL_DEFINED` (407), `-std` (95), `-DUSE_OPENMP` (56), `-DSPEC_OPENMP` (56), `-lamdlibm` (12)

