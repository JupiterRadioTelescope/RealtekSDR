"""
Grabs data at 1 MS/s and plots histograms for the I and Q samples.
"""
from rtlsdr import *
from pylab import *
import scipy.fftpack
from time import sleep
from sys import stdout


n = get_device_count()
vendor, product, serial = get_device_strings(0)
device = get_device_name(0)

start = 88
end = 98.5
step = 1
rtlsdr = RtlSdr(0)
sr = rtlsdr.set_samplerate(int(step*1000000))
gains = rtlsdr.get_tuner_gains()
print "gains =", gains
# rtlsdr.set_gain_manual(True)
gain = gains[0]
status = rtlsdr.set_gain(gain)
print "gain =", gain
status = rtlsdr.reset_buffer()
print "reset_buffer status:",status

fig = figure(figsize=(12,9))
count=1
for freq in arange(start,end,step): # MHz
  cf = rtlsdr.set_freq(int(freq*1000000))
  status = rtlsdr.reset_buffer()
  sleep(0.01)
  rawdata = rtlsdr.synch_read()
  data = unpack_to_complex(rawdata)
  print cf/1.e6,
  stdout.flush()
  datalen = len(data)
  subplot(3,4,count)
  hist(data.real, bins=50, log=True)
  hist(data.imag, bins=50, log=True)
  title(str(freq))
  count+=1
status = rtlsdr.close()
print "Close status:",status
show()

