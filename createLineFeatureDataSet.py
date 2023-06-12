
import arcpy, sys

Parm1 = arcpy.GetParameterAsText(0)
X1 = Parm1.split()[0]
Y1 = Parm1.split()[1]

Parm2 = arcpy.GetParameterAsText(1)
X2 = Parm2.split()[0]
Y2 = Parm2.split()[1]

arcpy.AddMessage("X : "+ X1)
arcpy.AddMessage("Y : "+ Y1)

workspace = r"C:\\Users\\afarrag\\Documents\\ArcGIS\\Projects\\splitTool\\splitTool.gdb" #arcpy.env.workspace
arcpy.env.workspace = workspace
spatial_reference = arcpy.SpatialReference(9358)


# Define the start and end points
start_point = arcpy.Point(X1, Y1)   #arcpy.Point(672138.4331758, 2743588.4005107)  
end_point =   arcpy.Point(X2, Y2)   #arcpy.Point(672065.9915564, 2743554.4877718)  

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
        cursor.insertRow([polyline])
    del cursor    
    arcpy.AddMessage("Insert line to LineFeature1...")    

    lyrTest = r"C:\Users\afarrag\Documents\ArcGIS\Projects\splitTool\splitTool.gdb\LineFeature1"         
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    #aprx = arcpy.mp.ArcGISProject(lyrTest)    
    mapx = aprx.listMaps()[0]  # Assuming you want to add the line to the first map in the project    
    mapx.addDataFromPath(lyrTest)
    arcpy.AddMessage("Done..." )
    
    
except Exception:
    e = sys.exc_info()[1]
    error_msg = e.args[0]
    arcpy.AddMessage("error_msg..." + error_msg)