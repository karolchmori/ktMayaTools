import maya.cmds as mc
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import importlib
import random

try:
    from PySide6 import QtCore, QtWidgets, QtGui
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui
    from shiboken2 import wrapInstance

class ktRangeSlider(QtWidgets.QWidget):
    # Define a custom signal to notify when the value changes
    valueChangedEvent = QtCore.Signal(float)

    def __init__(self, textWidth=60, sliderWidth=150, devValue=0, minValue=0, maxValue=10, showValueField=True, showMinMaxField=True, stepSize=1, enabled=True):
        super().__init__()

        """
        Variables definition
        """
        self.textWidth = textWidth
        self.sliderWidth = sliderWidth
        self.devValue = devValue
        self.minValue = minValue
        self.maxValue = maxValue
        self.showValueField = showValueField
        self.showMinMaxField = showMinMaxField
        self.stepSize = stepSize
        self.enabled = enabled
        
        """
        UI Creation
        """
        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        # Scaling factor to allow fractional precision (not modifiable pre=2)
        self.scaleFactor = 100 
        
        # Scale values to integers
        self.minValueScaled = int(self.minValue * self.scaleFactor)
        self.maxValueScaled = int(self.maxValue * self.scaleFactor)
        self.stepSizeScaled = int(self.stepSize * self.scaleFactor)
        self.devValueScaled = int(self.devValue * self.scaleFactor)

        
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(self.minValueScaled, self.maxValueScaled)
        self.slider.setValue(self.devValueScaled)
        self.slider.setFixedWidth(self.sliderWidth)
        self.slider.setTickInterval(self.stepSizeScaled)
        self.slider.setSingleStep(self.stepSizeScaled)

        # Create QDoubleSpinBox for min and max
        self.minField = QtWidgets.QDoubleSpinBox()
        self.minField.setFixedWidth(self.textWidth)
        self.minField.setValue(self.minValue)
        self.minField.setSingleStep(self.stepSize)

        self.maxField = QtWidgets.QDoubleSpinBox()
        self.maxField.setFixedWidth(self.textWidth)
        self.maxField.setValue(self.maxValue)
        self.maxField.setSingleStep(self.stepSize)

        # Create QDoubleSpinBox for the slider's value
        self.valueField = QtWidgets.QDoubleSpinBox()
        self.valueField.setRange(self.minValue, self.maxValue)
        self.valueField.setFixedWidth(self.textWidth)
        self.valueField.setSingleStep(self.stepSize)
        self.valueField.setValue(self.slider.value() / self.scaleFactor)
        
        self.setEnabled(self.enabled)

    def createLayouts(self):
        mainLayout = QtWidgets.QHBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        if self.showValueField:
            mainLayout.addWidget(self.valueField)
        
        mainLayout.addWidget(self.slider)

        if self.showMinMaxField:
            mainLayout.addWidget(self.minField)
            mainLayout.addWidget(self.maxField)

    def createConnections(self):
        """When values change update the widgets with the functions innit"""
        self.slider.valueChanged.connect(self.__onSliderValueChanged)
        self.minField.valueChanged.connect(self.__setMinSlider)
        self.maxField.valueChanged.connect(self.__setMaxSlider)
        self.valueField.valueChanged.connect(self.__setSliderValue)
    

    def setEnabled(self, enabled):
        self.slider.setEnabled(enabled)
        self.minField.setEnabled(enabled)
        self.maxField.setEnabled(enabled)
        self.valueField.setEnabled(enabled)

    def setMinValue(self, value):
        self.minField.setValue(value)
        self.setMinSlider()
    
    def setMaxValue(self, value):
        self.maxField.setValue(value)
        self.setMaxSlider()
    
    def setValueField(self, value):
        self.valueField.setValue(value)
        self.__setSliderValue()

    def __onSliderValueChanged(self):
        """This function will be called whenever the slider value changes, and will 
            emit a custom signal when the slider value changes"""
        self.valueField.setValue(self.slider.value() / self.scaleFactor)
        self.valueChangedEvent.emit(self.valueField.value())
        #print(f"Slider value changed: {value}")

    def __setMinSlider(self):
        """Update the slider's minimum value based on the input."""
        self.minValueScaled = int(self.minField.value() * self.scaleFactor)

        """If the min value is smaller than max then update it, otherwise revert it"""
        if self.minValueScaled < self.maxValueScaled:
            self.slider.setMinimum(self.minValueScaled)
            self.valueField.setMinimum(self.slider.minimum() / self.scaleFactor)
        else:
            self.minField.setValue(self.slider.minimum() / self.scaleFactor)

    def __setMaxSlider(self):
        """Update the slider's maximum value based on the input."""
        self.maxValueScaled = int(self.maxField.value() * self.scaleFactor)

        """If the max value is bigger than min then update it, otherwise revert it"""
        if self.maxValueScaled > self.minValueScaled:
            self.slider.setMaximum(self.maxValueScaled)
            self.valueField.setMaximum(self.slider.maximum() / self.scaleFactor)
        else:
            self.maxField.setValue(self.slider.maximum() / self.scaleFactor)
        

    def __setSliderValue(self):
        """Update the slider's value when the spinbox value changes."""
        self.slider.setValue(int(self.valueField.value() * self.scaleFactor))
    
    def getValue(self):
        return self.slider.value() / self.scaleFactor
    
    def getMinValue(self):
        return self.minField.value()
    
    def getMaxValue(self):
        return self.maxField.value()
    



