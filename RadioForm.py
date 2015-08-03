"""
"""
import HTMLgen
import time
import logging

module_logger = logging.getLogger(__name__)

from HTMLgen.StickyForm import StickyForm, FormState

def radioform(doctitle=None, fmin='25', fmax='1725', sdrID=None, gains=[],
              default_gain=496, cgi=None, homedir="./", devices=None,
              report=None, state=None):
  """
  Frequencies must be converted to Hz before sending to RTLSDR
  """
  module_logger.info("radioform: doctitle: %s", doctitle)
  module_logger.info("radioform: entered with state: %s", state)
  doc = HTMLgen.BasicDocument()
  doc.title = doctitle
  # Preamble to the form
  doc.append(HTMLgen.Heading(1, "SDR Scanner", align='center'))
  doc.append(HTMLgen.Heading(4, time.ctime(), align='center'))
  doc.append_file(homedir+'radioform-pre.html')
  doc.append(HTMLgen.HR())

  # A Sticky form can save its state and recall it.
  F = StickyForm('http://localhost/cgi-bin/'+cgi, state=state)
  module_logger.info("radioform: created form with state: %s", state)
  
  if state.has_key("debug"):
    if state['debug'] == 'on':
      debug_check = HTMLgen.Input(type="checkbox", name="debug",
                                  llabel="Debug output", checked=True)
    else:
      debug_check = HTMLgen.Input(type="checkbox", name="debug",
                                  llabel="Debug output", checked=False)
  else:
    debug_check = HTMLgen.Input(type="checkbox", name="debug",
                              llabel="Debug output") # default state if 'off'
  module_logger.info("radioform: added debug_check with state: %s", state)
  F.append(debug_check, HTMLgen.BR())
  F.with_state(debug_check)
  module_logger.info("radioform: added debug_check state: %s", state)


  if report:
    for line in report.split('\n'):
      F.append(HTMLgen.Text(line),
               HTMLgen.BR())
    F.append(HTMLgen.HR())

    # Device select widget
  if devices:
    F.append(HTMLgen.Text("SDR: "))
    if sdrID:
      F.append(HTMLgen.Select(devices, name='SDR', value=devices[sdrID],
                              size=1, multiple=False))
    else:
      F.append(HTMLgen.Select(devices, name='SDR', size=1, multiple=False))
  else:
    F.append(HTMLgen.Text("No SDRs available"))

  # Gain select widget
  gain_select = HTMLgen.Select(gains, name='gain', size=1, multiple=False) # ,
  #                            selected=[default_gain])
  F.append(HTMLgen.Text("Gain"), gain_select, HTMLgen.BR())
  F.with_state(gain_select)

  # All the following widgets are on the same 'line'
  rfbw = min((float(fmax)-float(fmin))/500., 2.5) # must be converted to Hz
  F.append(HTMLgen.Input(type='text', name='fmin', value=str(fmin), size=5,
                         llabel="Min. frequency", rlabel="MHz,"),
           HTMLgen.Text("         "),
           HTMLgen.Input(type='text', name='fmax', value=str(fmax), size=5,
                         llabel="Max. frequency", rlabel="MHz,"),
           HTMLgen.Text("         "),
           HTMLgen.Input(type='text', name='rfbw', value=("%7.2f" % rfbw),
                         size=7, llabel="Resolution", rlabel="MHz"),
           HTMLgen.BR())
  F.submit = HTMLgen.Input(type='submit', name='action', value='Scan',
                           onClick="/tmp/get_device_ID.sh")
  doc.append(F)

  doc.append(HTMLgen.HR())
  doc.append_file(homedir+'radioform-post.html')
  return doc
  