""" Neopixel effects test, DaveP Feb 2026 
    Rquires: 
        neopixel data line connected to pin with GPIO number 21 - or change it below.  Also adjust NUM_LEDS to match your strip.
        Neopixel GND and 5V connected as per manufacturer instuctions - long strips may require external power supply.
        Optinally a second strip connected to pin with GPIO number 22 - or change it below.  Also adjust NUM_LEDS2 to match your strip.
        neopixel_fx.py and cpu_usage.py saved to Pico.
"""

"""
Use two characer input to select pattern and effect.  For example "3d" means random sparkle.

1 - fill single
2 - fill three
3 - random
4 - random blue
5 - spectrum
6 - user single

a - null
b - rotate
c - fade
d - sparkle
e - flicker
f - wipe
g - push

Use single character input for the following:

x - fill queue
y - spectrum queue
z - spectrum loop

k - blue pulse loop
l - red pulse loop
m - green pulse bounce

s - switch strips

n - stop pulses
c - clear
q - quit
"""

from neopixel_fx import (NeopixelFX, 
                        FillPattern, SpectrumPattern, RandomPattern, UserPattern, PulsePattern, 
                        FadeFX, RotateFX, SparkleFX, FlickerFX, WipeFX, PushFX, PulseFX)  

from math import sin, cos, pi
from random import randint
from micropython import mem_info

from cpu_usage import CPUUsage
from utime import ticks_ms, ticks_diff

def main():
    
    PIN = 21    # First strip data pin GPIO number - change as required
    NUM_LEDS = 60

    PIN2 = 22   # Optional second strip data pin GPIO number.
    NUM_LEDS2 = 24

    BRIGHTNESS = 0.1
    PULSE_BRIGHTNESS = 1
    FREQUENCY = 50
    GRB = True

    SHOW_USAGE = True   # True to show (very) approxiate CPU usage for each effect.
    IDLE_TIMER = 0.2

    randCol = lambda max : (randint(0, max),randint(0, max),randint(0, max))

    mnp1 = NeopixelFX(PIN, NUM_LEDS, BRIGHTNESS, PULSE_BRIGHTNESS, FREQUENCY, GRB)
    print(mnp1)
    mnp1.clear()

    mnp2 = NeopixelFX(PIN2, NUM_LEDS2, BRIGHTNESS, PULSE_BRIGHTNESS, FREQUENCY, GRB)
    print(mnp2)
    mnp2.clear()

    if SHOW_USAGE:
        cpu_usage = CPUUsage(IDLE_TIMER)

    mnp = mnp1  # Default to first strip

    try:
        while True:
            switch = input('1a-6g effect, x-z sequence, k-m pulse, s=switch, n=stop, c=clear or q=quit? ')

            if switch == 'q':
                raise KeyboardInterrupt
            
            elif switch == 'c':   
                mnp.clear()

            elif switch == 's':   
                mnp = mnp2 if mnp == mnp1 else mnp1
                print('Strip =', mnp)

            elif switch == 'x':   
                mnp.queue( [
                    (FillPattern(mnp, [(255, 0, 0)]), ),
                    (FillPattern(mnp, [(0, 255, 0)]), FadeFX(mnp, 2)),
                    (FillPattern(mnp, [(0, 0, 255)]), FadeFX(mnp, 2)),
                    (FillPattern(mnp, [(255, 0, 0)]), FadeFX(mnp, 2))
                ] , lambda items: print('***Queue finished***') )

            elif switch == 'y':   
                mnp.queue( [
                    (SpectrumPattern(mnp, [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 0)]), ), 
                    (SpectrumPattern(mnp, [(0, 255, 0), (0, 0, 255), (255, 0, 0), (0, 255, 0)]), FadeFX(mnp, 2)),
                    (SpectrumPattern(mnp, [(0, 0, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255)]), FadeFX(mnp, 2)),
                    (SpectrumPattern(mnp, [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 0)]), FadeFX(mnp, 2))
                ] , lambda items: print('***Queue finished***') )  

            elif switch == 'z':   
                mnp.loop( [
                    (SpectrumPattern(mnp, [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 0)]), ),
                    (SpectrumPattern(mnp, [(0, 255, 0), (0, 0, 255), (255, 0, 0), (0, 255, 0)]), FadeFX(mnp, 2)),
                    (SpectrumPattern(mnp, [(0, 0, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255)]), FadeFX(mnp, 2)),
                    (SpectrumPattern(mnp, [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 0)]), FadeFX(mnp, 2))
                ] )

            elif switch == 'k': 
                pat = PulsePattern(mnp, [(0, 0, 255>>4), (0, 0, 255>>2), (0, 0, 255)])
                fx = PulseFX(mnp, 100, PulseFX.OPT_LOOP, PulseFX.OPN_OR)
                print(f'pattern = {pat}, fx = {fx}')       
                mnp.show(pat, fx)

            elif switch == 'l':
                pat = PulsePattern(mnp, [(255, 0, 0), (255>>2, 0, 0), (255>>4, 0, 0)])
                fx = PulseFX(mnp, -100, PulseFX.OPT_LOOP, PulseFX.OPN_OR)
                print(f'pattern = {pat}, fx = {fx}')       
                mnp.show(pat, fx)

            elif switch == 'm': 
                pat = PulsePattern(mnp, [(0, 255>>4, 0), (0, 255>>2, 0), (0, 255, 0)])
                fx = PulseFX(mnp, 100, PulseFX.OPT_BOUNCE, PulseFX.OPN_OR)
                print(f'pattern = {pat}, fx = {fx}')       
                mnp.show(pat, fx)

            elif switch == 'n': 
                mnp.stop_pulses()

            else:
                if len(switch) != 2:
                    print('???')
                    continue

                if switch[0] == '1':
                    pat = FillPattern(mnp, [randCol(255)])   

                elif switch[0] == '2':
                    pat = FillPattern(mnp, [randCol(255), randCol(255), randCol(255), (0, 0, 0)])  

                elif switch[0] == '3':
                    pat = RandomPattern(mnp)  

                elif switch[0] == '4':
                    pat = RandomPattern(mnp, "#000010", "#101020")

                elif switch[0] == '5':
                    pat = SpectrumPattern(mnp, [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 0)])  

                elif switch[0] == '6':
                    pat = UserPattern(mnp, lambda i : (255*(sin(2*pi*i/NUM_LEDS)**2), 0, 255*(cos(2*pi*i/NUM_LEDS)**2)))  

                else:
                    print('???')
                    continue

                if switch[1] == 'a':
                    fx = None
                    #fx = NullFX(mnp, 5)

                elif switch[1] == 'b':
                    fx = RotateFX(mnp, 20)

                elif switch[1] == 'c':
                    fx = FadeFX(mnp, 2)

                elif switch[1] == 'd':
                    fx = SparkleFX(mnp, 50)

                elif switch[1] == 'e':
                    fx = FlickerFX(mnp, 50)

                elif switch[1] == 'f':
                    fx = WipeFX(mnp, 50)

                elif switch[1] == 'g':
                    fx = PushFX(mnp, -50)

                else:
                    print('???')
                    continue

                print(f'pattern = {pat}, fx = {fx}')   
                try:    
                    mnp.show(pat, fx, lambda fx: print('Had callback ', fx))
                except Exception as ex:
                    print('ERROR:', ex)     

            if SHOW_USAGE:
                print(f'CPU usage = {cpu_usage.usage()}%')  

    except KeyboardInterrupt:
        print('KeyboardInterrupt - quitting')

    finally:
        mnp1.cleanup()
        mnp2.cleanup()

if __name__== "__main__":
    main()
