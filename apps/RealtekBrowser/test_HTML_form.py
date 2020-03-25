"""
Form builder for prototype program control through a web interface.

Classes and methods used::
 - SeriesDocument - primary container class for an HTML document as part of a
                    series.
 - SimpleDocument - class supporting all features of a self contained document.
 - HR             - horizontal rule
 - Form           - user filled form using the POST method; first argument is
                    the CGI
 - Select         - list or option widget.
 - Textarea       - entry widget to type multi-line text (for forms)
 - P              - <P> tag
 - Input          - password, checkbox, radio, file, submit, reset or hidden
 - BR             - one or more <BR> tags

Modules
=======
HTMLgen does a weird thing by not making supporting modules sub-directories of
the HTMLgen by including an __init__.py in the directory.  Instead, in
/usr/lib/pymodules/python2.7/ there is the HTMLgen directory and an HTMLgen.pth
which exposes additional modules::
 - barchart.py         - BarChart and StackedBarChart for positive data values.
 - colorcube.py        - functions for colored text and backgrounds
 - Formtools.py        - supporting classes to simplify Input Forms
 - GifImagePluginH.py  - 
 - HTMLcalendar.py
 - HTMLcolors.py
 - HTMLutil.py
 - ImageFileH.py
 - ImagePaletteH.py
 - imgsize.py
 - ImageH.py
 - JpegImagePluginH.py
 - NavLinks.py
 - PngImagePluginH.py

Reference
=========
file:///usr/share/doc/python-htmlgen/html/index.html
"""
import os
from Electronics.Instruments.RealtekSDR.RadioForm import radioform
import Electronics.Instruments.RealtekSDR as rltk

htmldir = os.getcwd()
print "HTML to", htmldir

devices = []
device_dict = rltk.get_devices()
if device_dict:
  for key,dev in rltk.get_devices().items():
    devices.append(dev[0]+' '+dev[1])
else:
  devices = []
if __name__ == "__main__":
  gains = [0, 9, 14, 27, 37, 77, 87, 125, 144, 157, 166, 197, 207, 229, 254,
           280, 297, 328, 338, 364, 372, 386, 402, 421, 434, 439, 445, 480,
           496]
  doc = radioform(doctitle="Radio Scanner",
                  gains=gains, default_gain=421, cgi="radio_scan.py",
                  devices=devices)
  # write the form to an HTML file
  doc.write(os.path.join(htmldir, "RadioForm.html"))