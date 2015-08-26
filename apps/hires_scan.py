"""
Scans through the spectrum with a 'step' MHz band and tranforming the
data into a 64 point spectrum.
"""
from pylab import *
from time import sleep
from sys import stdout
from numpy.polynomial.chebyshev import chebval
from cPickle import load
import logging

from RealtekSDR import *
from RealtekSDR.stations import FM_station, TV_station
from RealtekSDR.Signals import make_spectrogram

mylogger = logging.getLogger()
logging.basicConfig()
mylogger.setLevel(logging.INFO)

labels = True
normalize = True
start = 109
end = 139
step = 2
num_bins = 64

#n = get_device_count()
#vendor, product, serial = get_device_strings(0)
#device = get_device_name(0)
#rtlsdr = RtlSdr(0)
#sr = rtlsdr.set_samplerate(int(step*1000000))
rtlsdr = init_sdr(dev_ID=0, sample_rate=int(step*1000000))
gains = rtlsdr.get_tuner_gains()
mylogger.info(" gains = %s", gains)
# We want high gain (but not saturating) when examining the spectrum
# but low gain to get the baseline shape.
if normalize:
  gain = gains[-5]
else:
  gain = gains[1]
status = rtlsdr.set_gain(gain)
mylogger.info(" gain = %d", gain)
status = rtlsdr.reset_buffer()
mylogger.info(" reset_buffer status: %s",status)

if normalize:
  coeffile = open("baseline_coefs.pkl","rb")
  coef_dict = load(coeffile)
  coeffile.close()
  coefs = coef_dict[float(step)]
  print "Coefficients loaded"
fig = figure()
freqs = []
signl = []
for freq in arange(start,end,step): # MHz
  cf = rtlsdr.set_freq(int(freq*1000000))
  status = rtlsdr.reset_buffer()
  sleep(0.01)
  #rawdata = rtlsdr.synch_read()
  #data = unpack_to_complex(rawdata)
  data = rtlsdr.get_data_block()
  print cf/1.e6,
  stdout.flush()
  datalen = len(data)
  halfwidth = num_bins/2
  num_spec = datalen/num_bins
  image = make_spectrogram(data, num_spec, num_bins, log=False)
  spectrum = image.mean(axis=0)
  # fix up center channel
  spectrum[halfwidth] = (spectrum[halfwidth-1]+spectrum[halfwidth+1])/2
  offset = float(halfwidth-0.5)/num_bins
  specfreqs = linspace(-step*offset, +step*offset, num_bins)
  freqs += list(specfreqs+cf/1.e6)
  if normalize:
    signl += list(spectrum/chebval(specfreqs,coefs))
  else:
    signl += list(spectrum)
status = rtlsdr.close()
print "\nClose status:",status
plot(freqs,log10(array(signl)))
xlim(start-step/2.,end-step/2.)
xlabel("Frequency (MHz)")
title("Gain = "+str(gain))
grid()
if labels:
  z = argsort(array(signl))
  found = []
  for index in range(-1,-21,-1):
    fr = round(freqs[z[index]],1)
    try:
      name = FM_station[fr]
    except KeyError:
      name = ""
      for stn in TV_station.keys():
        if fr >= TV_station[stn][0] and fr <= TV_station[stn][1]:
          name = "Ch "+str(stn)
          break
      if name == "":
        name = str(fr)
    try:
      found.index(name)
      name = ''
    except:
      found.append(name)
    text(fr,log10(signl[z[index]]),name)
freq_string = "%06.1f:%06.1f:%03.1fMHz" % (start,end,step)
if normalize:
  savefig("Figures/hiresscan-norm_%s.png" % freq_string)
else:
  savefig("Figures/hiresscan-raw_%s.png" % freq_string)
  f = open("baselines_%s.dat" % freq_string, "w")
  for index in range(len(freqs)):
    f.write(str(freqs[index])+"\t"+str(signl[index])+"\n")
  f.close()
show()

