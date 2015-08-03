from struct import *
from pylab import *

fd = open("/tmp/capture.bin","r")
buf = fd.read()
fd.close()

rawdata = unpack(str(len(buf))+'b', buf)
figure()
hist(rawdata, bins=100)
show()