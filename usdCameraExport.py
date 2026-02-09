import maya.cmds as mc
import maya.OpenMayaUI as omui
import re
import os

try:
    from PySide6 import QtCore, QtWidgets, QtGui
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui
    from shiboken2 import wrapInstance


def mayaMainWindow():
    mainWindowPTR = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPTR), QtWidgets.QWidget)


class usdCameraExport(QtWidgets.QDialog):
    """Dialog for exporting USD animation data with UI controls and export logic."""
    
    def __init__(self, parent=mayaMainWindow()):
        """Initialize USD Animation dialog with UI setup and data loading.

        Args:
            parent (QWidget, optional): Parent window, defaults to Maya main window.
        """
        
        super(usdCameraExport, self).__init__(parent)

        self.setWindowTitle("USD Camera")
        self.setMinimumSize(750, 220)
        
        '''
        VARIABLES
        '''
        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.loadUI()
        

    def createWidgets(self):
        """Initialize UI widgets."""

        self.seqTXT = QtWidgets.QLineEdit()
        self.seqTXT.setReadOnly(True)
        self.shotTXT = QtWidgets.QLineEdit()
        self.shotTXT.setReadOnly(True)
        
        self.frameMinTXT = QtWidgets.QLineEdit()
        self.frameMaxTXT = QtWidgets.QLineEdit()
        self.frameResetBTN = QtWidgets.QPushButton()
        self.frameResetBTN.setIcon(QtGui.QIcon(":clockwise.png"))
        self.frameResetBTN.setIconSize(QtCore.QSize(20, 20))

        self.charCB = QtWidgets.QCheckBox("Character")
        self.charCB.setChecked(True)
        self.charPriorityCMB = QtWidgets.QComboBox()
        self.charPriorityCMB.addItems(["MODEL","SKINNED"])
        self.charPriorityCMB.setFixedSize(90, 20)
        self.charPathTXT = QtWidgets.QLineEdit()
        self.charPathTXT.setReadOnly(True)
        self.charPathBTN = QtWidgets.QPushButton()
        self.charPathBTN.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.charPathBTN.setFixedSize(40, 30)
        self.charPathBTN.setToolTip("Select Character Export directory")
        self.charVersionCMB = QtWidgets.QComboBox()


        self.camCB = QtWidgets.QCheckBox("Camera")
        self.camCB.setChecked(True)
        self.camPathTXT = QtWidgets.QLineEdit()
        self.camPathTXT.setReadOnly(True)
        self.camPathBTN = QtWidgets.QPushButton()
        self.camPathBTN.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.camPathBTN.setFixedSize(40, 30)
        self.camPathBTN.setToolTip("Select Camera Export directory")
        self.camVersionCMB = QtWidgets.QComboBox()

        self.exportBTN = QtWidgets.QPushButton("Export")
        


    def createLayouts(self):
        """Arrange widgets in layouts."""

        mainLayout = QtWidgets.QVBoxLayout(self)
    
        """ SWAP LAYOUT """
        self.shotInfoLYT = QtWidgets.QHBoxLayout(self)
        self.shotInfoLYT.addWidget(QtWidgets.QLabel('SQ: '))
        self.shotInfoLYT.addWidget(self.seqTXT)
        self.shotInfoLYT.addWidget(QtWidgets.QLabel('SH: '))
        self.shotInfoLYT.addWidget(self.shotTXT)
        self.shotInfoLYT.addWidget(QtWidgets.QLabel('Frame Range: '))
        self.shotInfoLYT.addWidget(self.frameMinTXT)
        self.shotInfoLYT.addWidget(self.frameMaxTXT)
        self.shotInfoLYT.addWidget(self.frameResetBTN)


        self.exportLYT = QtWidgets.QGridLayout()
        self.exportLYT.addWidget(self.charCB,0,0,1,2)
        self.exportLYT.addWidget(QtWidgets.QLabel('Tag'),1,0)
        self.exportLYT.addWidget(self.charPriorityCMB,1,1)
        
        self.exportLYT.addWidget(QtWidgets.QLabel('Path'),2,0)
        self.exportLYT.addWidget(self.charPathTXT, 2,1)
        self.exportLYT.addWidget(self.charPathBTN, 2,2)
        self.exportLYT.addWidget(self.charVersionCMB, 2,3)
        

        self.exportLYT.addWidget(self.camCB,3,0,1,2)
        self.exportLYT.addWidget(QtWidgets.QLabel('Path'),4,0)
        self.exportLYT.addWidget(self.camPathTXT, 4,1)
        self.exportLYT.addWidget(self.camPathBTN, 4,2)
        self.exportLYT.addWidget(self.camVersionCMB, 4,3)
        

        """ MAIN LAYOUT """
        mainLayout.addLayout(self.shotInfoLYT)
        mainLayout.addLayout(self.exportLYT)
        mainLayout.addWidget(self.exportBTN)
        self.setLayout(mainLayout)
        
        
    def createConnections(self):
        """Connect signals to their slots."""
        pass



if __name__ == "__main__":
    # Create 
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = usdCameraExport() 
    window.show()