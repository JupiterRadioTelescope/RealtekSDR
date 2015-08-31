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
sr = 200000
freq = FM_freq["KCRW"]
sdr = RtlTCP(samplerate=sr, freq=int(freq*1e6))

# Initialize plot
nspec = 256
last_read = nspec # initial value
nch = BUFFER_SIZE/2
oldest_displayed = 0
history = 16384

fig = plt.figure()
waterfall_axes = fig.add_axes([.1,.1,.75,.9])
data = zeros((nspec,nch))
for index in range(nspec):
  time.sleep(0.003)
  data[index,:] = log10(sdr.grab_SDR_spectrum())
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

# add a colorbar on the right
colorbar_axes = fig.add_axes([0.85,0.05,.15,.9],aspect=20)
fig.colorbar(waterfall_artist, cax=colorbar_axes)
fig.canvas.draw()

def init(*args):
  waterfall_artist.set_array(image)
  return waterfall_artist,

def animate(*args):
  global data, oldest_displayed, sdr, thisimage
  spectrum = log10(sdr.grab_SDR_spectrum())
  s = spectrum.reshape(1,nch)
  data = append(data, s, axis=0)
  oldest_displayed += 1
  first = oldest_displayed
  last = oldest_displayed + nspec
  mylogger.debug("Displaying from %d to %d", first, last)
  thisimage = data[first:last, :]
  mylogger.debug("animate: last image line max is %s", thisimage[-1].argmax())
  waterfall_artist.set_array(thisimage)
  return waterfall_artist,

mylogger.setLevel(logging.DEBUG)
#anim = animation.FuncAnimation(fig, animate, init_func=init, interval=1000,
#                               blit=True)
plt.show()

 

  

