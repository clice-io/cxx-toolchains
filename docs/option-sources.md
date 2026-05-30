# Option Metadata Source Strategy

This document records the extraction strategy for option metadata by tool.

## Implemented

### Clang

- Source: `llvm/llvm-project` release tags.
- Metadata input: Clang `Options.td` plus included TableGen files.
- Extraction: `llvm-tblgen -dump-json` and `-gen-opt-parser-defs`.
- Verification: regenerate TOML and byte-compare.

### GCC

- Source: `gcc-mirror/gcc` release tags.
- Metadata input: `gcc/**/*.opt`.
- Extraction: parse GCC option records, enum records, raw properties, help text,
  and source locations.
- Verification: regenerate TOML and byte-compare.

### LLD

- Source: `llvm/llvm-project` release tags.
- Metadata input: LLD driver `Options.td` files for ELF, COFF, Mach-O, MinGW,
  and WebAssembly.
- Extraction: `llvm-tblgen -dump-json` and `-gen-opt-parser-defs`.
- Verification: regenerate TOML and byte-compare.

## Planned

### GNU ld

- Source: `binutils-gdb` release tags.
- Primary metadata input: `ld/lexsup.c`, where GNU ld defines its long option
  table and option handling cases.
- Secondary inputs: emulation params and target-specific files under `ld/`.
- Extraction target: long option spelling, short option, argument kind, help
  text, option code, source location, and target/emulation guards where
  recoverable.

### NVCC

- Source: NVIDIA CUDA Toolkit documentation and installed toolkit probes.
- Primary metadata input: versioned CUDA documentation for `nvcc` options.
- Secondary validation: `nvcc --help` from installed CUDA Toolkit packages when
  available.
- Extraction target: option spelling, aliases, argument form, default value,
  phase forwarding, host compiler forwarding, target architecture constraints,
  and version provenance.

### MSVC

- Source: Microsoft versioned documentation and installed Visual Studio Build
  Tools probes.
- Primary metadata input: MSVC `cl.exe` and `link.exe` option reference pages.
- Secondary validation: `cl /?` and `link /?` from installed toolchains when
  available.
- Extraction target: spelling, argument form, category, default behavior,
  compiler/linker phase, environment requirements, and version provenance.

## Rule

Generated option metadata must always have:

- a manifest with immutable upstream source identity
- a generator or extractor committed in this repository
- generated TOML grouped by tool and major version
- a verification mode that regenerates and byte-compares output
- source provenance in each generated file
