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
    """Dialog for exporting USD animation data with UI controls and export logic."""
    
    def __init__(self, parent=mayaMainWindow()):
        """Initialize USD Animation dialog with UI setup and data loading.

        Args:
            parent (QWidget, optional): Parent window, defaults to Maya main window.
        """
        
        super(usdAnimation, self).__init__(parent)

        self.setWindowTitle("USD Animation")
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

        self.frameMinTXT.editingFinished.connect(self.frameCheck)
        self.frameMaxTXT.editingFinished.connect(self.frameCheck)
        self.frameResetBTN.clicked.connect(self.onClick_frameResetBTN)
        self.exportBTN.clicked.connect(self.onClick_exportBTN)
        self.charPathBTN.clicked.connect(self.onClick_selectDirectory)
        self.camPathBTN.clicked.connect(self.onClick_selectDirectory)
        self.charCB.stateChanged.connect(self.stateChanged_checkbox)
        self.camCB.stateChanged.connect(self.stateChanged_checkbox)


    def loadUI(self):
        """Load scene info and initialize UI data."""

        # 1. Only works for opened files, Detect file Path
        self.scenePath = mc.file(q=True, sn=True)
        if self.scenePath:
            # 1. Access here after having an scenePath
            self.scenePath = os.path.normpath(self.scenePath)
            self.sceneDir = os.path.dirname(self.scenePath)

            # 2. Detect SEQ and SHOT
            filename = os.path.basename(self.scenePath)
            self.loadShotInfo(filename)
        

            # 3. Default folder Path
            self.getDefaultPath()

            # 4. Update Version Folfders
            self.updateVersionFolders()
                

            # 5. Detect frame range
            self.loadFrameRange()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Please open an scene")
            QtCore.QTimer.singleShot(0, self.close)
    
    def stateChanged_checkbox(self):
        """Enable or disable related widgets based on checkbox state."""

        check = self.sender()
        status = check.isChecked()

        if check == self.charCB:
            self.charPathBTN.setEnabled(status)
            self.charPriorityCMB.setEnabled(status)
            self.charPathTXT.setEnabled(status)
            self.charVersionCMB.setEnabled(status)
        elif check == self.camCB:
            self.camPathBTN.setEnabled(status)
            self.camPathTXT.setEnabled(status)
            self.camVersionCMB.setEnabled(status)
        

#region Folders

    def onClick_selectDirectory(self):
        """Handle directory selection and update path fields."""
        button = self.sender()

        # 1. Get the user selected folder
        selectedPath = self.getPath()

        if selectedPath:
            # 2. Depending on the button save it
            if button == self.charPathBTN:
                self.charPathTXT.setText(selectedPath)
            else:
                self.camPathTXT.setText(selectedPath)
            
            self.updateVersionFolders()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Directory was not selected.")
    

    def getPath(self):
        """Open folder dialog and return selected directory path.

        Returns:
            str or None: Normalized directory path if selected, else None.
        """

        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select the \'Export\' directory")
    
        if folder:
            folder = os.path.normpath(folder)
            if not folder.endswith(os.sep):
                folder += os.sep

            return folder
        

    def getDefaultPath(self):
        """Set and create default export paths for character and camera."""

        #self.sceneDir = os.path.abspath(os.path.join(self.sceneDir, "..", "..", "..")) 

        tempPath = self.sceneDir

        #print(f"BASE: {tempPath}")
        
        pattern = re.compile(
                    r"""
                    ^
                    (?P<base>[A-Z]:\\[^\\]+)            # D:... P:.... 
                    (?:\\(?P<sequence>SQ_[0-9]{3}))?    # \SQ_001
                    (?:\\(?P<shot>SH_[0-9]{3}))?        # \SH_010
                    (?:\\(?P<export>(?i:export)))?      # \Export
                    (?:\\.*)?                           # anything after is ignored
                    """,
                    re.VERBOSE | re.IGNORECASE
                )
        
        match = pattern.match(tempPath)

        #print(match.groupdict())


        # Reconstruct path
        rootPath = match['base']
        seqPath = match['sequence'] if match['sequence'] else (f'SQ_{self.seqTXT.text()}' if len(self.seqTXT.text()) else '') 
        shPath = match['shot'] if match['shot'] else (f'SQ_{self.shotTXT.text()}' if len(self.shotTXT.text()) else '')
        expPath = match['export'] if match['export'] else 'Export'

        basePath = os.path.join(rootPath, seqPath, shPath, expPath)
        #print (f'NEW BASE: {basePath}')
    
        charPath = os.path.join(basePath, "USD_ANIM") + os.sep
        os.makedirs(charPath, exist_ok=True)
        self.charPathTXT.setText(charPath)

        camPath = os.path.join(basePath, "USD_CAM") + os.sep
        os.makedirs(camPath, exist_ok=True)
        self.camPathTXT.setText(camPath)


    def updateVersionFolders(self):
        """Populate version combo boxes based on current export paths."""

        charPath = self.charPathTXT.text()
        camPath = self.camPathTXT.text()

        # 1. Fill the path to export Character
        self.charVersionCMB.clear()
        tempDirs = self.getVersions(charPath) # 1.1.1 Detect the version. Order descendant
        self.charVersionCMB.addItems(tempDirs)
        self.charVersionCMB.setCurrentText(tempDirs[0])

        # 2. Fill the path to export Camera
        self.camVersionCMB.clear()
        tempDirs = self.getVersions(camPath) # 1.2.1 Detect the version. Order descendant
        self.camVersionCMB.addItems(tempDirs)
        self.camVersionCMB.setCurrentText(tempDirs[0])

    
    def getVersions(self, path):
        """Get existing version folders and the next version for a given path.

        Args:
            path (str): Directory path to scan for version folders.

        Returns:
            list of str: Sorted list of version folder names, including the next version.
        """
        
        if not path or not os.path.exists(path):
            return ["v0001"]
    
        # 1. Match all the folders that have the format "v00XX"
        dirs = []

        for d in os.listdir(path):
            full_path = os.path.join(path, d)

            if not os.path.isdir(full_path):
                continue

            if re.match(r"^v\d+$", d):
                dirs.append(d)


        dirs.sort(reverse=True)

        # 2. Get the last folder and create a new one
        if dirs:
            lastFolder = int(dirs[0][1:])
        else:
            lastFolder = 0
        
        nextFolder = f"v{lastFolder + 1:04d}"

        # 3. Append it on the list
        dirs.sort(reverse=True)
        dirs.append(nextFolder)
        dirs.sort(reverse=True)

        return dirs

