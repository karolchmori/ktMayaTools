import maya.cmds as mc
import maya.OpenMayaUI as omui
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

        self.charPathTXT = QtWidgets.QLineEdit()
        self.charPathTXT.setEnabled(False)
        self.charVersionCMB = QtWidgets.QComboBox()

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
        self.exportLYT.addWidget(QtWidgets.QLabel('Character'),0,0)
        self.exportLYT.addWidget(QtWidgets.QLabel('Path'),1,0)
        self.exportLYT.addWidget(self.charPathTXT, 1,1)
        self.exportLYT.addWidget(QtWidgets.QLabel('v'),1,2)
        self.exportLYT.addWidget(self.charVersionCMB, 1,3)
        

        self.exportLYT.addWidget(QtWidgets.QLabel('Camera'),2,0)
        self.exportLYT.addWidget(QtWidgets.QLabel('Path'),3,0)
        self.exportLYT.addWidget(self.camPathTXT, 3,1)
        self.exportLYT.addWidget(QtWidgets.QLabel('v'),3,2)
        self.exportLYT.addWidget(self.camVersionCMB, 3,3)
        

        """ MAIN LAYOUT """
        mainLayout.addLayout(self.shotInfoLYT)
        mainLayout.addLayout(self.exportLYT)
        mainLayout.addWidget(self.exportBTN)
        self.setLayout(mainLayout)
        
        
    def createConnections(self):
        pass

    def loadUI(self):
        pass
        # 1. Detect file Path
            # 1.1 Fill the path to export Character
                # 1.1.1 Detect the version. Order descendant
            # 1.2. Fill the path to export Camera
                # 1.2.1 Detect the version. Order descendant
            
        # 2. Detect SEQ and SHOT
        # 3. Detect frame range

    def frameCheck(self):
        pass
        # 1. After lineEdit, detect the min and max
        # 2. Min has to be <= than Max, if not write Max
        # 3. Max has to be >= than Min, if not write Min
    
    def loadShotInfo(self):
        pass

    def loadFrameRange(self):
        pass

    def resetFrameRange(self):
        self.loadFrameRange()
    

    def exportUSD(self):
        #help_info = mc.help('mayaUSDExport')
        #print(help_info)

        filePath = "D:/USD_Animation/test/automatic_export_v05.usd"


        mc.mayaUSDExport(
            file=filePath,
            selection=True,
            # ------------------------
            # --- Include Options ---
            # ------------------------
            # TODO Include these insputs History, Channels, Expressions, Constrains (Usually not exported to USD)
            shadingMode="none",


            # ------------------------
            # --- Output Options -----
            # ------------------------
            defaultUSDFormat="usda",
            # TODO: defaultPrim="Aychedral_Rigging_varyndor", 


            # ------------------------
            # --- Geometry Options ---
            # ------------------------
            # 
            defaultMeshScheme="catmullClark",
            exportColorSets=False,
            exportComponentTags=False,
            exportUVs=True,
            filterTypes="nurbsCurve",

            # ------------------------
            # ------  Materials ------
            # ------------------------
            exportMaterials=False,

            # ------------------------
            # ------  Animation ------
            # ------------------------
            #animation=True,
            frameRange=(1119, 1279), # Start and End frames

            # ------------------------
            # ------  Advanced ------
            # ------------------------
            excludeExportTypes=["Cameras","Lights"], #TODO: "Meshes"
            exportVisibility=False,

            mergeTransformAndShape=True,
            includeEmptyTransforms=True,
            stripNamespaces=True
            # TODO: unit=?? unit=mayaPrefs
            # TODO: metersPerUnit
            
            )



if __name__ == "__main__":
    # Create 
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = usdAnimation() 
    window.show()