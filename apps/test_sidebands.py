"""
Tests the sideband separation function by comparing the LSB and USB averages
to bar graph spectra taken with various resolutions from 4 to 16 channels.
"""
from rtlsdr import *
from pylab import *

from Data_Reduction import sideband_separate, unpack_to_complex


rawdata = get_sdr_samples()

# Now do something with the data
colors  =['y','r','g','b','m','c','w']
fig = figure()
data = unpack_to_complex(rawdata)
datalen = len(data)
lsb,usb = sideband_separate(data)
factor = 1024./datalen
bar([0,500], [(lsb**2).sum()*factor,(usb**2).sum()*factor],
    width=500, color=colors[0], label="LSB,USB")
for num_bins in [4,8,16]:
  avg = zeros(num_bins)
  for index in range(0,64,num_bins):
    dataslice = data[index:index+num_bins]
    xform = fft(dataslice)
    spectrum = fftshift(xform)
    avg += abs(spectrum*conj(spectrum))
  avg *= 64./num_bins
  print avg
  freqs = arange(0,1000,1000./num_bins)
  bar(freqs, avg, width=1000./num_bins, color=colors[int(log2(num_bins))], label=str(num_bins))
legend(numpoints=1)
xlabel("Frequency (kHz)")
show()

