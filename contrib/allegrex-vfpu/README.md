# Allegrex PSP/VFPU review branch

This branch is based on upstream `binutils-2_47`, commit
`6ce87bbc521cf46eaee9a1f7ef61cee2cdfb3e32`. It contains the complete PSP/VFPU
port used by the project-local toolchain, including the repaired `lvi`/`lvhi`
pseudoinstructions. It is a review branch, not a patch already submitted upstream.

## Provenance and scope

The PSP/VFPU implementation is ported from pspdev/binutils-gdb commit
`a8b53fe2b5825fa86337623c743d21a19aeb0daf` (`allegrex-v2.44`). Imported copyright
and license notices are retained. The port adapts the current assembler operand
initialization and `bool` API, and adds PSP target configuration/linker emulation.

Upstream 2.47 already recognizes scalar Allegrex. This branch adds VFPU operand
parsing, encoding, disassembly and PSP linking. It retains upstream's standard
Allegrex ELF machine flag `0x00840000` and GS464 support, rather than carrying the
older PSP fork's reassignment of the GS464 value.

Additional fixes made during validation:

- Parse `vfim.s` and `lvhi` values using GAS's IEEE binary16 parser, preserving
  subnormals and rounding while diagnosing overflow.
- Repair `lvi.s/p/t/q` and `lvhi.s/p` operand parsing and macro expansion, using
  consistent macro IDs and valid row/column lane offsets.
- Accept decimal binary32 values and explicit hexadecimal raw bits for `lvi`.
  `lvhi` packs two binary16 values per scalar, low half first.
- Diagnose malformed operands without internal assembler aborts.
- Correct half-subnormal disassembly.

The complete imported port is larger than the pseudoinstruction fixes alone.
Upstream review may require splitting it into smaller changes and converting the
standalone regression checks into the GAS testsuite before mailing a patch.

## Validation

The source changes match the already-built PSP project toolchain. That toolchain
passed normal and LTO GCC 17 runtime smoke tests in PPSSPP, including VFPU arithmetic
and auto-vectorized loops. A C++20 PSP game built successfully and completed its
35-view software-renderer tour. These are execution checks, not performance claims.

Run the focused standalone regression check with Python 3.9+ and installed tools:

```sh
python3 contrib/allegrex-vfpu/check-pseudo.py --tool-prefix /path/to/install/bin/psp-
```

The default prefix is `psp-` on PATH. The check verifies complete lane contents and
scalar register encodings for all six macro forms, rejects 21 malformed operands,
and checks half-subnormal disassembly. It uses temporary files and has no PSP SDK
or game source dependency.

For a standalone Binutils build (from an out-of-tree directory):

```sh
/path/to/binutils-gdb/configure --target=psp --prefix=/path/to/install \
  --disable-gdb --disable-gdbserver --disable-sim --disable-gprofng \
  --disable-nls --disable-werror --enable-plugins
make -j6 all-binutils all-gas all-ld
make install-binutils install-gas install-ld
```
