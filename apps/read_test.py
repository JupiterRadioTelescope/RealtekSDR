"""
Data obtained with something like:

 sudo rtl_sdr /tmp/capture.bin -s 1.8e6 -f 392e6

 Specifications::

  * The highest sample rate is 3.2 MSs; the highest at which samples are not
dropped is 2.8 MSs.
  * The tuning range is 24 - 1766 MHz.
  * The resolution is 8 bps.

Format example obtained from http://pastebin.com/hcwyKvX7
"""

from struct import *
from numpy import array
from numpy.fft import fft
from pylab import *
import argparse
from rtlsdr import show_image
from Graphics import make_spectrogram
from RealtekSDR.Signals import unpack_to_complex

files = {1: "/tmp/capture.bin"}
for f in files.keys():
  print f,files[f]
choice = int(raw_input("Select a file> "))
if choice == 1:
  command = raw_input("What were the rtl_sdr arguments? ")
  parser = argparse.ArgumentParser()
  parser.add_argument("-f", dest="centerfreq")
  parser.add_argument("-s", dest="samplerate", default=2048000)
  args = parser.parse_args(command.split())
  print args

  samplerate = float(args.samplerate)
  centerfreq = float(args.centerfreq)
else:
  raise RuntimeError("Invalid selection")
  
num_bins = 1024
num_spec = 2048
refreshinterval = 1/(samplerate/1024)*1e6 # usec
bandwidth = samplerate
  
freqs = array(arange(centerfreq-samplerate/2,
                     centerfreq+samplerate/2,
                     samplerate/num_bins))/1e6 # kHz

fd = open(files[choice],"r")
buf = fd.read()
fd.close()

rawdata = unpack(str(len(buf))+'b', buf)
data = unpack_to_complex(array(rawdata))

image = make_spectrogram(data,num_spec,num_bins)
extent=(freqs[0], freqs[-1], 0, num_spec*refreshinterval)
show_image(image, extent)
show()
response = raw_input("Save image? ")
if response[0] in "yY":
  savefig("Figures/spectrum.png")
