import maya.cmds as mc
import maya.OpenMayaUI as omui
import importlib

from PySide2 import QtCore
from PySide2 import QtWidgets

import util.kt_widgets as ktW
importlib.reload(ktW)


class kt_randomizer(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(kt_randomizer, self).__init__(parent)

        self.setWindowTitle("Randomizer")
        self.setFixedSize(510, 100)

        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint) #Remove the ? button

        self.createWidgets()
        self.createLayouts()

    def createWidgets(self):
        self.selBTN = QtWidgets.QPushButton("New Sel")
        self.selBTN.setFixedWidth(70)
        self.selSLD = ktW.ktRangeSlider(devValue=1, minValue=0, maxValue=1, showMinMaxField=False, stepSize=0.1, sliderWidth=100)
        self.resultBTN = QtWidgets.QPushButton("New Result")
        self.retouchBTN = QtWidgets.QPushButton("Retouch")
        self.clearBTN = QtWidgets.QPushButton("Clear")
        self.clearBTN.setFixedWidth(50)

        # --------------------------------------------
        self.optionsCMB = QtWidgets.QComboBox()
        self.optionsCMB.addItem('Translate')
        self.optionsCMB.addItem('Rotate')
        self.optionsCMB.addItem('Scale')
        self.xCB = QtWidgets.QCheckBox()
        self.yCB = QtWidgets.QCheckBox()
        self.zCB = QtWidgets.QCheckBox()
        self.translateSLD = ktW.ktRangeSlider(textWidth=55)


    def createLayouts(self):
        
        mainLayout = QtWidgets.QVBoxLayout(self)
        
        mainGridLYT = QtWidgets.QGridLayout(self)
        mainGridLYT.addWidget(self.selBTN, 0,0)
        mainGridLYT.addWidget(self.selSLD, 0,1)
        mainGridLYT.addWidget(self.resultBTN, 0,2)
        mainGridLYT.addWidget(self.retouchBTN, 0,3)
        mainGridLYT.addWidget(self.clearBTN, 0,4)

        """ Transformation Grid """
        coordGridLYT = QtWidgets.QGridLayout(self)
        coordGridLYT.setAlignment(QtCore.Qt.AlignCenter)
        coordGridLYT.addWidget(QtWidgets.QLabel('X'), 0,1, alignment=QtCore.Qt.AlignCenter)
        coordGridLYT.addWidget(QtWidgets.QLabel('Y'), 0,2, alignment=QtCore.Qt.AlignCenter)
        coordGridLYT.addWidget(QtWidgets.QLabel('Z'), 0,3, alignment=QtCore.Qt.AlignCenter)
        coordGridLYT.addWidget(QtWidgets.QLabel('Range'), 0,4)
        coordGridLYT.addWidget(QtWidgets.QLabel('Min'), 0,8)
        coordGridLYT.addWidget(QtWidgets.QLabel('Max'), 0,9)

        coordGridLYT.addWidget(self.optionsCMB, 1,0)
        coordGridLYT.addWidget(self.xCB, 1,1)
        coordGridLYT.addWidget(self.yCB, 1,2)
        coordGridLYT.addWidget(self.zCB, 1,3)
        coordGridLYT.addWidget(self.translateSLD, 1,4,1,6)


        mainLayout.addLayout(mainGridLYT)
        mainLayout.addLayout(coordGridLYT)

        self.setLayout(mainLayout)



    def printHelloName(self):
        pass