def mayaMainWindow():
    mainWindowPTR = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPTR), QtWidgets.QWidget)


class randomizer(QtWidgets.QDialog):
    def __init__(self, parent=mayaMainWindow()):
        super(randomizer, self).__init__(parent)

        self.setWindowTitle("Randomizer")
        self.setFixedSize(520, 100)

        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint) #Remove the ? button

        '''
        VARIABLES
        '''
        self.objData = {}

        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def createWidgets(self):
        self.selBTN = QtWidgets.QPushButton("New Sel")
        self.selBTN.setFixedWidth(70)
        self.selSLD = ktRangeSlider(devValue=1, minValue=0, maxValue=1, showMinMaxField=False, stepSize=0.1, sliderWidth=100, enabled=False)
        self.resultBTN = QtWidgets.QPushButton("New Result")
        self.retouchBTN = QtWidgets.QPushButton("Retouch")
        self.resetBTN = QtWidgets.QPushButton("Reset")
        self.resetBTN.setFixedWidth(50)

        # --------------------------------------------
        self.optionsCMB = QtWidgets.QComboBox()
        self.optionsCMB.addItem('translation')
        self.optionsCMB.addItem('rotation')
        self.optionsCMB.addItem('scale')
        self.xAxisCB = QtWidgets.QCheckBox()
        self.xAxisCB.setChecked(True)
        self.yAxisCB = QtWidgets.QCheckBox()
        self.zAxisCB = QtWidgets.QCheckBox()
        self.transformSLD = ktRangeSlider(textWidth=55, enabled=False)

        self.setWidgetsEnabled(False)

    def createLayouts(self):
        
        mainLayout = QtWidgets.QVBoxLayout(self)
        
        """ Main section Grid """
        mainGridLYT = QtWidgets.QGridLayout(self)
        mainGridLYT.addWidget(self.selBTN, 0,0)
        mainGridLYT.addWidget(self.selSLD, 0,1)
        mainGridLYT.addWidget(self.resultBTN, 0,2)
        mainGridLYT.addWidget(self.retouchBTN, 0,3)
        mainGridLYT.addWidget(self.resetBTN, 0,4)

        """ Transformation Grid """
        coordGridLYT = QtWidgets.QGridLayout(self)
        coordGridLYT.setAlignment(QtCore.Qt.AlignCenter)
        coordGridLYT.addWidget(QtWidgets.QLabel('X'), 0,1, alignment=QtCore.Qt.AlignCenter)
        coordGridLYT.addWidget(QtWidgets.QLabel('Y'), 0,2, alignment=QtCore.Qt.AlignCenter)
        coordGridLYT.addWidget(QtWidgets.QLabel('Z'), 0,3, alignment=QtCore.Qt.AlignCenter)
        coordGridLYT.addWidget(QtWidgets.QLabel('Range'), 0,4)
        coordGridLYT.addWidget(QtWidgets.QLabel('Min'), 0,8)
        coordGridLYT.addWidget(QtWidgets.QLabel('Max'), 0,9)

        coordGridLYT.addWidget(self.optionsCMB, 1,0)
        coordGridLYT.addWidget(self.xAxisCB, 1,1)
        coordGridLYT.addWidget(self.yAxisCB, 1,2)
        coordGridLYT.addWidget(self.zAxisCB, 1,3)
        coordGridLYT.addWidget(self.transformSLD, 1,4,1,6)

        mainLayout.addLayout(mainGridLYT)
        mainLayout.addLayout(coordGridLYT)

        self.setLayout(mainLayout)

    def createConnections(self):
        self.selBTN.clicked.connect(self.createSelection)
        self.resultBTN.clicked.connect(self.generateNewResult)
        self.retouchBTN.clicked.connect(self.retouchResult)
        self.resetBTN.clicked.connect(self.resetValues)
        self.selSLD.valueChangedEvent.connect(self.randomSelection)
        self.transformSLD.valueChangedEvent.connect(self.generateResult)

    def createSelection(self):
        '''
        Save all transformation values, "translate","rotate","scale"
        '''
        self.objData.clear()
        self.selectedObjects = mc.ls(selection=True, flatten=True)

        if self.selectedObjects:
            self.setWidgetsEnabled(True)

            for obj in self.selectedObjects:
                translate = mc.xform(obj, query=True, worldSpace=True, translation=True)
                rotate = mc.xform(obj, query=True, worldSpace=True, rotation=True)
                scale = mc.xform(obj, query=True, worldSpace=True, scale=True)

                self.objData[obj] = {
                    'translation': translate,
                    'rotation': rotate,
                    'scale': scale
                }
        else:
            om.MGlobal.displayError("Please select any object.")

        # Print the dictionary to verify
        #print(self.objData)


    def randomValues(self, range, xBool, yBool, zBool):
        newValues = [0.0, 0.0, 0.0]

        if xBool:
            newValues[0] = random.uniform(range[0], range[1])
        if yBool:
            newValues[1] = random.uniform(range[0], range[1])
        if zBool:
            newValues[2] = random.uniform(range[0], range[1])

        return newValues
    
    
    def generateResult(self, value):
        """
        - Get transformation
        - Gather Checkboxes to see which axis to apply
        - Get value of the slider
        - Apply transformation
        """
        transform = self.optionsCMB.currentText()
        boolValues = [self.xAxisCB.isChecked(), self.yAxisCB.isChecked(), self.zAxisCB.isChecked()]
        minVal = self.transformSLD.getMinValue()
        maxVal = float(value)

        if self.objData:
            if self.selectedObjects:
                for obj in self.selectedObjects:
                    if obj in self.objData:
                        initialPosition = self.objData[obj][transform]
                        
                        newPosition = self.randomValues([minVal, maxVal], *boolValues)

                        if transform == 'scale':
                            newPosition[1] = newPosition[0] if boolValues[1] else 0.0
                            newPosition[2] = newPosition[0] if boolValues[2] else 0.0

                        resultingPosition = [initialPosition[0] + newPosition[0], 
                                             initialPosition[1] + newPosition[1], 
                                             initialPosition[2] + newPosition[2]]
                        
                        print(f"{obj} transform: {transform}, initial pos: {initialPosition}, resultingPos: {resultingPosition}")
                        mc.xform(obj, **{transform: resultingPosition})
                    else:
                        om.MGlobal.displayWarning(f"The {obj} wasn't found in the selection. Skipping")
        else:
            om.MGlobal.displayError(f"No selection was made. Please create a selection.")

    def generateNewResult(self):
        self.generateResult(self.transformSLD.getValue())

    def randomSelection(self, value):
        originalSelection = list(self.objData.keys())
        numSelect = int(float(value) * len(originalSelection))

        # Randomly select a subset
        selectedSubset = random.sample(originalSelection, numSelect)
        mc.select(selectedSubset)

    def retouchResult(self):
        #Check if two objects Bounding Box intercept
        def checkIntersectionBBox(mesh1, mesh2):
            bbox1 = mc.exactWorldBoundingBox(mesh1)
            bbox2 = mc.exactWorldBoundingBox(mesh2)

            xmin1, ymin1, zmin1, xmax1, ymax1, zmax1 = bbox1
            xmin2, ymin2, zmin2, xmax2, ymax2, zmax2 = bbox2
            
            # Check for intersection
            if (xmin1 <= xmax2 and xmax1 >= xmin2 and
                ymin1 <= ymax2 and ymax1 >= ymin2 and
                zmin1 <= zmax2 and zmax1 >= zmin2):
                return True
            else:
                return False

        #Get the list of the objects that are touching
        def checkTouchingObjList(selectedObjects):
            touched = set()  # Keeps track of objects that have already been checked
            finalObjects = []

            for i in range(len(selectedObjects)):
                obj1 = selectedObjects[i]
                for j in range(i + 1, len(selectedObjects)):
                    obj2 = selectedObjects[j]
                    if obj2 in touched:
                        break
                    if checkIntersectionBBox(obj1, obj2):
                        finalObjects.append((obj2))
                        touched.add(obj2)
                        break  # Move to the next object after finding a touching pair
            return finalObjects
        
        # --------------------------------------------------------------------------
        if self.objData:
            selectedObjects = list(self.objData.keys())
            touchingObjects = []
            
            max_iterations = 100
            iteration_count = 0

            #Will break when all objects are in the same position
            while iteration_count < max_iterations:
                touchingObjects = checkTouchingObjList(selectedObjects)
                if touchingObjects:
                    mc.select(touchingObjects)
                    self.generateNewResult()
                    iteration_count += 1
                else:
                    break

            if iteration_count >= max_iterations:
                om.MGlobal.displayWarning("Max iterations reached. Objects may still be touching. Try again")
            
            mc.select(selectedObjects)
        else:
            om.MGlobal.displayError(f"No selection was made. Please create a selection.")
    
    def resetValues(self):
        mc.select(cl=True)
        self.setWidgetsEnabled(False)
        
        self.selSLD.setValueField(1)
        self.transformSLD.setValueField(0)
        self.transformSLD.setMinValue(0)
        self.transformSLD.setMaxValue(10)
        self.optionsCMB.setCurrentIndex(0)
        self.xAxisCB.setChecked(True)
        self.yAxisCB.setChecked(False)
        self.zAxisCB.setChecked(False)
        self.objData.clear()

    def setWidgetsEnabled(self, value):
        self.selSLD.setEnabled(value)
        self.optionsCMB.setEnabled(value)
        self.xAxisCB.setEnabled(value)
        self.yAxisCB.setEnabled(value)
        self.zAxisCB.setEnabled(value)
        self.transformSLD.setEnabled(value)
        self.resetBTN.setEnabled(value)
        self.resultBTN.setEnabled(value)
        self.retouchBTN.setEnabled(value)
        


if __name__ == "__main__":
    # Create 
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = randomizer() 
    window.show()