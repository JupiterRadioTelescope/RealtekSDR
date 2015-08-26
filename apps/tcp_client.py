import socket
from struct import *
from numpy import array
from RealtekSDR.Signals import unpack_to_complex

TCP_IP = '127.0.0.1'
TCP_PORT = 1234
BUFFER_SIZE = 1024
MESSAGE = "Hello, World!"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
run = True
while run:
  buf = s.recv(BUFFER_SIZE)
  print buf[:4]
  try:
    buf = s.recv(BUFFER_SIZE)
    rawdata = unpack(str(len(buf))+'b', buf)
    data = unpack_to_complex(array(rawdata))
    print "received data:", data
  except KeyboardInterrupt:
    s.close()
    run=False


