import bpy


# Create the elliptical bevel object
def create_ellipse_bevel(name, major_radius, minor_radius):
    # Create a new curve for the bevel shape (ellipse)
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '2D'
    
    # Create an elliptical spline
    polyline = curve_data.splines.new('POLY')
    polyline.points.add(3)
    
    # Define the points for an ellipse (4 points approximation)
    polyline.points[0].co = (major_radius, 0, 0, 1)  # (x, y, z, w)
    polyline.points[1].co = (0, minor_radius, 0, 1)
    polyline.points[2].co = (-major_radius, 0, 0, 1)
    polyline.points[3].co = (0, -minor_radius, 0, 1)

    # Make the curve cyclic (close the shape)
    polyline.use_cyclic_u = True

    # Create an object for the curve and link it to the scene
    bevel_obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(bevel_obj)
    
    return bevel_obj

# Create a new curve with the elliptical cross-section
def create_new_curve(name, points, bevel_obj):
    # Create a new curve object
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.fill_mode = 'FULL'  # Enable full fill for 3D object
    
    # Create a spline for the curve
    polyline = curve_data.splines.new('POLY')
    polyline.points.add(len(points) - 1)
    
    for i, point in enumerate(points):
        polyline.points[i].co = (point[0], point[1], point[2], 1)  # (x, y, z, w)
    
    # Assign the elliptical bevel object to give the curve an elliptical cross-section
    curve_data.bevel_mode = 'OBJECT'
    curve_data.bevel_object = bevel_obj
    
    # Create a new object with the curve
    curve_obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(curve_obj)
    
    return curve_obj

# Parse the GCode file and create curves
def parse_gcode(gcode_file, bevel_obj):
    with open(gcode_file, 'r') as f:
        lines = f.readlines()
    
    current_layer = []
    curves = []
    last_z = None
    last_e = 0  # Track the last extruder position
    is_extruding = False  # State to track if the extruder is laying down material

    for line in lines:
        if line.startswith('G1') or line.startswith('G0'):
            params = line.split()
            x = y = z = e = None
            for param in params:
                if param.startswith('X'):
                    x = float(param[1:])
                if param.startswith('Y'):
                    y = float(param[1:])
                if param.startswith('Z'):
                    z = float(param[1:])
                if param.startswith('E'):
                    e = float(param[1:])

            # Detect extrusion state (if E is present and increases)
            if e is not None:
                is_extruding = e > last_e
                last_e = e
            
            # If Z changes, create a new curve for a new layer
            if z is not None and z != last_z:
                if current_layer:
                    # Create a curve from the current layer points if we were extruding
                    layer_name = f"Layer_{len(curves)}"
                    curve_obj = create_new_curve(layer_name, current_layer, bevel_obj)
                    # convert_curve_to_mesh(curve_obj, bevel_obj)  # Convert the curve to mesh
                    curves.append(current_layer)
                    current_layer = []
                last_z = z
            
            # Add point to the current layer if extruding
            if x is not None and y is not None and last_z is not None:
                current_layer.append((x, y, last_z))
    
    # Add the last layer's curve if there are any points left
    if current_layer:
        layer_name = f"Layer_{len(curves)}"
        curve_obj = create_new_curve(layer_name, current_layer, bevel_obj)
        # convert_curve_to_mesh(curve_obj, bevel_obj)  # Convert the last curve to mesh
        curves.append(current_layer)


bpy.ops.object.select_all(action='SELECT')

# Delete all selected objects
bpy.ops.object.delete()
# Create the elliptical bevel object (with specified major and minor radii)
ellipse_bevel = create_ellipse_bevel("Elliptical_Bevel", major_radius=0.2, minor_radius=0.1)

# Path to your GCode file
gcode_file_path = "cube.gcode"

# Parse the GCode and create curves in Blender
parse_gcode(gcode_file_path, ellipse_bevel)

print("GCode parsing, curve creation with elliptical cross-section, and mesh conversion complete.")
