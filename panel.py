import functools
import math
import os
import sys
import time
from pathlib import Path

import bpy
import mathutils

bl_info = {
    "name": "GCode Parser",
    "description": "",
    "author": "Saleh",
    "version": (0, 0, 1),
    "blender": (4, 2, 1),
    "location": "GCode > GCode PA",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "Test"
}

import bpy

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Operator,
                       AddonPreferences,
                       PropertyGroup,
                       )

script_dir = os.path.dirname(bpy.data.filepath)
if script_dir not in sys.path:
    sys.path.append(script_dir)
    
class GCodeParser:

    def __init__(self, bed_size = 35, 
                        camera_location = (-58.39, 1.85, 38.8), 
                        camera_rotation = (math.radians(63.13), math.radians(-0.2), math.radians(-54.3)),
                        camera_lens = 29.7,
                        sensor_width = 45,
                        layer_height = 0.2,
                        layer_width = 0.4,
                        offset = 0.02
                        ) -> None:        
        
        self.bed_size = bed_size * 10
        self.offset_location = mathutils.Vector((self.bed_size/2,self.bed_size/2,0))
        
        self.light_init_location = (self.bed_size/2, -17.5, 38.8) # self.offset_location + mathutils.Vector((186, -234.22, 38))
        self.light_location =  self.light_init_location

        self.camera_init_location = camera_location # self.offset_location + mathutils.Vector((186, -234.22, 38))
        self.camera_init_rotation = camera_rotation
        self.camera_lens = camera_lens
        self.sensor_width = sensor_width
        self.head_pos = self.offset_location.copy()

        self.head = bpy.data.objects["Head"]

        mask_mat_name = "MaskMat"

        # Get the material by name
        
        self.mask_material = bpy.data.materials.get(mask_mat_name)

        self.remove_all()

        if not 'Elliptical_Bevel' in bpy.data.objects:
            self.ellipse_bevel = self.create_ellipse_bevel("Elliptical_Bevel", major_radius=(layer_width / 2) + offset, minor_radius=(layer_height / 2) + offset)
        else:
            self.ellipse_bevel = bpy.data.objects['Elliptical_Bevel']

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

            camera_data.lens = self.camera_lens
            camera_data.sensor_width = self.sensor_width
            # Set camera location and rotation
            camera_object.rotation_euler = self.camera_init_rotation

            # Set the camera as the active camera for the scene
            bpy.context.scene.camera = camera_object

            self.camera = camera_object
        else:
            self.camera = bpy.data.objects["Camera"]
        
                # Set the output path
        self.lines = []

        timestr = time.strftime("%Y%m%d-%H%M%S")
        cwd = Path.cwd()

        dir_path = f'{cwd}/images_{timestr}'
        self.dir_path = dir_path

        self.fdm_material = None
        self.current_layer = []
        self.collections = []
        self.layer_number = 0
        self.set_light(800 * 1000)
        self.reset_location()

    def set_filament_mat(self, material_name):
        self.fdm_material = bpy.data.materials.get(material_name)
        
    def set_light(self, power):
        self.light.data.energy = power

    def load_file(self, gcode_file):
        with open(gcode_file, 'r') as f:
            self.lines = f.readlines()

    def reset_location(self):
        self.camera.location = self.camera_init_location
        self.light.location = self.light_location
        self.head.location = (0,0,0)

    def create_light(self):
        light_data = bpy.data.lights.new("Light",'AREA')
        light_object = bpy.data.objects.new("Light", light_data)

        # light_object.data.size = 20
        light_object.data.size = 50
        bpy.context.collection.objects.link(light_object)
        light_object.location = self.light_location
        light_object.scale = (0.477,5.264,1)
        light_object.rotation_euler = (0, math.radians(75), math.radians(-90))

        return light_object
        
    def remove_all(self):
        bpy.ops.object.select_all(action='DESELECT')
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

        bed_obj.location = self.offset_location
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
        
        if curve_obj.data.materials:
            curve_obj.data.materials[0] = self.fdm_material
        else:
            curve_obj.data.materials.append(self.fdm_material)
        
        return curve_obj

    def _full_render(self,scene,filename):
        file_path = f'{self.dir_path}/sim_{filename}.png'
        scene.render.filepath = file_path

        bpy.ops.render.render(write_still=True)

    def _custom_render(self,scene,filename,show_head=True,show_bed=True):
        file_path = f'{self.dir_path}/bed_{filename}.png'
        scene.render.filepath = file_path

        if not show_head:
            self.head.hide_viewport = True
            self.head.hide_render = True
        
        if not show_bed:
            self.bed.hide_viewport = True
            self.bed.hide_render = True

        bpy.ops.render.render(write_still=True)

        if not show_head:
            self.head.hide_viewport = False
            self.head.hide_render = False
        
        if not show_bed:
            self.bed.hide_viewport = False
            self.bed.hide_render = False
        
    def _mask_render(self,scene,filename):
        file_path = f'{self.dir_path}/msk_{filename}.png'
        scene.render.filepath = file_path

        for obj in bpy.data.objects:
            if obj.type not in {'LIGHT', 'CAMERA'}:
                obj.hide_viewport = True
                obj.hide_render = True
            if obj.name.find("Layer_") != -1:
                obj.hide_viewport = False
                obj.hide_render = False
                obj.data.materials[0] = self.mask_material

        bpy.ops.render.render(write_still=True)

        for obj in bpy.data.objects:
            obj.hide_viewport = False
            obj.hide_render = False

            if obj.name.find("Layer_") != -1:
                obj.data.materials[0] = self.fdm_material

    def render_image(self, filename):
        print("Rendering...")

        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
        
        # Set the scene
        scene = bpy.context.scene

        # Set render resolution
        scene.render.resolution_x = 1280
        scene.render.resolution_y = 720
        scene.render.resolution_percentage = 100

        # Set the render file format
        scene.render.image_settings.file_format = 'PNG'

        # counter = 1
        # while os.path.exists(file_path):
        #     file_path = f'{self.dir_path}/layer_{self.layer_number}_{counter}.png'
        #     counter += 1

        # Render the scene
        self._full_render(scene,filename)

        self._custom_render(scene,filename,show_head=False)
        self._mask_render(scene,filename)

    def move_platform_up(self,z_height):
        self.light.location = (self.light.location.x, self.light.location.y, z_height + self.light_init_location[2])
        self.camera.location = (self.camera.location.x, self.camera.location.y, z_height + self.camera_init_location[2])

    def close_curve(self):
        if len(self.collections) == 0:
            new_collection = bpy.data.collections.new(f'Collection_{self.layer_number}')
            bpy.context.scene.collection.children.link(new_collection)
            self.collections.append(new_collection)

        last_collection = self.collections[-1]
        layer_name = f"Layer_{len(self.collections)}"
        curve_obj = self.create_new_curve(layer_name, self.current_layer, self.ellipse_bevel,last_collection)
    
    def set_head_pos(self, new_head_pos):
        self.head_pos = new_head_pos
        self.head.location = self.head_pos

        self.move_platform_up(new_head_pos.z)


    def parse_gcode(self,line_num,render = True,hide_new_collection=True):

        lines = self.lines[line_num:]
        last_line = 0

        for idx,line in enumerate(lines):
            is_g0 = line.startswith('G0')
            is_g1 = line.startswith('G1')
            is_g92 = line.startswith('G92')
            is_M118 = line.startswith('M118')
            is_G4P50 = line.startswith('G4 P50')
            
            x = y = z = e = None

            if is_g92 or is_g0 or is_g1:
                params = line.split()
                for param in params:
                    if param.startswith('X'):
                        x = float(param[1:])
                    if param.startswith('Y'):
                        y = float(param[1:])
                    if param.startswith('Z'):
                        z = float(param[1:])
                    if param.startswith('E'):
                        e = float(param[1:])

                    if param == ';':
                        break
                    
            # if is_G4P50 and render:
            #     print(f"G4 P50 on Line {idx+line_num}")
            #     self.render_image()
                
            if is_g92 and e == 0:
                if len(self.current_layer) > 1:
                    self.close_curve()

                self.current_layer = []        

            new_head_pos = self.head_pos.copy()

            if is_M118:
                new_collection = bpy.data.collections.new(f'Collection_{self.layer_number}')
                bpy.context.scene.collection.children.link(new_collection)
                if len(self.collections) > 0 and hide_new_collection:
                    self.collections[-1].hide_viewport = True

                self.collections.append(new_collection)

                self.layer_number += 1
                last_line = idx+line_num

                if len(self.current_layer) > 1:
                    self.close_curve()

                self.current_layer = []  
                self.set_head_pos(new_head_pos)

                if render:
                    filename = line.split(":")[1].split(",")[0]
                    self.render_image(filename)
                break
                
            if is_g1 or is_g0:       

                if x is not None:
                    new_head_pos.x = x

                if y is not None:
                    new_head_pos.y = y

                if z is not None:
                    new_head_pos.z = z

                if e is not None: #Extrusion Happen
                    new_pos_tup = (new_head_pos.x, new_head_pos.y, new_head_pos.z)
                    head_pos_tup = (self.head_pos.x, self.head_pos.y, self.head_pos.z)
                        
                    if len(self.current_layer) == 0:
                        self.current_layer.append(head_pos_tup)
                        self.current_layer.append(new_pos_tup)
                    else:
                        self.current_layer.append(new_pos_tup)

                self.set_head_pos(new_head_pos)


        if self.current_layer:
            self.close_curve()


        return last_line

