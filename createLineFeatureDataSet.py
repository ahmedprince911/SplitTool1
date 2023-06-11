
import arcpy, sys


workspace = r"C:\\Users\\afarrag\\Documents\\ArcGIS\\Projects\\splitTool\\splitTool.gdb" #arcpy.env.workspace
arcpy.env.workspace = workspace
spatial_reference = arcpy.SpatialReference(9358)


# Define the start and end points
start_point = arcpy.Point(672138.4331758, 2743588.4005107)  # Replace with your start point coordinates
end_point =   arcpy.Point(672065.9915564, 2743554.4877718)  # Replace with your end point coordinates

# Create a new feature dataset to store the line feature class    
#arcpy.management.CreateFeatureDataset(workspace, "FeatureDataset", spatial_reference)

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
    with arcpy.da.Editor(workspace, multiuser_mode=False):  
        with arcpy.da.InsertCursor("LineFeature1", "SHAPE@") as cursor:
            cursor.insertRow([polyline])
    del cursor
    
    print("Insert line to LineFeature1...")

    # Open ArcGIS Pro and add the feature dataset to the map
    # aprx_path = r"C:\path\to\your\project.aprx"  # Replace with the path to your ArcGIS Pro project
    # aprx = arcpy.mp.ArcGISProject(aprx_path)
    # mapx = aprx.listMaps()[0]  # Assuming you want to add the line to the first map in the project

    # Add the feature dataset to the map
    # mapx.addDataFromPath(feature_dataset)

    lyrTest = r"C:\\Users\\afarrag\\Documents\\ArcGIS\\Projects\\splitTool\\splitTool.gdb\\LineFeature1" 
    # aprx = arcpy.mp.ArcGISProject("CURRENT")
    # aprxMap = aprx.listMaps("MainMap")[0] 
    # aprxMap.addDataFromPath(lyrTest)

    # aprx_path = r"C:\path\to\your\project.aprx"  # Replace with the path to your ArcGIS Pro project
    aprx = arcpy.mp.ArcGISProject(lyrTest)
    mapx = aprx.listMaps()[0]  # Assuming you want to add the line to the first map in the project
    mapx.addDataFromPath(lyrTest)
    arcpy.AddMessage("Done..." )
    
except Exception:
    e = sys.exc_info()[1]
    error_msg = e.args[0]
    arcpy.AddMessage(error_msg)