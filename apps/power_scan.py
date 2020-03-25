"""
Steps through the spectrum in 1 MHz steps, capturing data at 1 MS/s and
converting that to LSB and USB.  In effect, 500 kHz resolution.

According to the scanner() code in /opt/rtl-sdr/src/rtl_power.c, the buffer is
not reset between tunings.
"""
from sys import path, stdout
from RealtekSDR import RtlSdr, get_devices
from RealtekSDR import get_device_count, get_device_name, get_device_strings
from pylab import *
import scipy.fftpack
from time import sleep
import logging
from Data_Reduction import sideband_separate, unpack_to_complex

mylogger = logging.getLogger()
logging.basicConfig()
mylogger.setLevel(logging.DEBUG)

n = get_device_count()
mylogger.info("There are %d devices", n)
vendor, product, serial = get_device_strings(0)
device = get_device_name(0)

start = 88
end = 108
step = 1
rtlsdr = RtlSdr(0)
sr = rtlsdr.set_samplerate(int(step*1000000))
gains = rtlsdr.get_tuner_gains()
mylogger.info("gains = %s", gains)
gain = gains[12]
status = rtlsdr.set_gain(gain)
mylogger.info("gain = %f", gain)
status = rtlsdr.reset_buffer()
mylogger.info("reset_buffer status: %d",status)

def get_power_scan(start, end, step, gain=0, num_samples=16384):
  freqs = []
  signlu = []
  signll = []
  pwru = []
  pwrl = []
  pwr = []
  for freq in arange(start,end,step): # MHz
    cf = rtlsdr.set_freq(int(freq*1000000))
    freqs.append(cf/1e6-0.25*step)
    freqs.append(cf/1e6+0.25*step)
    status = rtlsdr.reset_buffer()
    sleep(0.01)
    rawdata = rtlsdr.synch_read(num=num_samples)
    if rawdata.min() < -120 or rawdata.max() > 120:
      mylogger.warning("%7.2f MHz, min=%d, max=%d",
                       cf/1.e6, rawdata.min(), rawdata.max())
    data = unpack_to_complex(rawdata)
    mylogger.info("%7.2f MHz, min=%s, max=%s",
                  cf/1.e6, str(data.min()),str(data.max()))
    datalen = len(data)
    lsb,usb = sideband_separate(data)
    signll += list(lsb)
    signlu += list(usb)
    LSB = (lsb**2).sum()/datalen
    USB = (usb**2).sum()/datalen
    pwrl.append(LSB)
    pwru.append(USB)
    pwr.append(LSB)
    pwr.append(USB)
  return freqs,pwrl,pwru,pwr,signll,signlu

freqs,pwrl,pwru,pwr,signll,signlu = get_power_scan(start,end,step,
                                                   gain=gain, num_samples=2048)
status = rtlsdr.close()
print "Close status:",status
figure(1)
semilogy(freqs,pwr)
if len(freqs) < 200:
  semilogy(freqs[0:len(freqs):2],pwrl,'.', label="LSB")
  semilogy(freqs[1:len(freqs):2],pwru,'.', label="USB")
xlabel("Frequency (MHz)")
title("Gain = "+str(gain))
xlim(start-step,end+step)
grid()
legend(numpoints=1)
savefig("Figures/scan_%06.1f-%06.1fMHz.png" % (start,end))
figure(2)
subplot(1,2,1)
hist(signll,bins=100)
grid()
title("LSB")
subplot(1,2,2)
hist(signlu,bins=100)
grid()
title("USB")
savefig("Figures/samples_%06.1f-%06.1fMHz.png" % (start,end))
show()

