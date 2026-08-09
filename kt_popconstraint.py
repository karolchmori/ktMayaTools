import maya.cmds as mc
import json
import os
import math
import maya.mel as mel
import maya.OpenMaya as om

mainWidth = 450
mainHeight = 400

global vertexData
global geoData

#region Other Func



def getVertexInformation(geo):
    """ 
    #Function that checks all the position of the geo vertices and saves it in a list

    #Parameters:
        geo(str): name of the geo to check the vertices

    #Returns:
        verticesData(list): List of vertex information, with the following structure:
                {
                    "name": pCube1.vtx[50],
                    "index": 50,
                    "position": [5, 6, -1]
                }
    """
    #Select vertices of geometry
    mc.select(f"{geo}.vtx[*]")  
    vertices = mc.ls(sl=True, fl=True) 
    
    # Get world positions for each vertex
    verticesData = []
    for vtx in vertices:
        shortName = vtx.split(".")[-1]
        index = int(shortName.split("[")[-1][:-1])
        position = mc.pointPosition(vtx, world=True)

        #Append information
        verticesData.append({
            "name": f"{geo}.{shortName}",  
            "index": index,
            "position": position
        })

    return verticesData


def getClosestVertex(verticesData, geo):
    """ 
    #Function that gets the closest vertex of a geometry checking a given list with vertices position

    #Parameters:
        verticesData(list): list of vertices and position information
        geo(str): name of the geo to get the closest vertex

    #Returns:
        closestVertex(int): gets the index of the closest vertex (example: vtx[5] returns 5)
    """
    closestVertex = None
    minDistance = None

    #Get the position of the geometry
    geoPos = mc.xform(geo, q=True, ws=True, t=True)
    
    for vtx in verticesData:
        #Get the values needed from the list
        vtxIndex = vtx["index"]
        vtxPos = vtx["position"]

        #Euclidean formula
        distance = math.sqrt( 
            (geoPos[0] - vtxPos[0])**2 + 
            (geoPos[1] - vtxPos[1])**2 + 
            (geoPos[2] - vtxPos[2])**2
        )

        #Keep the mininum distance
        if minDistance:
            if distance < minDistance:
                minDistance = distance
                closestVertex = vtxIndex
        else:
            minDistance = distance
            closestVertex = vtxIndex

    return closestVertex


def popConstraint(mainGeo, secGeo):
    """
    #Function applies Poly on Point Constraint between two geometries (the first one is usually a vertex)
    The function is done in MEL because python has some bug where is not maintaining offsets even when applied it.

    #Parameters:
        mainGeo(str): name of the vertex to apply the constraint
        secGeo(str): name of the geo that will be constrained

    #Returns:
        None
    """
    if mc.objExists(mainGeo):
        if mc.objExists(secGeo):
            mc.select(mainGeo, secGeo)
            mel.eval('pointOnPolyConstraint -maintainOffset  -weight 1;')
        else:
            om.MGlobal.displayWarning(f"{secGeo} doesn't exist in the scene. Skipping")
    else:
        om.MGlobal.displayWarning(f"{mainGeo} doesn't exist in the scene. Skipping")


def listOnTable(table, itemsList):
    """
    #Function that will fill a table based on the information of a list, this function is not dynamic, is
    specifically done for this exercise thats why we are setting which columns should use.

    #Parameters:
        table(str): name of the table we'll fill
        itemsList(list): list with the information needed to fill the table

    #Returns:
        None
    """
    #Restart table
    rows = mc.scriptTable(table, query=True, rows=True)
    for i in range(rows, 0, -1):
        mc.scriptTable(table, edit=True, deleteRow=i)

    #Fill with new content
    for i in range(1,len(itemsList)+1):
            # Add another row and set values
            mc.scriptTable(table, edit=True, insertRow=i)
            mc.scriptTable(table, cellIndex=(i, 1), edit=True, cellValue=itemsList[i-1]["name"])
            mc.scriptTable(table, cellIndex=(i, 2), edit=True, cellValue=itemsList[i-1]["closestVertex"])


def writeFile(path, data):
    """ 
    #Function that will write a json file given the path and the data.

    #Parameters:
        path(str): path where the file is going to be saved
        data(list): information to write in the json

    #Returns:
        None
    """
    with open(path, 'w') as file:
        json.dump(data, file, indent=4)


def readFile(filename):
    """
    #Function that will read a json file and extract the data

    #Parameters:
        filename(str): path where the file is saved
        
    #Returns:
        data(list): information extracted from the json
    """
    with open(filename, 'r') as file:
        data = json.load(file)
    return data

#endregion

#region Button Func

