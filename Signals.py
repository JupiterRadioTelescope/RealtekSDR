"""
module Data_Reduction for operations on signals
"""
from numpy import empty, log10, conj
from numpy.fft import fft, fftshift

def unpack_to_complex(rawdata):
  """
  Converts a sequence of alternating real/imag samples to complex

  @param rawdata : alternating real and imaginary bytes
  @type  rawdata : numpy array of signed int8

  @return: numpy array of complex
  """
  datalen = len(rawdata)
  real = rawdata[0:datalen:2]
  imag = rawdata[1:datalen:2]
  data = real + 1j*imag
  return data

def sideband_separate(data):
  """
  Converts a complex array time series and returns two reals with USB and LSB

  This applies a Hilbert transform to the complex data.
  """
  usb = (data.real + scipy.fftpack.hilbert(data).imag)
  lsb = (scipy.fftpack.hilbert(data).real + data.imag)
  return lsb,usb

def make_spectrogram(data, num_spec, num_bins, log=False,
                     normalizer=None):
  """
  Converts a sequence of complex samples into a spectrogram

  matplotlib specgram takes real data.  This takes complex data.
  It returns an image array.

  @param data : complex time series data
  @type  data : numpy array of complex

  @param num_spec : number of spectra along the time axis
  @type  num_spec : int

  @param num_bins : number of spectral bins along the frequency axis
  @type  num_bins : int

  @param log : flag to plot logarithm of the power
  @type  log : bool

  @param normalizer : gain normalization reference for spectra
  @type  normalizer : numpy 1D array num_bins long

  @return: 2D numpay array
  """
  subsetlen = num_spec*num_bins
  image = empty((num_spec, num_bins))
  for index in range(0, subsetlen, num_bins):
    dataslice = data[index:index+num_bins]
    xform = fft(dataslice)
    spectrum = fftshift(xform)
    if normalizer == None:
      pass
    else:
      spectrum *= normalizer
    ptr = index/num_bins
    if log:
      image[ptr] = log10(abs(spectrum*conj(spectrum)))
    else:
      image[ptr] = abs(spectrum*conj(spectrum))
  return image
