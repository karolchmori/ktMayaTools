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

        self.charCB = QtWidgets.QCheckBox("Character")
        self.charCB.setChecked(True)
        self.charPathTXT = QtWidgets.QLineEdit()
        self.charPathTXT.setEnabled(False)
        self.charVersionCMB = QtWidgets.QComboBox()


        self.camCB = QtWidgets.QCheckBox("Camera")
        self.camCB.setChecked(True)
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
        self.exportLYT.addWidget(self.charCB,0,0)
        self.exportLYT.addWidget(QtWidgets.QLabel('Path'),1,0)
        self.exportLYT.addWidget(self.charPathTXT, 1,1)
        self.exportLYT.addWidget(self.charVersionCMB, 1,2)
        

        self.exportLYT.addWidget(self.camCB,2,0)
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
        self.scenePath = mc.file(q=True, sn=True)
        self.scenePath = os.path.normpath(self.scenePath)
        self.sceneDir = os.path.dirname(self.scenePath)
        filename = os.path.basename(self.scenePath)

        # 1. Update Version Folfders
        self.updateVersionFolders()
            
        # 2. Detect SEQ and SHOT
        self.loadShotInfo(filename)

        # 3. Detect frame range
        self.loadFrameRange()
    
    def updateVersionFolders(self):
        # 1.1 Fill the path to export Character
        self.charVersionCMB.clear()
        charPath = os.path.join(self.sceneDir, "Export", "USD_ANIM") + os.sep
        self.charPathTXT.setText(charPath)
        tempDirs = self.getVersions(charPath) # 1.1.1 Detect the version. Order descendant
        self.charVersionCMB.addItems(tempDirs)
        self.charVersionCMB.setCurrentText(tempDirs[0])

        # 1.2. Fill the path to export Camera
        self.camVersionCMB.clear()
        camPath = os.path.join(self.sceneDir, "Export", "USD_CAM") + os.sep
        self.camPathTXT.setText(camPath)
        tempDirs = self.getVersions(camPath) # 1.2.1 Detect the version. Order descendant
        self.camVersionCMB.addItems(tempDirs)
        self.camVersionCMB.setCurrentText(tempDirs[0])


    def resetFrameRange(self):
        self.loadFrameRange()

    def exportFiles(self):

        frameRange = (float(self.frameMinTXT.text()), float(self.frameMaxTXT.text()))

        # 4. Detect Characters
        if self.charCB.isChecked():
            self.exportCharacters(frameRange)

        # 5. Detect Cameras
        if self.camCB.isChecked():
            self.exportCamera(frameRange)

        # 6. Update the version of the folders
        self.updateVersionFolders()
        
    
    def exportCamera(self, frameRange):
        # 1. Duplicate camera SQx_SHx_CAMERA
        defaultCams = {'persp', 'top', 'front', 'side'}

        cameras = mc.ls(type='camera')
        transforms = mc.listRelatives(cameras, parent=True)

        userCam = [cam for cam in transforms if cam not in defaultCams][0]

        if userCam:
            
            #print(userCam)
            
            newCam = mc.duplicate(userCam, rr=True)
            mc.parent(newCam, world=True)

            group = mc.group(em=True, name='camera')
            mc.parent(newCam, group)

            newName = f"SQ{self.seqTXT.text()}_SH{self.shotTXT.text()}_CAMERA";
            newCam = mc.rename(newCam, newName)


            # 2. Create parent constraint (without maintain offset) original, new
            mc.parentConstraint(userCam, newCam, mo=False)


            # 3. Bake the camera with the same frameRange
            mc.bakeResults(
                newCam, 
                simulation=True, 
                t=(float(self.frameMinTXT.text()), float(self.frameMaxTXT.text())),
                sampleBy=1, 
                oversamplingRate=1, 
                disableImplicitControl=True, 
                preserveOutsideKeys=True, 
                sparseAnimCurveBake=False, 
                removeBakedAttributeFromLayer=False, 
                removeBakedAnimFromLayer=False, 
                bakeOnOverrideLayer=False, 
                minimizeRotation=True, 
                controlPoints=False, 
                shape=True
            )


            # 4. Remove old constraint 
            constraints = mc.listRelatives(newCam, type='parentConstraint')

            if constraints:
                mc.delete(constraints)


            # 5. Export new camera
            filePath = self.camPathTXT.text() + self.camVersionCMB.currentText() + "\\" + newName + ".usd";
            self.exportUSD(filePath, group, False, frameRange)

            # 6. Delete camera
            mc.delete(newCam)
            mc.delete(group)
        

    def exportCharacters(self, frameRange):
        layers = mc.ls(type='displayLayer')
        filteredLayers = [i for i in layers if 'defaultLayer' not in i]
        exportedCounts = {}

        for layer in filteredLayers:
            name = self.extractName(layer)

            if name:
                if name not in exportedCounts:
                    exportedCounts[name] = 0

                exportedCounts[name] += 1

                name = f"{name}_{exportedCounts[name]:03d}"

                fileName = f"SQ{self.seqTXT.text()}_SH{self.shotTXT.text()}_{name}.usd";

                filePath = self.charPathTXT.text() + self.charVersionCMB.currentText() + "\\" + fileName;
                objects = mc.editDisplayLayerMembers(layer, q=True, fn=True) or []
                self.exportUSD(filePath, objects, True, frameRange)

            

    def extractName(self, name):
        if ':' in name:
            name = name.split(':')[1]
        
        parts = name.split('_')

        if len(parts) != 2:
            return None
        
        name, tag = parts


        if 'MODEL' not in tag.upper():
            return None

        return name

    
    def exportUSD(self, filePath, objects, isMesh, frameRange):

        if isMesh:
            exclusion = ["Cameras","Lights"]
            defaultPrim = objects[0].split("|")[1]
        else:
            exclusion = ["Lights", "Meshes"]
            defaultPrim = None

        mc.select(objects)

        mc.mayaUSDExport(
            file=filePath,
            selection=True,
            # --- Include Options ---
            # NOT DO Include these insputs History, Channels, Expressions, Constrains (Usually not exported to USD)
            shadingMode="none",

            # --- Output Options -----
            defaultUSDFormat="usdc", # usdc usda
            defaultPrim=defaultPrim,
            #rootPrim = rootPrim,
            #kind="group",
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
            frameRange=frameRange,

            # ------  Advanced ------
            excludeExportTypes= exclusion,
            exportVisibility=True,

            mergeTransformAndShape=True,
            includeEmptyTransforms=True,
            stripNamespaces=True,
            # unit="meters"
            metersPerUnit=1, # TODO quitar?
            exportDistanceUnit=True # TODO quitar?
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