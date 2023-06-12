import arcpy, os, sys
import numpy as np
from datetime import datetime

# Function to update neighbours edges and nodes
def neighbours():
    report = ''
    return report

# Function for saving logs
def logging():

    # Write transaction log details
    fileName = pcp_id + "-" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".txt"
    logFile = os.path.join(logs_container, fileName)
    with open(logFile, 'w') as f:
        f.write(message) 

# Function for delete target parcel and dependencies
def delete():

    # targets count
    nodes_cnt = int(arcpy.management.GetCount(node_Fc)[0])
    edges_cnt = int(arcpy.management.GetCount(edge_Fc)[0])

    targets = ""
    tempLayer2 = "tmpLrx"
    query = ident + " = " + str(idv)
    tgt2 = arcpy.management.MakeFeatureLayer(parcel_Fc_T, tempLayer2, query)
    count = int(arcpy.management.GetCount(tgt2)[0])
    if count == 1:
        targets = "parcel"
        arcpy.management.DeleteFeatures(tgt2)
    
    # Delete nodes
    tgt2 = arcpy.management.MakeFeatureLayer(node_Fc, tempLayer2, expression)
    cnt = int(arcpy.management.GetCount(tgt2)[0])
    if cnt < nodes_cnt:
        arcpy.management.DeleteFeatures(tgt2)
        targets = targets + " - node"

    # Delete edges
    tgt2 = arcpy.management.MakeFeatureLayer(edge_Fc, tempLayer2, expression)
    cnt = int(arcpy.management.GetCount(tgt2)[0])
    if cnt < edges_cnt:
        arcpy.management.DeleteFeatures(tgt2)
        targets = targets + " - edge"
    
    return "\nDelete status ( " + targets + ")"

# Function to generate parcel nodes and edges
def GetNodesEdges(feat_geo, pID):
    report = ""
    nodes = []
    fields = ['SHAPE@','LP_ID','Angle','Easting','Northing']
    sp = feat_geo.spatialReference    
    geo = feat_geo
    feat_geo = feat_geo.getPart()
    feat_geo = np.asarray([[i.X, i.Y] for j in feat_geo for i in j])
    if len(feat_geo) < 2:
        return None
    elif len(feat_geo) == 2:
        ba = feat_geo[1] - feat_geo[0]
        return np.arctan2(*ba[::-1])
    else:
        if np.allclose(feat_geo[0], feat_geo[-1]):
            feat_geo = feat_geo[:-1]
            r = (-1,) + tuple(range(len(feat_geo))) + (0,)
        else:
            r = tuple(range(len(feat_geo)))
        with arcpy.da.InsertCursor(node_Fc_T, fields) as cursor:
            for i in range(len(r)-2):
                p0, p1, p2 = feat_geo[r[i]], feat_geo[r[i+1]], feat_geo[r[i+2]]
                ba = p1 - p0
                bc = p1 - p2
                cr = np.cross(ba, bc)
                dt = np.dot(ba, bc)
                ang = np.arctan2(np.linalg.norm(cr), dt)
                angle = np.degrees(ang)
                inAngle = angle

                if (angle <= 175):
                    pt = arcpy.Point(p1[0], p1[1])
                    pt_geometry = arcpy.PointGeometry(pt, spatial_reference = sp)
                    nodes.append(pt_geometry)
                    cursor.insertRow(((p1[0], p1[1]), pID, inAngle, p1[0], p1[1]))
        del cursor

        if len(nodes) > 0:
            try:
                report = "\nDone Generate new nodes"
                edges = geo.boundary()
                # output = os.path.join(arcpy.env.scratchGDB, "outSeg")
                output = os.path.join(arcpy.env.workspace, "outSeg")                      
                lyr = arcpy.management.SplitLineAtPoint(edges, nodes, output, '5 meters')                
                lyr_cnt = int(arcpy.management.GetCount(lyr)[0])
                if lyr_cnt > 1:

                    # output2 = os.path.join(arcpy.env.scratchGDB, "analysis")
                    output2 = os.path.join(arcpy.env.workspace, "analysis")                    
                    fields2 = ['ADJ_FEATURE_ID','ADJ_FEATURE_TYPE']

                    # Calculate dimension direction
                    arcpy.AddField_management(lyr, "ScriptCode", "LONG")
                    
                    arcpy.management.CalculateField(lyr, "ScriptCode", "!OBJECTID!")
                    arcpy.AddField_management(lyr, "LIMIT_DIRECTION", "LONG")
                    arcpy.management.CalculateField(lyr, "LIMIT_DIRECTION",
                        expression="calcDirection(!shape.firstPoint.X!, !shape.firstPoint.Y!, !shape.lastPoint.X!, !shape.lastPoint.Y!)",
                        expression_type="PYTHON3",
                        code_block="""def calcDirection(x1, y1, x2, y2):
                        angle = math.degrees(math.atan2(( y2 - y1 ),( x2 - x1 )))
                        if angle < 0:
                            angle += 360.0
                        if angle >= 0 and angle < 90:
                            return 1
                        elif angle >= 90 and angle < 180:
                            return 2
                        elif angle >= 180 and angle < 270:
                            return 4
                        else:
                            return 3 """
                    )

                    arcpy.analysis.SpatialJoin(lyr, parcel_Fc, output2, "JOIN_ONE_TO_MANY", "KEEP_COMMON", match_option = "SHARE_A_LINE_SEGMENT_WITH")
                    anaLayer = "anaLayer"
                    expree = fld_name + " <> '" + pID + "'"
                    analyr = arcpy.management.MakeFeatureLayer(output2, anaLayer, expree)

                    if int(arcpy.management.GetCount(analyr)[0]) > 0:
                        arcpy.AddField_management(lyr, fields2[0], "TEXT")
                        arcpy.AddField_management(lyr, fields2[1], "LONG")
                        join2 = arcpy.management.AddJoin(lyr, "ScriptCode", analyr, "ScriptCode")
                        arcpy.management.CalculateField(join2, fields2[1], "1")
                        arcpy.management.CalculateField(join2, fields2[0], "!analysis." + fld_name + "!")
                        arcpy.management.RemoveJoin(join2)
                    
                    arcpy.management.Append(lyr, edge_Fc_T, "NO_TEST")
                    report = report + " - Done Generate new edges"
            except Exception:
                e = sys.exc_info()[1]
                error_msg = e.args[0]
                arcpy.AddMessage("error_msg..." + error_msg)
    return report

