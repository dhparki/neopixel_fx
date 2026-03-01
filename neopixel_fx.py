""" neopixel effects library V0.3 for WS2812-compatible NeoPixel on Pi Pico 2, DaveP 26/2/26
    Dave Parkinson, davep@dhparki.com
    NB - This version uses Thumb2 assember for fast fade, so requires Pico 2 (RP2350).
    To run on Pico 1 (RP2040), find the line "if True:    # True for Pico 2 (RP2350)"
    and change it to "if False:"
    (It should be possible to automate this, but I can't find a way - sorry!)
"""

from array import array
from utime import ticks_ms, ticks_diff
from machine import Pin, Timer
from random import randint

import micropython
import rp2

# Base class for colour patterns
class BasePattern():
    def __init__(self, neofx, num_pix):
        self.neofx = neofx
        self.num_pix = num_pix
        self.pixels = array("I", [0 for _ in range(num_pix)])

    # _refresh needs override
    def _refresh(self):
        raise NotImplementedError("Pattern needs _refresh method!")
    
    # utility function - handle a colour as hex string or tuple
    def get_colour(self, col):
        if isinstance(col, str) and col[0] == '#':
            val = int(col[1:7], 16)
            return (val >> 16, (val >> 8) & 0xff, val & 0xff)
        elif isinstance(col, tuple) and len(col) == 3:
            return col
        else:
            raise ValueError('Requires colour as hex string "#RRGGBB" or tuple (r, g, b)') 

    # utility function - handle a list of colours as hex strings or tuples
    def get_colours(self, cols):
        return [self.get_colour(col) for col in cols]

