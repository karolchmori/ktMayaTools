import maya.cmds as mc
import maya.OpenMayaUI as omui
import os
import re

from PySide2 import QtCore
from PySide2 import QtWidgets

from shiboken2 import wrapInstance

def mayaMainWindow():
    mainWindowPTR = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPTR), QtWidgets.QWidget)


class kt_modelingHelper(QtWidgets.QDialog):
    def __init__(self, parent=mayaMainWindow()):
        super(kt_modelingHelper, self).__init__(parent)

        self.setWindowTitle("Modeling Helper")
        #self.setFixedSize(450, 150)

        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint) #Remove the ? button

        '''
        VARIABLES
        '''
        

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):

        '''
        DELIVERY
        '''

        self.deliveryGRB = QtWidgets.QGroupBox("Delivery")
        self.deliveryTypeBG = QtWidgets.QButtonGroup()
        self.deliveryOneRB = QtWidgets.QRadioButton("One Mesh")
        self.deliveryMultiRB = QtWidgets.QRadioButton("Multiple Meshes")
        self.deliveryTypeBG.addButton(self.deliveryOneRB)
        self.deliveryOneRB.setChecked(True)
        self.deliveryTypeBG.addButton(self.deliveryMultiRB)

        self.pivotCB = QtWidgets.QCheckBox("Pivot Position")
        self.pivotCB.setChecked(True)
        self.pivotCMB = QtWidgets.QComboBox()
        self.pivotCMB.addItem('Center')
        self.pivotCMB.addItem('Top')
        self.pivotCMB.addItem('Bottom')

        self.freezeCB = QtWidgets.QCheckBox("Freeze Transformation")
        self.freezeCB.setChecked(True)
        self.historyCB = QtWidgets.QCheckBox("Delete History")
        self.historyCB.setChecked(True)
        self.namingCB = QtWidgets.QCheckBox("Naming Convention")
        self.namingCB.setChecked(True)
        self.namingCMB = QtWidgets.QComboBox()
        self.namingCMB.addItem('CAPS')
        self.namingCMB.addItem('lower')

        self.positionCB = QtWidgets.QCheckBox("Position 0,0,0")
        self.positionCB.setChecked(True)
        self.positionCMB = QtWidgets.QComboBox()
        self.positionCMB.addItem('Center')
        self.positionCMB.addItem('Over')

        self.deliveryBTN = QtWidgets.QPushButton('GO')

        '''
        Utils
        '''
        self.utilsGRB = QtWidgets.QGroupBox("Utils")
        self.offsetCB = QtWidgets.QCheckBox("Offset Group")
        self.offsetCB.setChecked(True)
        self.offsetBTN = QtWidgets.QPushButton('GO')


    def createLayouts(self):
        
        mainLayout = QtWidgets.QVBoxLayout(self)
    
        """ SWAP LAYOUT """
        deliveryLYT = QtWidgets.QGridLayout()
        #deliveryLYT.setAlignment(QtCore.Qt.AlignCenter)
        
        deliveryLYT.addWidget(self.pivotCB, 0,0)
        deliveryLYT.addWidget(self.pivotCMB, 0,1)
        deliveryLYT.addWidget(self.freezeCB, 1,0)
        deliveryLYT.addWidget(self.historyCB, 2,0)
        deliveryLYT.addWidget(self.namingCB, 3,0)
        deliveryLYT.addWidget(self.namingCMB, 3,1)
        deliveryLYT.addWidget(self.positionCB, 4,0)
        deliveryLYT.addWidget(self.positionCMB, 4,1)
        
        deliveryLYT.addWidget(self.deliveryBTN, 5,0)

        self.deliveryGRB.setLayout(deliveryLYT)


        utilsLYT = QtWidgets.QGridLayout()
        utilsLYT.addWidget(QtWidgets.QLabel('File Type: '), 0,0)
        utilsLYT.addWidget(self.deliveryOneRB, 0,1)
        utilsLYT.addWidget(self.deliveryMultiRB, 0,2)
        utilsLYT.addWidget(self.offsetCB, 1,0)
        utilsLYT.addWidget(self.offsetBTN, 1,1)

        self.utilsGRB.setLayout(utilsLYT)
        
        """ MAIN LAYOUT """
        mainLayout.addWidget(self.deliveryGRB)
        mainLayout.addWidget(self.utilsGRB)
        self.setLayout(mainLayout)

    def createConnections(self):
        self.deliveryBTN.clicked.connect(self.onClick_deliveryBTN)
        self.offsetBTN.clicked.connect(self.onClick_offsetBTN)

    def onClick_deliveryBTN(self):
        selectedObjects = mc.ls(selection=True)
        newObjects = []
        

        for obj in selectedObjects:

            children = mc.listRelatives(obj, allDescendents=True, type='transform')
            family =  [obj] + (children or []) 
            family.reverse()

            for member in family:

                if self.pivotCB:
                    self.setPivotPosition(member, self.pivotCMB.currentIndex())
                    
                if self.freezeCB:
                    mc.makeIdentity(member, apply=True, translate=True, rotate=True, scale=True, normal=False)
                
                if self.historyCB:
                    mc.delete(member, constructionHistory=True)

                if self.namingCB:
                    newName = self.checkNaming(member, self.namingCMB.currentIndex())
                    if newName != member:
                        mc.rename(member,newName)
                        
                    if member == obj:
                        obj = newName

            if self.positionCB:
                #obj = self.checkNaming(obj, self.namingCMB.currentIndex())
                self.transformationZero(obj, self.positionCMB.currentIndex())
        

        mc.select(clear=True)

    def onClick_offsetBTN(self):

        selectedObjects = mc.ls(selection=True)
        newObjects = []
        

        for obj in selectedObjects:

            if self.offsetCB:
                parts = obj.split('_')
                basename = '_'.join(parts[:-1])

                offsetGroupName = basename + '_OFF'

                # Check if the offset group already exists to avoid naming conflict
                if not mc.objExists(offsetGroupName):
                    offsetGroup = mc.group(empty=True, name=offsetGroupName)
                else:
                    offsetGroup = offsetGroupName  # just reuse existing one

                descendants = mc.listRelatives(obj, allDescendents=True) or []
                if offsetGroup not in descendants and obj != offsetGroup:
                    mc.parent(obj, offsetGroup)
                
                newGroupName = basename+'_GRP'

                if not mc.objExists(newGroupName):
                    newGroup = mc.group(empty=True, name=newGroupName)
                    mc.parent(offsetGroup, newGroup)
                else:
                    newGroup = newGroupName

                newObjects.append(newGroup)

        # IF FileType is ONE MESH
        if self.deliveryOneRB.isChecked():
            filename = mc.file(query=True, sceneName=True, shortName=True)
            basename, ext = os.path.splitext(filename)
            parts = basename.split('_')

            if len(parts) > 1:
                basename = '_'.join(parts[:-1]) # Remove last part (e.g., 'v0001')

            if self.namingCMB.currentIndex() == 0:
                basename = basename.upper()
            elif self.namingCMB.currentIndex() == 1:
                basename = basename.lower()

           
            newGroup = mc.group(empty=True, name=basename+'_GRP')
            for obj in newObjects:
                mc.parent(obj, newGroup)

        mc.select(clear=True)



