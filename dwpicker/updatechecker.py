import re
import webbrowser
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen  # python2

from maya import cmds

from dwpicker.dialog import UpdateAvailableDialog
from dwpicker.appinfos import VERSION
from dwpicker.optionvar import CHECK_FOR_UPDATE


APPINFOS_URL = (
    'https://raw.githubusercontent.com/DreamWall-Animation/dwpicker/main/'
    'dwpicker/appinfos.py')
LATEST_RELEASE_URL = (
    'https://github.com/DreamWall-Animation/dwpicker/releases/latest')
VERSION_PATTERN = r'\d(\.|,).\d(\.|,).\d'


def warn_if_update_available():
    if not cmds.optionVar(query=CHECK_FOR_UPDATE):
        return
    try:
        appinfos = urlopen(APPINFOS_URL).read().decode()
        latest_version_str = re.search(VERSION_PATTERN, appinfos)[0]
        latest_version = tuple(
            int(n) for n in latest_version_str.replace(',', '.').split('.'))
        if VERSION < latest_version:
            if UpdateAvailableDialog(latest_version_str).exec_():
                webbrowser.open(LATEST_RELEASE_URL)
    except BaseException:
        print('DwPicker: could not check for new version')
