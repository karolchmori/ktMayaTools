"""
User Information and Program Documentation

File: followAnim.py
Author: Karol Ch. Mori
Date: 2026-11-27
Version: 1.1.0

Description:
    This program is designed to create a simulation of a driven curve following the driver direction using expressions. 
    All the parameters are added to the master controller. It allows also to manually modify any rotation by using offset rotations. 
    Finally you can bake this animation or undo the baking to modify the parameters and be able to bake again.

User Information:
    - User Name: Karol Ch. Mori
    - User Email: karolchmori@hotmail.com
    - Purpose of Use: School projects (Non-Commercial)

Notes:
    Found a bug? Let me know before you start tweaking things! I'm always happy to improve this tool.

For support or inquiries, contact: karolchmori@hotmail.com
"""

import maya.cmds as mc
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import math

try:
    from PySide6 import QtCore, QtWidgets, QtGui
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui
    from shiboken2 import wrapInstance


ROTATE_ATTRS = ["rotateX", "rotateY", "rotateZ"]

ATTRS_LIST = [
    {"name": "ovlSep", "label": "OVERLAP", "type": "enum", "default": 0.0},                         # Separator

    # Follow the root (fake simulation)
    {"name": "ovlFollow", "label": "Follow Strength", "type": "double", "default": 1.0, "min": 0.0},
    {"name": "ovlDragT", "label": "Translate Drag", "type": "double", "default": 5.0},              # Degrees per unit/frame
    {"name": "ovlDragR", "label": "Rotate Drag", "type": "double", "default": 3.0},                 # Roughly frames of lag
    {"name": "ovlSmooth", "label": "Smoothing", "type": "double", "default": 3.0, "min": 0.1},      # Frames
    {"name": "ovlMaxAngle", "label": "Max Angle", "type": "double", "default": 45.0, "min": 0.0},   # Degrees
    {"name": "ovlOvershoot", "label": "Overshoot", "type": "double", "default": 0.5, "min": 0.0, "max": 1.0},      # Counter swing

    # Delay and falloff along the chain
    {"name": "ovlDelay", "label": "Delay", "type": "double", "default": 2.0, "min": 0.0},           # Frames
    {"name": "ovlFalloff", "label": "Falloff", "type": "double", "default": 60.0},                  # Percentage
    {"name": "ovlFalloffStart", "label": "Falloff Start", "type": "double", "default": 70.0, "min": 1.0, "max": 100.0},     # Percentage
]

# Per-controller attributes (created on every curve of the chain, master included)
OFFSET_ATTRS_LIST = [
    {"name": "ovlOffSep", "label": "OFFSET", "type": "enum", "default": 0.0},   # Separator
    {"name": "ovlOffsetRotX", "label": "Offset Rotation X", "type": "double", "default": 0.0},
    {"name": "ovlOffsetRotY", "label": "Offset Rotation Y", "type": "double", "default": 0.0},
    {"name": "ovlOffsetRotZ", "label": "Offset Rotation Z", "type": "double", "default": 0.0},
]