# Fill with single colour or repeated pattern
class FillPattern(BasePattern):
    """FillPattern(neofx, colours) - colours is a list of colours as hex strings "#RRGGBB" or tuples (r, g, b)"""
    def __init__(self, neofx, colours):
        super().__init__(neofx, neofx.num_leds)
        self.colours = self.get_colours(colours)
        self._refresh()
    
    # String value
    def __str__(self):
        return f'FillPattern(colours = {self.colours})' 

    def _refresh(self):
        j = 0
        for i in range(self.num_pix):
            colour = self.colours[j]
            self.pixels[i] = (colour[self.neofx.cind1]*self.neofx.brightness//255 << 16) + (colour[self.neofx.cind2]*self.neofx.brightness//255 << 8) + \
                colour[self.neofx.cind3]*self.neofx.brightness//255
            j = (j+1) % len(self.colours)

# Fill with random colours
class RandomPattern(BasePattern):
    """RandomPattern(neofx, start_colour="#000000", end_colour="#FFFFFF") - start_colour and end_colour are optional colours as hex strings "#RRGGBB" 
    or tuples (r, g, b) which define the range for the random colours - defaults #00000 to #FFFFFF"""
    def __init__(self, neofx, start_colour="#000000", end_colour="#FFFFFF"):
        super().__init__(neofx, neofx.num_leds)
        self.start_colour = self.get_colour(start_colour)
        self.end_colour = self.get_colour(end_colour)
        self._refresh()

    # String value
    def __str__(self):
        return f'RandomPat(start_colour = {self.start_colour}, end_colour = {self.end_colour})' 

    def _refresh(self):
        randel = lambda start,end : randint(start, end) if end >= start else randint(end, start)

        for i in range(self.neofx.num_leds):
            colour = [randel(self.start_colour[i], self.end_colour[i]) for i in range(3)]
            self.pixels[i] = (colour[self.neofx.cind1]*self.neofx.brightness//255 << 16) + (colour[self.neofx.cind2]*self.neofx.brightness//255 << 8) + \
                colour[self.neofx.cind3]*self.neofx.brightness//255

# Fill with a continuous spectrum of colours
class SpectrumPattern(BasePattern):
    """SpectrumPattern(neofx, colours) - colours is a list of colours as hex strings "#RRGGBB" or tuples (r, g, b) which define the end or mid-points of the spectrum - the colours will be blended between these."""
    def __init__(self, neofx, colours):
        super().__init__(neofx, neofx.num_leds)
        self.colours = self.get_colours(colours)
        self._refresh()
    
    # String value
    def __str__(self):
        return f'SpectrumPatern(colours = {self.colours})' 

    def _refresh(self):
        nleds = self.neofx.num_leds
        npoints = len(self.colours)
        for i in range(nleds):
            p = i * (npoints-1) / (nleds-1)
            start = int(p)
            offset = p - start
            #print(f'i = {i}, p = {p}, start = {start}, offset = {offset}')
            ledcol = [0,0,0]
            for j in range(3): 
                ledcol[j] = self.colours[start][j]
                if start < npoints-1:
                    ledcol[j] += int(offset * (self.colours[start+1][j] - self.colours[start][j]))
            #print('ledcol = ',ledcol)
            self.pixels[i] = (ledcol[self.neofx.cind1]*self.neofx.brightness//255 << 16) + (ledcol[self.neofx.cind2]*self.neofx.brightness//255 << 8) + \
                ledcol[self.neofx.cind3]*self.neofx.brightness//255          

# Fill with a user-defined pattern
class UserPattern(BasePattern):
    """UserPattern(neofx, generator) - generator is a function which takes a led number and returns a colour as a hex string "#RRGGBB" or tuple (r, g, b)"""
    def __init__(self, neofx, generator):
        super().__init__(neofx, neofx.num_leds)
        self.generator = generator
        self._refresh()
    
    # String value
    def __str__(self):
        return f'UserPattern(generator = {self.generator.__name__})' 

    def _refresh(self):
        clamp = lambda n, minn, maxn: max(min(maxn, n), minn)   # Ensure range minn to maxn
        for i in range(self.num_pix):
            colour = self.generator(i)
            colour2 = [clamp(int(col), 0, 255) for col in colour]
            self.pixels[i] = (colour2[self.neofx.cind1]*self.neofx.brightness//255 << 16) + (colour2[self.neofx.cind2]*self.neofx.brightness//255 << 8) + \
                colour2[self.neofx.cind3]*self.neofx.brightness//255

# A single pulse to overlay
class PulsePattern(BasePattern):
    """PulsePattern(neofx, colours) - colours is a list of colours as hex strings "#RRGGBB" or tuples (r, g, b) which define the pattern to pulse over the base pattern"""

    def __init__(self, neofx, colours):
        self.colours = self.get_colours(colours)
        super().__init__(neofx, len(self.colours))
        self._refresh()
    
    # String value
    def __str__(self):
        return f'PulsePattern(colours = {self.colours})'

    def _refresh(self):
        for i in range(self.num_pix):
            colour = self.colours[i]
            self.pixels[i] = (colour[self.neofx.cind1]*self.neofx.pulse_brightness//255 << 16) + (colour[self.neofx.cind2]*self.neofx.pulse_brightness//255 << 8) + \
                colour[self.neofx.cind3]*self.neofx.pulse_brightness//255

# Base class for colour effects
class BaseFX():
    def __init__(self, neofx):
        self.neofx = neofx

    # These functions need override
    def _start_fx(self, pat, oldpat):
        raise NotImplementedError("FX needs start method!")

    def _stop_fx(self):
        raise NotImplementedError("FX needs stop method!")

    def _on_timer(self, ticks):
        raise NotImplementedError("FX needs _on_timer method!")
    
    def _on_render(self, ticks):
        raise NotImplementedError("FX needs _on_render method!")

# Do nothing effect - useful for the timer
class NullFX(BaseFX):
    """NullFX(neofx, time=0.0) - does nothing for the specified time in s - useful in a queue or loop"""
    def __init__(self, neofx, time=0.0):
        super().__init__(neofx)
        self.time_ms = int(time * 1000)

    # String value
    def __str__(self):
        return f'NullFX(time = {self.time_ms} ms)' 
    
    def _start_fx(self, pat, oldpat):
        #print('NullF/X init pat =', pat)
        self.start_ticks = ticks_ms()

        self.neofx._fast_copy(self.neofx.pixels, pat.pixels, self.neofx.num_leds)
        self.neofx._set_output(self.neofx.pixels)

        self.neofx.active_fx.append(self)
        return True

    def _stop_fx(self):
        self.neofx.active_fx.remove(self)

    def _on_timer(self, ticks):
        #print('NullFX _on_timer', ticks)
        elapsed = ticks_diff(ticks, self.start_ticks)
        if elapsed >= self.time_ms:
            self.neofx._fx_ended(self)        
        return False

# Rotate single pattern effect
class RotateFX(BaseFX):
    """RotateFX(neofx, speed, time=0.0) - rotates the pattern at the specified speed in pixels/s (positive for one direction, negative for the other) 
    for the specified time in s (0 means forever)"""
    def __init__(self, neofx, speed, time=0.0):
        super().__init__(neofx)
        self.incled = -1 if speed < 0 else 1 
        self.delay_ms = int(1000 / abs(speed))
        self.time_ms = int(time * 1000)

    # String value
    def __str__(self):
        return f'RotateFX(delay = {self.delay_ms} ms, direction = {self.incled}, time = {self.time_ms} ms)' 
    
    def _start_fx(self, pat, oldpat):
        #print('RotateFx init pat =', pat)
        self.pattern = pat
        self.start_ticks = ticks_ms()
        self.startled = 0
        self.neofx.active_fx.append(self)
        return True

    def _stop_fx(self):
        self.neofx.active_fx.remove(self)

    def _on_timer(self, ticks):
        #print('RotateFx _on_timer', ticks)

        elapsed = ticks_diff(ticks, self.start_ticks)
        if self.time_ms and (elapsed >= self.time_ms):
            self.neofx._fx_ended(self)
            return False

        newstart = ((elapsed * self.incled) // self.delay_ms) % self.neofx.num_leds 

        if newstart != self.startled:
            self.startled = newstart
            for i in range(0, self.startled):
                self.neofx.pixels[i] = self.pattern.pixels[self.neofx.num_leds - self.startled + i]
                        
            for i in range(self.startled, self.neofx.num_leds):
                self.neofx.pixels[i] = self.pattern.pixels[i - self.startled]
            
            return True
        else:
            return False

# Fade old to new pattern effect
class FadeFX(BaseFX):
    """FadeFX(neofx, time=0.0) - fades from the old pattern to the new pattern over the specified time in s"""
    def __init__(self, neofx, time):
        super().__init__(neofx)
        self.time_ms = int(1000 * time)

    # String value
    def __str__(self):
        return f'FadeFX(time = {self.time_ms} ms)' 
    
    def _start_fx(self, pat, oldpat):
        #print('FadeFx init pat =', pat)
        self.endpix = pat.pixels
        self.startpix = oldpat.pixels
        self.start_ticks = ticks_ms()
        self.neofx.active_fx.append(self)
        return True

    def _stop_fx(self):
        self.neofx.active_fx.remove(self)

    def _on_timer(self, ticks):        
        #print('FadeFx _on_timer', ticks) 
        elapsed = ticks_diff(ticks, self.start_ticks)
        if elapsed > self.time_ms:
            #We need to ensure we have the end pattern - so copy it and return dirty=True
            self.neofx._fast_copy(self.neofx.pixels, self.endpix, self.neofx.num_leds) 
            self.neofx._fx_ended(self)
            return True

        return self.neofx._fast_fade(self.neofx.pixels, self.startpix, self.endpix, self.neofx.num_leds, elapsed, self.time_ms)

# Random sparkle effect
class SparkleFX(BaseFX):
    """SparkleFX(neofx, speed, time=0.0)  - randomly changes the pattern at the specified speed in pixels/s for the specified time in s (0 means forever).
       Note that this currently only works with random patterns."""
    def __init__(self, neofx, speed, time=0.0):
        super().__init__(neofx)
        self.delay_ms = int(1000 / abs(speed))
        self.time_ms = int(time * 1000)

    # String value
    def __str__(self):
        return f'SparkleFX(delay = {self.delay_ms} ms), time = {self.time_ms} ms' 
    
    def _start_fx(self, pat, oldpat):
        #print('SparkleFx init pat =', pat)
        if not isinstance(pat, RandomPattern):
            raise TypeError("Sparkle currently requires random pattern")
        
        self.pattern = pat
        self.lastticks = self.start_ticks = ticks_ms()
        self.neofx.active_fx.append(self)
        return True

    def _stop_fx(self):
        self.neofx.active_fx.remove(self)

    def _on_timer(self, ticks):
        #print('SparkleFx _on_timer', ticks)
        elapsed = ticks_diff(ticks, self.start_ticks)
        if self.time_ms and (elapsed >= self.time_ms):
            self.neofx._fx_ended(self)
            return False

        if ticks_diff(ticks, self.lastticks) > self.delay_ms:
            self.lastticks = ticks
            self.pattern._refresh()
            for i in range(self.neofx.num_leds):
                self.neofx.pixels[i] = self.pattern.pixels[i]
            return True
        else:
            return False

# Flicker transition effect
class FlickerFX(BaseFX):
    """FlickerFX(neofx, speed) - randomly changes the pattern at the specified speed in pixels/s until the new pattern is fully revealed."""
    def __init__(self, neofx, speed):
        super().__init__(neofx)
        self.delay_ms = int(1000 / abs(speed))

    # String value
    def __str__(self):
        return f'FlickerFX(delay = {self.delay_ms} ms)' 

    def _start_fx(self, pat, oldpat):
        self.patpix = pat.pixels
        self.lastticks = ticks_ms()
        self.randsel = list(range(len(pat.pixels)))
        self.neofx.active_fx.append(self)
        return True

    def _stop_fx(self):
        self.neofx.active_fx.remove(self)

    def _on_timer(self, ticks):
        #print('FlickerFx _on_timer', ticks)
        if ticks_diff(ticks, self.lastticks) > self.delay_ms:
            if not self.randsel:
                self.neofx._fx_ended(self)
                return False

            i = self.randsel.pop(randint(0, len(self.randsel)-1))
            self.neofx.pixels[i] = self.patpix[i]
            self.lastticks = ticks
            return True
        else:
            return False

# Wipe transition effect
class WipeFX(BaseFX):
    """WipeFX(neofx, speed) - perform a wipe from the old pattern to the new pattern at the specified speed in pixels/s 
    (positive for one direction, negative for the other)."""
    def __init__(self, neofx, speed):
        super().__init__(neofx)
        self.incled = -1 if speed < 0 else 1 
        self.delay_ms = int(1000 / abs(speed))

    # String value
    def __str__(self):
        return f'WiperFX(delay = {self.delay_ms} ms)' 

    def _start_fx(self, pat, oldpat):
        self.newpix = pat.pixels
        self.endled = 0 if self.incled == 1 else self.neofx.num_leds-1
        self.startled = self.endled
        self.start_ticks = ticks_ms()
        self.neofx.active_fx.append(self)
        return True

    def _stop_fx(self):
        self.neofx.active_fx.remove(self)

    def _on_timer(self, ticks):
        #print('WipeFx _on_timer', ticks)

        elapsed = ticks_diff(ticks, self.start_ticks)
        newstart = self.endled + (elapsed * self.incled) // self.delay_ms

        if newstart != self.startled:
            if newstart < 0 or newstart > self.neofx.num_leds:
                self.neofx._fx_ended(self)
                return False

            self.startled = newstart
            if self.incled == 1:
                for i in range(0, self.startled):
                    self.neofx.pixels[i] = self.newpix[i]
            else:
                for i in range(self.startled, self.neofx.num_leds):
                    self.neofx.pixels[i] = self.newpix[i]

            return True
        else:
            return False

# Push transition effect
class PushFX(BaseFX):
    """PushFX(neofx, speed) - the new pattern pushes out the old pattern at the specified speed in pixels/s 
    (positive for one direction, negative for the other)."""
    def __init__(self, neofx, speed):
        super().__init__(neofx)
        self.incled = -1 if speed < 0 else 1 
        self.delay_ms = int(1000 / abs(speed))

    # String value
    def __str__(self):
        return f'PushFX(delay = {self.delay_ms} ms)' 

    def _start_fx(self, pat, oldpat):
        self.newpix = pat.pixels
        self.oldpix = oldpat.pixels
        self.endled = 0 if self.incled == 1 else self.neofx.num_leds-1
        self.startled = self.endled
        self.start_ticks = ticks_ms()
        self.neofx.active_fx.append(self)
        return True

    def _stop_fx(self):
        self.neofx.active_fx.remove(self)

    def _on_timer(self, ticks):
        #print('PushFx _on_timer', ticks)

        elapsed = ticks_diff(ticks, self.start_ticks)
        newstart = self.endled + (elapsed * self.incled) // self.delay_ms

        if newstart != self.startled:
            if newstart < 0 or newstart > self.neofx.num_leds:
                self.neofx._fx_ended(self)
                return False

            self.startled = newstart
            if self.incled == 1:
                left = self.newpix
                right = self.oldpix
            else:
                left = self.oldpix
                right = self.newpix

            for i in range(0, self.startled):
                self.neofx.pixels[i] = left[self.neofx.num_leds-self.startled+i]
            for i in range(self.startled, self.neofx.num_leds):
                self.neofx.pixels[i] = right[i-self.startled]

            return True
        else:
            return False

# Pulse effect
class PulseFX(BaseFX):
    """PulseFX(neofx, speed, opt = 0, opn = 0, start = -1, time = 0.0) - pulses the pattern over the base pattern at the specified 
    speed in pixels/s (positive for one direction, negative for the other) with the specified options (none, loop, bounce) and 
    operations (overlay, and, or, xor) for the specified time (0 means forever)."""
    OPN_OVER = 0
    OPN_AND = 1
    OPN_OR = 2
    OPN_XOR = 3

    OPT_NONE = 0
    OPT_LOOP = 1
    OPT_BOUNCE = 2

    def __init__(self, neofx, speed, opt = 0, opn = 0, start = -1, time = 0.0) :
        super().__init__(neofx)
        self.delay_ms = int(1000 / abs(speed))
        self.incled = -1 if speed < 0 else 1 
        self.opt = opt
        self.opn = opn
        self.start = start # Fix on _start_fx if default -1
        self.time_ms = int(time * 1000)

    # String value
    def __str__(self):
        return f'PulseFX(delay = {self.delay_ms}ms, opt = {self.opt}, opn = {self.opn}, start = {self.start}, time = {self.time_ms} ms)'

    def _start_fx(self, pat, oldpat):
        self.lastticks = self.start_ticks = ticks_ms()
        if self.start == -1:  
            self.start = 0 if self.incled > 0 else self.neofx.num_leds-len(pat.pixels)
        self.pos = self.start
        self.pattern = pat
        self.neofx.active_pulses.append(self)
        return True

    def _stop_fx(self):
        self.neofx.active_pulses.remove(self)

    # For pulses, we need two timer calls.  The first just updates position parameters
    def _on_timer(self, ticks):
        #print('PulseFx _on_timer', ticks)

        if self.time_ms and (ticks_diff(ticks, self.start_ticks) >= self.time_ms):
            self.neofx._pulse_ended(self)
            return False

        elapsed = ticks_diff(ticks, self.lastticks)
        newpos = self.start + (elapsed * self.incled) // self.delay_ms

        if newpos != self.pos:
            if newpos >= self.neofx.num_leds:
                if self.opt == self.OPT_LOOP:
                    #print('loop', newpos)
                    newpos %= self.neofx.num_leds
                    self.lastticks = ticks 
                    self.start = 0
                elif self.opt == self.OPT_BOUNCE:
                    #print('bounce', newpos)
                    self.incled *= -1
                    self.lastticks = ticks 
                    self.neofx._reverse_buffer(self.pattern.pixels) # Optional - flip the buffer!
                    newpos = self.start = self.neofx.num_leds-len(self.pattern.pixels) 
                else:
                    self.neofx._pulse_ended(self)
                    return False

            if newpos < -self.pattern.num_pix:
                if self.opt == self.OPT_LOOP:
                    #print('loop', newpos)
                    newpos %= self.neofx.num_leds
                    self.lastticks = ticks 
                    self.start = self.neofx.num_leds-len(self.pattern.pixels)
                elif self.opt == self.OPT_BOUNCE:
                    #print('bounce', newpos)                
                    self.incled *= -1 
                    self.lastticks = ticks 
                    self.neofx._reverse_buffer(self.pattern.pixels) # Optional - flip the buffer!
                    newpos = self.start = 0
                else:
                    self.neofx._pulse_ended(self)
                    return False

            self.pos = newpos
            return True
        
        return False

    # The second timer call for pulses only does the actual rendering into neofx.pixels2
    def _on_render(self):
        #print('PulseFx _on_timer_render')
        imin = 0
        imax = self.pattern.num_pix
        if self.opt != self.OPT_LOOP:
            if self.pos < 0:
                imin -= self.pos
            while imax > self.neofx.num_leds - self.pos:
                imax -= 1
        #print(f'self.pos ={self.pos}, imin = {imin}, imax = {imax}')
        if self.opn == self.OPN_OVER:
            for i in range(imin, imax):
                self.neofx.pixels2[(self.pos+i) % self.neofx.num_leds] = self.pattern.pixels[i]
        elif self.opn == self.OPN_AND:
            for i in range(imin, imax):
                self.neofx.pixels2[(self.pos+i) % self.neofx.num_leds] &= self.pattern.pixels[i]
        elif self.opn == self.OPN_OR:
            for i in range(imin, imax):
                self.neofx.pixels2[(self.pos+i) % self.neofx.num_leds] |= self.pattern.pixels[i]
        elif self.opn == self.OPN_XOR:
            for i in range(imin, imax):
                self.neofx.pixels2[(self.pos+i) % self.neofx.num_leds] ^= self.pattern.pixels[i]
        else:
            raise ValueError(f'Unknown operation {self.opn}')

# The master-class which acts as controller    
class NeopixelFX():
    """NeopixelFX(pin, num_leds, brightness = 1.0, pulse_brightness = -1.0, frequency = 50, grb = True) 
    pin is the output data pin GPIO number, num_leds is the number of LEDs in the strip, 
    brightness is the overall brightness (0.0 to 1.0), pulse_brightness is the brightness for pulse patterns 
    (0.0 - 1.0, -1 means same as brightness), frequency is the update frequency in Hz for the timer, 
    and grb is a boolean which is True if the strip expects GRB order rather than RGB"""

    state_machine_ids = set()    # Which state machine ids are in use (class variable)

    # State machine assember code from https://datasheets.raspberrypi.com/pico/raspberry-pi-pico-python-sdk.pdf section 3.9.2.
    @rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
    def ws2812():
        T1 = 2
        T2 = 5
        T3 = 3
        wrap_target()                                    # type:ignore
        label("bitloop")                                 # type:ignore  
        out(x, 1)               .side(0)    [T3 - 1]     # type:ignore
        jmp(not_x, "do_zero")   .side(1)    [T1 - 1]     # type:ignore
        jmp("bitloop")          .side(1)    [T2 - 1]     # type:ignore
        label("do_zero")                                 # type:ignore
        nop()                   .side(0)    [T2 - 1]     # type:ignore
        wrap()                                           # type:ignore 

    # fast word copy between buffers uses only thumb1 instructions - works on Pico 1 (RP2040)
    @staticmethod
    @micropython.asm_thumb
    def _fast_copy(r0, r1, r2):     # dest, source, n
        mov(r4, 2)                  # type:ignore
        lsl(r2, r4)                 # type:ignore
        add(r3, r1, r2)	            # type:ignore 
                                    # r3 = end of source
        label(loop1)		        # type:ignore 
        ldr(r4, [r1, 0])            # type:ignore 
        str(r4, [r0, 0])            # type:ignore 
        add(r0, 4)                  # type:ignore 
        add(r1, 4)                  # type:ignore 
        cmp(r1, r3)                 # type:ignore 
        bne(loop1)                  # type:ignore 

    """ 
    # Old slow copy
    def _fast_copy(self, dest, source, n):
        for i in range(n):
            dest[i] = source[i]
    """

    if True:    # True for Pico 2 (RP2350)
        # fast fade uses thumb2 instructions
        @staticmethod
        @micropython.asm_thumb
        def _fast_fade_asm(r0, r1, r2, r3): # r0=dest, r1=startpix, r2=endpix, r3=[n, elapsed, total]
            push({r8, r9, r10, r11, r12})   # type:ignore grab the lot for temp storage
            ldr(r4, [r3,4])                 # type:ignore 
            mov(r8, r4)                     # type:ignore r8=elapsed time
            ldr(r4, [r3,8])                 # type:ignore 
            mov(r9, r4)                     # type:ignore r9=total time

            mov(r4, 2)                      # type:ignore r4 = temp shift
            ldr(r3, [r3,0])                 # type:ignore r3 = n  
            lsl(r3, r4)                     # type:ignore r3 *= 4
            add(r3, r1, r3)	                # type:ignore r3 = end of startpix

            mov(r4, 0)                      # type:ignore
            mov(r11, r4)                    # type:ignore r11 = dirty

            label(loop1)                    # type:ignore
            mov(r7, 0)                      # type:ignore r7 = new pixel

            mov(r4, 16)                     # type:ignore r4 = shift count 

            label(loop2)                    # type:ignore
            ldr(r5, [r1, 0])                # type:ignore r5 = start pixel
            ldr(r6, [r2, 0])                # type:ignore r6 = end pixel
            lsr(r5, r4)                     # type:ignore r5 = start r g or b
            lsr(r6, r4)                     # type:ignore r6 = end r g or b
            mov(r10, r4)                    # type:ignore r10 saves shift
            mov(r4, 0xff)                   # type:ignore r4 = byte mask
            and_(r5, r4)                    # type:ignore
            and_(r6, r4)                    # type:ignore
            sub(r6, r6, r5)                 # type:ignore r6 = end r g or b - start r g or b
            mov(r4, r8)                     # type:ignore
            mul(r6, r4)                     # type:ignore r6 *= elapsed
            mov(r4, r9)                     # type:ignore
            sdiv(r6, r6, r4)                # type:ignore r6 /= total
            add(r5, r5, r6)                 # type:ignore r5 = start rg or b + (end rg or b - start rg or b) * elapsed / total
            mov(r4, r10)                    # type:ignore restore shift to r4
            lsl(r5, r4)                     # type:ignore
            orr(r7, r5)                     # type:ignore
            cmp(r4, 0)                      # type:ignore
            beq(loop3)                      # type:ignore
            sub(r4, 8)                      # type:ignore
            b(loop2)                        # type:ignore

            label(loop3)                    # type:ignore
            ldr(r5, [r0, 0])                # type:ignore r5 = current pixel
            cmp(r5, r7)                     # type:ignore
            beq(loop4)                      # type:ignore
            str(r7, [r0, 0])                # type:ignore
            mov(r4, 1)                      # type:ignore
            mov(r11, r4)                    # type:ignore r11 = dirty = True

            label(loop4)                    # type:ignore
            add(r0, 4)                      # type:ignore 
            add(r1, 4)                      # type:ignore 
            add(r2, 4)                      # type:ignore 
            cmp(r1, r3)                     # type:ignore 
            bne(loop1)                      # type:ignore 

            mov(r0, r11)                    # type:ignore return dirty value
            pop({r8, r9, r10, r11, r12})    # type:ignore restore regs

        def _fast_fade(self, dest, startpix, endpix, n, elapsed, total):
            return self._fast_fade_asm(dest, startpix, endpix, array("I", [n, elapsed, total]))
    else:
        # Old slow fade works on Pico 1 (2040) 
        def _fast_fade(self, dest, startpix, endpix, n, elapsed, total):
            to_tuple = lambda val: (val >> 16, (val >> 8) & 0xff, val & 0xff)
            to_val = lambda tuple: (tuple[0] << 16) + (tuple[1] << 8) + (tuple[2])
            
            dirty = False   # Flags we need to write the neopixel strip
            for i in range(n):
                start = to_tuple(startpix[i])
                end = to_tuple(endpix[i]) 
                col = to_val([start[j] + (end[j] - start[j]) * elapsed // total for j in range(0,3)])

                if col != dest[i]:
                    dest[i] = col
                    dirty = True
            return dirty

    # reverse a word buffer
    def _reverse_buffer(self, buffer):
        l = len(buffer)
        for i in range(l//2):
            t = buffer[i]
            buffer[i] = buffer[l-i-1]
            buffer[l-i-1] = t  

    # Constructor
    def __init__(self, pin, num_leds, brightness = 1.0, pulse_brightness = -1.0, frequency = 50, grb = True):  
        clamp = lambda n, minn, maxn: max(min(maxn, n), minn)   # Ensure range minn to maxn

        self.pin = pin
        self.num_leds = num_leds
        self.brightness = clamp(int(brightness * 255), 0, 255) # range 0 to 255
        if pulse_brightness >= 0:
            self.pulse_brightness = clamp(int(pulse_brightness * 255), 0, 255) # range 0 to 255
        else:
            self.pulse_brightness = self.brightness
        self.timer_period = 1000 // frequency
        self.cind1 = 1 if grb else 0    # buffer order is usually green red blue (why?)
        self.cind2 = 0 if grb else 1
        self.cind3 = 2
        self.current_pat = FillPattern(self, [(0,0,0)])
        self.current_fx = None
        self.callback = None
        self.queue_items = []
        self.queue_index = 0
        self.queue_callback = None
        self.queue_loop = False
        self.pulse_callback = None

        # Needs next available state machine!
        id = 0
        while id in self.state_machine_ids:
            id += 1

        self.sm = rp2.StateMachine(id, self.ws2812, freq=8_000_000, sideset_base=Pin(pin))
        self.machine_id = id
        NeopixelFX.state_machine_ids.add(id)

        self.sm.active(1)   # Start the StateMachine
        self.pixels = array("I", [0 for _ in range(num_leds)])
        self.pixels2 = None

        self.timer = Timer(-1, period=self.timer_period, mode=Timer.PERIODIC, callback=self._on_timer)
        self.active_fx = []
        self.active_pulses = []

    # Destructor.  No __del__ in MicroPython, so DIY!
    def cleanup(self):
        """NeopixelFX cleanup() - call this to free resources when finished"""
        self.timer.deinit()
        self.clear()
        NeopixelFX.state_machine_ids.remove(self.machine_id)     # Free machine id for reuse

    # String value
    def __str__(self):
        return f'MyNeopixel(pin = {self.pin}, num_leds = {self.num_leds}, brightness (0-255) = {self.brightness}, pulse_brightness (0-255) = {self.pulse_brightness})' 
    
    def _set_output(self, pixels):
        self.sm.put(pixels, 8)

    def clear(self):
        """NeopixelFX clear() - clear the strip and stop all effects and pulses"""
        self.queue_items = []
        self.queue_index = 0

        self.active_pulses = []

        if self.current_fx:
            self.current_fx._stop_fx()
            self.current_fx = None

        for i in range(self.num_leds):
            self.pixels[i] = 0
        self._set_output(self.pixels)

    # Single item show - external version zaps any queue
    def show(self, pattern, fx=None, callback=None):
        """NeopixelFX show(pat, fx=None, callback=None) - show a single pattern with an optional effect, cancelling any current effects or queue.  
        Optional callback(fx) is called when effect finished, with single parameter fx."""

        self.queue_items = []
        self.queue_index = 0
        self._show(pattern, fx, callback)

    # Single item show - internal version
    def _show(self, pat, fx=None, callback=None):
        #print('_show', pat, fx)

        if not pat:     # Re-show - is this useful?
            pat = self.current_pat

        if not isinstance(pat, BasePattern):
            raise TypeError("Requires a pattern")

        if fx and not isinstance(fx, BaseFX):
            raise TypeError("Requires an effect")

        # Pulses get special treatment
        if isinstance(fx, PulseFX):
            if not isinstance(pat, PulsePattern):
                raise TypeError("Pulse effect requires a pulse pattern")

            self.pulse_callback = callback
            fx._start_fx(pat, None)
            return
        
        elif isinstance(pat, PulsePattern):
            raise TypeError("Pulse pattern requires a pulse effect")

        if self.current_fx:
            self.current_fx._stop_fx()
            self.current_fx = None

        self.callback = callback

        if fx:
            if fx._start_fx(pat, self.current_pat):
                self.current_fx = fx
        else:
            self._fast_copy(self.pixels, pat.pixels, self.num_leds) # Keep self.pixels matching strip
            self._set_output(self.pixels)

        self.current_pat = pat  # Do this last

    # Stop all pulses
    def stop_pulses(self):
        """NeopixelFX stop_pulses() - stop all active pulses immediately."""
        self.active_pulses = []
        self._set_output(self.pixels)

    # Multi item show
    def queue(self, items, callback=None):
        """NeopixelFX queue(items, callback=None) - show several effects in sequence, with an optional callback(items) when finished.
        items is a list of tuples [(pat, fx),...].  If pat is None, the current pattern is re-shown with the new effect. 
        If fx is None, the new pattern is shown immediately."""
        self.queue_items = items
        self.queue_index = 0
        self.queue_callback = callback
        self.queue_loop = False
        self._next_queue()

    # Multi item loop
    def loop(self, items):
        """NeopixelFX loop(items) - loop repeatedly through several effects in sequence until a new show() or queue() is called.
        items is a list of tuples [(pat, fx),...].  If pat is None, the current pattern is re-shown with the new effect.  
        If fx is None, the new pattern is shown immediately."""
        self.queue_items = items
        self.queue_index = 0
        self.queue_callback = None
        self.queue_loop = True
        self._next_queue()

    def _next_queue(self):
        if self.queue_loop and (self.queue_index >= len(self.queue_items)):
            self.queue_index = 0    

        if self.queue_index < len(self.queue_items):
            item = self.queue_items[self.queue_index]
            self.queue_index += 1
            pat = item[0]
            fx = item[1] if len(item) > 1 else None
            self._show(pat, fx)
            if not fx:  # Nothing to wait for!
                self._next_queue()
        else:
            if self.queue_callback:
                self.queue_callback(self.queue_items)
                self.queue_callback = None
            self.queue_items = []
            self.queue_index = 0

    # The master timer - everything else chains off this
    def _on_timer(self, timer):
        ticks = ticks_ms()
        dirty = False
        for fx in self.active_fx:           # Background effects
            dirty |= fx._on_timer(ticks)    # This renders into self.pixels
        for pulse in self.active_pulses:    # Superimposed pulses
            dirty |= pulse._on_timer(ticks)  # This just updates position parameters
        if dirty:
            if self.active_pulses:          # If pulses, we need a new buffer
                if not self.pixels2:        # Init on demand
                    self.pixels2 = array("I", [0 for _ in range(self.num_leds)])
               
                self._fast_copy(self.pixels2, self. pixels, self.num_leds)  # Copy current background

                for pulse in self.active_pulses:    # Then superimpose pulses
                    pulse._on_render()
                
                self._set_output(self.pixels2)
            else:
                self._set_output(self.pixels)

    # Called when transition ended
    def _fx_ended(self, fx):
        fx._stop_fx()
        self.current_fx = None
        if self.queue_items:
            self._next_queue()
        elif self.callback:
            self.callback(fx)
            self.callback = None

    # Called when pulse ended
    def _pulse_ended(self, fx):
        fx._stop_fx()
        if self.queue_items:
            self._next_queue()
        elif self.pulse_callback:
            self.pulse_callback(fx)
            self.pulse_callback = None

# Test/demo routine!
def main():
    from math import sin, cos, pi
    from random import randint, randrange
    
    PIN = 21        # GPIO number for data pin (GPIO 21 = physical pin 27 on Pico)
    NUM_LEDS = 60
    BRIGHTNESS = 0.1
    PULSE_BRIGHTNESS = 1
    FREQUENCY = 50
    GRB = True

    # Misc randoms for effects
    randCol = lambda max : (randint(0, max),randint(0, max),randint(0, max))
    randMinus = lambda val : val if randrange(10) > 5 else -val
    randTrans = lambda mnp : (FadeFX(mnp, 2), FlickerFX(mnp, 50), WipeFX(mnp, randMinus(50)), PushFX(mnp, randMinus(50)))[randrange(4)] 
    randFX = lambda mnp, t=0: (RotateFX(mnp, randMinus(20), t),)[randrange(1)]
    randFX2 = lambda mnp, t=0: (SparkleFX(mnp, 50, t),)[randrange(1)]
    
    # Return queue parameters for a given effect for a given time
    def get_demo(n,t):
        if n == 0:
            return [(FillPattern(mnp, [randCol(255) for _ in range(0, randint(1,6))]), randTrans(mnp)), (None, randFX(mnp, t))]
        elif n == 1:
            return [(RandomPattern(mnp), randTrans(mnp)), (None, randFX2(mnp, t))]
        elif n == 2:
            return [(SpectrumPattern(mnp, [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 0)]), randTrans(mnp)), (None, randFX(mnp, t))]
        elif n == 3:
            return [(UserPattern(mnp, lambda i : (255*(sin(2*pi*i/NUM_LEDS)**2), 0, 255*(cos(2*pi*i/NUM_LEDS)**2))), randTrans(mnp)), (None, randFX(mnp, t))]
        elif n == 4:
            return [(RandomPattern(mnp, "#000010","#101020"), SparkleFX(mnp, 50, t))]
        elif n == 5:
            return [(PulsePattern(mnp, [(0, 0, 255>>4), (0, 0, 255>>2), (0, 0, 255)]), PulseFX(mnp, 100, PulseFX.OPT_LOOP, PulseFX.OPN_OR, -1, t))]
        elif n == 6:
            return [(PulsePattern(mnp, [(255, 0, 0), (255>>2, 0, 0), (255>>4, 0, 0)]), PulseFX(mnp, -100, PulseFX.OPT_LOOP, PulseFX.OPN_OR, -1, t))]
        elif n == 7:
            return [(PulsePattern(mnp, [(0, 255>>4, 0), (0, 255>>2, 0), (0, 255, 0)]), PulseFX(mnp, 100, PulseFX.OPT_BOUNCE, PulseFX.OPN_OR, -1, t))]
        else:
            return []

    mnp = NeopixelFX(PIN, NUM_LEDS, BRIGHTNESS, PULSE_BRIGHTNESS, FREQUENCY, GRB)
    mnp.clear()

    try:
        while True:
            switch = input('Demo 1-9, c=clear, q=quit? ')

            if switch == 'q':
                raise KeyboardInterrupt
            
            elif switch == 'c':
                print('Clear')   
                mnp.clear()

            elif switch >= '1' and switch <= '8':
                val = int(switch)-1
                demo = get_demo(val, 0)
                for d in demo:
                    print(d[0], d[1])   # pattern, effect
                if val < 5:
                    mnp.stop_pulses()
                mnp.queue(demo)  

            elif switch == '9':
                print('All demos loop...')
                mnp.stop_pulses()
                all_demos = []
                for i in range(8):
                    all_demos += get_demo(i, 5)
                mnp.loop(all_demos)
                     
            else:
                print('???')

    except KeyboardInterrupt:
        print('KeyboardInterrupt - quitting')

    finally:
        mnp.cleanup()

if __name__== "__main__":
    main()
