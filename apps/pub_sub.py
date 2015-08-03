"""
The objective here is to enable a number of separate threads to operate on the
same RF data. A receiver thread gets the data from the SDR.  Then various threads can process these data, such as::

  * a thread that looks for 'events' in the data;
  * a thread that demodulates the signals;
  * a thread that displays a waterfall plot; etc.

Each thread has an input queue.  It is registered with the receiver thread.
The receiver thread keeps a list of output queues that are these registered
input queues. The generic thread both an inpute and an outpute queue.  This
enables a client thread to pass processed data to another thread.

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
