# Clang Option Metadata

This directory contains generated Clang driver option metadata.

- `manifest.toml` pins LLVM release tags to immutable commit SHAs.
- `<major>/<version>.toml` contains the option metadata generated for one Clang
  release.
- Versions are grouped by major release, for example
  `option/clang/22/22.1.6.toml`.

## Regeneration

The generator fetches pinned upstream TableGen files from `llvm/llvm-project`,
resolves their includes, runs `llvm-tblgen`, and writes deterministic TOML.
Fetched sources are cached under `.cache/llvm-options`, which is not committed.

```sh
pixi run refresh-clang-options
pixi run generate-clang-options
pixi run verify-clang-options
```

Equivalent direct commands are useful while developing generator changes:

```sh
python3 scripts/update_clang_options.py --refresh-manifest
python3 scripts/update_clang_options.py --generate --clean --tblgen llvm-tblgen
python3 scripts/update_clang_options.py --verify --tblgen llvm-tblgen
```

To regenerate or verify a subset while developing:

```sh
python3 scripts/update_clang_options.py --generate --versions 3.0.0 11.0.0 22.1.6 --tblgen llvm-tblgen
python3 scripts/update_clang_options.py --verify --versions 3.0.0 11.0.0 22.1.6 --tblgen llvm-tblgen
```

## Reproducibility

Generation is expected to be reproducible from:

- this repository revision
- `option/clang/manifest.toml`
- the pinned upstream LLVM commits
- the `pixi.lock` environment, including `llvm-tblgen`

Each generated file records the upstream source path, commit, source SHA-256,
all fetched TableGen source files, and any local compatibility patch applied to
old `OptParser.td` schemas before invoking the current `llvm-tblgen`.

`--verify` regenerates the selected versions into a temporary directory and
byte-compares them with the committed TOML files.
