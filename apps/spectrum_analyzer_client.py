"""
Spectrum analyzer client for rtl_tcp.

For a complex sample rate of 200 ksamp/s (corresponding to a typical FM station
bandwidth), the refresh rate for a 512 point spectrum is::
  In [6]: 1./200000
  Out[6]: 5e-06
  In [7]: 512./200000
  Out[7]: 0.00256
2.56 ms.  A typical video refresh rate is 50 Hz or every 20 ms.
"""
import logging
from math import log10
from matplotlib import pyplot as plt
from matplotlib import animation
from numpy import linspace

from RealtekSDR.TCPclient import RtlTCP, BUFFER_SIZE
from RealtekSDR.stations import FM_freq

mylogger = logging.getLogger()

# Configure SDR    
sr = 200000
freq = FM_freq["KCRW"]
sdr = RtlTCP(samplerate=sr, freq=int(freq*1e6))

# Initialize plot
spectrum = sdr.grab_SDR_spectrum()
yminexp = int(log10(spectrum.min()))
ymaxexp = int(log10(spectrum.max())+1)
mylogger.debug(" Y axis limits: %e, %e", yminexp,ymaxexp)
fig = plt.figure()
ax = plt.axes(xlim=(freq-sr/2e6, freq+sr/2e6), ylim=(10**yminexp,10**ymaxexp))
x = linspace(freq-sr/2e6, freq+sr/2e6, BUFFER_SIZE/2)
line, = ax.semilogy([], [])
ax.grid(True)
ax.set_xlabel("Frequency (MHz)")

def init():
    line.set_data([], [])
    return line,

def animate(i):
    global sdr
    spectrum = sdr.grab_SDR_spectrum()
    line.set_data(x, spectrum)
    return line,

anim = animation.FuncAnimation(fig, animate, init_func=init, interval=20,
                               blit=True)
plt.show()

