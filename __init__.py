"""
Notes
=====

USB Permissions
---------------

This file must be executed as root or with sudo unless the appropriate USB
rules are installed.  This is done as follows::

 kuiper@kuiper:/opt/rtl-sdr$ sudo cp -p rtl-sdr.rules \
                                          /etc/udev/rules.d/99-rtl-sdr.rules
 kuiper@kuiper:/etc/udev/rules.d$ sudo su -
 root@kuiper:~# udevadm control --reload-rules

Now remove and re-connect the dongle to invoke the new rule.

Frequency Range
---------------

The official Rafael R820T tuning range is 42 to 1002 MHz, as per the data
sheet.  However, the author of http://superkuh.com/rtlsdr.html claims a tuning
range from 24 to 1700 MHz.

When the specifies frequency is way off, the Library generates error messages:
[R82XX] PLL not locked!
INFO:root:   5.00 MHz, min=(-2-2j), max=0j
[R82XX] PLL not locked!
INFO:root:   6.00 MHz, min=(-2-1j), max=(1-1j)
[R82XX] PLL not locked!
INFO:root:   7.00 MHz, min=(-2-1j), max=0j
[R82XX] PLL not locked!
INFO:root:   8.00 MHz, min=(-2-1j), max=0j
[R82XX] PLL not locked!
INFO:root:   9.00 MHz, min=(-2-1j), max=(1-1j)

When the frequency is too high, an error results:
WARNING:root:1726.00 MHz, min=-128, max=127
[R82XX] No valid PLL values for 1771570000 Hz!
r82xx_set_freq: failed=-1

Between 10 and 25 MHz, no signal is seen.  I see the same between 1000 and
1400 MHz.  I'm not sure that I trust the results between 1400 and 1725 MHz.
"""
import ctypes as ct
import struct
from numpy import arange, array
from time import sleep
import logging

from RealtekSDR.Data_Reduction import sideband_separate, unpack_to_complex

module_logger = logging.getLogger(__name__)

DEFAULT_BUF_LENGTH = 16 * 16384 # used by librtlsdr and apps in /opt/rtl-sdr.
rtlsdrlib = ct.CDLL("/usr/local/lib/librtlsdr.so")

############################## object typing ##################################

get_dev_str = rtlsdrlib.rtlsdr_get_device_usb_strings
get_dev_str.argtypes = [ct.c_int, ct.c_char_p, ct.c_char_p, ct.c_char_p]
get_dev_str.restype = ct.c_int

get_dev_nam = rtlsdrlib.rtlsdr_get_device_name
get_dev_nam.restype = ct.c_char_p
get_dev_nam.argtypes = [ct.c_int]

class RtlSdrDevStr(ct.Structure):
  """
  The parent library has defined a type called 'rtlsdr_dev' in
  /opt/rtl-sdr/src/librtlsdr.c.  It is very complicated but we don't
  plan to use its components.  We just need a generic Python class to
  represent it so we can use it as an argument in library calls.
  """
  _fields_ = []

dev_open = rtlsdrlib.rtlsdr_open
dev_open.argtypes = [ct.POINTER(ct.POINTER(RtlSdrDevStr)), ct.c_int]
dev_open.restype = ct.c_int

get_f = rtlsdrlib.rtlsdr_get_center_freq
get_f.restype = ct.c_int
get_f.argtypes = [ct.POINTER(RtlSdrDevStr)]

set_f = rtlsdrlib.rtlsdr_set_center_freq
set_f.restype = ct.c_int
set_f.argtypes = [ct.POINTER(RtlSdrDevStr),ct.c_int]

get_samp_rate = rtlsdrlib.rtlsdr_get_sample_rate
get_samp_rate.restype = ct.c_int
get_samp_rate.argtypes = [ct.POINTER(RtlSdrDevStr)]

set_samp_rate = rtlsdrlib.rtlsdr_set_sample_rate
set_samp_rate.restype = ct.c_int
set_samp_rate.argtypes = [ct.POINTER(RtlSdrDevStr), ct.c_int]

get_g = rtlsdrlib.rtlsdr_get_tuner_gain
get_g.restype = ct.c_int
get_g.argtypes = [ct.POINTER(RtlSdrDevStr)]

set_g = rtlsdrlib.rtlsdr_set_tuner_gain
set_g.restype = ct.c_int
set_g.argtypes = [ct.POINTER(RtlSdrDevStr), ct.c_int]

