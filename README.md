# Badge Firmware Patch

A one-shot binary patcher that unlocks the hidden `set` command on the BSides
Perth badge firmware, so you can paint the LED slots any colour you like over
the USB serial console, instead of waiting for the bird to decide you've earned it.

This is the patcher that got my badge ID blocked from participating in the challenge
within the first hour of having it!

## What it is

The stock firmware already knows how to do `set <slot> <colour>`. The code is all
there. It's just fenced off. The badge won't accept the command until you've
reached the final phase of the conference game. This script removes the fence.

It's a pure byte patch (no toolchain, no recompile). You feed it the original
`firmware.bin` that you dump off your badge and it writes out a modified image 
you can flash straight back over the onboard CH340.

## How it works

The `set` handler is guarded by two conditional branches in the serial
command parser, found by decompiling the firmware:

1. **Word recognition** (`0x08009184`) — when the parser matches the word `set`,
   it reads game progress via `config_get(22)` and bails with a `BLS` branch
   unless the gauge has reached 4.
2. **Execution** (`0x080093c8`) — even if the word is accepted, the handler for
   the `set` opcode re-checks a phase byte and fails with another `BLS` unless
   phase > 3.

Both gates are the same shape: a comparison followed by a *branch-if-lower-or-same*
that skips the real work. The patch overwrites each `BLS` (2 bytes) with a Thumb
`NOP` (`bf 00`). With the branches gone, both checks simply fall through and the
command runs at any point.

Before writing anything, the script verifies the exact original bytes are present
at each offset. If they don't match (wrong firmware, wrong version, already
patched) it refuses rather than corrupt the image.

## Usage

```sh
python3 patch_set.py firmware.bin firmware_set_unlocked.bin
```

```sh
stm32flash -b 115200 -w firmware_set_unlocked.bin /dev/ttyUSB0
```

Open a serial terminal at **115200 8N1** and try:

```
set 0 r     # slot 0 -> red
```

## The offsets

| File offset | Original | Patched | What it was |
|-------------|----------|---------|-------------|
| `0x91a2`    | `da d9`  | `00 bf` | `bls.n 0x800915a` (gate 1) |
| `0x93d4`    | `94 d9`  | `00 bf` | `bls.n 0x8009300` (gate 2) |

File offsets map to flash by adding the `0x08000000` base.
