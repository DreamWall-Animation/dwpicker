"""
A developper hack to reload the Dreamwall picker without having to restart
Maya each time.
"""


# If the picker is not in a known PYTHONPATH.
import sys
sys.path.insert(0, "<dwpicker path>")

# Code to clean modules and relaunch a Dreamwall picker with updated code.
try:
    # Important step to not let some callbacks left behind.
    dwpicker.close()
except:
    pass

for module in list(sys.modules):
    if "dwpicker" in module:
        print("deleted: " + module)
        del sys.modules[module]

import dwpicker
dwpicker.show()