set_gm = rtlsdrlib.rtlsdr_set_tuner_gain_mode
set_gm.restype = ct.c_int
set_gm.argtypes = [ct.POINTER(RtlSdrDevStr), ct.c_int]

gtg = rtlsdrlib.rtlsdr_get_tuner_gains
gtg.argtypes = [ct.POINTER(RtlSdrDevStr),ct.POINTER(None)]
gtg.restype = ct.c_int

reset_buf = rtlsdrlib.rtlsdr_reset_buffer
reset_buf.restype = ct.c_int
reset_buf.argtypes = [ct.POINTER(RtlSdrDevStr)]

read_sync = rtlsdrlib.rtlsdr_read_sync
read_sync.restype = ct.c_int
read_sync.argtypes = [ct.POINTER(RtlSdrDevStr), ct.c_void_p,
                          ct.c_int, ct.POINTER(ct.c_int)]

rtlsdr_close = rtlsdrlib.rtlsdr_close
rtlsdr_close.argtypes = [ct.POINTER(RtlSdrDevStr)]
rtlsdr_close.restype = ct.c_int

######################### libusb errors ###################################

# Documented in http://libusb.sourceforge.net/api-1.0/group__misc.html

LIBUSB_ERROR_IO = -1,
LIBUSB_ERROR_INVALID_PARAM = -2,
LIBUSB_ERROR_ACCESS = -3,
LIBUSB_ERROR_NO_DEVICE = -4,
LIBUSB_ERROR_NOT_FOUND = -5,
LIBUSB_ERROR_BUSY = -6,
LIBUSB_ERROR_TIMEOUT = -7,
LIBUSB_ERROR_OVERFLOW = -8,
LIBUSB_ERROR_PIPE = -9,
LIBUSB_ERROR_INTERRUPTED = -10,
LIBUSB_ERROR_NO_MEM = -11,
LIBUSB_ERROR_NOT_SUPPORTED = -12,
LIBUSB_ERROR_OTHER = -99,

libusb_error_text = {
  -1:"libusb input/output error",
  -2:"libusb invalid parameter",
  -3:"access denied (insufficient permissions)",
  -4:"no device found (disconnected?)",
  -5:"entity not found",
  -6:"resource busy",
  -7:"operation timed out",
  -8:"overflow",
  -9:"pipe error",
  -10:"system call interrupted (signal?)",
  -11:"insufficient memory",
  -12:"operation not supported"
}
########################## Classes ############################################

class RtlSdrException(Exception):
  """
  Exception class for rtlsdr module
  """
  def __init__(self, value=None, details=None):
    """
    Creates an instance of RtlSdrException()
    """
    self.value = value
    self.details = details
    
  def __str__(self):
    """
    RtlSdrException() instance message
    """
    msg = "error"
    if self.value:
      msg += " " + repr(self.value)
    if self.details:
      msg += ": " + self.details
    return repr(msg)

