"""
Notes on timing
===============
It takes 0.8 s to grab the 256 lines for the initial image. That works out to
3 ms per line.  A 512 point spectrum of a 200 kHz bandwidth requires 2.56 ms
of data sampling.  So the two are matched pretty well and no extra delay is
required.

It takes about 10 s for a line to scroll up the 256 line dynamic spectrum. That
means it takes 39 ms per line.  So 36 ms are required to repaint the image. It
means that 12 spectra are lost while this is happening, for a duty cycle of
7.7%.  If we take 12 spectra quickly, that will take 39 s for a duty cycle of
50%.

The formula for duty cycle in percent is 100*(1 + 36/(n*3)) where n is the 
number of spectra in a group.
n    =  8  12  13  16  32  64 128 256
d.c. = 40  50  52  57  73  84  91  96

The speed at which the dynamic spectrum flows by is a function of the
bandwidth. For a 100 kHz spectrum, spectra are formed every 5.12 ms. Timing the
initial 256 spectrum loop works out to 6 ms per spectrum.  The efficiencies in
the table above move left one column.

Another way to slow the plot down is to increase the number of channels.  This
means making BUFFER_SIZE a parameter.
"""
import logging
import time
from math import log10

import matplotlib
from matplotlib import pyplot as plt
from matplotlib import animation
from matplotlib.figure import Figure

from numpy import append, linspace, log10, zeros

from RealtekSDR.TCPclient import RtlTCP, BUFFER_SIZE
from RealtekSDR.stations import FM_freq

logging.basicConfig()
mylogger = logging.getLogger()

# Configure SDR 
station = "KCRW"
sr = 100000
freq = FM_freq[station]
sdr = RtlTCP(samplerate=sr, freq=int(freq*1e6))

# Initialize plot
nspec = 256
last_read = nspec # initial value
nch = BUFFER_SIZE/2
oldest_displayed = 0
history = 16384

sampling_interval = 1./sr
num_complex_samples = nch
spectrum_interval = nch*sampling_interval
spectrum_interval_ms = spectrum_interval*1000 # ms

fig = plt.figure()
waterfall_axes = fig.add_axes([.1,.1,.75,.9])
data = zeros((nspec,nch))
t0 = time.time()
for index in range(nspec):
  time.sleep(spectrum_interval)
  data[index,:] = log10(sdr.grab_SDR_spectrum())
t1 = time.time()
image = data[oldest_displayed:oldest_displayed + nspec, :]
waterfall_artist = waterfall_axes.imshow(
          image,
          aspect = 'auto',
          cmap=matplotlib.cm.spectral,
          interpolation='bicubic',
          animated = True,
          origin='lower')
          #extent=(freq-sr/2, freq+sr/2, last_read, last_read-nspec))
# set the limits to channel number
waterfall_axes.set_xlim(0,nch-1)
# set the nspec range
waterfall_axes.set_ylim(last_read,last_read-nspec)
waterfall_axes.autoscale_view()
# add the labels
waterfall_axes.set_xlabel("Frequency")
waterfall_axes.set_ylabel("Time")
waterfall_axes.set_title(station)

# add a colorbar on the right
colorbar_axes = fig.add_axes([0.85,0.05,.15,.9],aspect=20)
fig.colorbar(waterfall_artist, cax=colorbar_axes)
fig.canvas.draw()

def init(*args):
  waterfall_artist.set_array(image)
  return waterfall_artist,

def animate(*args):
  global data, oldest_displayed, sdr, thisimage
  for index in range(16):
    spectrum = log10(sdr.grab_SDR_spectrum())
    s = spectrum.reshape(1,nch)
    data = append(data, s, axis=0)
  oldest_displayed += 16
  first = oldest_displayed
  last = oldest_displayed + nspec
  mylogger.debug("Displaying from %d to %d", first, last)
  thisimage = data[first:last, :]
  mylogger.debug("animate: last image line max is %s", thisimage[-1].argmax())
  waterfall_artist.set_array(thisimage)
  return waterfall_artist,

mylogger.setLevel(logging.INFO)
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               interval=spectrum_interval_ms,
                               blit=True)
plt.show()
 

  

