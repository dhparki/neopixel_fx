# NeoPixelFX

Asynchronous effects library for WS2812-compatible NeoPixel on Pi Pico - MicroPython with some inline assembler

## Description

This module implements a small framework for building and applying colour `Pattern`s and time-based `FX` (effects) to WS2812-compatible NeoPixel LED strips on the Raspberry Pi Pico 2 (MicroPython). Operation is asynchronous, so effects
can be kept running in background.  Patterns supported are Fill, Random, Spectrum, User and Pulse, the last being used for "pulses" superimposed on a background (think light-sabre).  Effects supported are Null (timer), Rotate, Fade, Sparkle, Flicker, Wipe, Push and Pulse.  It includes fast assembly implementations for copy when running on Pico 1 or 2, and fade when running on Pico 2 (RP2350) only, but can be easily modified to run on Pico 1 if wanted.

## Video

https://www.dhparki.com/video/NeoPixelFX.mp4

### Installing

For how to connect a NeoPixel strip or ring to Pi Pico 2, see the manufacturers instructions.  Note that longer strips (over about 24 LEDs) will probably require an exernal power supply as they can take quite a bit of current (typically up to 50mA peak, 20mA typical per LED - but again, see the manufacturer's data-sheet).

To use the library, you need to install neopixel_fx.py on your Pico - e.g. using "SaveAs To Raspberry Pi Pico" from Thonny, or "Upload file to Pico" from Visual Studio Code.  Some of the demos require additional files to be installed on the Pico such as bounce_button.py and cpu_usage.py - see the examples directory for details.

### Executing program

The file neopixel_fx.py contains a demo which you can run on the Pico from an editor such as Thonny or Visual Studio Code.  The demo assumes a 60 pixel GBR NeoPixel with its data line connected to GPIO 21 on the Pico, but you can edit the code to change this.  Press 1-8 to show various patterns and effects, 9 to run a continuous demo in a loop, c to clear the strip or q to quit.

### Limitations

The code uses Thumb2 assember for fast fade, so requires Pico 2 (RP2350).  To run on Pico 1 (RP2040), find the line 
    `if True:    # True for Pico 2 (RP2350)`
and change it to `if False:`

The current code is for RGB or GRB WS2812-compatible strips only.  Other formats such as RGBA are not currently supported.

## Example (examples/neopixel_demo2.py)

The following code uses buttons to fire red and blue pulses over a flickering blue background.  It requires:
    Neopixel data line connected to pin with GPIO number 21 - or change it below.  Also adjust NUM_LEDS to match your strip.
    Neopixel GND and 5V connected as per manufacturer instuctions - long strips may require external power supply.
    Two push-buttons connected between pins with GPIO numbers 16 and 17 and GDN - or change these below.
    neopixel_fx.py and bounce_button.py saved to Pico.

```python
from neopixel_fx import NeopixelFX, RandomPattern, PulsePattern, SparkleFX, PulseFX
from bounce_button import BounceButton

from utime import sleep

def main():
    NEO_PIN = 21    # Nopixel data pin GPIO number - change as required
    NUM_LEDS = 60   # LEDs in the strip - change as required
    BTN1_PIN = 16   # Button 1 pin GPIO number - change as required
    BTN2_PIN = 17   # Button 2 pin GPIO number - change as required

    npfx = NeopixelFX(pin=NEO_PIN, num_leds=NUM_LEDS, brightness=0.1, pulse_brightness=1.0)
    btn1 = BounceButton(pin=BTN1_PIN)
    btn2 = BounceButton(pin=BTN2_PIN)

    npfx.show(RandomPattern(npfx, "#000010", "#101020"), SparkleFX(npfx, 50))   # dim blue sparkle

    def btn1_down(button):
        npfx.show(PulsePattern(npfx, ["#000010", "#000040", "#0000FF"]), PulseFX(npfx, 100))   # blue pulse forwards
    
    def btn2_down(button):
        npfx.show(PulsePattern(npfx, ["#FF0000", "#400000", "#100000"]), PulseFX(npfx, -100))  # red pulse backwards
        
    btn1.on_down(btn1_down)
    btn2.on_down(btn2_down)

    try:
        print('Use buttons to fire pulses, ^C to quit')
        while True:
            sleep(3600)

    except KeyboardInterrupt:
        print('KeyboardInterrupt - quitting')

    finally:
        npfx.cleanup()
        btn1.cleanup()
        btn2.cleanup()

if __name__== "__main__":
    main()
```

## Documentation
    See docs/neopixel_fx.md (AI-generated, sorry!) - or just look at the docstrings in neopixel_fx.py.

## Authors

Dave Parkinson, davep@dhparki.com

## Version History

* 0.3
    * First public release on GitHub

## License

This project is licensed under the MIT License - see the LICENSE.md file for details