class RtlSdr(object):
  """
  Class to represent a RealTek-based SDR.
  
  Public attribute::

   devp        - ptr to the 'rtlsdr_dev' structure provided by the C library
   blk_size    - default size of block read
   gain        - gain; gain=0 means AGC
   manual_gain - gain set automatically if False (default)
   cf          - center frequency
   samplerate  - number of complex samples per sec (= bandwidth)
  """
  def __init__(self, dev_ID, dflt_blk_size=DEFAULT_BUF_LENGTH):
    """
    Creates an RtlSdr instance.

    When we call '_open' the C library creates a structure instance and
    associates a pointer with it.  It returns a pointer to the pointer.

    @param dev_ID : device numeric ID
    @type  dev_ID : int
    """
    self.devp = self._open(dev_ID)
    self.blk_size = dflt_blk_size

  def _open(self, dev_ID):
    """
    This creates an alias for the library 'rtlsdr_open' function and defines
    the types of the arguments and the return value type. The first argument
    is a pointer to the pointer in which the C library returns a pointer to
    the 'rtlsdr_dev' structure associated with the device whose number is
    given by the second arguemnt.

    @param dev_ID : device numeric ID
    @type  dev_ID : int

    @return: pointer to a RtlSdrDevStr instance
    """
    # create an instance of the device structure
    dev = RtlSdrDevStr()
    # we get a pointer to this instance
    devp = ct.pointer(dev)
    # open returns a pointer to the pointer where the struct is defined
    status = dev_open(devp, dev_ID)
    if status == -6:
      raise RtlSdrException("", "SDR is already open")
    elif status:
      raise RtlSdrException(status, "error return in RtlSdr open")
    # now that we have a pointer to the struct instance we can ask the device
    # defined by that struct for various things
    self.manual_gain = False
    return devp

  def get_freq(self):
    """
    Gets the SDR center frequency

    @return: int, frequency in Hz
    """
    self.cf = get_f(self.devp)
    return self.cf

  def set_freq(self,cf):
    """
    Sets the SDR center frequency

    @param cf : center frequency in Hz
    @type  cf : int

    @return: int, frequency in Hz
    """
    status = set_f(self.devp, cf)
    if status:
      raise RtlSdrException(status, "error return in set_freq")
    return self.get_freq()

  def get_samplerate(self):
    """
    Get the SDR sampling rate

    @return: int, sampling rate in Hz
    """
    self.samplerate = float(get_samp_rate(self.devp))
    return self.samplerate

  def set_samplerate(self, sr):
    """
    Set the SDR sampling rate

    @param sr : sampling rate in Hz
    @type  sr : int

    @return: int, sampling rate in Hz
    """
    status = set_samp_rate(self.devp, sr)
    if status:
      raise RtlSdrException(status, "error return in set_samplerate")
    return self.get_samplerate()

  def get_gain(self):
    """
    Get the current tuner gain value

    @return: int, gain
    """
    self.gain = get_g(self.devp)
    return self.gain
    
  def set_gain(self, gain):
    status = set_g(self.devp, gain)
    if status:
      raise RtlSdrException(status, "error return in set_gain")
    self.gain = self.get_gain()

  def set_gain_manual(self, manual):
    """
    This is not necessary.  It is done automatically depending on the value of
    'gain' in 'set_gain'.
    """
    status = set_gm(self.devp, int(manual))
    if status:
      raise RtlSdrException(status, "error return in set_gain_mode")
    self.manual_gain = manual
    
  def reset_buffer(self):
    """
    The tuner has a pointer which tells the device where to write the data and
    we need to reset it to zero to take fresh data.

    @return: True if successful
    """
    status = reset_buf(self.devp)
    if status:
      raise RtlSdrException(status, "error return in reset_buffer")
    return True

  def synch_read(self, num=None):
    """
    Request a read operation and wait for the results

    @param num : number of samples
    @type  num : int
    """
    # create a buffer to hold the data
    if num == None:
      num = self.blk_size
    module_logger.debug("synch_read: requesting %d samples", num)
    buf = ct.create_string_buffer(num)
    # create a pointer to the integer which records how many bytes were read
    # note that invoking the type as a class creates an instance of an int
    nreadp = ct.pointer(ct.c_int())
    # Now we read from the device
    status = read_sync(self.devp, buf, num, nreadp)
    if status:
      if libusb_error_text.has_key(status):
        raise RtlSdrException(status, libusb_error_text[status])
      else:
        raise RtlSdrException(status, "error return in synch_read")
    datalen = nreadp.contents.value
    module_logger.debug("synch_read: got %d samples", datalen)
    # now decode the data
    try:
      unsigned_data = struct.unpack(str(datalen)+'B', buf.raw)
    except Exception, details:
      module_logger.debug("synch_read: buffer length is %d", len(buf.raw))
      print buf.raw
      raise RtlSdrException(details)
    return array(unsigned_data)-128

  def get_data_block(self, num_samples=None):
    """
    """
    rawdata = self.synch_read(num=num_samples)
    if rawdata.min() < -125 or rawdata.max() > 125:
      module_logger.warning("data min=%d, max=%d",
                            rawdata.min(), rawdata.max())
    data = unpack_to_complex(rawdata)
    return data

  def get_tuner_gains(self):
    """
    Get gain values available for this tuner

    This is called once with a null pointer for the gains to get the number
    of gain values so that an array of the right length can be created. Then
    it is called again to get the actual array of gains.

    @return: list of int
    """
    n_gains = gtg(self.devp, None)
    # define an integer array type of the right length
    gains_t = ct.c_int * n_gains
    # create an instance of this array
    gains = gains_t()
    # define a pointer for this array type
    gains_p = ct.POINTER(gains_t)
    # now redefine the second argument as this type of pointer
    gtg.argtypes = [ct.POINTER(RtlSdrDevStr), gains_p]
    # now call the function passing the address of the array instance
    status = gtg(self.devp, gains)
    if status != n_gains:
      raise RtlSdrException(status, "error return in get_tuner_gains")
    gain_list = []
    for ptr in gains:
      gain_list.append(ptr)
    return gain_list
    
  def close(self):
    """
    Close the device; release it for others

    @return: True on success
    """
    status = rtlsdr_close(self.devp)
    if status:
      raise RtlSdrException(status, "error return in close")
    return True

  def state(self):
    """
    Gets the current state of the SDR

    @return: frequency, sample rate and gain as tuple of int
    """
    freq = self.get_freq()
    module_logger.info("current frequency = %d", freq)
    samp_rate = self.get_samplerate()
    module_logger.info("current sampling rate = %d",samp_rate)
    # Next we check the gain.  The default 0 means 'auto' so we leave it alone
    gain = self.get_gain()
    module_logger.info("Gain = %d",gain)
    return freq, samp_rate, gain

  def configure(self, cf, sr):
    """
    Sets the SDR center frequency and sample rate.

    @param cf : center frequency in Hz
    @type  cf : int

    @param sr : sample rate in Hz
    @type  sr : int

    @return: Center frequency and sample rate as tuple of int
    """
    centerfreq = self.set_freq(cf)
    module_logger.info("configure: new frequency = %d", centerfreq)
    samplerate = self.set_samplerate(sr)
    module_logger.info("configure: sampling rate = %d",samplerate)
    status = self.reset_buffer()
    module_logger.info("configure: reset_buffer status: %s",status)
    return centerfreq, samplerate

  def get_power_scan(self, start, end, step, gain=0):
    """
    Performs a power scan between two frequencies with a given step size.

    Returns lists with frequencies, LSB powers, USB powers, total powers,
    LSB voltages, USB voltages.

    @param start : lower end of scan in MHz.
    @type  start : float or int.

    @param end : upper end of scan in MHz.
    @type  end : float or int

    @param step : step size and sampling rate in MHz
    @type  step : float or int

    @return: tuple(freqs,pwrl,pwru,pwr,signll,signlu)
    """
    freqs = []
    signlu = []
    signll = []
    pwru = []
    pwrl = []
    pwr = []
    for freq in arange(start,end,step): # MHz
      cf = self.set_freq(int(int(freq*1000000)))
      freqs.append(cf/1e6-0.25*step)
      freqs.append(cf/1e6+0.25*step)
      status = self.reset_buffer()
      sleep(0.01)
      rawdata = self.synch_read()
      if rawdata.min() < -120 or rawdata.max() > 120:
        module_logger.warning(
                       "get_power_scan: saturating; %7.2f MHz, min=%d, max=%d",
                       cf/1.e6, rawdata.min(), rawdata.max())
      data = unpack_to_complex(rawdata)
      module_logger.debug("get_power_scan: %7.2f MHz, min=%s, max=%s",
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

################### module methods ############################################

def get_device_count():
  """
  Returns the number of RTL SDR devices on the bus
  """
  return rtlsdrlib.rtlsdr_get_device_count()

def get_devices():
  """
  Returns dict of devices with vendor,product,serial
  """
  count = get_device_count()
  if count:
    devices = {}
    for index in range(count):
      devices[index] = get_device_strings(index)
    return devices
  else:
    return None
    
def get_device_strings(dev_ID):
  """
  Returns identifying information from the SDR assigned number 'dev_ID'.
  
  Note
  ====
  The second, third and fourth arguments of the library function are return
  values so storage needs to be allocated.  We name the pointers to these
  strings.

  @param dev_ID : number of the rtlsdr device
  @type  dev_ID : int

  @return: vendor, product and serial number as tuple of str
  """
  vendor  = ct.create_string_buffer('\000'*256)
  product = ct.create_string_buffer('\000'*256)
  serial  = ct.create_string_buffer('\000'*256)
  status = get_dev_str(dev_ID, vendor, product, serial)
  if status:
    if status == -2:
      raise RtlSdrException(None,"No device connected")
    else:
      raise RtlSdrException(status, "error return in get_device_strings")
  return vendor.value, product.value, serial.value

def get_device_name(dev_ID):
  """
  Get the name of the specified RTL SDR device.
  
  @param dev_ID : number of the rtlsdr device
  @type  dev_ID : int

  @return: device name (str)
  """
  return get_dev_nam(dev_ID)

def init_sdr(dev_ID=0,
             sample_rate=1000000,
             dflt_blk_size=None):
  """
  Initialize an RtlSdr instance.

  The default block size in librtlsdr.so is 16384.
  
  @param dev_ID : number of the rtlsdr device
  @type  dev_ID : int

  @param sample_rate : sampling rate in Hz
  @type  sample_rate : int

  @param dflt_blk_size : default number of samples to grab
  @type  dflt_blk_size : int

  @return: RtlSdr instance
  """
  n = get_device_count()
  module_logger.info("init_sdr: %d devices", n)
  vendor, product, serial = get_device_strings(dev_ID)
  module_logger.info("init_sdr: Vendor: %s",vendor)
  module_logger.info("init_sdr: Product: %s",product)
  module_logger.info("init_sdr: Serial number: %s",serial)
  device = get_device_name(dev_ID)
  module_logger.info("init_sdr: Device name: %s",device)
  if dflt_blk_size:
    rtlsdr = RtlSdr(dev_ID, dflt_blk_size=dflt_blk_size)
  else:
    rtlsdr = RtlSdr(dev_ID)
  rtlsdr.set_samplerate(sample_rate)
  return rtlsdr

def get_sdr_samples(sdr=0, freq=89600000, samprate=1000000):
  """
  Utility to grab some quick data and release the SDR.

  @param sdr : SDR device numeric ID
  @type  sdr : int

  @param freq : center frequency in Hz
  @type  freq : int

  @param samprate : sample rate in Hz
  @type  samprate : int

  @return: default number of raw I and Q samples (numpy array of int)
  """
  rtlsdr = RtlSdr(sdr)
  cf = rtlsdr.set_freq(freq)
  print "current frequency =", rtlsdr.get_freq()
  sr = rtlsdr.set_samplerate(samprate)
  status = rtlsdr.reset_buffer()
  print "reset_buffer status:",status
  rawdata = rtlsdr.synch_read()
  status = rtlsdr.close()
  print "Close status:",status
  return rawdata

def show_image(image, extent):
  """
  Display a static dynamic spectrum

  @param image : 2D array of time (Y) vs frequency (X)
  @type  image : numpy array

  @param extent : limits of image axes (frequency min, max and time min, max)
  @type  extent : tuple of float
  
  @return: matplotlib Figure instance
  """
  fig = pl.figure()
  pl.imshow(image, extent=extent, aspect="auto")
  pl.grid()
  pl.xlabel("Frequency (MHz)")
  pl.ylabel("Elapsed Time (s)")
  pl.colorbar()
  return fig
  
#################### module test program ################################

if __name__ == "__main__":
  from pylab import *
  from Graphics import make_spectrogram
  from stations import FM_freq
  from cPickle import load
  from numpy.polynomial.chebyshev import chebval

  mylogger = logging.getLogger()
  logging.basicConfig()
  mylogger.setLevel(logging.DEBUG)
  
  plot_it = True
  normalize = True
  
  #cf =   88900000 # 89.9 at band edge
  #cf =   89900000 # 89.9 KCRW
  #cf =   94700000 # 94.7 KTWV
  #cf =   97500000
  #cf =   98700000 # 98.7 KYSR
  #cf =   99700000 # 98.7 at band edge
  cf =  110000000
  #cf = 25000000
  #cf = int(FM_freq['KCRW']*1e6)
  sr =    2000000

  rtlsdr = init_sdr()
  freq, samp_rate, gain = rtlsdr.state()
  centerfreq, samplerate = rtlsdr.configure(cf,sr)
  
  # Let's get some data using the synchronous read method
  rawdata = rtlsdr.synch_read()
  print "raw data samples:",rawdata[:16]
  status = rtlsdr.close()
  print "Close status:",status

  if plot_it:
    # Now do something with the data
    data = unpack_to_complex(rawdata)
    datalen = len(data)
    num_bins = 512
    num_spec = datalen/num_bins
    freqs = array(arange(centerfreq-samplerate/2,
                         centerfreq+samplerate/2,
                         samplerate/num_bins))/1e6 # MHz
    if normalize:
      coeffile = open("baseline_coefs.pkl","rb")
      coef_dict = load(coeffile)
      coeffile.close()
      coefs = coef_dict[float(sr/1e6)]
      print "Coefficients loaded"
      normalizer = 1./chebval(freqs-centerfreq/1.e6,coefs)
      image = make_spectrogram(data, num_spec, num_bins, log=True,
                               normalizer=normalizer)
    else:
      image = make_spectrogram(data, num_spec, num_bins, log=True)

    spectrum_intvl = 1/(samplerate/num_bins) # sec
    extent=(freqs[0], freqs[-1], 0, num_spec*spectrum_intvl)
    
    fig = show_image(image, extent)
    pl.savefig("Figures/wf_%5.1fMHz-%3.1f.png" % (cf/1.e6, sr/1.e6))
    pl.show()
