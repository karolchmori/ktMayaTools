import maya.cmds as mc
import maya.OpenMayaUI as omui

from PySide2 import QtCore
from PySide2 import QtWidgets

from shiboken2 import wrapInstance

def mayaMainWindow():
    mainWindowPTR = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPTR), QtWidgets.QWidget)

class kt_textureHelper(QtWidgets.QDialog):
    def __init__(self, parent=mayaMainWindow()):
        super(kt_textureHelper, self).__init__(parent)

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

        self.fuse2dGRB = QtWidgets.QGroupBox("Fuse place2dTexture")
        self.fuse2dBTN = QtWidgets.QPushButton("GO")

    def createLayouts(self):
        
        mainLayout = QtWidgets.QVBoxLayout(self)
    
        """ Transformation Grid """
        shaderGridLYT = QtWidgets.QGridLayout(self)
        shaderGridLYT.setAlignment(QtCore.Qt.AlignCenter)
        shaderGridLYT.addWidget(QtWidgets.QLabel('Old'), 0,0, alignment=QtCore.Qt.AlignCenter)
        shaderGridLYT.addWidget(QtWidgets.QLabel('New'), 0,1, alignment=QtCore.Qt.AlignCenter)

        shaderGridLYT.addWidget(self.oldShaderCMB, 1,0)
        shaderGridLYT.addWidget(self.newShaderCMB, 1,1)
        shaderGridLYT.addWidget(self.swapBTN, 1,2)

        self.swapGRB.setLayout(shaderGridLYT)
        
        fuseLYT = QtWidgets.QHBoxLayout(self)
        fuseLYT.addWidget(self.fuse2dBTN)

        self.fuse2dGRB.setLayout(fuseLYT)

        mainLayout.addWidget(self.swapGRB)
        mainLayout.addWidget(self.fuse2dGRB)
        self.setLayout(mainLayout)

    def createConnections(self):
        self.swapBTN.clicked.connect(self.swapTextures)
        self.fuse2dBTN.clicked.connect(self.fuse2dTexture)


    def swapTextures(self):

        oldMat = self.oldShaderCMB.currentText()
        newMat = self.newShaderCMB.currentText()
        
        materials = [mat for mat in mc.ls(materials=True) if mc.nodeType(mat) == oldMat and mat not in ('lambert1', 'standardSurface1')]

        for mat in materials:
            sgs = mc.listConnections(mat, type='shadingEngine') or []

            if mc.objExists(mat):
                mc.delete(mat)
    
            for sg in sgs:
                newShader = mc.shadingNode(newMat, asShader=True, name=mat)
                mc.connectAttr(newShader + ".outColor", sg + ".surfaceShader", force = True)

    def fuse2dTexture(self):

        # Get all selected file nodes
        fileNodes = mc.ls(sl=True, type="file")

        # Create or pick one shared place2dTexture node
        place2d = mc.shadingNode("place2dTexture", asUtility=True)

        for node in fileNodes:
            mc.defaultNavigation(connectToExisting=True, source=place2d, destination=node)

        # Delete unused place2dTexture nodes
        for node in mc.ls(type="place2dTexture"):
            connections = mc.listConnections(node, s=True, d=True)
            if connections:
                if len(connections) == 1 and connections[0] == "defaultRenderUtilityList1":
                    mc.delete(node)


if __name__ == "__main__":
    # Create 
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = kt_textureHelper() 
    window.show()