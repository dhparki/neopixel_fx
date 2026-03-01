""" Get a rough idea of CPU usage when making heavy use of interrupts. DaveP Feb 26
    Loosly based on https://www.oceanlabz.in/estimating-cpu-usage-on-esp32-esp32-c3-with-micropython/"""

from utime import ticks_ms, ticks_diff

class CPUUsage():
    """CPUUsage(duration = 1.0) - Estimate CPU usage over the specified duration in seconds.  Need to init with CPU otherwise idle."""
    def __init__(self, duration = 1.0):
        self._duration_ms = int(duration * 1000)
        self.rebase()

    def _idle_count(self):
        start = ticks_ms()
        idle_count = 0
        while ticks_diff(ticks_ms(), start) < self._duration_ms:
            idle_count += 1
        return idle_count
    
    def rebase(self):
        """Rebase the CPU usage baseline.  Call this if you want to reset the baseline, with CPU otherwise idle."""
        self._baseline = self._idle_count() 

    def usage(self):
        """Returns a rough estimate of current CPU usage as a percentage."""
        idle_count = self._idle_count()
        return (100 * (self._baseline - idle_count)) // self._baseline

# Test/demo code
def main():
    from machine import Timer
    
    cpu_usage = CPUUsage(0.2)   # Init with CPU otherwise idle

    def busyFn(timer):
        # Just do some busy looping to load the CPU.
        # (Some systems might optimise this out, but not current MicroPython apparently.)
        x = 0
        for i in range(1000):
            x += i*i
        
    # Call the busyFn on timer interrupts - adjust the period as required.
    timer = Timer(-1, period=10, mode=Timer.PERIODIC, callback = busyFn)

    # Print the approximage CPU usage.
    print(f'CPU usage = {cpu_usage.usage()}%')  

    timer.deinit()  # Clear up!

if __name__== "__main__":
      main()