gcode = GCodeParser()

def render_with_delay(settings):       
    global gcode

    render = settings.enable_render
    hide_collection = settings.hide_collection
    rendering = settings.rendering

    current_line = settings.current_line
     
    line = gcode.lines[current_line]
    current_line += 1
    newLine = gcode.parse_gcode(current_line,render=render,hide_new_collection=hide_collection)
    print(f"{current_line} - {newLine}")
    current_line = newLine
    
    settings.current_line = newLine

    if newLine == 0 or not rendering:
        for col in gcode.collections:
            col.hide_viewport = False
        return None
    
    return 0.1

    
def load_gcodefile(my_settings,force = False):

    if len(gcode.lines) == 0 or force:
        gcode.load_file(my_settings.file_path)

# Define the operator to read GCode file
class ReadGCodeOperator_Full(bpy.types.Operator):
    """Read GCode File"""
    bl_idname = "wm.read_gcode"
    bl_label = "Read GCode"

    
    def execute(self, context):
        try:
            # Check if we are still within the bounds of the file
            scene = context.scene
            my_settings = scene.my_settings

            load_gcodefile(my_settings)

            if len(gcode.lines) > 0:
                my_settings.rendering = True

                bpy.app.timers.register(functools.partial(render_with_delay, my_settings))
                
                self.report({'INFO'}, "End of GCode file reached.")
            else:
                self.report({'ERROR'}, f"GCode Data Empty")

            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read file: {str(e)}")
            return {'CANCELLED'}
    

