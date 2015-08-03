"""
The objective here is to enable a number of threads to operate on RF data
in a chain.  A receiver thread gets the data from the SDR.  Then various threads can process these data, such as::

  * a thread that looks for 'events' in the data;
  * a thread that demodulates the signals;
  * a thread that displays a waterfall plot; etc.

Each thread has an input queue and an output queue.  The receiver thread,
however, has only an output queue, and the last thread in the chain has no
output queue.  The generic thread both both but the first and last links
will have None for the input and output queues respectively.

The queues will all be the same length, amounting to some fixed length of
signal, e.g. one second. The number of samples will be some 2**n where
2**n = time_length * bandwidth.

A thread in the chain will be able to be paused or put to sleep, but in
that case it will continue to drain its input queue so the upstream links
are not affected.
"""
import threading
import time
import rtlsdr
import logging
import Queue
import math
from pylab import *
from Data_Reduction import unpack_to_complex

module_logger = logging.getLogger(__name__)

class BaseThread(threading.Thread):
  """
  Superclass for SDR threads.
  
  This creates a thread which can be started, terminated, suspended, put to
  sleep and resumed.

  Public attributes::

   end_flag       - True if the thread is to end
   thread_suspend - True if the thread is to be suspended
   sleep_duration - length of time the thread can be put to sleep
   thread_sleep   - True if the thread is to enter a sleep period
  """
  def __init__(self, Qin=None, Qout=None):
    """
    """
    threading.Thread.__init__(self, target=self.thread_task)
    self.end_flag = False
    self.thread_suspend = False
    self.thread_sleep = False
    self.Qin = Qin
    self.Qout = Qout
    self.logger = logging.getLogger(__name__+"."+self.name)
    module_logger.debug("%s created",self.name)

  def _pass_on(self):
    """
    Just pass on the data
    """
    if self.Qin:
      self.data = self.Qin.get()
    if self.Qin and self.Qout:
      self.Qout.put(self.data)
      
  def run(self):
    """
    """
    while self.end_flag == False:
      # Optional sleep; when sleeping just pass on the data
      if self.thread_sleep:
        if time.time() > self._sleepend:
          self.thread_sleep = False
        else:
          self._pass_on()
          return
      # always pass on the data
      self._pass_on()
      if self.thread_suspend:
        return
      else:
        try:
          self.thread_task()
        except KeyboardInterrupt:
          self.end_flag = True
    else:
      self.logger.debug("run: ends")

  def thread_task(self):
    """
    This must be implemented in the sub-class.
    """
    pass

  def terminate(self):
    """
    Thread termination routine
    """
    self.end_flag = True
  
  def set_sleep(self, duration):
    """
    """
    self.thread_sleep = True
    self._sleepend = time.time()+duration

  def suspend_thread(self):
    """
    """
    self.thread_suspend = True

  def resume_thread(self):
    """
    """
    self.thread_suspend = False

class CaptureThread(BaseThread):
  """
  Class to capture signals with SDR
  """
  def __init__(self, sdr, Qin=None, Qout=None):
    super(CaptureThread, self).__init__(Qin=Qin, Qout=Qout)
    self.sdr = sdr
    self.Qout = Qout

  def thread_task(self):
    try:
      data = self.sdr.get_data_block()
    except rtlsdr.RtlSdrException, details:
      self.logger.error("Capture failed to get data: %s",str(details))
      self.terminate()
    except KeyboardInterrupt:
      self.terminate()
    else:
      self.Qout.put(data)

class SpectrumMonitor(BaseThread):
  """
  Class to grab a dynamic spectrum

  Once created this is automatically suspended until a snapshot is
  required.  In suspended mode the thread just passes on the data.
  """
  def __init__(self, sdr, num_freqs, Qin, Qout=None):
    super(SpectrumMonitor, self).__init__()
    self.sdr = sdr
    self.Qin = Qin
    self.Qout = Qout
    self.num_freqs = num_freqs
    self.specfig, self.specaxes = subplots()
    
  def thread_task(self):
    self.data = self.Qin.get()
    if self.Qout:
      self.Qout.put(self.data)
    cmplx_data = unpack_to_complex(self.data)
    datalen = len(self.data)
    module_logger.debug("Obtained %d samples from the queue",datalen)
    num_spectra = datalen/self.num_freqs
    module_logger.debug("%d spectra will be processed",num_spectra)
    avg = zeros(self.num_freqs)
    for i in range(num_spectra-1):
      index = i*self.num_freqs
      module_logger.debug("Taking data from %d to %d",
                          index,index+self.num_freqs)
      dataslice = cmplx_data[index:index+self.num_freqs]
      module_logger.debug("spectrum has %d points", len(dataslice))
      xform = fft(dataslice)
      spectrum = fftshift(xform)
      avg += abs(spectrum*conj(spectrum))
    self.specaxis.semilogy(avg)
   
if __name__ == "__main__":
  from stations import FM_freq
   
  mylogger = logging.getLogger()
  logging.basicConfig()
  mylogger.setLevel(logging.DEBUG)

  rtlsdr.module_logger.setLevel(logging.INFO)
  
  cf = int(FM_freq['KCRW']*1e6)
  sr = 1000000
  exp_num_samp_per_decisec = round(math.log(sr/10.,2))
  blocksize = int(math.pow(2,exp_num_samp_per_decisec))
  mylogger.debug("Requested block size is %d", blocksize)
  sdr = rtlsdr.init_sdr(dflt_blk_size=blocksize)
  centerfreq, samplerate = sdr.configure(cf,sr)

  threads = []
  Qreceived = Queue.Queue()
  rcvr = CaptureThread(sdr,Qout=Qreceived)
  rcvr.start()
  mylogger.debug("CaptureThread started")
  threads.append(rcvr)
  QmonOut = Queue.Queue()
  mon = SpectrumMonitor(sdr,1024,Qreceived,Qout=QmonOut)
  mon.start()
  mylogger.debug("SpectrumMonitor started")
  threads.append(mon)
  busy = True
  while busy == True:
    try:
      mylogger.debug("Sleeping")
      time.sleep(1)
      if rcvr.end_flag:
        busy = False
        break
      mylogger.debug("Requesting data from the queue")
      print QmonOut.get()[:16]
    except KeyboardInterrupt:
      busy = False
      rcvr.terminate()
      mylogger.info("terminated")
  rcvr.join()
  mon.join()
  mylogger.info("finished")
  sdr.close()