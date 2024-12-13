import os
import sys


plugin_path = os.path.dirname(__file__)
if plugin_path not in sys.path:
    sys.path.append(plugin_path)


from GCodeParser import GCodeParser
import functools
import bpy
import functools


bl_info = {
    "name": "GCode Parser",
    "description": "Simulate 3D Printer",
    "author": "Saleh Ebrahimian",
    "version": (1, 1, 1),
    "blender": (4, 2, 1),
    "location": "GCode > GCode PA",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "3D Print"
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

gcode = GCodeParser(context=None)
# print(gcode.dir_path)
gcode_init = False

def render_with_delay(settings):       
    global gcode

    render = settings.enable_render
    hide_collection = settings.hide_collection
    rendering = settings.rendering

    current_line = settings.current_line
    newLine = gcode.parse_gcode(current_line,render=render,hide_new_collection=hide_collection)
    print(f"{current_line} - {newLine}")
    
    settings.current_line = newLine

    if newLine == 0 or not rendering:
        for col in gcode.collections:
            col.hide_viewport = False
        return None
    
    return 0.001

    
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

            gcode.set_context(context=context)

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

            gcode.set_context(context=context)
            load_gcodefile(my_settings)

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
        global gcode_init
        try:
            scene = context.scene
            my_settings = scene.my_settings
            my_settings.current_line = 0
            my_settings.enable_render = False
            my_settings.hide_collection = False
            my_settings.rendering = False
            my_settings.cam_lens = 29.6
            my_settings.sen_width = 45
            my_settings.layer_width = 0.4
            my_settings.layer_height = 0.2
            my_settings.light_power = 1200 * 1000
            my_settings.material_selector = "FilamentMat"
            # my_settings.file_path = os.getcwd()
            # my_settings.save_path = os.getcwd()

            gcode.__init__(context=context, camera_lens=my_settings.cam_lens,sensor_width=my_settings.sen_width,
                           layer_height=my_settings.layer_height, layer_width=my_settings.layer_width)
            
            on_setting_change(my_settings, None)

            gcode_init = True
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}

def on_setting_change(self, context):
    gcode.camera.data.lens = self.cam_lens
    gcode.camera.data.sensor_width = self.sen_width
    gcode.set_light(self.light_power)
    gcode.set_filament_mat(self.material_selector)

    gcode.set_elip_bevel(self.layer_height,self.layer_width)
    
    save_path = self.save_path
    if save_path:
        print(f"Save Path Set: {save_path}")
        gcode.set_save_path(save_path)
    else:
        print("Please select a valid GCode file (.gcode)")

    file_path = self.file_path
    if os.path.exists(file_path) and file_path and file_path.lower().endswith('.gcode'):
        print(f"Loading GCode file: {file_path}")
        load_gcodefile(self,True)
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
        global gcode_init
        
        layout = self.layout

        scene = context.scene
        my_settings = scene.my_settings

        row = layout.column()
        
        if not gcode_init:
            layout.operator("wm.gcode_reset", text="Press this Button To Start")
        else:
            row.prop(my_settings, "file_path", text="File Path")
            row.prop(my_settings, "save_path", text="Save Path")
            row = layout.row()
            row.prop(my_settings, "material_selector")
            row = layout.row()
            row.prop(my_settings, "layer_width", text="Layer Width")
            row.prop(my_settings, "layer_height", text="Layer Height")
            row = layout.row()
            row.prop(my_settings, "sen_width", text="Sensor")
            row.prop(my_settings, "cam_lens", text="Lens")
            row = layout.row()
            row.prop(my_settings, "light_power", text="Brightness")
            row = layout.row()
            row.prop(my_settings, "enable_render", text="Render?")
            row.prop(my_settings, "hide_collection", text="Hide Collection")
            row = layout.row()
            row.prop(my_settings, "current_line", text="Line Number")
            if len(gcode.lines) > 0:
                layout.label(text=f"Progress: {(my_settings.current_line / len(gcode.lines)) * 100:.1f}%")
            
            row = layout.column()
            if not my_settings.rendering:
                row.operator("wm.read_gcode", text="GCode Full")
            else:
                row.operator("wm.stop_render", text="Stop Render")

            row.operator("wm.read_gcode_line", text="GCode Line By Line")

            layout.operator("wm.gcode_reset", text="Reset")
        layout.label(text=f"version {bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}")

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
    
    cam_lens : FloatProperty(
        name = "Set a value",
        description="Setting the camera lens",
        default=29.6,
        update=on_setting_change
        )
    
    sen_width : IntProperty(
        name = "Set a value",
        description="Setting the sensor width",
        default=45,
        update=on_setting_change
        )
    
    layer_width : FloatProperty(
        name = "Set a value",
        description="Setting the layer width",
        default=0.4,
        update=on_setting_change
        )
    
    layer_height : FloatProperty(
        name = "Set a value",
        description="Setting the layer height",
        default=0.2,
        update=on_setting_change
        )
    
    light_power : IntProperty(
        name = "Set a value",
        description="Setting the brightness of the light",
        default=800 * 1000,
        update=on_setting_change
        )
    
    material_selector : EnumProperty(
        name="FDM Material",
        description="Select a material",
        default=2,
        items=get_materials,
        update=on_setting_change
    )
    
    file_path : StringProperty(
        name="Select File",
        description="Select a file to load",
        default=os.getcwd(),
        subtype='FILE_PATH',
        update=on_setting_change
    )

    save_path : StringProperty(
        name="Select Save Path",
        description="Select a path for save rendered files",
        default=os.getcwd(),
        subtype='DIR_PATH',
        update=on_setting_change
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
    global gcode_init
    
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_settings = PointerProperty(type=MySettings)
    gcode_init = False

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
        
if __name__ == "<run_path>":
    register()