import maya.cmds as mc
import maya.OpenMayaUI as omui
import os

from PySide2 import QtCore
from PySide2 import QtWidgets

from shiboken2 import wrapInstance

def mayaMainWindow():
    mainWindowPTR = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPTR), QtWidgets.QWidget)

class Texture(object):
    textureMapping = {
            "baseColor": {"label": "Base Color", "abbreviation": "BC", "mapping": ["basecolor", "base", "albedo"]},
            "metalness": {"label": "Metalness", "abbreviation": "M", "mapping": ["metalness", "metallic"]},
            "specularRough": {"label": "Specular Rough", "abbreviation": "SR", "mapping": ["roughness", "specular"]},
            "normal": {"label": "Normal", "abbreviation": "N", "mapping": ["normal"]},
            "displacement": {"label": "Displacement", "abbreviation": "D", "mapping": ["height", "displacement"]},
            "ambientOcclusion": {"label": "Ambient Occlusion", "abbreviation": "AO", "mapping": ["ao","ambientocclusion","ambientoclussion"]},
            "opacity": {"label": "Opacity", "abbreviation": "OP", "mapping": ["opacity"]},
    }
    
    def __init__(self, baseColor=None, metalness=None, specularRough=None, normal=None, displacement=None, ambientOcclusion=None,
                 opacity=None):
        self.baseColor = baseColor
        self.metalness = metalness
        self.specularRough = specularRough
        self.normal = normal
        self.displacement = displacement
        self.ambientOcclusion = ambientOcclusion
        self.opacity = opacity

    def getTypeFromAttr(self, attr, text):
        for parent, children in self.textureMapping.items():
            if text in children[attr]:
                return parent
        return None

    def showInformation(self, tableWidget=None):
        """If a QTableWidget is provided, fill it with texture data. Otherwise, print."""
        attributes = vars(self)

        if tableWidget:
            # --- Fill the QTableWidget ---
            tableWidget.clearContents()
            tableWidget.setRowCount(len(attributes))
            tableWidget.setColumnCount(2)
            tableWidget.setHorizontalHeaderLabels(["Attribute", "Value"])

            for row, (attribute, value) in enumerate(attributes.items()):
                mapping = self.textureMapping.get(attribute)
                label = mapping["label"]

                attrItem = QtWidgets.QTableWidgetItem(label)
                valItem = QtWidgets.QTableWidgetItem(str(value) if value else "None")

                attrItem.setFlags(attrItem.flags() ^ QtCore.Qt.ItemIsEditable)
                valItem.setFlags(valItem.flags() ^ QtCore.Qt.ItemIsEditable)

                tableWidget.setItem(row, 0, attrItem)
                tableWidget.setItem(row, 1, valItem)

            tableWidget.resizeColumnsToContents()
        else:
            """Prints all texture file assignments."""
            print("-----------------------------------------")
            for attribute, value in attributes.items():  # Iterate over the instance's attributes
                print(f"{attribute}: {value}")
            print("-----------------------------------------")



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

        '''
        CONNECTION TEMP
        '''
        self.tempTexture = Texture()

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
        self.fuse2dGRB = QtWidgets.QGroupBox("Fuse place2dTexture")
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
        self.swapBTN.clicked.connect(self.swapTextures)
        self.fuse2dBTN.clicked.connect(self.fuse2dTexture)
        self.connectLoadNodesBTN.clicked.connect(self.connectLoadNodes)
        self.connectBTN.clicked.connect(self.onClick_connectBTN)


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

        fileNodes = mc.ls(sl=True, type="file")
        place2d = mc.shadingNode("place2dTexture", asUtility=True)
        for node in fileNodes:
            mc.defaultNavigation(connectToExisting=True, source=place2d, destination=node)

        # Delete unused place2dTexture nodes
        for node in mc.ls(type="place2dTexture"):
            connections = mc.listConnections(node, s=True, d=True)
            if connections:
                if len(connections) == 1 and connections[0] == "defaultRenderUtilityList1":
                    mc.delete(node)

    def connectLoadNodes(self):
        selectionObjects = mc.ls(selection=True)
        texture = Texture()

        for obj in selectionObjects:
            if mc.nodeType(obj) == 'file':
                filepath = mc.getAttr(obj + ".fileTextureName")
                filenameExt = os.path.basename(filepath)
                filename , _ = os.path.splitext(filenameExt)
                textureType = filename.split('_')[-1]
                textureType = textureType.lower()

                textureParent = texture.getTypeFromAttr("mapping", textureType)
                setattr(texture, textureParent, obj)

        texture.showInformation(self.connectTBL)

        self.tempTexture = texture

    def onClick_connectBTN(self):
        #Get shaders
        selectionObjects = mc.ls(selection=True)

        if selectionObjects:
            baseColor = self.tempTexture.baseColor
            ao = self.tempTexture.ambientOcclusion
            metalness = self.tempTexture.metalness
            specular = self.tempTexture.specularRough
            normal = self.tempTexture.normal
            displacement = self.tempTexture.displacement

            for obj in selectionObjects:
                if mc.nodeType(obj) == 'aiStandardSurface':
                    connections = mc.listConnections(obj, type="shadingEngine")
                    if connections:
                        shadingEngine = connections[0]

                    if baseColor:
                        if ao:
                            #Check if it has connections as multiply
                            connections = mc.listConnections(ao, s=True, d=True)
                            multNode = None

                            for node in connections:
                                if mc.nodeType(node) == "aiMultiply":
                                    multNode = node
                                    break
                            #If has existent connection use it, if not create one
                            if multNode:
                                mc.connectAttr(multNode + ".outColor", obj + ".baseColor", force=True)
                            else:
                                multiply = mc.shadingNode("aiMultiply", asUtility=True, name=f"baseColorAO_mult")
                                mc.connectAttr(baseColor + ".outColor", multiply + ".input1", force=True)
                                mc.connectAttr(ao + ".outColor", multiply + ".input2", force=True)
                                mc.connectAttr(multiply + ".outColor", obj + ".baseColor", force=True)
                        
                    else:
                        mc.connectAttr(baseColor + ".outColor", obj + ".baseColor", force=True)
                    
                    if metalness:
                        mc.connectAttr(metalness + ".outAlpha", obj + ".metalness", force=True)
                    
                    if specular:
                        mc.connectAttr(specular + ".outAlpha", obj + ".specularRoughness", force=True)

                    if normal:
                        #Check if it has connections as multiply
                        connections = mc.listConnections(normal)
                        normalMap = None

                        for node in connections:
                            if mc.nodeType(node) == "aiNormalMap":
                                normalMap = node
                                break
                            
                        if normalMap:
                            mc.connectAttr(normalMap + ".outValue", obj + ".normalCamera", force=True)
                        else:
                            normalMap = mc.shadingNode("aiNormalMap", asUtility=True)
                            mc.connectAttr(normal + ".outColor", normalMap + ".input", force=True)
                            mc.connectAttr(normalMap + ".outValue", obj + ".normalCamera", force=True)
                    
                    if displacement:
                        #Check if it has connections as multiply
                        connections = mc.listConnections(displacement)
                        dispShader = None

                        for node in connections:
                            print(node)
                            if mc.nodeType(node) == "displacementShader":
                                dispShader = node
                                break

                        if dispShader:
                            mc.connectAttr(dispShader + ".displacement", shadingEngine + ".displacementShader", force=True)
                        else:
                            dispShader = mc.shadingNode("displacementShader", asShader=True)
                            mc.setAttr("displacementShader1.scale", 0.020)
                            mc.connectAttr(displacement + ".outAlpha", dispShader + ".displacement", force=True)
                            mc.connectAttr(dispShader + ".displacement", shadingEngine + ".displacementShader", force=True)


        #For each attribute in texture connect to each shader




if __name__ == "__main__":
    # Create 
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = kt_textureHelper() 
    window.show()