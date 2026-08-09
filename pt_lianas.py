import maya.cmds as mc
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import importlib
import random
import math


try:
    from PySide6 import QtCore, QtWidgets, QtGui
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui
    from shiboken2 import wrapInstance




def mayaMainWindow():
    mainWindowPTR = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPTR), QtWidgets.QWidget)


class pt_lianas(QtWidgets.QDialog):
    def __init__(self, parent=mayaMainWindow()):
        super(pt_lianas, self).__init__(parent)

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
        self.resultBTN = QtWidgets.QPushButton("New Result")
        self.retouchBTN = QtWidgets.QPushButton("Retouch")
        self.resetBTN = QtWidgets.QPushButton("Reset")
        self.resetBTN.setFixedWidth(50)


    def createLayouts(self):
        
        mainLayout = QtWidgets.QVBoxLayout(self)
        
        """ Main section Grid """
        mainGridLYT = QtWidgets.QGridLayout(self)
        mainGridLYT.addWidget(self.selBTN, 0,0)
        mainGridLYT.addWidget(self.resultBTN, 0,2)
        mainGridLYT.addWidget(self.retouchBTN, 0,3)
        mainGridLYT.addWidget(self.resetBTN, 0,4)

        mainLayout.addLayout(mainGridLYT)

        self.setLayout(mainLayout)

    def createConnections(self):
        pass

    
    def createRoot(self):
        rootGeo = mc.polyCube(n='root_GEO', w=0.5, d=1, h=3, sy=5)[0]


    def createRollito(self):
        # 1. Create the Profile and Path
        profile = mc.curve(d=1, p=[(-0.5,0,0), (0.5,0,0), (0.5,2,0), (-0.5,2,0), (-0.5,0,0)], k=[0,1,2,3,4])

        turns = 3
        segments = 60 
        radius_step = 2
        path_points = []
        for i in range(segments):
            angle = (float(i) / segments) * (turns * 2 * math.pi)
            r = 1 + (float(i) / segments) * (turns * radius_step) 
            x = r * math.cos(angle)
            z = r * math.sin(angle)
            path_points.append((x, 0, z))

        path = mc.curve(d=3, p=path_points)

        # 2. Extrude
        nurbs_result = mc.extrude(profile, path, et=2, fpt=True, ucp=1, sc=1)[0]

        # 3. Convert to Polygons using your exact MEL settings
        # Corrected flags for Python: pt=1 (Quads)
        poly_result = mc.nurbsToPoly(nurbs_result, 
                                    mnd=1, ch=1, f=3, pt=1, pc=200, chr=0.9, 
                                    ft=0.01, mel=0.001, d=0.1, ut=1, un=3, vt=1, vn=3, 
                                    uch=0, ucr=0, cht=0.2, es=0, ntr=0, mrt=0, uss=1)[0]

        # 4. Add Caps to the open ends
        # polyCloseBorder is the correct command to fill the holes
        mc.polyCloseBorder(poly_result, ch=False)

        # 5. Harden All Edges
        # Setting angle to 0 degrees makes the mesh look faceted
        mc.polySoftEdge(poly_result, angle=0, ch=False)

        # 6. Cleanup
        mc.delete(nurbs_result, profile, path)
        mc.xform(poly_result, cp=True)

        print("Hard-edged Polygon Roll with Caps created: " + poly_result)    

    def createRollitoAlrevez(self):
        
        # 1. Create the Profile
        profile = mc.curve(d=1, p=[(-0.5,0,0), (0.5,0,0), (0.5,2,0), (-0.5,2,0), (-0.5,0,0)], k=[0,1,2,3,4])

        # 2. Generate the Path (Starts away from center)
        turns = 2
        segments = 30 
        radius_start = 5.0  # Adjust this to control how "hollow" the center is
        radius_growth = 6.0 # INCREASED: This now moves 3.0 units outward per turn
        path_points = []

        for i in range(segments):
            angle = (float(i) / segments) * (turns * 2 * math.pi)
            # The radius starts at 'radius_start' instead of 0 or 1
            r = radius_start + (float(i) / segments) * radius_growth 
            x = r * math.cos(angle)
            z = r * math.sin(angle)
            path_points.append((x, 0, z))

        path = mc.curve(d=3, p=path_points)

        # 3. Extrude & Convert
        nurbs_result = mc.extrude(profile, path, et=2, fpt=True, ucp=1, sc=1)[0]
        poly_result = mc.nurbsToPoly(nurbs_result, mnd=1, ch=1, f=3, pt=1, pc=200, chr=0.9, 
                                    ft=0.01, mel=0.001, d=0.1, ut=1, un=3, vt=1, vn=3, 
                                    uch=0, ucr=0, cht=0.2, es=0, ntr=0, mrt=0, uss=1)[0]

        # 4. Cap and Harden
        mc.polyCloseBorder(poly_result, ch=False)
        mc.polySoftEdge(poly_result, angle=0, ch=False)

        # 5. Cleanup
        mc.delete(nurbs_result, profile, path)
        mc.xform(poly_result, cp=True)
    


    def export_mesh_info(mesh_name):
        """
        Export the mesh vertex positions, polygon counts, and vertex connections
        for a given mesh.
        """
        # 1. Get DAG path of the mesh
        sel = om.MSelectionList()
        sel.add(mesh_name)
        dag_path = sel.getDagPath(0)
        
        # 2. Get MFnMesh function set
        mesh_fn = om.MFnMesh(dag_path)
        
        # 3. Get vertex positions
        vertices = mesh_fn.getPoints(om.MSpace.kWorld)
        
        # 4. Get face info
        face_counts_per_polygon = []
        flattened_connections = []
        
        for i in range(mesh_fn.numPolygons):
            verts = mesh_fn.getPolygonVertices(i)  # returns list of vertex indices for this polygon
            face_counts_per_polygon.append(len(verts))
            flattened_connections.extend(verts)
        
        # 5. Print results
        print("Vertices:")
        for i, v in enumerate(vertices):
            print(f"{i}: ({v.x}, {v.y}, {v.z})")
        
        print("\nFace counts per polygon:", face_counts_per_polygon)
        print("Flattened vertex connections:", flattened_connections)
        
        return vertices, face_counts_per_polygon, flattened_connections

    


    def create_mesh_from_data(vertices, face_counts, connections, mesh_name='recreatedMesh'):
        fn_mesh = om.MFnMesh()
        new_mesh = fn_mesh.create(vertices, face_counts, connections)
        print(f"Mesh '{mesh_name}' created!")
        return new_mesh


    # Example usage
    vertices, face_counts, connections = export_mesh_info('LIANAS_V04_21')
    # Create the mesh
    new_mesh = create_mesh_from_data(vertices, face_counts, connections)


if __name__ == "__main__":
    # Create 
    try:
        window.close()  # type: ignore
        window.deleteLater()  # type: ignore
    except:
        pass

    window = pt_lianas() 
    window.show()