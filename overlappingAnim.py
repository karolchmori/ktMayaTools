import maya.cmds as mc
import maya.OpenMayaUI as omui
import re
import os


from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtGui

from shiboken6 import wrapInstance

def mayaMainWindow():
    mainWindowPTR = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPTR), QtWidgets.QWidget)

class overlappingAnim(QtWidgets.QDialog):
    """Dialog for exporting USD animation data with UI controls and export logic."""
    
    def __init__(self, parent=mayaMainWindow()):
        
        super(overlappingAnim, self).__init__(parent)

        self.setWindowTitle("Overlapping Animation")
        self.setMinimumSize(400, 100)
        
        '''
        VARIABLES
        '''
        self.createWidgets()
        self.createLayouts()
        self.createConnections()


    def createWidgets(self):
        self.selectedTXT = QtWidgets.QLineEdit()
        self.selectedTXT.setReadOnly(True)
        self.loadBTN = QtWidgets.QPushButton("Load")
        self.createBTN = QtWidgets.QPushButton("Create system")
        self.deleteBTN = QtWidgets.QPushButton("Delete system")
        

    def createLayouts(self):
        mainLayout = QtWidgets.QVBoxLayout(self)

        self.hierarchyLYT = QtWidgets.QHBoxLayout(self)
        self.hierarchyLYT.addWidget(QtWidgets.QLabel('Hierarchy Control: '))
        self.hierarchyLYT.addWidget(self.selectedTXT)
        self.hierarchyLYT.addWidget(self.loadBTN)


        self.actionsLYT = QtWidgets.QGridLayout()
        self.actionsLYT.addWidget(self.createBTN,0,0,1,2)
        self.actionsLYT.addWidget(self.deleteBTN,0,2)

        mainLayout.addLayout(self.hierarchyLYT)
        mainLayout.addLayout(self.actionsLYT)
        
        mainLayout.addStretch()
        self.setLayout(mainLayout)
        

    def createConnections(self):
        self.createBTN.clicked.connect(self.onClick_createBTN)
        self.deleteBTN.clicked.connect(self.onClick_deleteBTN)

    def onClick_createBTN(self):
        pass

    def onClick_deleteBTN(self):
        pass
    




if __name__ == "__main__":
    # Create 
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = overlappingAnim() 
    window.show()