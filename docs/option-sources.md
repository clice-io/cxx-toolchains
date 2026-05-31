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

### GNU ld

- Source: `binutils-gdb` release tags.
- Metadata input: `ld/lexsup.c`, where GNU ld defines its option table.
- Extraction: parse the option table for long spellings, short spellings,
  argument kind, help text, option code, metavar, dash kind, and source
  locations.
- Verification: regenerate TOML and byte-compare.

### NVCC

- Source: NVIDIA CUDA Toolkit documentation archive.
- Metadata input: versioned `cuda-compiler-driver-nvcc/index.html` pages.
- Extraction: parse older table-based pages and newer section/TOC pages for
  option spellings, aliases, argument text, section anchors, help text, source
  URL, and source SHA-256.
- Verification: regenerate TOML and byte-compare.

### MSVC

- Source: `MicrosoftDocs/cpp-docs` plus Microsoft Learn moniker metadata.
- Metadata input: public markdown pages for compiler options listed
  alphabetically and linker options.
- Extraction: parse markdown option tables for `cl` and `link` spellings,
  syntax, argument shape, purpose text, detail-page links, source locations, and
  source SHA-256.
- Version granularity: Visual Studio major monikers such as `msvc-140` through
  `msvc-180`, normalized to `14.0.0` through `18.0.0`.
- Verification: regenerate TOML and byte-compare.

### mold

- Source: `rui314/mold` release tags.
- Metadata input: versioned manpage sources, using `docs/mold.md` for newer
  releases and `docs/mold.1` for older releases.
- Extraction: parse markdown, man, and mdoc option lists for option groups,
  spellings, syntax forms, argument shape, descriptions, source locations, and
  source SHA-256.
- Verification: regenerate TOML and byte-compare.

## Planned

### MSVC Installed Probes

- Source: installed Visual Studio Build Tools and Windows SDK toolchains.
- Metadata input: `cl /?`, `link /?`, and environment setup scripts from each
  installed toolset.
- Extraction target: minor toolset version deltas, target-specific options,
  localized help differences, default values, and options absent from public
  docs.

## Rule

Generated option metadata must always have:

- a manifest with immutable upstream source identity
- a generator or extractor committed in this repository
- generated TOML grouped by tool and major version
- a verification mode that regenerates and byte-compares output
- source provenance in each generated file
