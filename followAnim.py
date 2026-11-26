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

    {"name": "ovlOvershoot", "label": "Overshoot", "type": "double", "default": 0.5,
     "min": 0.0, "max": 1.0},                                                                      # Counter swing

    # Delay and falloff along the chain
    {"name": "ovlDelay", "label": "Delay", "type": "double", "default": 2.0, "min": 0.0},           # Frames
    {"name": "ovlFalloff", "label": "Falloff", "type": "double", "default": 60.0},                  # Percentage
    {"name": "ovlFalloffStart", "label": "Falloff Start", "type": "double", "default": 70.0,
     "min": 1.0, "max": 100.0},                                                                     # Percentage
]

# Wave settings from older versions, removed from controllers that still have them
OLD_ATTRS = ["ovlWave", "ovlAmpX", "ovlAmpY", "ovlAmpZ", "ovlCyLen"]


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

// 7. Apply movement
float $dx = ($drag.x) * $ampMultiplier;
float $dy = ($drag.y) * $ampMultiplier;
float $dz = ($drag.z) * $ampMultiplier;

@Driven.rotateX = clamp(-$maxAngle, $maxAngle, $dx);
@Driven.rotateY = clamp(-$maxAngle, $maxAngle, $dy);
@Driven.rotateZ = clamp(-$maxAngle, $maxAngle, $dz);
"""


# ---------------------------------------------------------------- math helpers
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


def mayaMainWindow():
    mainWindowPTR = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPTR), QtWidgets.QWidget)


class followAnim(QtWidgets.QDialog):

    def __init__(self, parent=mayaMainWindow()):

        super(followAnim, self).__init__(parent)

        self.setWindowTitle("Overlapping Animation")
        self.setMinimumSize(400, 100)

        self.selectedCurve = None
        self.rootObject = None

        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.loadFrameRange()
        self.updateButtons()

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

        bakeLYT = QtWidgets.QHBoxLayout()
        bakeLYT.addWidget(QtWidgets.QLabel('Start'))
        bakeLYT.addWidget(self.frameMinSB)
        bakeLYT.addWidget(QtWidgets.QLabel('End'))
        bakeLYT.addWidget(self.frameMaxSB)
        bakeLYT.addWidget(self.bakeKeysBTN)

        mainLayout.addLayout(pickLYT)
        mainLayout.addLayout(actionsLYT)
        mainLayout.addLayout(bakeLYT)
        mainLayout.addStretch()

    def createConnections(self):
        self.loadBTN.clicked.connect(self.onClick_loadBTN)
        self.loadRootBTN.clicked.connect(self.onClick_loadRootBTN)
        self.createBTN.clicked.connect(self.onClick_createBTN)
        self.deleteBTN.clicked.connect(self.onClick_deleteBTN)
        self.bakeKeysBTN.clicked.connect(self.onClick_bakeBTN)

    def loadFrameRange(self):
        """Load timeline frame range into input fields."""
        start = int(mc.playbackOptions(q=True, min=True))
        end = int(mc.playbackOptions(q=True, max=True))

        self.frameMinSB.setValue(start)
        self.frameMaxSB.setValue(end)

    def updateButtons(self):
        hasChain = self.selectedCurve is not None
        self.createBTN.setEnabled(hasChain and self.rootObject is not None)
        self.deleteBTN.setEnabled(hasChain)
        self.bakeKeysBTN.setEnabled(hasChain)

    def onClick_loadBTN(self):
        selected = mc.ls(selection=True, long=True) or []
        self.selectedCurve = None
        self.selectedTXT.setText("")

        if selected and mc.listRelatives(selected[0], shapes=True, type="nurbsCurve"):
            self.selectedCurve = selected[0]
            self.selectedTXT.setText(selected[0].split("|")[-1])
        else:
            om.MGlobal.displayError("Please select a curve.")

        self.updateButtons()

    def onClick_loadRootBTN(self):
        selected = mc.ls(selection=True, long=True, type="transform") or []
        self.rootObject = None
        self.rootTXT.setText("")

        if selected:
            self.rootObject = selected[0]
            self.rootTXT.setText(selected[0].split("|")[-1])
        else:
            om.MGlobal.displayError("Please select the root (curve, joint or transform).")

        self.updateButtons()

    def onClick_createBTN(self):
        chain = self.getDescendants(self.selectedCurve)

        if self.rootObject in chain:
            om.MGlobal.displayError("The root cannot be part of the driven chain.")
            return

        # Remove a previous system so the chain goes back to rest
        self.deleteExpressions(self.selectedCurve)

        busy = [f"{c}.{a}" for c in chain for a in ROTATE_ATTRS
                if mc.getAttr(f"{c}.{a}", lock=True)
                or mc.listConnections(f"{c}.{a}", source=True, destination=False)
                or mc.listConnections(f"{c}.rotate", source=True, destination=False)]
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

        mc.bakeResults(chain, attribute=ROTATE_ATTRS, time=(start, end),
                       simulation=True, preserveOutsideKeys=True)

        for name in names:
            if mc.objExists(name):
                mc.delete(name)

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

            if direction is None:
                chainAxis = [1.0, 0.0, 0.0]
            else:
                chainAxis = normalize([dot(direction, axis) for axis in axes])

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

            mc.expression(string=expression, name=exprName(ctrl),
                          alwaysEvaluate=True, unitConversion="all")

    def deleteExpressions(self, master):
        for ctrl in self.getDescendants(master):
            name = exprName(ctrl)
            if mc.objExists(name):
                mc.delete(name)
                for attr in ROTATE_ATTRS:
                    if mc.getAttr(f"{ctrl}.{attr}", settable=True):
                        mc.setAttr(f"{ctrl}.{attr}", 0)

    def getDescendants(self, obj):
        descendants = mc.listRelatives(obj, allDescendents=True, fullPath=True, type="transform") or []
        curves = [c for c in reversed(descendants)
                  if mc.listRelatives(c, shapes=True, type="nurbsCurve")]
        return [obj] + curves

    def createAttributes(self, obj):
        for attr in ATTRS_LIST:
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

            if longName == "ovlSep":
                kwargs["enumName"] = "__________"
            if "min" in attr:
                kwargs["minValue"] = attr["min"]
            if "max" in attr:
                kwargs["maxValue"] = attr["max"]

            mc.addAttr(obj, **kwargs)

        self.deleteOldAttributes(obj)
        mc.setAttr(obj + ".ovlSep", edit=True, channelBox=True, lock=True)

        # Mark the curve to know it has Overlapping controls
        self.setWidthCurve(obj, 4)

    def deleteAttributes(self, obj):
        for attr in ATTRS_LIST:
            longName = attr["name"]
            if mc.attributeQuery(longName, node=obj, exists=True):
                if longName == "ovlSep":
                    mc.setAttr(obj + ".ovlSep", lock=False)  # Unlock the separator

                mc.deleteAttr(obj, attribute=longName)

        self.deleteOldAttributes(obj)
        self.setWidthCurve(obj, 1)

    def deleteOldAttributes(self, obj):
        for name in OLD_ATTRS:
            if mc.attributeQuery(name, node=obj, exists=True):
                mc.deleteAttr(obj, attribute=name)

    def setWidthCurve(self, obj, value):
        shapes = mc.listRelatives(obj, shapes=True, fullPath=True) or []
        for shape in shapes:
            mc.setAttr(shape + ".lineWidth", value)


if __name__ == "__main__":
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = followAnim()
    window.show()