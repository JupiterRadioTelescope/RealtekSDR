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