class ReadGCodeOperator_Line(bpy.types.Operator):
    """Read GCode File"""
    bl_idname = "wm.read_gcode_line"
    bl_label = "Read GCode"

    
    def execute(self, context):
        try:
            scene = context.scene
            my_settings = scene.my_settings

            load_gcodefile(my_settings)

            my_settings.current_line += 1
            newLine = gcode.parse_gcode(my_settings.current_line,render=my_settings.enable_render, hide_new_collection= my_settings.hide_collection)
            print(f"{my_settings.current_line} - {newLine}")
            my_settings.current_line = newLine
            
            self.report({'INFO'}, "End of GCode file reached.")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read file: {str(e)}")
            return {'CANCELLED'}

class StopRender(Operator):
    bl_idname = "wm.stop_render"
    bl_label = "Stop Render"

    def execute(self, context):
        settings = context.scene.my_settings
        settings.rendering = False
        return {'FINISHED'}
        
class GCodeReset(bpy.types.Operator):
    """Read GCode File"""
    bl_idname = "wm.gcode_reset"
    bl_label = "Read GCode"
    
    def execute(self, context):
        try:
            scene = context.scene
            my_settings = scene.my_settings
            my_settings.current_line = 0

            gcode.__init__()
            gcode.set_filament_mat(my_settings.material_selector)
            load_gcodefile(my_settings,True)

            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read file: {str(e)}")
            return {'CANCELLED'}

def on_light_change(self, context):
    gcode.set_light(self.light_power)

def on_filamentmat_change(self, context):
    gcode.set_filament_mat(self.material_selector)

def on_file_select_change(self, context):
    file_path = self.file_path

    if file_path and file_path.lower().endswith('.gcode'):
        print(f"Loading GCode file: {file_path}")
        load_gcodefile(file_path,True)
    else:
        print("Please select a valid GCode file (.gcode)")

def get_materials(self, context):
    # This function dynamically retrieves all materials in the scene for the EnumProperty
    items = [(mat.name, mat.name, "") for mat in bpy.data.materials]
    return items if items else [('NONE', 'No Materials', '')]

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

        scene = context.scene
        my_settings = scene.my_settings

        row = layout.column()
        layout.prop(my_settings, "material_selector")
        row.prop(my_settings, "file_path", text="File Path")
        row = layout.row()
        row.prop(my_settings, "light_power", text="Brightness")
        row = layout.row()
        row.prop(my_settings, "enable_render", text="Render?")
        row.prop(my_settings, "hide_collection", text="Hide Collection")
        row = layout.row()
        row.prop(my_settings, "current_line", text="Line Number")
        row = layout.column()
        
        if not my_settings.rendering:
            row.operator("wm.read_gcode", text="GCode Full")
        else:
            row.operator("wm.stop_render", text="Stop Render")

        row.operator("wm.read_gcode_line", text="GCode Line By Line")

        layout.operator("wm.gcode_reset", text="Reset")

class MySettings(PropertyGroup):

    enable_render : BoolProperty(
        name="Enable or Disable",
        description="Render when parsing GCode",
        default = False
        )
    
    hide_collection : BoolProperty(
        name="Enable or Disable",
        description="Hide Newly Collection",
        default = False
        )
    
    rendering : BoolProperty(
        name="Stop Render",
        description="Stop Render",
        default = False
        )

    current_line : IntProperty(
        name = "Set a value",
        description="Render when parsing GCode",
        default=0
        )
    
    light_power : IntProperty(
        name = "Set a value",
        description="Setting the brightness of the light",
        default=800 * 1000,
        update=on_light_change
        )
    
    material_selector : EnumProperty(
        name="FDM Material",
        description="Select a material",
        default=2,
        items=get_materials,
        update=on_filamentmat_change
    )
    
    file_path : StringProperty(
        name="Select File",
        description="Select a file to load",
        default=os.getcwd(),
        subtype='FILE_PATH',
        update=on_file_select_change
    )
    
classes = (
    MySettings,
    ReadGCodeOperator_Full,
    ReadGCodeOperator_Line,
    GCodeReset,
    GCodeReaderPanel,
    StopRender
)

# Register and Unregister Classes
def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_settings = PointerProperty(type=MySettings)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

register()
