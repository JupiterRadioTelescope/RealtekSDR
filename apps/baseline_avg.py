"""
The data files consist of rows with (freq, power) pairs. There are 64 pairs for
each spectrum.  The spectra are taken so that the frequencies increase
monotonically.  The number of rows must be n*64, where n is the number of
spectra.
"""
from pylab import *
from numpy.polynomial.chebyshev import chebfit, chebval
from cPickle import dump, load
from support.text import select_files, user_input

files = select_files("baselines_*MHz.dat","Select one file by number: ")
data = loadtxt(files)
nrows,ncols = data.shape
if nrows % 64:
  raise RuntimeError("%d rows is not a multiple of 64" % nrows)
num_spectra = nrows/64
use_spectra = user_input("Select spectra",range(num_spectra)).split(',')

avg = zeros(64)
for spectrum in use_spectra:
  base_index = int(spectrum)*64
  for index in range(64):
    avg[index] += data[base_index+index,1]
averages = avg/num_spectra
# normalize the spectrum
mean = averages.mean()
averages /= mean
# fit the normalized spectrum
freqs = data[:64,0] - data[:64,0].mean()
coefs = chebfit(freqs,averages,11)
model = chebval(freqs,coefs)

freqstep = freqs[1]-freqs[0]
bandwidth = freqs[-1]-freqs[0]+freqstep
coeffile = open("baseline_coefs.pkl","rb")
try:
  coef_dict = load(coeffile)
  print "Loaded:",coef_dict.keys()
except EOFError:
  print "Empty coefficients file"
coeffile.close()
try:
  coef_dict[bandwidth] = coefs
except NameError:
  coef_dict = {bandwidth: coefs}
print "Dumping:",coef_dict.keys()
coeffile = open("baseline_coefs.pkl","wb")
dump(coef_dict, coeffile)
coeffile.close()

plot(freqs,averages,'.')
plot(freqs,model)
title(str(bandwidth)+" MHz Bandwidth")
xlabel("Frequency (MHz)")
ylabel("Normalized Power")
grid()
savefig("Figures/baseline-"+str(bandwidth)+".png")
show()