def onClick_maingeoLoadBTN(txt, button):
    """
    #Function that will trigger when clicking the button that loads the main object

    #Parameters:
        txt(str): name of the textfield widget to fill the selected object
        button(str): name of the button that will be enabled after pressing the current button
        
    #Returns:
        None
    """
    global vertexData

    selectedObjects = mc.ls(selection=True)

    #User control in case there is more than one object selected
    if len(selectedObjects) > 1:
        om.MGlobal.displayWarning(f"More than one main object was selected. Only the first one will be chosen.")
    elif len(selectedObjects) == 0:
        om.MGlobal.displayError(f"No object was selected. Please select main geometry")

    if selectedObjects: 
        selectedObject = selectedObjects[0]
        mc.button(button, e=True, en=True)
        mc.textField(txt, e=True, tx=selectedObject)
        vertexData = getVertexInformation(selectedObject)

        mc.select(selectedObject)


def onClick_secgeoLoadBTN(table, buttons, txt):
    """ 
    #Function that will trigger when clicking the button that loads the secondary objects

    #Parameters:
        table(str): name of the table that will be filled with the secondary objects
        buttons(list): list name of the buttons that will be enabled after pressing the current button
        txt(str): name of the textfield widget to get the main geo and check if is not included in the sec objects list
        
    #Returns:
        None
    """
    global geoData
    geoData = []

    selectedObjects = mc.ls(selection=True, long=True)
    if selectedObjects:
        mainGeo = mc.textField(txt, q=True, tx=True)
        mc.scriptTable(table, e=True, en=True)
        #Enabling buttons
        for btn in buttons:
            mc.button(btn, e=True, en=True)

        for obj in selectedObjects:
            shortName = obj.split("|")[-1]
            #Check if the main geo is not included in the sec geo list
            if shortName != mainGeo:
                geoData.append({
                "name": shortName,
                "longName": obj,
                "closestVertex": None
                })
            else: 
                om.MGlobal.displayWarning(f"Skipping {obj}, because is the main geo.")

    #If we have data fill the table        
    if geoData:
        listOnTable(table, geoData)


def onClick_popconsBTN(table, txt, button):
    """
    #Function that will trigger when clicking the button that creates the Poly On Point Constraint

    #Parameters:
        table(str): name of the table that will be filled with the information
        txt(str): name of the textfield widget to get the main geo
        button(str): name of the button that will be enabled after pressing the current button
        
    #Returns:
        None
    """
    #If we have information
    if vertexData and geoData:
        mainGeo = mc.textField(txt, q=True, tx=True)
        mc.button(button, e=True, en=True)

        #If the main geo exists
        if mc.objExists(mainGeo):
            #Fill the geoData closestvertex
            for obj in geoData:
                secGeo = obj["name"]

                #If the secGeo exists
                if mc.objExists(secGeo):
                    index = getClosestVertex(vertexData, secGeo)
                    obj["closestVertex"] = index

                    #For each obj in geoData apply popConstraint
                    popConstraint(f"{mainGeo}.vtx[{index}]", secGeo)
                else:
                    om.MGlobal.displayWarning(f"{secGeo} doesn't exist in the scene. Skipping")
            #Fill the table
            listOnTable(table, geoData)
        else:
            om.MGlobal.displayError(f"Unable to parent, the {mainGeo} object doesn't exist on the scene.")



def onClick_exportBTN():
    """
    #Function that will export a json file with the information of secondary objects constraint

    #Parameters:
        None
        
    #Returns:
        None
    """
    # Define a filename (or use a file dialog to choose one)
    result = mc.fileDialog2(fileMode=0, caption='Export Constraint information', fileFilter='JSON Files (*.json)')

    try:
        if result:
            filename = result[0]
            if not filename.lower().endswith('.json'):
                filename += '.json'
            writeFile(filename, geoData)
        else:
            om.MGlobal.displayError("The file wasn't saved. Please try again")
        
    except PermissionError:
        om.MGlobal.displayError("Permission denied: You don't have the necessary permissions")



def onClick_importBTN(table, txt, button):
    """ 
    #Function that will import a json file with the information of secondary objects constraint and will apply it

    #Parameters:
        table(str): name of the table that will be filled with the information
        txt(str): name of the textfield widget to get the main geo
        button(str): name of the button that will be disabled after pressing the current button
        
    #Returns:
        None
    """
    global geoData
    geoDataTemp = {}
    # Define a filename (or use a file dialog to choose one)
    result = mc.fileDialog2(fileMode=4, caption='Load Selection', fileFilter='JSON Files (*.json)')
    
    if result:
        for filename in result:
            #Dumping information from the json to the list
            data = readFile(filename)

            # Convert list of dictionaries to a dictionary with 'name' as the key
            geoDataTemp = {item['name']: item for item in data}
        

        mainGeo = mc.textField(txt, q=True, tx=True)
        if mc.objExists(mainGeo):
            mc.button(button, e=True, en=False)

            try:
                for obj in geoData:
                    #Recovers original data
                    secGeo = obj["name"]
                    try:
                        index = geoDataTemp[secGeo]["closestVertex"]

                        if index:
                            #Fill the missing data on geoData
                            obj["closestVertex"] = index

                            #For each obj in geoData apply popConstraint
                            popConstraint(f"{mainGeo}.vtx[{index}]", secGeo)
                    except Exception:
                        om.MGlobal.displayWarning(f"Unable to parent, the {secGeo} object doesn't exist on the imported file. Skipping.")

            except Exception:
                om.MGlobal.displayError("The file imported doesn't containt the columns name and closestVertex. Please try again.")
            
            listOnTable(table, geoData)
        else:
            om.MGlobal.displayError(f"Unable to parent, the {mainGeo} object doesn't exist on the scene.")
    else:
        om.MGlobal.displayError("The file wasn't selected. Please try again")



