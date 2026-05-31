# Option Metadata

Tool option metadata is stored by tool name and then by major version:

```text
option/
  clang/
    manifest.toml
    22/22.1.6.toml
  gcc/
    manifest.toml
    16/16.1.0.toml
  ld/
    manifest.toml
    2/2.46.0.toml
  lld/
    manifest.toml
    22/22.1.6.toml
  msvc/
    manifest.toml
    17/17.0.0.toml
  nvcc/
    manifest.toml
    12/12.5.0.toml
```

Each tool directory owns its manifest, generator, generated TOML files, and
verification command. The common rule is that generated files must be
reconstructible from pinned upstream sources and the pixi-locked environment.

```sh
pixi run verify-clang-options
pixi run verify-gcc-options
pixi run verify-ld-options
pixi run verify-lld-options
pixi run verify-msvc-options
pixi run verify-nvcc-options
pixi run validate-options
```
