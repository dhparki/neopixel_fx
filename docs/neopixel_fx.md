# NeopixelFX

neopixel effects library V0.3 for WS2812-compatible NeoPixel on Pi Pico, DaveP 26/2/26
Dave Parkinson, davep@dhparki.com

---

## Table of contents

- [Overview](#overview)
- [Patterns](#patterns)
  - [`BasePattern`](#basepattern)
  - [`FillPattern`](#fillpattern)
  - [`RandomPattern`](#randompattern)
  - [`SpectrumPattern`](#spectrumpattern)
  - [`UserPattern`](#userpattern)
  - [`PulsePattern`](#pulsepattern)
- [Effects (FX)](#effects-fx)
  - [`BaseFX`](#basefx)
  - [`NullFX`](#nullfx)
  - [`RotateFX`](#rotatefx)
  - [`FadeFX`](#fadex)
  - [`SparkleFX`](#sparklefx)
  - [`FlickerFX`](#flickerfx)
  - [`WipeFX`](#wipefx)
  - [`PushFX`](#pushfx)
  - [`PulseFX`](#pulsefx)
- [Controller](#controller)
  - [`NeopixelFX`](#neopixelfx)
- [Example / `main()`](#example--main)

---

## Overview

This module implements a small framework for building and applying colour `Pattern`s and time-based `FX` (effects) to WS2812-compatible NeoPixel LED strips on the Raspberry Pi Pico 2 (MicroPython). It includes fast assembly implementations for copy when running on Pico 1 or 2, and fade when running on Pico 2 (RP2350) only, but can be easily modified to fall back to Python loops for fade on Pico 1 if wanted (see top of neopixel_fx.py for details).

## Patterns

### `BasePattern`

Base class for colour patterns.  Override this if you want to add new patterns.

Key methods:
- `__init__(neofx, num_pix)` — initialize pattern with `num_pix` slots.
- `get_colour(col)` — utility to accept hex string `"#RRGGBB"` or `(r,g,b)` tuple, returns `(r,g,b)` tuple
- `get_colours(cols)` — map list of colours via `get_colour`.

### `FillPattern`

`FillPattern(neofx, colours)`

Fill with a single colour or repeated pattern.

Colours is a list of colours as CSS-style hex strings `"#RRGGBB"` or tuples `(r, g, b)`.  Note that if using an editor like Visual Studio Code, hex strings can be input using a visual colour selector.

### `RandomPattern`

`RandomPattern(neofx, start_colour="#000000", end_colour="#FFFFFF")`

Fill with random colours in the provided range.

`start_colour` / `end_colour` may be hex or tuples; defaults cover full range.

### `SpectrumPattern`

`SpectrumPattern(neofx, colours)`

Fill with a continuous blended spectrum between the supplied colour points.

Colours is a list of colours as hex strings "#RRGGBB" or tuples (r, g, b) which define the end or mid-points of the spectrum - the colours will be blended between these.

### `UserPattern`

`UserPattern(neofx, generator)`

User-provided `generator(i)` returns a colour for LED `i` (hex or tuple). The generator output is clamped to 0–255.

### `PulsePattern`

`PulsePattern(neofx, colours)`

A compact pattern used for pulses (overlayed on base pattern). The pattern length is `len(colours)` and its pixels use `pulse_brightness`.

## Effects (FX)

Effects are time-driven behaviours that modify or transition between patterns. Each effect extends `BaseFX` and implements `_start_fx`, `_stop_fx`, `_on_timer`, and optionally `_on_render`.

### `BaseFX`

Abstract base class for effects. Override this if you want to add new effects.

### `NullFX`

`NullFX(neofx, time=0.0)` — does nothing for `time` seconds; useful as a delay in queues.

### `RotateFX`

`RotateFX(neofx, speed, time=0.0)` — rotates the pattern at `speed` pixels/sec.

### `FadeFX`

`FadeFX(neofx, time)` — fades between `oldpat` and `pat` over `time` seconds. Uses `_fast_fade` (asm on Pico 2) to interpolate quickly.

### `SparkleFX`

`SparkleFX(neofx, speed, time=0.0)` — random sparkle updates; currently requires `RandomPattern`.

### `FlickerFX`

`FlickerFX(neofx, speed)` — randomly reveals the new pattern until fully shown.

### `WipeFX`

`WipeFX(neofx, speed)` — wipe transition at `speed` pixels/sec (direction by sign of speed).

### `PushFX`

`PushFX(neofx, speed)` — new pattern pushes out the old one across the strip.

### `PulseFX`

`PulseFX(neofx, speed, opt=0, opn=0, start=-1, time=0.0)`

Complex pulse effect that moves a `PulsePattern` over the base pattern. Options and operations:

- Operations (`opn`): `OPN_OVER` (0), `OPN_AND` (1), `OPN_OR` (2), `OPN_XOR` (3).
- Options (`opt`): `OPT_NONE` (0), `OPT_LOOP` (1), `OPT_BOUNCE` (2).

## Controller

### `NeopixelFX`

`NeopixelFX(pin, num_leds, brightness = 1.0, pulse_brightness = -1.0, frequency = 50, grb = True)`

Master controller class. Responsibilities:

- Manage RP2040 PIO state machine for WS2812 output (`ws2812` PIO program).
- Maintain current pattern (`current_pat`), active background effects (`active_fx`), and active pulses (`active_pulses`).
- Timer callback `_on_timer` drives FX and pulses and writes output via the PIO state machine.
- Provide public APIs:
  - `show(pattern, fx=None, callback=None)` — display single pattern with optional effect (cancels queues).
        Optional callback(fx) is called when effect finished, with single parameter fx."""
  - `queue(items, callback=None)` - show several effects in sequence, with an optional callback(items) when finished.
        items is a list of tuples [(pat, fx),...].  If pat is None, the current pattern is re-shown with the new effect. 
        If fx is None, the new pattern is shown immediately.
  - `loop(items)` - loop repeatedly through several effects in sequence until a new show() or queue() is called.
        items is a list of tuples [(pat, fx),...].  If pat is None, the current pattern is re-shown with the new effect.  
        If fx is None, the new pattern is shown immediately.
  - `stop_pulses()` — immediately stop all pulses.
  - `clear()` — clear strip and stop all effects/pulses.
  - `cleanup()` — deinit timer, clear, free state machine.

Implementation notes:
- Uses `microPython` inline assembly for `_fast_copy` and `_fast_fade` when running on compatible hardware. The code contains a compile-time branch keyed by `if True: # True for Pico 2 (RP2350)` which selects the Thumb2 optimized fade implementation.
- Colour buffer ordering can be `GRB` or `RGB` via the `grb` parameter (affects channel indices used when computing packed 24-bit pixel values).

## Example / `main()`

The module includes a demo `main()` which builds a `NeopixelFX` instance and presents a small interactive CLI to choose demos (1-9), clear, or quit. The demo shows usage of `FillPattern`, `RandomPattern`, `SpectrumPattern`, `UserPattern`, `PulsePattern`, and several FX types.

## Source

See the original implementation in `neopixel_fx.py` for full details and inline comments (PIO/ASM implementations, demo harness, and all helper internals).

---

AI Generated from `neopixel_fx.py`, somewhat edited by DaveP 28/2/26