# Function for backup target parcel and dependencies
def backup():

    # targets count
    nodes_cnt = int(arcpy.management.GetCount(node_Fc)[0])
    edges_cnt = int(arcpy.management.GetCount(edge_Fc)[0])

    targets = "parcel"

    tempLayer2 = "tmpLrx"
    query = ident + " = " + str(idv)
    tgt2 = arcpy.management.MakeFeatureLayer(parcel_Fc, tempLayer2, query)

    # Backup and archiving process
    arcpy.management.Append(tgt2, parcel_history, "NO_TEST")

    # Backup nodes
    tmp = arcpy.management.MakeFeatureLayer(node_Fc, tempLYR, expression)
    cnt = int(arcpy.management.GetCount(tmp)[0])
    if cnt < nodes_cnt:
        arcpy.management.Append(tmp, node_history, "NO_TEST")
        targets = targets + " - node"

    # Backup edges
    tmp = arcpy.management.MakeFeatureLayer(edge_Fc_T, tempLYR, expression)
    cnt = int(arcpy.management.GetCount(tmp)[0])
    if cnt < edges_cnt:
        arcpy.management.Append(tmp, edge_history, "NO_TEST")
        targets = targets + " - edge"

    return "\nBackup for PCP ( " + targets + ") has been taken and archived"