def onUpdate_secgeoTB(row, column, value):
    """
    #Function that will refresh the table

    #Parameters:
        row(int): current row
        column(int): current column
        value(str)
        
    #Returns:
        True
    """
    return 1    

#endregion



def createUI(height = 400, width = 450):
    """ 
    #Function that will create the UI of the PointOnPoly Tool.

    #Parameters:
        height(int): height of the window
        width(int): width of the window

    #Returns:
        None
    """
    #Verify if the window exists, if exists delete it
    if mc.window('popConstraintWND', exists= True):
        mc.deleteUI('popConstraintWND')

    mainWindow = mc.window('popConstraintWND', t='PointOnPoly Tool', h=height, w=width, s=False)

    tableColumnW = (width-20)/3

    # -------------------------------------------------------------------------
    # ---------------------------- MAIN GEO -----------------------------------
    # -------------------------------------------------------------------------
    mc.frameLayout(label='Main Object', collapsable=False, collapse=False, marginWidth=0, marginHeight=0)
    mc.rowLayout(nc=2, adj=True, mar=5) # Start rowLayout 3
    maingeoTXT = mc.textField('mainGeoTXT', ed=False, it='Select and load main geometry -->', h=25)
    mc.button('maingeoLoadBTN', l='Load', w=80, c= lambda _: onClick_maingeoLoadBTN(maingeoTXT, secgeoLoadBTN))
    mc.setParent('..') # End rowLayout 3
    mc.setParent('..') # End frameLayout 1

    # -------------------------------------------------------------------------
    # ------------------------------ SEC GEO ----------------------------------
    # -------------------------------------------------------------------------
    mc.frameLayout(label='Secondary Objects', collapsable=False, collapse=False, marginWidth=0, marginHeight=0)
    mc.columnLayout(adj=True) # Start columnLayout 9
    mc.rowLayout(nc=2, adj=True, mar=5) # Start rowLayout 4
    mc.columnLayout() # Start columnLayout 5
    mc.text(l='From scene:')
    mc.rowLayout(nc=2, mar=5) # Start rowLayout 7
    secgeoLoadBTN = mc.button('secgeoLoadBTN',l='Load', w=40, c= lambda _: onClick_secgeoLoadBTN(secgeoTB, [popconsBTN, importBTN], maingeoTXT), en=False)
    popconsBTN = mc.button('popconsBTN', l='Constraint', w=100, c= lambda _: onClick_popconsBTN(secgeoTB, maingeoTXT, exportBTN), en=False)
    mc.setParent('..') # End rowLayout 7
    mc.setParent('..') # End columnLayout 5
    mc.columnLayout() # Start columnLayout 6
    mc.text(l='Constraint Information:')
    mc.rowLayout(nc=2, mar=5) # Start rowLayout 8
    exportBTN = mc.button('exportBTN', l='Export', c= lambda _: onClick_exportBTN(), en=False)
    importBTN = mc.button('importBTN', l='Import', c= lambda _: onClick_importBTN(secgeoTB, maingeoTXT, popconsBTN), en=False)
    mc.setParent('..') # End rowLayout 8
    mc.setParent('..') # End columnLayout 6
    mc.setParent('..') # End rowLayout 4
    secgeoTB = mc.scriptTable('secgeoTB', columns=2, label=[(1,"Geometry"), (2,"Vertex Constraint")], h=height-150, cw=[(1,tableColumnW*2),(2, tableColumnW)], 
                              ed=False, cellChangedCmd=onUpdate_secgeoTB, en=False)
    mc.setParent('..') # End columnLayout 9
    mc.setParent('..') # End frameLayout 2


    #Show window
    mc.showWindow(mainWindow)

# ---------------------------------------------------------------
# ------------------------- MAIN --------------------------------
# ---------------------------------------------------------------

if __name__ == '__main__':
    createUI(mainHeight, mainWidth)