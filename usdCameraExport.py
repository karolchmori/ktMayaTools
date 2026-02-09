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
        self.setMinimumSize(450, 150)
        
        '''
        VARIABLES
        '''
        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.loadUI()
        

    def createWidgets(self):
        """Initialize UI widgets."""

        self.plugTypeCMB = QtWidgets.QComboBox()
        self.plugTypeCMB.addItems(['Arnold','None'])

        self.frameMinTXT = QtWidgets.QLineEdit()
        self.frameMaxTXT = QtWidgets.QLineEdit()
        self.frameResetBTN = QtWidgets.QPushButton()
        self.frameResetBTN.setIcon(QtGui.QIcon(":clockwise.png"))
        self.frameResetBTN.setIconSize(QtCore.QSize(20, 20))


        self.camPathTXT = QtWidgets.QLineEdit()
        self.camPathTXT.setReadOnly(True)
        self.camPathBTN = QtWidgets.QPushButton()
        self.camPathBTN.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.camPathBTN.setFixedSize(40, 30)
        self.camPathBTN.setToolTip("Select Camera Export directory")

        self.exportBTN = QtWidgets.QPushButton("Export")
        


    def createLayouts(self):
        """Arrange widgets in layouts."""

        mainLayout = QtWidgets.QVBoxLayout(self)
    
        """ SWAP LAYOUT """
        self.shotInfoLYT = QtWidgets.QHBoxLayout(self)
        self.shotInfoLYT.addWidget(QtWidgets.QLabel('Plug-in: '))
        self.shotInfoLYT.addWidget(self.plugTypeCMB)
        self.shotInfoLYT.addWidget(QtWidgets.QLabel('Frame Range: '))
        self.shotInfoLYT.addWidget(self.frameMinTXT)
        self.shotInfoLYT.addWidget(self.frameMaxTXT)
        self.shotInfoLYT.addWidget(self.frameResetBTN)
        


        self.exportLYT = QtWidgets.QGridLayout()
        self.exportLYT.addWidget(QtWidgets.QLabel('Path'),0,0)
        self.exportLYT.addWidget(self.camPathTXT, 0,1)
        self.exportLYT.addWidget(self.camPathBTN, 0,2)
        

        """ MAIN LAYOUT """
        mainLayout.addLayout(self.shotInfoLYT)
        mainLayout.addLayout(self.exportLYT)
        mainLayout.addWidget(self.exportBTN)
        self.setLayout(mainLayout)
        
        
    def createConnections(self):
        """Connect signals to their slots."""
        self.camPathBTN.clicked.connect(self.onClick_selectDirectory)
        self.frameMinTXT.editingFinished.connect(self.frameCheck)
        self.frameMaxTXT.editingFinished.connect(self.frameCheck)
        self.frameResetBTN.clicked.connect(self.onClick_frameResetBTN)
        self.exportBTN.clicked.connect(self.onClick_exportBTN)

    
    def loadUI(self):
        """Load scene info and initialize UI data."""

        # 1. Only works for opened files, Detect file Path
        scenePath = mc.file(q=True, sn=True)
        if scenePath:
            # 1. Access here after having an scenePath
            scenePath = os.path.normpath(scenePath)
            sceneDir = os.path.dirname(scenePath)

            if not sceneDir.endswith(os.sep):
                sceneDir += os.sep
            self.camPathTXT.setText(sceneDir)
            

        # 5. Detect frame range
        self.loadFrameRange()

#region Folders
    
    def onClick_selectDirectory(self):
        """Handle directory selection and update path fields."""
        button = self.sender()

        # 1. Get the user selected folder
        selectedPath = self.getPath()

        if selectedPath:
            self.camPathTXT.setText(selectedPath)
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

#endregion

#region Frame

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

#endregion

#region Export

    def onClick_exportBTN(self):
        """Export character and camera data if enabled and valid."""

        frameRange = (float(self.frameMinTXT.text()), float(self.frameMaxTXT.text()))
        camPath = self.camPathTXT.text()

        if camPath:
            export = self.exportCamera(frameRange, camPath, self.plugTypeCMB.currentText())
            if export:
                QtWidgets.QMessageBox.information(self, "Success", "Export complete")
            
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "No camera path has been found. Camera can't be exported.")
        

    def exportCamera(self, frameRange, path, plugin):
        """Bake and export the user camera as USD.

        Args:
            seq (str): Sequence number.
            shot (str): Shot number.
            frameRange (tuple): Start and end frames (float).
            path (str): Export directory path.
            version (str): Version folder name.
        """
        
        selectedObjects = mc.ls(selection=True, long=True)
        userCams = self.filterByType(selectedObjects)

        if userCams:
            for userCam in userCams:
                

                newName = userCam.split('|')[-1]
                newName = newName.replace(':','_')

                # 1. Duplicate camera 
                newCam = mc.duplicate(userCam, rr=True)
                mc.parent(newCam, world=True)

                newCam = mc.rename(newCam, newName)


                group = mc.group(em=True, name='camera')
                mc.parent(newCam, group)

            
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
                filePath = path + newCam + ".usd";
                #print(f"Exporting in path: {filePath}")
                self.exportUSD(filePath, group, False, frameRange, plugin)

                # 7. Delete camera
                mc.delete(newCam)
                mc.delete(group)

                return True
        
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "No camera have been selected to export.")
            return False


    def exportUSD(self, filePath, objects, isMesh, frameRange, plugin):
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
            defaultUSDFormat="usda", # usdc usda
            #defaultPrim=defaultPrim,
            defaultMeshScheme="catmullClark",
            exportDisplayColor=False,
            exportColorSets=False,
            exportComponentTags=False,
            exportUVs=True,
            exportSkels="none",
            exportBlendShapes=False,
            filterTypes="nurbsCurve",
            #exportMaterials=False,
            frameRange=frameRange,
            #excludeExportTypes= exclusion,
            exportVisibility=True,

            mergeTransformAndShape=True,
            #includeEmptyTransforms=True,
            stripNamespaces=True,
            jobContext=[plugin]
            # unit="meters"
            #metersPerUnit=1,
            #exportDistanceUnit=True
            )
        

        mc.select(clear=True)





#endregion

#region Camera Util

    
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



    def filterByType(self, objectList):
        filteredObjects = []

        for obj in objectList:
            objType = mc.nodeType(obj)

            matched = False
            
            if objType == 'camera':
                filteredObjects.append(obj)
                matched = True
                break  # Once found, no need to check other types for this object
            
            if matched:
                continue  # Skip shape checking if the object type already matched
            
            # Then, check the shape types if the object isn't matched as a transform type
            shapes = mc.listRelatives(obj, shapes=True, fullPath=True)
            
            if shapes:
                for shape in shapes:
                    objType = mc.nodeType(shape)

                    if objType == 'camera':
                        filteredObjects.append(obj)
                        break  # Once found, no need to check other types for this object
                    
        #print(filteredObjects)
        return filteredObjects

#endregion

if __name__ == "__main__":
    # Create 
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = usdCameraExport() 
    window.show()