#region Transformation

    def transformationZero(self, obj, index):
        # Create a locator
        loc = mc.spaceLocator(name=obj + '_tempLoc')[0]

        if index == 0: 
            pivotY = 'neutral'
        else:
            pivotY = 'negative'
        
        pivotPos = self.getPivotPos(obj, 'neutral', pivotY,'neutral')
        # Move the locator to the pivot position
        mc.xform(loc, worldSpace=True, translation=pivotPos)
        
        # Parent the object to the locator
        mc.parent(obj, loc)
        
        # Move the locator to world origin (0,0,0)
        mc.xform(loc, worldSpace=True, translation=(0, 0, 0))
        
        # Unparent the object (keeping world transform)
        mc.parent(obj, world=True)
        
        # Delete the locator
        mc.delete(loc)

        mc.makeIdentity(obj, apply=True, translate=True, rotate=True, scale=True, normal=False)
        mc.delete(obj, constructionHistory=True)

#endregion

#region Naming Convention

    def checkNaming(self, obj, index):
        validSuffixes = ['GEO', 'GRP', 'OFFSET']
        addSuffix = False

        # Get the parts
        parts = obj.split('_')
        suffix = ''
        baseName = ''

        # Step 1: Extract suffix if possible
        if len(parts) > 1:
            suffix = parts[-1]
        
        # Step 2: Build baseName according to number of parts
        if len(parts) >= 3:
            baseName = '_'.join(parts[:2])  # first two parts only
        elif len(parts) == 2:
            baseName = parts[0]  # maybe missing suffix
        else:
            baseName = obj  # just one part


        # Step 3: Check suffix validity
        if suffix not in validSuffixes:
            suffix = self.getSuffix(obj)  # returns proper suffix with underscore
        else:
            # Suffix is valid, so keep it as is
            suffix = '_' + suffix
        
        # Apply casing
        if index == 0:
            baseName = baseName.upper()
        elif index == 1:
            baseName = baseName.lower()

        if addSuffix:
            suffix = self.getSuffix(obj)


        # Recompose the name
        newName = baseName + suffix

        if newName != obj:
            return newName
        else:
            return obj
        

    def getSuffix(self, obj):
        objType = mc.nodeType(obj)

        if objType == 'transform':
            shapes = mc.listRelatives(obj, shapes=True, fullPath=True) or []

            if any(mc.nodeType(shape) == 'mesh' for shape in shapes): # This is a mesh transform
                suffix = '_GEO'
            else: # This is a group transform
                suffix = '_GRP'

        return suffix    
            



#endregion

#region Pivot Position 

    def setPivotPosition(self, obj, index):

        if index == 0: # Center
            self.movePivot(obj, 'neutral','neutral','neutral')
        elif index == 1: # Top
            self.movePivot(obj, 'neutral','positive','neutral')
        elif index == 2: # Bottom
            self.movePivot(obj, 'neutral','negative','neutral')


    def movePivot(self, obj, choiceX, choiceY, choiceZ):
        pivotPos = self.getPivotPos(obj, choiceX, choiceY, choiceZ)

        mc.xform(obj, pivots=pivotPos, ws=True)

    def getPivotPos(self, obj, choiceX, choiceY, choiceZ):
        objBoundaries = mc.exactWorldBoundingBox(obj)
        # min_x, min_y, min_z, max_x, max_y, max_z = bbox

        valueX = self.getMinMax(objBoundaries[0],objBoundaries[3],choiceX)
        valueY = self.getMinMax(objBoundaries[1],objBoundaries[4],choiceY)
        valueZ = self.getMinMax(objBoundaries[2],objBoundaries[5],choiceZ)

        return (valueX, valueY, valueZ)

    def getMinMax(self, minimun,maximun,choice):
        value = 0
        if choice == 'negative':
            value = minimun
        elif choice == 'neutral':
            value = (minimun + maximun) / 2
        elif choice == 'positive':
            value = maximun

        return value

#endregion

if __name__ == "__main__":
    # Create 
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = kt_modelingHelper() 
    window.show()