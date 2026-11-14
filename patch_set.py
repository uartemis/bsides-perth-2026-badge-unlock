#!/usr/bin/env python3
"""Unlock the badge's `set <slot> <colour>` serial command.

The firmware already implements `set`, but it is gated behind reaching the
final game phase. Two conditional branches reject it before then:

  gate 1 @ 0x08009184 (word recognition):
      movs r0,#22 ; bl config_get ; cmp r0,#3 ; BLS skip   <- only if gauge(0x16) >= 4
  gate 2 @ 0x080093c8 (execution, opcode 'p'):
      ldrb r2,[phase,#0x1f] ; cmp r2,#3 ; BLS fail         <- only if phase byte > 3

Replacing each BLS with a NOP (bf00) makes both checks always fall through,
so `set` works at any time.
"""
import sys

PATCHES = {
    0x91a2: (b"\xda\xd9", b"\x00\xbf"),  # gate 1: bls.n 0x800915a -> nop
    0x93d4: (b"\x94\xd9", b"\x00\xbf"),  # gate 2: bls.n 0x8009300 -> nop
}

src = sys.argv[1] if len(sys.argv) > 1 else "firmware.bin"
dst = sys.argv[2] if len(sys.argv) > 2 else "firmware_set_unlocked.bin"

data = bytearray(open(src, "rb").read())
for off, (old, new) in PATCHES.items():
    if data[off:off + len(old)] != old:
        raise SystemExit(f"offset 0x{off:x}: expected {old.hex()}, found {data[off:off+len(old)].hex()}")
    data[off:off + len(new)] = new
    print(f"patched 0x{off:x}: {old.hex()} -> {new.hex()}")

open(dst, "wb").write(data)
print(f"wrote {dst}")
