import maya.cmds as mc
import maya.OpenMayaUI as omui
import os

from PySide2 import QtCore
from PySide2 import QtWidgets

from shiboken2 import wrapInstance

def mayaMainWindow():
    mainWindowPTR = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPTR), QtWidgets.QWidget)


class kt_modelingHelper(QtWidgets.QDialog):
    def __init__(self, parent=mayaMainWindow()):
        super(kt_modelingHelper, self).__init__(parent)

        self.setWindowTitle("Texture Helper")
        #self.setFixedSize(450, 150)

        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint) #Remove the ? button

        '''
        VARIABLES
        '''
        self.objData = {}

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):

        '''
        SWAP
        '''

        self.swapGRB = QtWidgets.QGroupBox("Swap")

        self.oldShaderCMB = QtWidgets.QComboBox()
        self.oldShaderCMB.addItem('lambert')
        self.oldShaderCMB.addItem('aiStandardSurface')
        self.oldShaderCMB.addItem('Phong')

        self.newShaderCMB = QtWidgets.QComboBox()
        self.newShaderCMB.addItem('lambert')
        self.newShaderCMB.addItem('aiStandardSurface')
        self.newShaderCMB.addItem('Phong')
        self.newShaderCMB.setCurrentIndex(1)

        self.swapBTN = QtWidgets.QPushButton("GO")
        self.swapBTN.setFixedWidth(70)

        '''
        FUSE PLACE 2D TEXTURE
        '''
        self.fuse2dGRB = QtWidgets.QGroupBox("Fuse place2dTexture - Select Files")
        self.fuse2dBTN = QtWidgets.QPushButton("GO")

        '''
        CONNECT BY FILE NODE NAME
        '''
        self.connectNodesGRP = QtWidgets.QGroupBox("Connect by nodes")
        self.connectLoadNodesBTN = QtWidgets.QPushButton("Load Nodes")
        self.connectBTN = QtWidgets.QPushButton("GO")
        self.connectTBL = QtWidgets.QTableWidget()
        self.connectTBL.setColumnCount(2)
        self.connectTBL.setHorizontalHeaderLabels(["Attribute", "Value"])
        self.connectTBL.horizontalHeader().setStretchLastSection(True)
        self.connectTBL.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.connectTBL.verticalHeader().setVisible(False)

    def createLayouts(self):
        
        mainLayout = QtWidgets.QVBoxLayout(self)
    
        """ SWAP LAYOUT """
        shaderGridLYT = QtWidgets.QGridLayout(self)
        shaderGridLYT.setAlignment(QtCore.Qt.AlignCenter)
        shaderGridLYT.addWidget(QtWidgets.QLabel('Old'), 0,0, alignment=QtCore.Qt.AlignCenter)
        shaderGridLYT.addWidget(QtWidgets.QLabel('New'), 0,1, alignment=QtCore.Qt.AlignCenter)

        shaderGridLYT.addWidget(self.oldShaderCMB, 1,0)
        shaderGridLYT.addWidget(self.newShaderCMB, 1,1)
        shaderGridLYT.addWidget(self.swapBTN, 1,2)

        self.swapGRB.setLayout(shaderGridLYT)
        
        """ FUSE LAYOUT """
        fuseLYT = QtWidgets.QHBoxLayout(self)
        fuseLYT.addWidget(self.fuse2dBTN)

        self.fuse2dGRB.setLayout(fuseLYT)

        """ CONNECT BY NODES LAYOUT """
        connectNNLYT = QtWidgets.QVBoxLayout(self)
        connectButtonsLYT = QtWidgets.QHBoxLayout(self)
        connectButtonsLYT.addWidget(self.connectLoadNodesBTN)
        connectButtonsLYT.addWidget(self.connectBTN)

        connectNNLYT.addLayout(connectButtonsLYT)
        connectNNLYT.addWidget(self.connectTBL)

        self.connectNodesGRP.setLayout(connectNNLYT)


        """ MAIN LAYOUT """
        mainLayout.addWidget(self.swapGRB)
        mainLayout.addWidget(self.fuse2dGRB)
        mainLayout.addWidget(self.connectNodesGRP)
        self.setLayout(mainLayout)

    def createConnections(self):
        pass



if __name__ == "__main__":
    # Create 
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = kt_modelingHelper() 
    window.show()