EXPR_TEMPLATE = """
// 1. Gather information from the master
float $delay = @Master.ovlDelay;
float $falloff = @Master.ovlFalloff * 0.01;
float $falloffStart = clamp(0.0, 0.9, @Master.ovlFalloffStart * 0.01);
float $follow = @Master.ovlFollow;
float $dragT = @Master.ovlDragT;
float $dragR = @Master.ovlDragR;
float $smooth = max(0.1, @Master.ovlSmooth);
float $maxAngle = @Master.ovlMaxAngle;
float $overshoot = @Master.ovlOvershoot;

// 2. Get this driven object's delay
float $index = @Index;
float $chainPos = $index / max(1.0, @ChainLen - 1.0);
float $t1 = frame - $delay * $index;
float $t0 = $t1 - $smooth;
float $t2 = $t0 - $smooth;

// 3. Sample the root in the past
float $m1[] = `getAttr -time $t1 "@Root.worldMatrix[0]"`;
float $m0[] = `getAttr -time $t0 "@Root.worldMatrix[0]"`;
float $m2[] = `getAttr -time $t2 "@Root.worldMatrix[0]"`;

vector $x1 = unit(<<$m1[0], $m1[1], $m1[2]>>);
vector $y1 = unit(<<$m1[4], $m1[5], $m1[6]>>);
vector $z1 = unit(<<$m1[8], $m1[9], $m1[10]>>);
vector $x0 = unit(<<$m0[0], $m0[1], $m0[2]>>);
vector $y0 = unit(<<$m0[4], $m0[5], $m0[6]>>);
vector $z0 = unit(<<$m0[8], $m0[9], $m0[10]>>);
vector $x2 = unit(<<$m2[0], $m2[1], $m2[2]>>);
vector $y2 = unit(<<$m2[4], $m2[5], $m2[6]>>);
vector $z2 = unit(<<$m2[8], $m2[9], $m2[10]>>);

// Root velocity (units per frame), in root space
vector $move = (<<$m1[12], $m1[13], $m1[14]>> - <<$m0[12], $m0[13], $m0[14]>>) / $smooth;
vector $vRoot = <<dot($move, $x1), dot($move, $y1), dot($move, $z1)>>;

// Root angular velocity (degrees per frame), in root space
vector $wRoot = <<asind(clamp(-1.0, 1.0, dot($y1, $z0))),
                  asind(clamp(-1.0, 1.0, dot($z1, $x0))),
                  asind(clamp(-1.0, 1.0, dot($x1, $y0)))>> / $smooth;

// Same speeds one step earlier
vector $oldMove = (<<$m0[12], $m0[13], $m0[14]>> - <<$m2[12], $m2[13], $m2[14]>>) / $smooth;
vector $vOld = <<dot($oldMove, $x0), dot($oldMove, $y0), dot($oldMove, $z0)>>;
vector $wOld = <<asind(clamp(-1.0, 1.0, dot($y0, $z2))),
                 asind(clamp(-1.0, 1.0, dot($z0, $x2))),
                 asind(clamp(-1.0, 1.0, dot($x0, $y2)))>> / $smooth;

// Overshoot: a change of speed adds a kick, so stopping swings past the rest pose
$vRoot = $vRoot + ($vRoot - $vOld) * $overshoot;
$wRoot = $wRoot + ($wRoot - $wOld) * $overshoot;

// 4. Convert to this controller's axes (measured in rest pose)
vector $o0 = @O0;
vector $o1 = @O1;
vector $o2 = @O2;
vector $v = <<dot($vRoot, $o0), dot($vRoot, $o1), dot($vRoot, $o2)>>;
vector $w = <<dot($wRoot, $o0), dot($wRoot, $o1), dot($wRoot, $o2)>>;

// 5. Drag: bend away from the movement, lag behind the turn
vector $chainAxis = @Axis;
vector $drag = (cross($v, $chainAxis) * $dragT - $w * $dragR) * $follow;

// 6. FallOff calculation
float $falloffPos = clamp(0.0, 1.0, ($chainPos - $falloffStart) / (1.0 - $falloffStart));
float $ampMultiplier = 1.0 + ($falloff * $falloffPos);

// 7. Apply movement + per-controller offset
float $dx = ($drag.x) * $ampMultiplier;
float $dy = ($drag.y) * $ampMultiplier;
float $dz = ($drag.z) * $ampMultiplier;

float $offX = @Driven.ovlOffsetRotX;
float $offY = @Driven.ovlOffsetRotY;
float $offZ = @Driven.ovlOffsetRotZ;

@Driven.rotateX = clamp(-$maxAngle, $maxAngle, $dx) + $offX;
@Driven.rotateY = clamp(-$maxAngle, $maxAngle, $dy) + $offY;
@Driven.rotateZ = clamp(-$maxAngle, $maxAngle, $dz) + $offZ;
"""


#region Global Helpers
def dot(a, b):
    return sum(i * j for i, j in zip(a, b))


def normalize(v, fallback=(1.0, 0.0, 0.0)):
    length = math.sqrt(dot(v, v))
    if length < 1e-6:
        return list(fallback)
    return [i / length for i in v]


def worldAxes(obj):
    m = mc.getAttr(obj + ".worldMatrix[0]")
    return [normalize(m[0:3]), normalize(m[4:7]), normalize(m[8:11])]


def melVector(v):
    return "<<{:.6f}, {:.6f}, {:.6f}>>".format(*v)


def exprName(obj):
    return mc.ls(obj)[0].replace("|", "_").replace(":", "_") + "_expr"

#endregion

def mayaMainWindow():
    mainWindowPTR = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPTR), QtWidgets.QWidget)


