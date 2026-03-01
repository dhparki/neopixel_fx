""" Button with built-in debounce DaveP Sep 25, updated Feb 26. """

from machine import Pin
from utime import sleep, ticks_ms, ticks_diff

class BounceButton(Pin):
    """BounceButton(pin, debounce = 20) - A button with built-in debounce. pin = GPIO number for button pin, debounce - debounce time in ms"""
    # Constructor
    def __init__(self, pin, debounce = 20):
        super().__init__(pin, Pin.IN, Pin.PULL_UP)
        self._pin = pin
        self._debounce = debounce
        self._button_tick = ticks_ms()
        self._button_value = 1
        self._on_down_fn = None
        self._on_up_fn = None
        super().irq(self._button_change, Pin.IRQ_FALLING | Pin.IRQ_RISING)
    
    # Destructor
    # No __del__ in MicroPython, so DIY!
    def cleanup(self):
        """BounceButton cleanup() - call this before quitting to clean up the IRQ handler"""
        super().irq(None)
    
    # String value
    def __str__(self):
        return f'BounceButton({self._pin})' 
    
    # IRQ handler
    def _button_change(self, pin):
        #print(pin.value())
        if (ticks_diff(ticks_ms(), self._button_tick) < self._debounce) or (pin.value() == self._button_value):
            return
        self._button_tick = ticks_ms()
        self._button_value = pin.value()
        if self._button_value:
            if self._on_up_fn:
                self._on_up_fn(self)
        else:
            if self._on_down_fn:
                self._on_down_fn(self)
     
    # Override value() function 
    def value(self):
        """BounceButton value() - return the current button value (0 or 1)"""
        return self._button_value;
    
    # Set down button handler
    def on_down(self, function):
        """BounceButton on_down(function) - set the function to call when the button goes down. The function will be passed the button as an argument."""
        self._on_down_fn = function

    # Set up button handler
    def on_up(self, function):
        """BounceButton on_up(function) - set the function to call when the button goes up. The function will be passed the button as an argument.  """
        self._on_up_fn = function

# Test/demo code
def main():
    PIN = 16 # Button connected between pin with this GPIO number and GND - change as required

    def go_down(button):
        print(button,'down')
        led.value(1)
    
    def go_up(button):
        print(button,'up')
        led.value(0)
        
    led = Pin('LED', Pin.OUT)
    button = BounceButton(16)
    
    button.on_down(go_down)
    button.on_up(go_up)

    # Main loop just sleeps
    try:
        print('Running demo, ^C to quit')
        while True:
            sleep(3600)
    finally:
        print('Quitting')
        # Needs an explicit cleanup call, or IRQ code will keep running.
        button.cleanup()
        
if __name__== "__main__":
      main()
