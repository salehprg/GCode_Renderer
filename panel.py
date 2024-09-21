import functools
import math
import os
from pathlib import Path
import sys
import time

import bpy

script_dir = os.path.dirname(bpy.data.filepath)
if script_dir not in sys.path:
    sys.path.append(script_dir)
    
class GCodeParser:

    def __init__(self) -> None:

        gcode_file = 'cube.gcode'

        self.remove_all()

        if not 'Elliptical_Bevel' in bpy.data.objects:
            self.ellipse_bevel = self.create_ellipse_bevel("Elliptical_Bevel", major_radius=0.2, minor_radius=0.1)
        else:
            self.ellipse_bevel = bpy.data.objects['Elliptical_Bevel']

        if not 'Bed' in bpy.data.objects:
            self.bed = self.create_bed("Bed", size=60)
        else:
            self.bed = bpy.data.objects['Bed']


        light_exist = any(light.name == "Light" for light in bpy.data.objects)

        if not light_exist:
            self.light = self.create_light()
        else:
            self.light = bpy.data.objects["Light"]

        camera_exists = any(obj.type == 'CAMERA' for obj in bpy.data.objects)

        if not camera_exists:
            # Add a new camera to the scene
            camera_data = bpy.data.cameras.new(name="Camera")
            camera_object = bpy.data.objects.new("Camera", camera_data)

            # Link the camera object to the current scene
            bpy.context.collection.objects.link(camera_object)

            camera_data.lens = 60
            camera_data.sensor_width = 56
            # Set camera location and rotation
            camera_object.rotation_euler = (math.radians(50), 0, math.radians(45))

            # Set the camera as the active camera for the scene
            bpy.context.scene.camera = camera_object

            self.camera = camera_object
        else:
            self.camera = bpy.data.objects["Camera"]

        with open(gcode_file, 'r') as f:
            self.lines = f.readlines()
        
                # Set the output path
        
        timestr = time.strftime("%Y%m%d-%H%M%S")
        cwd = Path.cwd()

        dir_path = f'{cwd}/images_{timestr}'

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        self.dir_path = dir_path

        self.current_layer = []
        self.curves = []
        self.layer_number = 0
        self.last_z = None
        self.last_e = 0  # Track the last extruder position
        self.last_g0 = False
        self.last_x = None
        self.last_y = None
        self.is_extruding = False  # State to track if the extruder is laying down material

        self.reset()

    def reset(self):
        self.camera.location = (16, -16.5, 17.5)
        self.light.location = (0, 0, 3.8)

    def create_light(self):
        light_data = bpy.data.lights.new("Light",'AREA')
        light_object = bpy.data.objects.new("Light", light_data)

        light_object.data.size = 20
        light_object.data.energy = 1000
        bpy.context.collection.objects.link(light_object)
        light_object.location = (0, 0, 3.8)

        return light_object
        
    def remove_all(self):
        bpy.ops.object.select_pattern(pattern="Layer_*")
        bpy.ops.object.delete()

        for collection in bpy.data.collections:
            if collection.name.startswith("Collection_"):
                bpy.data.collections.remove(collection)

    def create_bed(self, name, size):
        # Create a new curve for the bevel shape (ellipse)
        curve_data = bpy.data.curves.new(name=name, type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.fill_mode = 'FULL'  # Enable full fill for 3D object

        # Create a Bézier spline
        bezier_spline = curve_data.splines.new('BEZIER')
        bezier_spline.bezier_points.add(3)  # Add points for a 4-point elliptical approximation

        # Define the Bézier points for an ellipse (approximation with handles)
        bezier_points = [
            (size / 2, size / 2, 0), (size / 2,-size / 2, 0),
            (-size / 2, -size / 2, 0), (-size / 2, size / 2, 0)
        ]
        
        for i, (x, y, z) in enumerate(bezier_points):
            point = bezier_spline.bezier_points[i]
            point.co = (x, y, z)  # Set the main control point (the point itself)
            
            # Set the left and right handle positions to create a smoother curve (simple approximation)
            point.handle_left_type = 'FREE'
            point.handle_right_type = 'FREE'

        # Make the curve cyclic (close the shape)
        bezier_spline.use_cyclic_u = True

        curve_data.bevel_mode = 'PROFILE'
        curve_data.bevel_depth = 0.9

        # Create an object for the curve and link it to the scene
        bed_obj = bpy.data.objects.new(name, curve_data)
        bpy.context.collection.objects.link(bed_obj)

        # Switch to edit mode
        bpy.context.view_layer.objects.active = bed_obj
        bpy.ops.object.mode_set(mode='EDIT')

        # Select all Bézier points and scale down handles to zero length
        for i, point in enumerate(bed_obj.data.splines[0].bezier_points):
            # Deselect all points to ensure only one is selected at a time
            bpy.ops.curve.select_all(action='DESELECT')

            # Select the current point
            point.select_control_point = True
            point.select_left_handle = True
            point.select_right_handle = True

            # Scale down handles to zero
            bpy.ops.transform.resize(value=(0, 0, 0))

        # Switch back to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
    
        return bed_obj

    
    # Create the elliptical bevel object
    def create_ellipse_bevel(self,name, major_radius, minor_radius):
        # Create a new curve for the bevel shape (ellipse)
        curve_data = bpy.data.curves.new(name=name, type='CURVE')
        curve_data.dimensions = '2D'
        
        # Create an elliptical spline
        polyline = curve_data.splines.new('POLY')
        polyline.points.add(7)
        
        # Define the points for an ellipse (4 points approximation)
        polyline.points[0].co = (major_radius, 0, 0, 1)  # (x, y, z, w)
        polyline.points[1].co = (major_radius * 0.75 , minor_radius * 0.75, 0, 1)
        polyline.points[2].co = (0, minor_radius, 0, 1)
        polyline.points[3].co = (-major_radius * 0.75 , minor_radius * 0.75, 0, 1)
        polyline.points[4].co = (-major_radius, 0, 0, 1)
        polyline.points[5].co = (-major_radius * 0.75 , -minor_radius * 0.75, 0, 1)
        polyline.points[6].co = (0, -minor_radius, 0, 1)
        polyline.points[7].co = (major_radius * 0.75 , -minor_radius * 0.75, 0, 1)

        # Make the curve cyclic (close the shape)
        polyline.use_cyclic_u = True

        # Create an object for the curve and link it to the scene
        bevel_obj = bpy.data.objects.new(name, curve_data)
        bpy.context.collection.objects.link(bevel_obj)
        
        return bevel_obj

    # Create a new curve with the elliptical cross-section
    def create_new_curve(self,name, points, bevel_obj,collection):
        # Create a new curve object
        curve_data = bpy.data.curves.new(name=name, type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.fill_mode = 'FULL'  # Enable full fill for 3D object
        
        # Create a spline for the curve
        polyline = curve_data.splines.new('BEZIER')
        polyline.bezier_points.add(len(points) - 1)

        is_close_curve = (points[0][0] - points[-1][0])  +  (points[0][1] - points[-1][1]) +  (points[0][2] - points[-1][2]) 
        is_close_curve = is_close_curve == 0
        
        for i, point in enumerate(points):
            bezier_point = polyline.bezier_points[i]
            bezier_point.co = point
            bezier_point.handle_left_type = 'FREE'
            bezier_point.handle_right_type = 'FREE'
        
        if is_close_curve:
            polyline.use_cyclic_u = True
        # Assign the elliptical bevel object to give the curve an elliptical cross-section
        curve_data.bevel_mode = 'OBJECT'
        curve_data.use_fill_caps = True
        curve_data.bevel_object = bevel_obj
        
        # Create a new object with the curve
        curve_obj = bpy.data.objects.new(name, curve_data)
        collection.objects.link(curve_obj)
        
        # Switch to edit mode
        bpy.context.view_layer.objects.active = curve_obj
        bpy.ops.object.mode_set(mode='EDIT')

        # Select all Bézier points and scale down handles to zero length
        for i, point in enumerate(curve_obj.data.splines[0].bezier_points):
            # Deselect all points to ensure only one is selected at a time
            bpy.ops.curve.select_all(action='DESELECT')

            # Select the current point
            point.select_control_point = True
            point.select_left_handle = True
            point.select_right_handle = True

            # Scale down handles to zero
            bpy.ops.transform.resize(value=(0, 0, 0))

        # Switch back to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        return curve_obj

    def render_image(self):
        # Set the scene
        scene = bpy.context.scene

        # Set render resolution
        scene.render.resolution_x = 1280
        scene.render.resolution_y = 720
        scene.render.resolution_percentage = 100

        # Set the render file format
        scene.render.image_settings.file_format = 'PNG'

        scene.render.filepath = f'{self.dir_path}/layer_{self.layer_number}.png'


        # Render the scene
        bpy.ops.render.render(write_still=True)

    def move_platform_up(self,z_height):
        self.light.location = (self.light.location.x, self.light.location.y, z_height + 1)
        self.camera.location = (self.camera.location.x, self.camera.location.y, z_height + 16.5)

    # Parse the GCode file and create curves
    def parse_gcode(self,line_num):

        lines = self.lines[line_num:]
        last_line = 0

        new_collection = bpy.data.collections.new(f'Collection_{self.layer_number}')
        bpy.context.scene.collection.children.link(new_collection)

        for idx,line in enumerate(lines):
            is_g0 = line.startswith('G0')
            is_g1 = line.startswith('G1')
            

            if is_g1 or is_g0:
                params = line.split()
                x = y = z = e = None
                for param in params:
                    if param.startswith('X'):
                        x = float(param[1:])
                    if param.startswith('Y'):
                        y = float(param[1:])
                    if param.startswith('Z'):
                        z = float(param[1:])
                               
                if is_g0 and x is not None and y is not None:
                    self.last_g0 = True
                    self.last_x = x
                    self.last_y = y

                    if len(self.current_layer) > 1:
                        # Create a curve from the current layer points if we were extruding
                        layer_name = f"Layer_{len(self.curves)}"
                        curve_obj = self.create_new_curve(layer_name, self.current_layer, self.ellipse_bevel,new_collection)
                        # convert_curve_to_mesh(curve_obj, bevel_obj)  # Convert the curve to mesh
                        self.curves.append(self.current_layer)

                    self.current_layer = []

                if z is not None and z != self.last_z:
                    self.last_z = z
                    self.layer_number += 1
                    last_line = idx+line_num

                    self.render_image()
                    self.move_platform_up(z)
                    break
                
                # Add point to the current layer if extruding

                if self.last_z is not None:
                    if self.last_g0 and is_g1:
                        self.current_layer.append((self.last_x, self.last_y, self.last_z))
                        self.last_g0 = False
                        self.last_x = None
                        self.last_y = None

                    if x is not None and y is not None and is_g1:
                        self.current_layer.append((x, y, self.last_z))

                                # If Z changes, create a new curve for a new layer


        # Add the last layer's curve if there are any points left
        if self.current_layer:
            layer_name = f"Layer_{len(self.curves)}"
            curve_obj = self.create_new_curve(layer_name, self.current_layer, self.ellipse_bevel,new_collection)
            # convert_curve_to_mesh(curve_obj, bevel_obj)  # Convert the last curve to mesh
            self.curves.append(self.current_layer)

        return last_line

gcode = GCodeParser()
current_line = 0

def render_with_delay():       
    global gcode
    global current_line

    
    line = gcode.lines[current_line]

    current_line += 1
    newLine = gcode.parse_gcode(current_line)
    print(f"{current_line} - {newLine}")
    current_line = newLine
    
    if newLine == 0:
        return None
    
    return 0.1

# Define the operator to read GCode file
class ReadGCodeOperator_Full(bpy.types.Operator):
    """Read GCode File"""
    bl_idname = "wm.read_gcode"
    bl_label = "Read GCode"

    def execute(self, context):
        try:
            # Check if we are still within the bounds of the file
            gcode.__init__()
            bpy.app.timers.register(functools.partial(render_with_delay))
            
            self.report({'INFO'}, "End of GCode file reached.")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read file: {str(e)}")
            return {'CANCELLED'}

class ReadGCodeOperator_Line(bpy.types.Operator):
    """Read GCode File"""
    bl_idname = "wm.read_gcode_line"
    bl_label = "Read GCode"


    current_line : bpy.props.IntProperty(default=0)
    
    def execute(self, context):
        try:
    
            self.current_line += 1
            newLine = gcode.parse_gcode(self.current_line)
            print(f"{self.current_line} - {newLine}")
            self.current_line = newLine
            
            self.report({'INFO'}, "End of GCode file reached.")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read file: {str(e)}")
            return {'CANCELLED'}

class GCodeReset(bpy.types.Operator):
    """Read GCode File"""
    bl_idname = "wm.gcode_reset"
    bl_label = "Read GCode"
    
    def execute(self, context):
        try:
    
            gcode.__init__()
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read file: {str(e)}")
            return {'CANCELLED'}
        
# Define a panel that will show the button
class GCodeReaderPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "My GCode Reader"
    bl_idname = "SCENE_PT_gcode_reader"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GCode Reader'
    
    def draw(self, context):
        layout = self.layout
        layout.operator("wm.read_gcode", text="Select and Read GCode")
        layout.operator("wm.read_gcode_line", text="Select and Read GCode Line By Line")
        layout.operator("wm.gcode_reset", text="Reset")


# Register and Unregister Classes
def register():
    bpy.utils.register_class(ReadGCodeOperator_Full)
    bpy.utils.register_class(ReadGCodeOperator_Line)
    bpy.utils.register_class(GCodeReset)
    bpy.utils.register_class(GCodeReaderPanel)

def unregister():
    bpy.utils.unregister_class(ReadGCodeOperator_Full)
    bpy.utils.unregister_class(ReadGCodeOperator_Line)
    bpy.utils.unregister_class(GCodeReset)
    bpy.utils.unregister_class(GCodeReaderPanel)

register()
