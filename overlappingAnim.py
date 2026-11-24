import maya.cmds as mc
import maya.OpenMaya as om
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

        self.setWidgetsEnabled(False)
        

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
        self.loadBTN.clicked.connect(self.onClick_loadBTN)
        self.createBTN.clicked.connect(self.onClick_createBTN)
        self.deleteBTN.clicked.connect(self.onClick_deleteBTN)

    def onClick_loadBTN(self):
        selectedObjects = mc.ls(selection=True, long=True) or []
        self.selectedCurve = None
        
        # 1. Select the objects, if not selected send an error 
        if selectedObjects:
            obj = selectedObjects[0]

            # 2. Detect if its a curve, if not send error, only check the first one selected
            if self.isCurve(obj):
                # 3. If its a curve save the full path and show short one for user
                self.selectedCurve = obj
                shortNameCurve = self.selectedCurve.split("|")[-1]
                print(self.selectedCurve)

                self.selectedTXT.setText(shortNameCurve)
                self.setWidgetsEnabled(True)
            else:
                self.selectedTXT.setText("")
                self.setWidgetsEnabled(False)
                om.MGlobal.displayError("Please select a curve.")
        else:
            self.setWidgetsEnabled(False)
            om.MGlobal.displayError("Please select any object.")
            

    def onClick_createBTN(self):
        # 1. Create the attributes on the selected curve


        # 2. Get the curves from the hierarchy


        # 3. Add expressions to all of them
        pass

    def onClick_deleteBTN(self):
        pass


    def setWidgetsEnabled(self, value):
        self.createBTN.setEnabled(value)
        self.deleteBTN.setEnabled(value)

    def isCurve(self, obj):
        shapes = mc.listRelatives(obj, shapes=True, fullPath=True) or []
        for shape in shapes:
            if mc.nodeType(shape) == "nurbsCurve":
                return shape
            else:
                return None


    def createAttributes(self, obj):
        mc.addAttr(obj, longName="ovlSep", niceName="OVERLAP", attributeType="enum", enumName="__________")
        mc.setAttr(obj + ".ovlSep", edit=True, channelBox=True, lock=True)


    def deleteAttributes(self, obj):
        # 1. Check if the attrb exists on the obj
        mc.attributeQuery("ovlSep", node=obj, exists=True)
        # 2. If exists delete it
        mc.deleteAttr(obj, attribute="ovlSep")



if __name__ == "__main__":
    # Create 
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = overlappingAnim() 
    window.show()