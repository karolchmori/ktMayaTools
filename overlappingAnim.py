import maya.cmds as mc
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import re
import os


from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtGui

from shiboken6 import wrapInstance


ATTRS_LIST = [
    {"name": "ovlAmpX", "label": "Amplitude X", "default": 0.0},        # Degrees
    {"name": "ovlAmpY", "label": "Amplitude Y", "default": 0.0},        # Degrees
    {"name": "ovlAmpZ", "label": "Amplitude Z", "default": 10.0},       # Degrees
    {"name": "ovlCyLen", "label": "Cycle Length", "default": 100.0},    # Frames
    {"name": "ovlDelay", "label": "Delay", "default": 25.0},            # Degrees
    {"name": "ovlFalloff", "label": "Falloff", "default": 60.0},        # Percentage
]


def mayaMainWindow():
    mainWindowPTR = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPTR), QtWidgets.QWidget)

class overlappingAnim(QtWidgets.QDialog):

    
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
        self.createAttributes(self.selectedCurve)

        # 2. Mark the curve somehow to know it has Overlapping controls
        self.setWidthCurve(self.selectedCurve, 4)

        # 3. Get the curves from the hierarchy
        self.descendants = self.getDescendants(self.selectedCurve)
        print(self.descendants)
        # 4. Add expressions to all of them
        

    def onClick_deleteBTN(self):
        # 1. Get the curves from the hierarchy
        self.descendants = self.getDescendants(self.selectedCurve)        
                
        # 2. Delete expressions to all of them


        # 3. Delete the attributes on the selected curve
        self.deleteAttributes(self.selectedCurve)
        self.setWidthCurve(self.selectedCurve, 1)
        


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

    def createExpressions(self, obj):
        pass

    def getDescendants(self, obj):
        descendants = mc.listRelatives(obj, allDescendents=True, fullPath=True, type="transform" ) or []
        filteredCurves = [obj] + [ obj for obj in descendants if mc.listRelatives(obj, shapes=True, type="nurbsCurve") ]

        return filteredCurves

    def createAttributes(self, obj):
        exists = mc.attributeQuery("ovlSep", node=obj, exists=True)
        if not exists:
            mc.addAttr(obj, longName="ovlSep", niceName="OVERLAP", attributeType="enum", enumName="__________")
            mc.setAttr(obj + ".ovlSep", edit=True, channelBox=True, lock=True)

        for attr in ATTRS_LIST:
            longName = attr["name"]
            exists = mc.attributeQuery(longName, node=obj, exists=True)
            if not exists:
                kwargs = {
                    "longName": longName,
                    "niceName": attr["label"],
                    "attributeType": "double",
                    "defaultValue": attr["default"],
                    "keyable": True
                }

                if longName == "ovlCyLen":
                    kwargs["minValue"] = 1

                mc.addAttr(obj, **kwargs)

    def deleteAttributes(self, obj):
        # 1. Check if the attrb exists on the obj
        exists = mc.attributeQuery("ovlSep", node=obj, exists=True)
        # 2. If exists delete it
        if exists:
            mc.setAttr(obj + ".ovlSep", lock=False) # Unlock the separator
            mc.deleteAttr(obj, attribute="ovlSep")

        for attr in ATTRS_LIST:
            longName = attr["name"]
            exists = mc.attributeQuery(longName, node=obj, exists=True)
            if exists:
                mc.deleteAttr(obj, attribute=longName)


    def setWidthCurve(self, obj, value):
        shapes = mc.listRelatives(obj, shapes=True, fullPath=True) or []
        for shape in shapes:
            mc.setAttr(shape + ".lineWidth", value)



if __name__ == "__main__":
    # Create 
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = overlappingAnim() 
    window.show()