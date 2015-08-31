"""
Realtek SDR TCP client class

Start the server on a remote Realtek SDR equipped host with, for example,
  rtl_tcp -a 192.168.0.13 -f 89900000 -s 200000
  
For the server commands see https://gist.github.com/simeonmiteff/3792676
"""
import socket
import errno
import logging
import struct
from struct import unpack
from numpy import arange, array, conj
from numpy.fft import fft, fftshift
from RealtekSDR.Signals import unpack_to_complex

TCP_IP = '192.168.0.13'
TCP_PORT = 1234
BUFFER_SIZE = 1024

SET_FREQUENCY = 0x01
SET_SAMPLERATE = 0x02
SET_GAINMODE = 0x03
SET_GAIN = 0x04
SET_FREQENCYCORRECTION = 0x05

logging.basicConfig()
module_logger = logging.getLogger(__name__)

class RtlTCP(object):
  """
  Adapted from class by Simeon Miteff <simeon.miteff@gmail.com> 2012
  """
  def __init__(self,samplerate=2048000,freq=89000000):
    """
    """
    self.logger = logging.getLogger(module_logger.name+".RtlTCP")
    self.remote_host = TCP_IP
    self.remote_port = TCP_PORT
    self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connected = False
    while not connected:
      try:
        self.conn.connect((self.remote_host, self.remote_port))
        self.__send_command(SET_FREQUENCY, freq)
        self.__send_command(SET_SAMPLERATE, samplerate)
        buf = self.conn.recv(BUFFER_SIZE)
        connected = True
      except socket.error as (code, msg):
        if code != errno.EINTR:
          raise Exception(msg)
    self.logger.info("__init__: connected to %s", buf[:4])
        
  def tune(self, freq):
        """
        """
        self.__send_command(SET_FREQUENCY, freq)
        
  def __send_command(self, command, parameter):
        """
        """
        cmd = struct.pack(">BI", command, parameter)
        self.conn.send(cmd)

  def grab_SDR_spectrum(self):
    """
    Grab a set of samples and compute the power spectrum
    
    Example of timing
    =================
    On server::
      rtl_tcp -a 192.168.0.13 -f 89900000 -s 200000
      Found 1 device(s).
      Found Rafael Micro R820T tuner
      Using Generic RTL2832U OEM
      Tuned to 89900000 Hz.
      listening...
      client accepted!
      set freq 89900000
      set sample rate 200000
    On client::
      In [1]: from RealtekSDR.TCPclient import RtlTCP
      In [2]: from RealtekSDR.stations import FM_freq
      In [3]: sr = 200000
      In [4]: freq = FM_freq["KCRW"]
      In [5]: sdr = RtlTCP(samplerate=sr, freq=int(freq*1e6))
      In [6]: t0 = time(); spectrum = sdr.grab_SDR_spectrum(); t1 = time()
      In [7]: t1-t0
      Out[7]: 0.0011088848114013672

    It requires 5 us to take one complex sample.  BUFFER_SIZE = 1024 means
    512 complex samples which takes 2.56 ms so we can process faster than
    the spectrum refresh rate.
    """
    not_read = True
    while not_read:
        try:
          buf = self.conn.recv(BUFFER_SIZE)
        except socket.error as (code, msg):
          if code != errno.EINTR:
            raise Exception(msg)
        if len(buf) == BUFFER_SIZE:
          rawdata = unpack(str(len(buf))+'b', buf)
          data = unpack_to_complex(array(rawdata))
          self.logger.debug("grab_SDR_spectrum: got %d", len(data))   
          xform = fft(data)
          shifted = fftshift(xform)
          spectrum = abs(shifted*conj(shifted))
          not_read = False
        elif len(buf) == 0:
          self.logger.warning("grab_SDR_spectrum: server died")
          self.conn.close()
          exit()
        else:
          self.logger.warning("grab_SDR_spectrum: short read")
    return spectrum

  def close(self):
    """
    """
    self.conn.close()
    
