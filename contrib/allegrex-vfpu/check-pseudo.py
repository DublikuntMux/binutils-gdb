#!/usr/bin/env python3
"""Check PSP VFPU macro encodings and rejected operands using installed tools."""
import argparse
from pathlib import Path
import struct
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--tool-prefix', default='psp-',
                    help='installed Binutils prefix, optionally including an absolute directory')
args = parser.parse_args()

def run(tool, *arguments):
    tool = args.tool_prefix + tool.removeprefix('psp-')
    return subprocess.run([tool, *map(str, arguments)],
                          capture_output=True, text=True, timeout=15)

def require_ok(result):
    assert result.returncode == 0, result.stderr

with tempfile.TemporaryDirectory(prefix='psp-pseudos-') as directory:
    work = Path(directory)
    obj, binary = work / 'pseudo.o', work / 'pseudo.bin'
    require_ok(run('psp-as', '-march=allegrex', Path(__file__).with_name('pseudo.s'), '-o', obj))
    require_ok(run('psp-objcopy', '-O', 'binary', '-j', '.text', obj, binary))
    data = binary.read_bytes()
    # Interpret only the integer constant construction and mtv instructions.
    # This checks both the full 32-bit lane contents and the scalar targets.
    regs, actual = [0] * 32, []
    for (word,) in struct.iter_unpack('<I', data):
        opcode, rs, rt, imm = word >> 26, word >> 21 & 31, word >> 16 & 31, word & 0xffff
        if word == 0:
            continue
        if opcode == 15:  # lui
            regs[rt] = imm << 16
        elif opcode == 13:  # ori
            regs[rt] = regs[rs] | imm
        elif opcode == 9:  # addiu
            regs[rt] = (regs[rs] + (imm if imm < 0x8000 else imm - 0x10000)) & 0xffffffff
        elif word & 0xffe0ff80 == 0x48e00000:  # mtv
            actual.append((word & 0x7f, regs[rt]))
        else:
            raise AssertionError(f'unexpected macro instruction {word:08x}')
        regs[0] = 0
    expected = [
        (127, 0x4048f5c3), (0, 0x7fc12345), (32, 0x80000000),
        (1, 0), (33, 0x1234), (65, 0xffff8000), (97, 0xffffffff),
        (93, 0x3f800000), (125, 0xc0200000),
        (62, 0x4048f5c3), (63, 0x80000000),
        (63, 0x3f800000), (95, 0x40000000), (127, 0x40400000),
        (125, 0xbf800000), (126, 0xc0000000), (127, 0xc0400000),
        (28, 0x3f800000), (60, 0x40000000), (92, 0x40400000), (124, 0x40800000),
        (124, 0x40800000), (125, 0x40400000), (126, 0x40000000), (127, 0x3f800000),
        (102, 0x00018000), (92, 0xc0003c00), (124, 0x00017bff),
        (30, 0x3c013c00), (31, 0xfbff8000),
    ]
    assert actual == expected, (actual, expected)
    bad = [
        'lvi.s C000,1.0', 'lvi.p S000,[1.0,2.0]',
        'lvi.t C002,[1.0,2.0,3.0]', 'lvi.q R010,[1.0,2.0,3.0,4.0]',
        'lvi.p C000,[1.0]', 'lvi.p C000,[1.0,2.0,3.0]',
        'lvi.p C000,1.0,2.0', 'lvi.p C000,[1.0,2.0',
        'lvi.p C000,[,2.0]', 'lvi.s S000,', 'lvi.s S000,0x100000000',
        'lvi.s S000,-0x80000001', 'lvi.s S000,unknown_symbol',
        'lvhi.s S000,[1.0]', 'lvhi.s S000,[1.0,2.0,3.0]',
        'lvhi.p C000,[1.0,2.0,3.0]', 'lvhi.p S000,[1.0,2.0,3.0,4.0]',
        'lvhi.s S000,[65536.0,0.0]', 'lvhi.s S000,[-65536.0,0.0]',
        'lvhi.s S000,[unknown_symbol,0.0]', 'lvhi.s S000,[[1.0,2.0]]',
    ]
    for instruction in bad:
        source = work / 'invalid.s'
        source.write_text(instruction + '\n')
        result = run('psp-as', '-march=allegrex', source, '-o', obj)
        assert result.returncode > 0, (instruction, result.returncode, result.stderr)
        assert 'Error:' in result.stderr, (instruction, result.stderr)
        assert 'internal' not in result.stderr.lower(), (instruction, result.stderr)
        assert 'assert' not in result.stderr.lower(), (instruction, result.stderr)
    # The half subnormal disassembler must use exponent -14 rather than -15.
    source = work / 'subnormal.s'
    source.write_text('vfim.s S000,0.000000059604644775390625\n')
    require_ok(run('psp-as', '-march=allegrex', source, '-o', obj))
    result = run('psp-objdump', '-d', obj)
    require_ok(result)
    assert '5.96046e-08' in result.stdout, result.stdout
print('PASS VFPU load-immediate macros and invalid operands')
