import maya.cmds as mc
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import re
import os

try:
    from PySide6 import QtCore, QtWidgets, QtGui
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui
    from shiboken2 import wrapInstance



ATTRS_LIST = [
    {"name": "ovlSep", "label": "OVERLAP", "type": "enum", "default": 0.0},                 # Separator
    {"name": "ovlWave", "label": "Wave Type", "type": "enum", "default": 0.0},              # Menu
    {"name": "ovlAmpX", "label": "Amplitude X", "type": "double", "default": 0.0},          # Degrees
    {"name": "ovlAmpY", "label": "Amplitude Y", "type": "double", "default": 0.0},          # Degrees
    {"name": "ovlAmpZ", "label": "Amplitude Z", "type": "double", "default": 10.0},         # Degrees
    {"name": "ovlCyLen", "label": "Cycle Length", "type": "double", "default": 100.0},      # Frames
    {"name": "ovlDelay", "label": "Delay", "type": "double", "default": 25.0},              # Degrees
    {"name": "ovlFalloff", "label": "Falloff", "type": "double", "default": 60.0},          # Percentage
    {"name": "ovlEnergy", "label": "Energy", "type": "double", "default": 100.0},           # Percentage
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
        self.loadFrameRange()

    def createWidgets(self):
        self.selectedTXT = QtWidgets.QLineEdit()
        self.selectedTXT.setReadOnly(True)
        self.loadBTN = QtWidgets.QPushButton("Load")
        self.createBTN = QtWidgets.QPushButton("Create system")
        self.deleteBTN = QtWidgets.QPushButton("Delete system")


        self.frameMinSB = QtWidgets.QSpinBox()
        self.frameMinSB.setRange(-100, 100000)
        self.frameMaxSB = QtWidgets.QSpinBox()
        self.frameMaxSB.setRange(-100, 100000)
        self.bakeKeysBTN = QtWidgets.QPushButton("Bake")

        self.setWidgetsEnabled(False)
        

    def createLayouts(self):
        mainLayout = QtWidgets.QVBoxLayout(self)

        self.hierarchyLYT = QtWidgets.QHBoxLayout(self)
        self.hierarchyLYT.addWidget(QtWidgets.QLabel('Controller: '))
        self.hierarchyLYT.addWidget(self.selectedTXT)
        self.hierarchyLYT.addWidget(self.loadBTN)


        self.actionsLYT = QtWidgets.QGridLayout()
        self.actionsLYT.addWidget(self.createBTN,0,0,1,2)
        self.actionsLYT.addWidget(self.deleteBTN,0,2)


        self.bakeLYT = QtWidgets.QHBoxLayout()
        self.bakeLYT.addWidget(QtWidgets.QLabel('Start'))
        self.bakeLYT.addWidget(self.frameMinSB)
        self.bakeLYT.addWidget(QtWidgets.QLabel('End'))
        self.bakeLYT.addWidget(self.frameMaxSB)
        self.bakeLYT.addWidget(self.bakeKeysBTN)

        mainLayout.addLayout(self.hierarchyLYT)
        mainLayout.addLayout(self.actionsLYT)

        mainLayout.addLayout(self.bakeLYT)
        
        mainLayout.addStretch()
        self.setLayout(mainLayout)
        

    def createConnections(self):
        self.loadBTN.clicked.connect(self.onClick_loadBTN)
        self.createBTN.clicked.connect(self.onClick_createBTN)
        self.deleteBTN.clicked.connect(self.onClick_deleteBTN)

    def loadFrameRange(self):
        """Load timeline frame range into input fields."""

        start = int(mc.playbackOptions(q=True, min=True))
        end = int(mc.playbackOptions(q=True, max=True))

        self.frameMinSB.setValue(start)
        self.frameMaxSB.setValue(end)

    def onClick_loadBTN(self):

        selectedObjects = mc.ls(selection=True, long=True) or []
        self.selectedCurve = None
        
        # 1. Select the objects, if not selected send an error 
        if selectedObjects:
            obj = selectedObjects[0]

            # 2. Detect if its a curve, if not send error, only check the first one selected
            if mc.listRelatives(obj, shapes=True, type="nurbsCurve"):
                # 3. If its a curve save the full path and show short one for user
                self.selectedCurve = obj
                shortNameCurve = self.selectedCurve.split("|")[-1]

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
        # 2. Add expressions to all of them
        self.createExpressions(self.selectedCurve)

    def onClick_deleteBTN(self):  
        # 1. Delete expressions to all of them
        self.deleteExpressions(self.selectedCurve)
        # 2. Delete the attributes on the selected curve
        self.deleteAttributes(self.selectedCurve)
        
    

    def setWidgetsEnabled(self, value):
        self.createBTN.setEnabled(value)
        self.deleteBTN.setEnabled(value)


    def createExpressions(self, obj):
        descendants = self.getDescendants(obj)
        
        for curve in descendants:
            nameCurve = curve.split("|")[-1]
            expression = f"{curve}.translateY = sin(time);"

            mc.expression(string=expression, name=nameCurve + "_expr", alwaysEvaluate=True, unitConversion="all")

    def deleteExpressions(self, obj):
        descendants = self.getDescendants(obj)

        for curve in descendants:
            nameCurve = curve.split("|")[-1]
            mc.delete(f"{nameCurve}_expr")


    def getDescendants(self, obj):
        descendants = mc.listRelatives(obj, allDescendents=True, fullPath=True, type="transform" ) or []
        filteredCurves = [obj] + [ obj for obj in descendants if mc.listRelatives(obj, shapes=True, type="nurbsCurve") ]

        return filteredCurves

    def createAttributes(self, obj):

        for attr in ATTRS_LIST:
            longName = attr["name"]
            exists = mc.attributeQuery(longName, node=obj, exists=True)
            if not exists:
                kwargs = {
                    "longName": longName,
                    "niceName": attr["label"],
                    "attributeType": attr["type"],
                    "defaultValue": attr["default"],
                    "keyable": True
                }

                if longName == "ovlSep":
                    kwargs["enumName"] = "__________"
                if longName == "ovlCyLen":
                    kwargs["minValue"] = 1
                if longName == "ovlEnergy":
                    kwargs["minValue"] = 5
                    kwargs["maxValue"] = 100
                

                mc.addAttr(obj, **kwargs)

        mc.setAttr(obj + ".ovlSep", edit=True, channelBox=True, lock=True)

        # 2. Mark the curve somehow to know it has Overlapping controls
        self.setWidthCurve(obj, 4)

    def deleteAttributes(self, obj):
        for attr in ATTRS_LIST:
            longName = attr["name"]
            exists = mc.attributeQuery(longName, node=obj, exists=True)
            if exists:

                if longName == "ovlSep":
                    mc.setAttr(obj + ".ovlSep", lock=False) # Unlock the separator
                
                mc.deleteAttr(obj, attribute=longName)

        self.setWidthCurve(obj, 1)

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