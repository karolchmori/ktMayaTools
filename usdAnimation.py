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

class usdAnimation(QtWidgets.QDialog):
    def __init__(self, parent=mayaMainWindow()):
        super(usdAnimation, self).__init__(parent)

        self.setWindowTitle("USD Animation")
        self.setFixedSize(550, 220)

        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint) #Remove the ? button

        '''
        VARIABLES
        '''
        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.loadUI()

    def createWidgets(self):

        self.seqTXT = QtWidgets.QLineEdit()
        self.seqTXT.setEnabled(False)
        self.shotTXT = QtWidgets.QLineEdit()
        self.shotTXT.setEnabled(False)
        
        self.frameMinTXT = QtWidgets.QLineEdit()
        self.frameMaxTXT = QtWidgets.QLineEdit()
        self.frameResetBTN = QtWidgets.QPushButton()
        self.frameResetBTN.setIcon(QtGui.QIcon(":clockwise.png"))
        self.frameResetBTN.setIconSize(QtCore.QSize(20, 20))

        self.charPathTXT = QtWidgets.QLineEdit()
        self.charPathTXT.setEnabled(False)
        self.charVersionCMB = QtWidgets.QComboBox()

        self.camPathTXT = QtWidgets.QLineEdit()
        self.camPathTXT.setEnabled(False)
        self.camVersionCMB = QtWidgets.QComboBox()

        self.exportBTN = QtWidgets.QPushButton("Export")
        


    def createLayouts(self):
        
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
        self.exportLYT.addWidget(QtWidgets.QLabel('Character'),0,0)
        self.exportLYT.addWidget(QtWidgets.QLabel('Path'),1,0)
        self.exportLYT.addWidget(self.charPathTXT, 1,1)
        self.exportLYT.addWidget(self.charVersionCMB, 1,2)
        

        self.exportLYT.addWidget(QtWidgets.QLabel('Camera'),2,0)
        self.exportLYT.addWidget(QtWidgets.QLabel('Path'),3,0)
        self.exportLYT.addWidget(self.camPathTXT, 3,1)
        self.exportLYT.addWidget(self.camVersionCMB, 3,2)
        

        """ MAIN LAYOUT """
        mainLayout.addLayout(self.shotInfoLYT)
        mainLayout.addLayout(self.exportLYT)
        mainLayout.addWidget(self.exportBTN)
        self.setLayout(mainLayout)
        
        
    def createConnections(self):
        self.frameMinTXT.editingFinished.connect(self.frameCheck)
        self.frameMaxTXT.editingFinished.connect(self.frameCheck)
        self.frameResetBTN.clicked.connect(self.resetFrameRange)
        self.exportBTN.clicked.connect(self.exportFiles)

    def loadUI(self):
        # 1. Detect file Path
        scenePath = mc.file(q=True, sn=True)
        scenePath = os.path.normpath(scenePath)
        sceneDir = os.path.dirname(scenePath)
        filename = os.path.basename(scenePath)

        # 1.1 Fill the path to export Character
        charPath = os.path.join(sceneDir, "Export", "USD_ANIM") + os.sep
        self.charPathTXT.setText(charPath)
        tempDirs = self.getVersions(charPath) # 1.1.1 Detect the version. Order descendant
        self.charVersionCMB.addItems(tempDirs)
        self.charVersionCMB.setCurrentText(tempDirs[0])

        # 1.2. Fill the path to export Camera
        camPath = os.path.join(sceneDir, "Export", "USD_CAM") + os.sep
        self.camPathTXT.setText(camPath)
        tempDirs = self.getVersions(camPath) # 1.2.1 Detect the version. Order descendant
        self.camVersionCMB.addItems(tempDirs)
        self.camVersionCMB.setCurrentText(tempDirs[0])
            
        # 2. Detect SEQ and SHOT
        self.loadShotInfo(filename)

        # 3. Detect frame range
        self.loadFrameRange()

    def resetFrameRange(self):
        self.loadFrameRange()

    def exportFiles(self):
        # 4. Detect Characters
        self.exportCharacters()

        # 5. Detect Cameras


    def exportCharacters(self):
        layers = mc.ls(type='displayLayer')
        filteredLayers = [i for i in layers if 'defaultLayer' not in i]
        exportedCounts = {}

        for layer in filteredLayers:
            if 'MODEL' in layer:
                name = self.extractName(layer)

                if name not in exportedCounts:
                    exportedCounts[name] = 0

                exportedCounts[name] += 1

                name = f"{name}_{exportedCounts[name]:03d}"


                fileName = f"SQ{self.seqTXT.text()}_SH{self.shotTXT.text()}_{name}.usd";

                filePath = self.charPathTXT.text() + self.charVersionCMB.currentText() + "\\" + fileName;
                
                objects = mc.editDisplayLayerMembers(layer, q=True, fn=True) or []
                self.exportUSD(filePath, objects, True)

            

    def extractName(self, name):
        if ':' in name:
            name = name.split(':')[1]

        name = name.split('_')[0]

        return name

    
    def exportUSD(self, filePath, objects, isMesh):

        if isMesh:
            exclusion = ["Cameras","Lights"]
        else:
            exclusion = ["Lights", "Meshes"]
        

        mc.select(objects)
        
        defaultPrim = objects[0].split("|")[1]


        mc.mayaUSDExport(
            file=filePath,
            selection=True,
            # --- Include Options ---
            # NOT DO Include these insputs History, Channels, Expressions, Constrains (Usually not exported to USD)
            shadingMode="none",

            # --- Output Options -----
            defaultUSDFormat="usda",
            defaultPrim=defaultPrim, 

            # --- Geometry Options ---
            defaultMeshScheme="catmullClark",
            exportDisplayColor=False,
            exportColorSets=False,
            exportComponentTags=False,
            exportUVs=True,
            exportSkels="none",
            exportBlendShapes=False,
            filterTypes="nurbsCurve",

            # ------  Materials ------
            exportMaterials=False,

            # ------  Animation ------
            #animation=True,
            frameRange=(float(self.frameMinTXT.text()), float(self.frameMaxTXT.text())),

            # ------  Advanced ------
            excludeExportTypes= exclusion,
            exportVisibility=True,

            mergeTransformAndShape=True,
            includeEmptyTransforms=True,
            stripNamespaces=True,
            # unit="meters"
            # TODO: metersPerUnit
            )
        

        mc.select(clear=True)


    def frameCheck(self):
        # Read values
        minVal = int(self.frameMinTXT.text())
        maxVal = int(self.frameMaxTXT.text())

        # Fix invalid ranges
        if minVal > maxVal:
            self.frameMinTXT.setText(str(maxVal)) # If Min is greater than Max, set Min = Max
        elif maxVal < minVal:
            self.frameMaxTXT.setText(str(minVal)) # If Max is less than Min, set Max = Min        

    def loadShotInfo(self, name):
        match = re.search(r"SQ_(\d+)-SH_(\d+)", name)

        if match:
            sqValue = match.group(1)
            shValue = match.group(2)

            self.seqTXT.setText(sqValue)
            self.shotTXT.setText(shValue)

    def loadFrameRange(self):
        start = int(mc.playbackOptions(q=True, min=True))
        end = int(mc.playbackOptions(q=True, max=True))

        self.frameMinTXT.setText(str(start))
        self.frameMaxTXT.setText(str(end))

    
    def getVersions(self, path):
        dirs = [d for d in os.listdir(path) 
                    if os.path.isdir(os.path.join(path, d)) and d != "master"]
        
        dirs.sort(reverse=True)

        lastFolder = int(dirs[0][1:]) if dirs else 0
        nextFolder = f"v{lastFolder + 1:04d}"

        dirs.sort(reverse=True)
        dirs.append(nextFolder)
        dirs.sort(reverse=True)

        return dirs





if __name__ == "__main__":
    # Create 
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = usdAnimation() 
    window.show()