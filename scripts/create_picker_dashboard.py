

picker_files = (
    r"c:\Users\Lionel\Downloads\swisstransfer_92887b0f-7703-4685-b90c-fbc1b59c242c\CHR_Acu.json",
    r"c:\Users\Lionel\Downloads\swisstransfer_92887b0f-7703-4685-b90c-fbc1b59c242c\CHR_Bibi.json",
    r"c:\Users\Lionel\Downloads\swisstransfer_92887b0f-7703-4685-b90c-fbc1b59c242c\CHR_BirdPigeonA.json",
)

from PySide2 import QtCore, QtWidgets
import json
from dwpicker.picker import PickerView
from dwpicker.dashbord import DashboardDisplay
from dwpicker.qtutils import maya_main_window, set_shortcut
from dwpicker.compatibility import ensure_retro_compatibility
pickers = []


layout_data = {
    'grid_width': 16,
    'grid_height': 16,
    'widgets_rectangles': [
        (0, 0, 11, 16),
        (11, 0, 5, 9),
        (11, 9, 5, 7)]
}


for picker in picker_files:
    with open(picker, 'r') as f:
        data = json.load(f)
        data = ensure_retro_compatibility(data)
        view = PickerView(editable=False)
        view.register_callbacks()
        view.set_picker_data(data)
        view.reset()
        set_shortcut('F', view, view.reset)
        pickers.append(view)


dashboard = DashboardDisplay(maya_main_window())
dashboard.setWindowFlags(QtCore.Qt.Window)
layout = dashboard.grid

splitter1 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
splitter1.addWidget(pickers[1])
splitter1.addWidget(pickers[2])
splitter2 = QtWidgets.QSplitter()
splitter2.addWidget(pickers[0])
splitter2.addWidget(splitter1)


# Spacing & margins
layout.setSpacing(5)
layout.setContentsMargins(0, 0, 0, 0)
layout.grid_width = layout_data['grid_width']
layout.grid_height = layout_data['grid_height']

# Widgets
layout.clear()
for picker in pickers:
    layout.addWidget(picker)
layout.rects = layout_data['widgets_rectangles']
dashboard.show()