# Function for create line 
def createLine(Parm1, Parm2):
    # arcpy.AddMessage("Parm1..."+ Parm1 )
    X1 = Parm1.split()[0]
    Y1 = Parm1.split()[1]
    
    X2 = Parm2.split()[0]
    Y2 = Parm2.split()[1]

    LineGeo = None
    workspace = arcpy.env.workspace
    # workspace = r"C:\\Users\\afarrag\\Documents\\ArcGIS\\Projects\\splitTool\\splitTool.gdb" #arcpy.env.workspace
    #arcpy.env.workspace = workspace
    arcpy.AddMessage("Wrkspace..."+ workspace )
    spatial_reference = arcpy.SpatialReference(9358)

    # Define the start and end points
    start_point = arcpy.Point(X1, Y1)   #arcpy.Point(672138.4331758, 2743588.4005107)  #
    end_point   = arcpy.Point(X2, Y2)   #arcpy.Point(672065.9915564, 2743554.4877718)  #

    # Create a new feature class to store the line feature    
    output_fc = "LineFeature1" #arcpy.management.CreateFeatureclass(workspace, "LineFeature1", "Polyline", "", "", "", spatial_reference)

    # Create an array of point objects and add the start and end points
    array = arcpy.Array()
    array.add(start_point)
    array.add(end_point)

    # Create a Polyline object using the array of points
    polyline = arcpy.Polyline(array,spatial_reference)

    try:    
    # Check if the feature class already exists
        if not arcpy.Exists(output_fc):
            arcpy.management.CreateFeatureclass(workspace, "LineFeature1", "Polyline", "", "", "", spatial_reference)
            print(f"Create feature class {output_fc}.")

        # Create a new row in the feature class
        #with arcpy.da.Editor(workspace, multiuser_mode=False):  
        with arcpy.da.InsertCursor("LineFeature1", "SHAPE@") as cursor:
            LineGeo = polyline
            cursor.insertRow([polyline])
        del cursor    
        arcpy.AddMessage("Insert line to LineFeature1...")    

        lyrTest = r"C:\Users\afarrag\Documents\ArcGIS\Projects\splitTool\splitTool.gdb\LineFeature1"         
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        #aprx = arcpy.mp.ArcGISProject(lyrTest)    
        mapx = aprx.listMaps()[0]  # Assuming you want to add the line to the first map in the project    
        mapx.addDataFromPath(lyrTest)
        arcpy.AddMessage("Done..." )
        
        return LineGeo
    except Exception:
        e = sys.exc_info()[1]
        error_msg = e.args[0]
        arcpy.AddMessage("error_msg..." + error_msg)
####################################################################################################################
# Get parcel id
pcp_id = arcpy.GetParameterAsText(0)

# Get operation type
opt = arcpy.GetParameterAsText(1)

# Get feature set
# featureSet = arcpy.GetParameterAsText(2)

Parm1 = arcpy.GetParameterAsText(3)
Parm2 = arcpy.GetParameterAsText(4)

# Configure setting
arcpy.env.workspace = arcpy.env.workspace
arcpy.env.overwriteOutput = True

#logs_container = "D:\\Tools\\CustomEdit\\log"
logs_container = "D:\\Temp\\CustomEdit\\log"

tempLayer = "targetLayer"
tempLYR = "tempLYR"

# Original targets
parcel_Fc = "Land_Parcels_38"
node_Fc = "Parcel_Nodes_38"
edge_Fc = "Dimensions_38"

# Temp 
parcel_Fc_T = "Land_Parcels_38_T"
node_Fc_T = "Parcel_Nodes_38_T"
edge_Fc_T = "Dimensions_38_T"

# Basemap street center line
StreetCenterLine = "tnRoadCenterLineL"

# History targets
parcel_history = "Land_Parcels_38_H"
node_history = "Parcel_Nodes_38_H"
edge_history = "Dimensions_38_H"

# Prepare query
ident = "OBJECTID"
fld_name = "LP_ID"
expression = fld_name + " = '" + pcp_id + "'"

