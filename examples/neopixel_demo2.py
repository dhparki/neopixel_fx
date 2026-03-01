""" Neopixel effects demo2, DaveP Feb 2026.  As demo1, but uses buttons to fire red and blue pulses.
    Rquires: 
        neopixel data line connected to pin with GPIO number 21 - or change it below.  Also adjust NUM_LEDS to match your strip.
        Neopixel GND and 5V connected as per manufacturer instuctions - long strips may require external power supply.
        Two push-buttons connected between pins with GPIO numbers 16 and 17 and GDN - or change these below.
        neopixel_fx.py and bounce_button.py saved to Pico.
"""

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
