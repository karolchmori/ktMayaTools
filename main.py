import maya.cmds as mc
import maya.OpenMayaUI as omui
import sys
import os
import importlib

from PySide2 import QtCore
from PySide2 import QtWidgets

from shiboken2 import wrapInstance

script_dir = "E:\KATPC\Programming\ktMayaTools\ktMayaTools"
if script_dir not in sys.path:
    sys.path.append(script_dir)

import util
import kt_randomizer
import kt_popconstraint

importlib.reload(util)
importlib.reload(kt_randomizer)
importlib.reload(kt_popconstraint)


def mayaMainWindow():
    mainWindowPTR = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPTR), QtWidgets.QWidget)

class MainWindow(QtWidgets.QWidget):

    WINDOW_TITLE = "ktMayaTools"

    def __init__(self, parent=mayaMainWindow()):
        super(MainWindow, self).__init__(parent)

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setWindowFlags(QtCore.Qt.WindowType.Window)

        self.setMinimumSize(300, 200)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        self.test1SLD = util.kt_widgets.ktRangeSlider()

        self.randomizerBTN = QtWidgets.QPushButton("Randomizer Tool")
        self.popconsBTN = QtWidgets.QPushButton("Pop Constraint Tool")


    def create_layout(self):
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addWidget(QtWidgets.QLabel("Custom Widgets: "))
        mainLayout.addWidget(self.test1SLD)


        mainLayout.addWidget(self.randomizerBTN)
        mainLayout.addWidget(self.popconsBTN)

        self.setLayout(mainLayout)

    def create_connections(self):
        self.randomizerBTN.clicked.connect(self.openRandomizerTool)
        self.popconsBTN.clicked.connect(self.openPOPConstraintTool)

    def openRandomizerTool(self):
        randDLG = kt_randomizer.kt_randomizer(parent=self) 
        randDLG.show() 

    def openPOPConstraintTool(self):
        popcDLG = kt_popconstraint.createUI()
        popcDLG.show() 



if __name__ == "__main__":
    # Create 
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = MainWindow() 
    window.show()