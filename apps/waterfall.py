from pylab import *
import socket
import logging
from struct import *
from numpy import array
from RealtekSDR.Signals import unpack_to_complex
from matplotlib.pyplot import ion
  
# Turn interactive mode on. This obviates the need for 'draw()' commands.
# Alternately, invoke 'ioff()' and explicitly invoke 'draw()' when it
# makes sense to do so.
ion()

TCP_IP = '192.168.0.13'
TCP_PORT = 1234
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

nspec = 512
last_read = nspec # initial value
nch = BUFFER_SIZE/2
oldest_displayed = 0
history = 16384
waterfall_on = False
# One row smaller so first row append gives right shape
data = np.zeros((nch,nspec))

fig = figure()
# Add the upper X-Y axes area to the figure for the current spectrum
# x,y = 0.1,0.75, width = 0.8, height = 0.2.  This method also
# creates the XY-plot
# Add a lower axes for the waterfall image. The bottom axis goes from
# x,y = 0.1,0.75, width 0.8, height = 0.7.  This method also creates
# the image.
waterfall_top_axes    = fig.add_axes([.1,.75,.75,.2])
# Plot the current spectrum starting
ydata = data[nspec-1,:]
max_data = np.amax(ydata)
water_spectrum_lines = waterfall_top_axes.plot(ydata,animated=True)
# We'd like the ticks across the top but this doesn't seen to do it
waterfall_top_axes.set_axisbelow(False)
waterfall_top_axes.set_xticks([])
# set the limits to channel numbers
waterfall_top_axes.set_xlim(0,nch-1)
waterfall_top_axes.set_ylim(0,max_data)
# When hold is True, subsequent plot commands will add to the
# current axes.  If it is None, the hold state is toggled. In
# this case each plot commands replaces the existing line.
waterfall_top_axes.hold(False)

# This creates the axes for the waterfall plot (bottom axes).
# It shares the X-axis with the top one.  This means that scrolling
# and zooming along the x-axis affects both plots."""
waterfall_bottom_axes = fig.add_axes([.1,.05,.75,.65],
                                     sharex = waterfall_top_axes)
    
# This creates the waterfall plot
# clear the bottom axes
waterfall_bottom_axes.cla()
im = data[oldest_displayed:oldest_displayed + nspec, :]
waterfall_artist_bottom = waterfall_bottom_axes.imshow(
          im,
          aspect = 'auto',
          cmap=matplotlib.cm.spectral,
          interpolation='bicubic',
          animated = True,
          origin='lower',
          extent=(0, nch-1, last_read,last_read-nspec))
# set the limits to channel number
waterfall_bottom_axes.set_xlim(0,nch-1)
# set the nspec range
waterfall_bottom_axes.set_ylim(last_read,last_read-nspec)
waterfall_bottom_axes.autoscale_view()
# add the labels
waterfall_bottom_axes.set_xlabel(xlabel)
waterfall_bottom_axes.set_ylabel(ylabel)

# add a colorbar on the right
colorbar_axes = fig.add_axes([0.85,0.05,.15,.9],aspect=20)
fig.colorbar(waterfall_artist_bottom, cax=colorbar_axes)
fig.canvas.draw()
fig.show()

run = True
buf = s.recv(BUFFER_SIZE)
print buf[:4]
while run:
  try:
    buf = s.recv(BUFFER_SIZE)
    rawdata = unpack(str(len(buf))+'b', buf)
    cmplx_data = unpack_to_complex(array(rawdata)).reshape(nch,1)
    ydata = unpack_to_complex(array(rawdata)).reshape(nch,1)
    xform = fft(ydata)
    shifted = fftshift(xform)
    spectrum = (shifted*conj(shifted)).real
    water_spectrum_lines[0].set_ydata(spectrum)
    waterfall_top_axes.redraw_in_frame()
    waterfall_top_axes.draw_artist(water_spectrum_lines[0])
    
    data = np.append(data,spectrum,1)
    im = data[oldest_displayed:oldest_displayed+nspec,:]
    if waterfall_on:
      waterfall_bottom_axes.cla()
    # Just update the image data
    waterfall_artist_bottom.set_data(im)
    waterfall_bottom_axes.draw_artist(waterfall_artist_bottom)
    # The waterfall plot is now on.
    waterfall_on = True
  except KeyboardInterrupt:
    s.close()
    run=False