#endregion


#region Frame & Shot Info


    def onClick_frameResetBTN(self):
        """Reset frame range to scene's timeline settings."""
        self.loadFrameRange()


    def frameCheck(self):
        """Validate and correct frame range input fields."""

        # 1. Read values
        minVal = int(self.frameMinTXT.text())
        maxVal = int(self.frameMaxTXT.text())

        # 2. Fix invalid ranges
        if minVal > maxVal:
            self.frameMinTXT.setText(str(maxVal)) # If Min is greater than Max, set Min = Max
        elif maxVal < minVal:
            self.frameMaxTXT.setText(str(minVal)) # If Max is less than Min, set Max = Min        

    def loadFrameRange(self):
        """Load timeline frame range into input fields."""

        start = int(mc.playbackOptions(q=True, min=True))
        end = int(mc.playbackOptions(q=True, max=True))

        self.frameMinTXT.setText(str(start))
        self.frameMaxTXT.setText(str(end))

    
    def loadShotInfo(self, name):
        """Extract and display sequence and shot info from filename.

        Args:
            name (str): Filename containing sequence and shot data.
        """
        
        match = re.search(r"SQ_(\d+)-SH_(\d+)", name)

        if match:
            sqValue = match.group(1)
            shValue = match.group(2)

            self.seqTXT.setText(sqValue)
            self.shotTXT.setText(shValue)
        #else:
            #QtWidgets.QMessageBox.warning(self, "Error", "Sequence and Shot information has not been found.")


#endregion


