"""
Updated version of power_scan.py which uses the RtlSdr class.

It also will accomodate scans at various gain settings.

Steps through the spectrum in 1 MHz steps, capturing data at 1 MS/s and
converting that to LSB and USB.  In effect, 500 kHz resolution.

According to the scanner() code in /opt/rtl-sdr/src/rtl_power.c, the buffer is
not reset between tunings.
"""
from rtlsdr import *
from pylab import *
import scipy.fftpack
import logging

mylogger = logging.getLogger()
logging.basicConfig()
mylogger.setLevel(logging.WARNING)


def plot_spectrum(fignum,gain,freqs,pwr):
  semilogy(freqs,pwr,label=str(gain))
  #if len(freqs) < 200:
  #  semilogy(freqs[0:len(freqs):2],pwrl,'.', label=str(gain)+" LSB")
  #  semilogy(freqs[1:len(freqs):2],pwru,'.', label=str(gain)+" USB")

def plot_data_histogram(fignum,signll,signlu, savefig=False):
  figure(fignum)
  subplot(1,2,1)
  hist(signll,bins=100)
  grid()
  title("LSB")
  subplot(1,2,2)
  hist(signlu,bins=100)
  grid()
  title("USB")
  if savefig:
    savefig("Figures/samples_%06.1f-%06.1fMHz.png" % (start,end))

n = get_device_count()
vendor, product, serial = get_device_strings(0)
device = get_device_name(0)

start = 25
end = 108
step = 1

rtlsdr = init_sdr(sample_rate=step*1000000, dflt_blk_size=2048)

gains = rtlsdr.get_tuner_gains()
print "gains =", gains

specfig = figure(1)
for gain_idx in [4,7,13,17,22]:
  status = rtlsdr.set_gain(gains[gain_idx])
  gain = gains[gain_idx]
  print "gain =", gain
  status = rtlsdr.reset_buffer()
  print "reset_buffer status:",status
  freqs,pwrl,pwru,pwr,signll,signlu = rtlsdr.get_power_scan(start,end,step,
                                             gain=gain)
  plot_spectrum(specfig,gain,freqs,pwr)

status = rtlsdr.close()
print "Close status:",status

figure(1)
xlabel("Frequency (MHz)")
title("Power for various gains")
xlim(start-step,end+step)
legend(loc="upper left",numpoints=1)
grid()
savefig("Figures/scan_%06.1f-%06.1fMHz.png" % (start,end))

show()

