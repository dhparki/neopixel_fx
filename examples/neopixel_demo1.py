""" Neopixel effects demo1, DaveP Feb 2026.  Red green and blue pulses over a flickering blue background.
    Rquires: 
        neopixel data line connected to pin with GPIO number 21 - or change it below.  Also adjust NUM_LEDS to match your strip.
        Neopixel GND and 5V connected as per manufacturer instuctions - long strips may require external power supply.
        neopixel_fx.py saved to Pico.
"""

from neopixel_fx import NeopixelFX, RandomPattern, PulsePattern, SparkleFX, PulseFX
from bounce_button import BounceButton

from utime import sleep

def main():
    PIN = 21        # Nopixel data pin GPIO number - change as required
    NUM_LEDS = 60   # LEDs in the strip - change as required
    
    npfx = NeopixelFX(pin=PIN, num_leds=NUM_LEDS, brightness=0.1, pulse_brightness=1.0)

    npfx.show(RandomPattern(npfx, "#000010", "#101020"), SparkleFX(npfx, 50))   # dim blue sparkle
    npfx.show(PulsePattern(npfx, ["#000010", "#000040", "#0000FF"]), PulseFX(npfx, 100, PulseFX.OPT_LOOP, PulseFX.OPN_OR))  # blue pulse forwards loop
    npfx.show(PulsePattern(npfx, ["#FF0000", "#400000", "#100000"]), PulseFX(npfx, -100, PulseFX.OPT_LOOP, PulseFX.OPN_OR)) # red pulse backwards loop
    npfx.show(PulsePattern(npfx, ["#001000", "#004000", "#00FF00"]), PulseFX(npfx, 100, PulseFX.OPT_BOUNCE, PulseFX.OPN_OR)) # green pulse bounce

    try:
        print('Running demo, ^C to quit')
        while True:
            sleep(3600)

    except KeyboardInterrupt:
        print('KeyboardInterrupt - quitting')

    finally:
        npfx.cleanup()

if __name__== "__main__":
    main()