# Locate parcel
tgt = arcpy.management.MakeFeatureLayer(parcel_Fc, tempLayer, expression)
cnt = int(arcpy.management.GetCount(tgt)[0])
if cnt == 1:

    # Handle JSON parameter for feature set
    error_msg = None
    # try:
    #     featureSet = arcpy.FeatureSet(featureSet)
    # except Exception:
    #     e = sys.exc_info()[1]
    #     error_msg = e.args[0]
    
    # if error_msg:
    #     arcpy.SetParameterAsText(2, "error geometry parameter")
    #     sys.exit(0)

    # Get geometry from feature set
    opGeo = None

    #create line
    opGeo = createLine(Parm1, Parm2)
    arcpy.AddMessage("type..." + opGeo.type)
    
    # with arcpy.da.SearchCursor(featureSet, ['SHAPE@']) as cursor:
    #     for row in cursor:
    #         opGeo = row[0]
    # del cursor

    # Validation before operation process
    if opGeo:

        # Check if it's point
        if opGeo.type == "point":
            arcpy.SetParameterAsText(2, "geometry parameter is point")
            sys.exit(0)

        # Check if it has z
        '''
        pnt = opGeo.firstPoint
        if not pnt.Z:
            arcpy.SetParameterAsText(2, "geometry parameter not has Z")
            sys.exit(0)
        '''

        # Get target parcel attribute
        pcl = None
        fields = ['OID@', 'SHAPE@', 'LP_ID', 'RE_ID', 'REA_ID', 'RL_PARCEL_ID', 'MOMRAH_PARCEL_ID', 'SUBDIVISIONPARCELNUMBER', 'SUBDIVISIONPLAN_ID', 'BLOCK_ID', 'NHC_AQAR_NUMBER', 'SUBTYPE', 'MAINLANDUSE_AR', 'MAINLANDUSE_EN', 'DETAILSLANDUSE', 'BUILDING_AVAILABILITY', 'MOMRAH_AREA_SQM', 'RL_AREA_SQM', 'REGION_ID', 'GOVERNORATE_ID', 'CITY_ID', 'AMANA_ID', 'MUNICIPALITY_ID', 'SUBMUNICIPALITY_ID', 'DISTRICT_ID', 'DESCRIPTION']
        with arcpy.da.SearchCursor(tgt, fields) as cursor:
            for row in cursor:
                pcl = row
        del cursor
        idv = pcl[0]
        geo = pcl[1]
        
        # Check parcel and parameter are intersect
        flag = not geo.disjoint(opGeo)

        # Start operation process
        output = ""
        operation_status = ""
        features = []

        if flag:

            if opt == "Split":
                if opGeo.type == "polyline":

                    # Start editing
                    try:
                        features = geo.cut(opGeo)
                        operation_status = "edit"
                    except Exception:
                        e = sys.exc_info()[1]
                        operation_status = e.args[0]
                else:
                    arcpy.SetParameterAsText(2, "geometry parameter must be polyline for " + opt)
                    sys.exit(0)
        
            if opt == "Merge":
                if opGeo.type == "polygon":
                    
                    # Start editing
                    try:
                        features.append(geo.union(opGeo))
                        operation_status = "edit"
                    except Exception:
                        e = sys.exc_info()[1]
                        operation_status = e.args[0]
                else:
                    arcpy.SetParameterAsText(2, "geometry parameter must be polygon for " + opt)
                    sys.exit(0)
        else:
            arcpy.SetParameterAsText(2, "geometry parameter far from parcel")
            sys.exit(0)

        # Configure log details
        message = "Date : " + datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        message = message + "\nFound pcp parcel : " + pcp_id

        if operation_status == "edit":
            message = message + "\n" + opt + " Operation Succeeded"

            # Start saving process
            try:
                # Handel multipart 
                if features[0].isMultipart:
                    arcpy.AddMessage("isMultipart..." + features[0].isMultipart)
                    output = os.path.join(arcpy.env.scratchGDB, "multipart")
                    arcpy.management.MultipartToSinglepart(features, output)
                    features = []
                    with arcpy.da.SearchCursor(output, ['SHAPE@']) as cursor:
                        for row in cursor:
                            features.append(row[0])
                    del cursor

                with arcpy.da.InsertCursor(parcel_Fc_T, fields) as cursor:
                    for feature in features:
                        yList = list(pcl)
                        yList[1] = feature
                        tp = tuple(yList)
                        cursor.insertRow(tp)
                del cursor
                operation_status = "save"
            except Exception:
                e = sys.exc_info()[1]
                operation_status = e.args[0]
        else:
            message = message + "\n" + opt + " Operation Failed"
            message = message + "\n" + operation_status
            
            # Log operation details in text file
            logging()

            arcpy.SetParameterAsText(2, "transaction failed")
            sys.exit(0)
                    
        if operation_status == "save":
            message = message + "\nSave Succeeded"

            # Backup process
            report = backup()
            message = message + report

            # Delete Process
            report = delete()
            message = message + report

            # Generate Nodes & Edges
            for feature in features:
                report = GetNodesEdges(feature, pcp_id)
                message = message + report
            
            # Update neighbours
            
            # Log operation details in text file
            logging()           

            arcpy.SetParameterAsText(2, "transaction ok")
        else:
            message = message + "\nSave Failed"
            message = message + "\n" + operation_status
        
            # Log operation details in text file
            logging()

            arcpy.SetParameterAsText(2, "transaction failed")

    else:
        arcpy.SetParameterAsText(2, "missing geometry parameter")
else:
    arcpy.SetParameterAsText(2, "Parcel Not Exist")