#region Export

    def onClick_exportBTN(self):
        """Export character and camera data if enabled and valid."""

        frameRange = (float(self.frameMinTXT.text()), float(self.frameMaxTXT.text()))
        
        seq = self.seqTXT.text()
        shot = self.shotTXT.text()

        if seq and shot:
            shotInfo = f"SQ{seq}_SH{shot}_"
        else:
            shotInfo = ''
    

        charPath = self.charPathTXT.text()
        camPath = self.camPathTXT.text()
        export = False

        if charPath or camPath:
            # 4. Detect Characters
            if self.charCB.isChecked():
                if charPath:
                    self.exportCharacters(shotInfo, frameRange, charPath, self.charVersionCMB.currentText(), self.charPriorityCMB.currentText())
                    export = True
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", "No character path has been found. Characters can't be exported.")

            # 5. Detect Cameras
            if self.camCB.isChecked():
                if camPath:
                    self.exportCamera(shotInfo, frameRange, camPath, self.camVersionCMB.currentText())
                    export = True
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", "No camera path has been found. Camera can't be exported.")

            # 6. Update the version of the folders
            self.updateVersionFolders()

            
            # 7. Show a MessageBox to let know it has finished
            if export:
                QtWidgets.QMessageBox.information(self, "Success", "Export complete")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "No character or camera were enabled to export.")
    
    def exportCamera(self, shotInfo, frameRange, path, version):
        """Bake and export the user camera as USD.

        Args:
            seq (str): Sequence number.
            shot (str): Shot number.
            frameRange (tuple): Start and end frames (float).
            path (str): Export directory path.
            version (str): Version folder name.
        """
        

        defaultCams = {'persp', 'top', 'front', 'side'}
        difference = frameRange[1] - frameRange[0]

        cameras = mc.ls(type='camera')
        transforms = mc.listRelatives(cameras, parent=True)

        userCams = [cam for cam in transforms if cam not in defaultCams]

        if userCams:
            userCam = userCams[0]

            # 1. Duplicate camera SQx_SHx_CAMERA
            newCam = mc.duplicate(userCam, rr=True)
            mc.parent(newCam, world=True)

            group = mc.group(em=True, name='camera')
            mc.parent(newCam, group)

            if difference == 0:
                newName = f"{shotInfo}CAMERA_restPose";
            else: 
                newName = f"{shotInfo}CAMERA";

            
            newCam = mc.rename(newCam, newName)

            # 2. Unlock new camera parameters
            self.toggleCameraLock(newCam, False)

            # 3. Create parent constraint (without maintain offset) original, new
            constraint = mc.parentConstraint(userCam, newCam, mo=False)[0]

            # 4. Bake the camera with the same frameRange
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

            # 5. Remove old constraint 
            mc.delete(constraint)


            # 6. Export new camera
            filePath = path + version + "\\" + newName + ".usd";
            self.exportUSD(filePath, group, False, frameRange)

            # 7. Delete camera
            mc.delete(newCam)
            mc.delete(group)
        
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "No camera have been found to export.")


    def toggleCameraLock(self, camera, status):
        """Lock or unlock transform attributes of the given camera.

        Args:
            camera (str): Camera name.
            status (bool): True to lock, False to unlock attributes.
        """
        
        attrs = ['translateX', 'translateY', 'translateZ',
                'rotateX', 'rotateY', 'rotateZ',
                'scaleX', 'scaleY', 'scaleZ']
        
        for attr in attrs:
            mc.setAttr(f"{camera}.{attr}", lock=status)

        

    def exportCharacters(self, shotInfo, frameRange, path, version, priority):
        """Export character layers as USD files.

        Args:
            seq (str): Sequence number.
            shot (str): Shot number.
            frameRange (tuple): Start and end frames (float).
            path (str): Export directory path.
            version (str): Version folder name.
        """
            
        # 1. Select all display layers
        layers = mc.ls(type='displayLayer')
        filteredLayers = [i for i in layers if 'defaultLayer' not in i]
        exportedCounts = {}
        difference = frameRange[1] - frameRange[0]

        # 2. For each layer get the name
        for layer in filteredLayers:
            name = self.extractName(layer, priority)

            if name:
                # 3. Save the name to exportedCounts so we know we are going to export a new version
                if name not in exportedCounts:
                    exportedCounts[name] = 0

                exportedCounts[name] += 1

                # 4. Prepare data
                if difference == 0:
                    name = f"{name}_restPose_{exportedCounts[name]:03d}"
                else: 
                    name = f"{name}_{exportedCounts[name]:03d}"


                fileName = f"{shotInfo}{name}.usd";
                filePath = path + version + "\\" + fileName;

                objects = mc.editDisplayLayerMembers(layer, q=True, fn=True) or []

                # 5. Export USD
                self.exportUSD(filePath, objects, True, frameRange)
                #print(f"DEBUG: Exported {layer}")

            else:
                print(f"DEBUG: Skipped {layer}")
            
    
    def exportUSD(self, filePath, objects, isMesh, frameRange):
        """Export given objects to a USD file with specified options.

        Args:
            filePath (str): Destination file path for USD export.
            objects (list): List of scene objects to export.
            isMesh (bool): True if exporting meshes, False for cameras or others.
            frameRange (tuple): Start and end frames (float).
        """
            
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
            # NOT DO Include these insputs History, Channels, Expressions, Constrains (Usually not exported to USD)
            shadingMode="none",
            defaultUSDFormat="usdc", # usdc usda
            defaultPrim=defaultPrim,
            defaultMeshScheme="catmullClark",
            exportDisplayColor=False,
            exportColorSets=False,
            exportComponentTags=False,
            exportUVs=True,
            exportSkels="none",
            exportBlendShapes=False,
            filterTypes="nurbsCurve",
            exportMaterials=False,
            frameRange=frameRange,
            excludeExportTypes= exclusion,
            exportVisibility=True,

            mergeTransformAndShape=True,
            includeEmptyTransforms=True,
            stripNamespaces=True,
            # unit="meters"
            metersPerUnit=1,
            exportDistanceUnit=True
            )
        

        mc.select(clear=True)

    def extractName(self, name, priority):
        """Extract base name if format matches and tag contains 'MODEL'.

        Args:
            name (str): Input string to parse.

        Returns:
            str or None: Extracted base name if valid, else None.
        """
            
        if ':' in name:
            name = name.split(':')[1]
        
        parts = name.split('_')
        name = parts[0]
        tag = parts[1]

        # CASO SIMULACION
        notSimulation = ['MAIASAURA', 'AZUREAN']

        if name not in notSimulation:
            if tag == priority:
                return name
            else:
                return None
        
        else:

            if 'MODEL' not in tag.upper():
                return None

            return name
    
#endregion


if __name__ == "__main__":
    # Create 
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = usdAnimation() 
    window.show()