class followAnim(QtWidgets.QDialog):

    def __init__(self, parent=mayaMainWindow()):

        super(followAnim, self).__init__(parent)

        self.setWindowTitle("Follow Animation")
        self.setFixedSize(400, 200)

        self.selectedCurve = None
        self.rootObject = None

        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.loadUI()

    def createWidgets(self):
        self.selectedTXT = QtWidgets.QLineEdit()
        self.selectedTXT.setReadOnly(True)
        self.loadBTN = QtWidgets.QPushButton("Load")

        self.rootTXT = QtWidgets.QLineEdit()
        self.rootTXT.setReadOnly(True)
        self.loadRootBTN = QtWidgets.QPushButton("Load")

        self.createBTN = QtWidgets.QPushButton("Create system")
        self.deleteBTN = QtWidgets.QPushButton("Delete system")

        self.frameMinSB = QtWidgets.QSpinBox()
        self.frameMinSB.setRange(-100, 100000)
        self.frameMaxSB = QtWidgets.QSpinBox()
        self.frameMaxSB.setRange(-100, 100000)
        self.bakeKeysBTN = QtWidgets.QPushButton("Bake")
        self.undoBakeBTN = QtWidgets.QPushButton("Undo bake")

    def createLayouts(self):
        mainLayout = QtWidgets.QVBoxLayout(self)

        pickLYT = QtWidgets.QGridLayout()
        pickLYT.addWidget(QtWidgets.QLabel('Controller: '), 0, 0)
        pickLYT.addWidget(self.selectedTXT, 0, 1)
        pickLYT.addWidget(self.loadBTN, 0, 2)
        pickLYT.addWidget(QtWidgets.QLabel('Root: '), 1, 0)
        pickLYT.addWidget(self.rootTXT, 1, 1)
        pickLYT.addWidget(self.loadRootBTN, 1, 2)

        actionsLYT = QtWidgets.QGridLayout()
        actionsLYT.addWidget(self.createBTN, 0, 0, 1, 2)
        actionsLYT.addWidget(self.deleteBTN, 0, 2)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)

        bakeLYT = QtWidgets.QGridLayout()
        bakeLYT.addWidget(QtWidgets.QLabel('Start'), 0, 0)
        bakeLYT.addWidget(self.frameMinSB, 0, 1)
        bakeLYT.addWidget(QtWidgets.QLabel('End'), 0, 2)
        bakeLYT.addWidget(self.frameMaxSB, 0, 3)
        bakeLYT.addWidget(self.bakeKeysBTN, 1, 0, 1, 3)
        bakeLYT.addWidget(self.undoBakeBTN, 1, 3, 1, 1)

        mainLayout.addLayout(pickLYT)
        mainLayout.addLayout(actionsLYT)
        mainLayout.addWidget(line)
        mainLayout.addLayout(bakeLYT)
        mainLayout.addStretch()

    def createConnections(self):
        self.loadBTN.clicked.connect(self.onClick_loadBTN)
        self.loadRootBTN.clicked.connect(self.onClick_loadRootBTN)
        self.createBTN.clicked.connect(self.onClick_createBTN)
        self.deleteBTN.clicked.connect(self.onClick_deleteBTN)
        self.bakeKeysBTN.clicked.connect(self.onClick_bakeBTN)
        self.undoBakeBTN.clicked.connect(self.onClick_undoBakeBTN)

    def loadUI(self):
        """Load timeline frame range into input fields."""
        start = int(mc.playbackOptions(q=True, min=True))
        end = int(mc.playbackOptions(q=True, max=True))

        self.frameMinSB.setValue(start)
        self.frameMaxSB.setValue(end)

        self.updateButtons()

    #region Actions

    def onClick_loadBTN(self):
        selectedObjects = mc.ls(selection=True, long=True) or []
        self.selectedCurve = None
        self.selectedTXT.setText("")

        if selectedObjects and mc.listRelatives(selectedObjects[0], shapes=True, type="nurbsCurve"):
            self.selectedCurve = selectedObjects[0]
            self.selectedTXT.setText(self.selectedCurve.split("|")[-1])
        else:
            om.MGlobal.displayError("Please select a curve.")

        self.updateButtons()

    def onClick_loadRootBTN(self):
        selectedObjects = mc.ls(selection=True, long=True, type="transform") or []
        self.rootObject = None
        self.rootTXT.setText("")

        if selectedObjects:
            self.rootObject = selectedObjects[0]
            self.rootTXT.setText(self.rootObject.split("|")[-1])
        else:
            om.MGlobal.displayError("Please select the root (curve, joint or transform).")

        self.updateButtons()

    def onClick_createBTN(self):
        chain = self.getDescendants(self.selectedCurve)

        if self.rootObject in chain:
            om.MGlobal.displayError("The root cannot be part of the driven chain.")
            return

        busy = self.busyRotations(chain)
        if busy:
            om.MGlobal.displayError("These rotations are locked or connected: " + ", ".join(busy))
            return

        self.createAttributes(self.selectedCurve)
        self.createExpressions(self.selectedCurve, self.rootObject)

    def onClick_deleteBTN(self):
        self.deleteExpressions(self.selectedCurve)
        self.deleteAttributes(self.selectedCurve)

    def onClick_bakeBTN(self):
        chain = self.getDescendants(self.selectedCurve)
        names = [exprName(c) for c in chain]

        if not any(mc.objExists(n) for n in names):
            om.MGlobal.displayError("Nothing to bake, create the system first.")
            return

        start = self.frameMinSB.value()
        end = self.frameMaxSB.value()
        if end <= start:
            om.MGlobal.displayError("End frame must be greater than start frame.")
            return

        mc.bakeResults(chain, attribute=ROTATE_ATTRS, time=(start, end), simulation=True, preserveOutsideKeys=True)

        for name in names:
            if mc.objExists(name):
                mc.delete(name)

    def onClick_undoBakeBTN(self):
        """Delete the baked keys and build the expressions again.
        The Overlap and Offset attributes already exist, so their values are kept."""
        chain = self.getDescendants(self.selectedCurve)

        if self.rootObject in chain:
            om.MGlobal.displayError("The root cannot be part of the driven chain.")
            return

        if any(mc.objExists(exprName(c)) for c in chain):
            om.MGlobal.displayError("The expressions already exist, nothing to undo.")
            return

        if not mc.attributeQuery("ovlDelay", node=self.selectedCurve, exists=True):
            om.MGlobal.displayError("No overlap system found on this controller, use Create system.")
            return

        # The baked keys must be deleted first, otherwise the expressions can't drive the rotations -- gives an error
        self.clearBakedAnimation(chain)

        busy = self.busyRotations(chain)
        if busy:
            om.MGlobal.displayError("These rotations are still locked or connected: " + ", ".join(busy))
            return

        # Only adds what is missing
        self.createAttributes(self.selectedCurve)
        self.createExpressions(self.selectedCurve, self.rootObject)
    #endregion

    #region Logic creation

    def createExpressions(self, master, root):
        chain = self.getDescendants(master)
        nameMaster = mc.ls(master)[0]
        nameRoot = mc.ls(root)[0]

        # Put the chain in rest pose before measuring anything
        for ctrl in chain:
            for attr in ROTATE_ATTRS:
                mc.setAttr(f"{ctrl}.{attr}", 0)

        rootAxes = worldAxes(root)
        positions = [mc.xform(c, q=True, worldSpace=True, rotatePivot=True) for c in chain]

        # Measure everything before the first expression starts moving the chain
        setups = []
        direction = None
        for i, ctrl in enumerate(chain):
            axes = worldAxes(ctrl)

            # Each controller axis written in root space
            offsets = [[dot(axis, r) for r in rootAxes] for axis in axes]

            # Direction to the next controller (the last one reuses the previous)
            if i + 1 < len(chain):
                direction = [b - a for a, b in zip(positions[i], positions[i + 1])]

            chainAxis = [1.0, 0.0, 0.0] if direction is None else normalize([dot(direction, axis) for axis in axes])

            setups.append((offsets, chainAxis))

        for i, (ctrl, (offsets, chainAxis)) in enumerate(zip(chain, setups)):
            expression = (EXPR_TEMPLATE
                          .replace("@Master", nameMaster)
                          .replace("@Driven", mc.ls(ctrl)[0])
                          .replace("@Root", nameRoot)
                          .replace("@Index", str(i))
                          .replace("@ChainLen", str(len(chain)))
                          .replace("@O0", melVector(offsets[0]))
                          .replace("@O1", melVector(offsets[1]))
                          .replace("@O2", melVector(offsets[2]))
                          .replace("@Axis", melVector(chainAxis)))

            mc.expression(string=expression, name=exprName(ctrl), alwaysEvaluate=True, unitConversion="all")

    def deleteExpressions(self, master):
        for ctrl in self.getDescendants(master):
            name = exprName(ctrl)
            if mc.objExists(name):
                mc.delete(name)
                for attr in ROTATE_ATTRS:
                    if mc.getAttr(f"{ctrl}.{attr}", settable=True):
                        mc.setAttr(f"{ctrl}.{attr}", 0)

    def createAttributes(self, obj):
        # Master controls
        self.addAttributes(obj, ATTRS_LIST)

        # Offset controls on every curve of the chain (master included)
        for ctrl in self.getDescendants(obj):
            self.addAttributes(ctrl, OFFSET_ATTRS_LIST)

        # Mark the curve to know it has Overlapping controls
        self.setWidthCurve(obj, 4)

    def deleteAttributes(self, obj):
        for ctrl in self.getDescendants(obj):
            self.removeAttributes(ctrl, OFFSET_ATTRS_LIST)

        self.removeAttributes(obj, ATTRS_LIST)
        self.setWidthCurve(obj, 1)

    #endregion


    #region Helpers

    def addAttributes(self, obj, attrList):
        for attr in attrList:
            longName = attr["name"]
            if mc.attributeQuery(longName, node=obj, exists=True):
                continue

            kwargs = {
                "longName": longName,
                "niceName": attr["label"],
                "attributeType": attr["type"],
                "defaultValue": attr["default"],
                "keyable": True
            }

            if attr["type"] == "enum":
                kwargs["enumName"] = "__________"
            if "min" in attr:
                kwargs["minValue"] = attr["min"]
            if "max" in attr:
                kwargs["maxValue"] = attr["max"]

            mc.addAttr(obj, **kwargs)

            if attr["type"] == "enum":  # lock the separator
                mc.setAttr(f"{obj}.{longName}", edit=True, channelBox=True, lock=True)

    def removeAttributes(self, obj, attrList):
        for attr in attrList:
            longName = attr["name"]
            if mc.attributeQuery(longName, node=obj, exists=True):
                if attr["type"] == "enum":
                    mc.setAttr(f"{obj}.{longName}", lock=False)
                mc.deleteAttr(obj, attribute=longName)

    def busyRotations(self, chain):
        """Rotation channels that are locked or already driven by something."""
        return [f"{c}.{a}" for c in chain for a in ROTATE_ATTRS
                if mc.getAttr(f"{c}.{a}", lock=True)
                or mc.listConnections(f"{c}.{a}", source=True, destination=False)
                or mc.listConnections(f"{c}.rotate", source=True, destination=False)]

    def clearBakedAnimation(self, chain):
        """Delete the animation curves (and pairBlends) driving the rotations."""
        for ctrl in chain:
            for attr in ROTATE_ATTRS:
                plug = f"{ctrl}.{attr}"
                sources = mc.listConnections(plug, source=True, destination=False) or []

                for node in set(sources):
                    if not mc.objExists(node):
                        continue

                    if mc.nodeType(node) == "pairBlend":
                        curves = mc.listConnections(node, source=True, destination=False, type="animCurve") or []
                        mc.delete(list(set(curves)) + [node])
                    elif "animCurve" in mc.nodeType(node, inherited=True):
                        mc.delete(node)

    def setWidthCurve(self, obj, value):
        shapes = mc.listRelatives(obj, shapes=True, fullPath=True) or []
        for shape in shapes:
            mc.setAttr(shape + ".lineWidth", value)

    def getDescendants(self, obj):
        descendants = mc.listRelatives(obj, allDescendents=True, fullPath=True, type="transform") or []
        curves = [curve for curve in reversed(descendants) if mc.listRelatives(curve, shapes=True, type="nurbsCurve")]
        return [obj] + curves

    def updateButtons(self):
        hasCtrl = bool(self.selectedCurve)
        hasRoot = bool(self.rootObject)

        self.createBTN.setEnabled(hasCtrl and hasRoot)     # controller + root
        self.deleteBTN.setEnabled(hasCtrl)                 # controller
        self.bakeKeysBTN.setEnabled(hasCtrl)               # controller
        self.undoBakeBTN.setEnabled(hasCtrl and hasRoot)   # controller + root

    #endregion


if __name__ == "__main__":
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = followAnim()
    window.show()