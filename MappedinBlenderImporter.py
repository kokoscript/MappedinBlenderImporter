"""
    Mappedin Embed Blender Importer
    Copyright (C) 2024 kokoscript

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import bpy
import json
from math import radians, inf
from mathutils import Vector

bl_info = {
    'name': 'Mappedin Embed Geometry Importer',
    'version': (1, 0, 0),
    'blender': (4, 0, 0),
    'author': 'kokoscript',
    'description': 'Importer for JSON-based geometry data from a Mappedin embed.',
    'location': 'File > Import > Mappedin Embed Geometry',
    'category': 'Import-Export'
}

""" Creates a new shape object in the scene.
Args:
    vertices (array): Array of dicts, each with 'x' and 'y' keys, representing the shape.
    geometry (dict): Additional geometry information, including z position and depth.
    isHole (bool): Specifies whether or not this shape is a hole. Default is False.
Returns:
    Instance of bpy.types.Object (the resultant object)
"""
def createShapeObj(vertices, geometry, isHole=False):
    mesh_vtx = []
    mesh_face = []
    
    # read in vertex data
    for vtx in vertices:
        mesh_face.append(len(mesh_vtx))
        mesh_vtx.append((-vtx['x']/10, vtx['y']/10, geometry['position']['z']))
    
    # create mesh and parent object
    mesh = bpy.data.meshes.new('Mesh')
    mesh.from_pydata(mesh_vtx, [], [mesh_face])
    mesh.update()
    obj = bpy.data.objects.new('Mesh', mesh)
    
    # add solidify
    solidify = obj.modifiers.new('Solidify', 'SOLIDIFY')
    solidify.offset = 0
    solidify.thickness = geometry['scale']['z'] if not isHole else 999
    
    # apply solidify
    with bpy.context.temp_override(object=obj):
        bpy.ops.object.modifier_apply(modifier='Solidify')
    
    # make the object sit atop the xy plane
    loc_z = geometry['scale']['z']/2
    obj.location = Vector((0, 0, loc_z))

    bpy.data.collections['Collection'].objects.link(obj)
    return obj

""" Applies color attributes to all vertices in an object.
Args:
    obj (bpy.types.Object): Object to apply the color to.
    material (dict): Material information (color + opacity).
"""
def applyColorAttrib(obj, material):
    mesh_col = []
    mesh_col.append(int(material['color'][1:3], 16)/255)
    mesh_col.append(int(material['color'][3:5], 16)/255)
    mesh_col.append(int(material['color'][5:7], 16)/255)
    mesh_col.append(material['opacity'])
    
    # apply color vtx attributes
    if material is not None:
        colattr = obj.data.color_attributes.new(name='Color', type='FLOAT_COLOR', domain='POINT')
        for vtx in colattr.data:
            vtx.color = mesh_col
    
""" Boolean subtracts obj2 from obj1, and deletes obj2 from the scene.
Args:
    obj1 (bpy.types.Object): Object to subtract from.
    obj2 (bpy.types.Object): Object defining the shape of the subtraction.
"""
def subtractObj(obj1, obj2):
    # add boolean
    boolean = obj1.modifiers.new('Boolean', 'BOOLEAN')
    boolean.object = obj2
    boolean.operation = 'DIFFERENCE'
    boolean.solver = 'EXACT'
    
    # apply boolean, delete obj2
    with bpy.context.temp_override(object=obj1):
        bpy.ops.object.modifier_apply(modifier='Boolean')
    with bpy.context.temp_override(selected_objects=[obj2]):
        bpy.ops.object.delete()

""" Calculates the origin of a shape.
Args:
    vertices (array): Array of dicts, each with 'x' and 'y' keys, representing the shape.
Returns:
    Tuple containing the (x, y) coordinates of the origin.
"""
def getShapeOrigin(vertices):
    min_x = inf
    max_x = -inf
    min_y = inf
    max_y = -inf
    for vtx in vertices:
        if vtx['x'] < min_x:
            min_x = vtx['x']
        if vtx['x'] > max_x:
            max_x = vtx['x']
        if vtx['y'] < min_y:
            min_y = vtx['y']
        if vtx['y'] > max_y:
            max_y = vtx['y']
    return ((min_x+max_x)/2, (min_y+max_y)/2)

""" Creates a text object in the scene.
Args:
    lb (dict): Label information, including the text string, size, alignment, position, and rotation.
    vtx (array): Array of dicts, each with 'x' and 'y' keys, representing the label's parent shape.
"""
def createLabel(lb, vtx):
    # create text curve
    curve = bpy.data.curves.new(type='FONT', name='Label')
    curve.body = lb['text']
    curve.size = lb['fontSize']/1.5
    curve.align_x = 'LEFT' if lb['align'] == 'left' else 'RIGHT' if lb['align'] == 'right' else 'CENTER'
    obj = bpy.data.objects.new(name='Label', object_data=curve)
    
    # label position
    origin = getShapeOrigin(vtx)
    loc = lb['position']
    # pos values seem to be relative to the parent shape, but I can't get the offsets to look right
    # they genuinely look more accurate if we don't bother and just go with the shape origin
    loc_x = -origin[0]/10 #- (loc['x']/10 if 'x' in loc else 0)
    loc_y = origin[1]/10 #- (loc['y']/10 if 'y' in loc else 0)
    loc_z = loc['z']/10 if 'z' in loc else 0
    obj.location = Vector((loc_x, loc_y, loc_z))
    
    # label rotation
    rot = lb['rotation']
    rot_x = radians(rot['x']) if 'x' in rot else 0
    rot_y = radians(rot['y']) if 'y' in rot else 0
    rot_z = radians(rot['z']+180) if 'z' in rot else 0
    obj.rotation_euler = Vector((rot_x, rot_y, rot_z))
    
    bpy.data.collections['Collection'].objects.link(obj)

""" Main import worker; parses a json file, iterates through it, and creates objects as necessary.
Args:
    path (string): Location of the json file.
"""
def importJson(path):
    f = open(path, 'r')
    data = json.load(f)
    f.close()
    
    for shape in data:
        # create shape geometry
        if 'vertexes' in shape and shape['geometry']['visible']:
            shapeObj = createShapeObj(shape['vertexes'], shape['geometry'])
            # if this shape has a hole, create a mesh for it and subtract it
            if 'holes' in shape:
                for hole in shape['holes']:
                    holeObj = createShapeObj(hole, shape['geometry'], True)
                    subtractObj(shapeObj, holeObj)
            # apply color after optionally making a hole, so we don't end up with uncolored verts
            applyColorAttrib(shapeObj, shape['material'])
        # create text labels
        if 'label' in shape and 'visible' in shape['label'] and shape['label']['visible']:
            createLabel(shape['label'], shape['vertexes'])
    
    return {'FINISHED'}

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator

class MIImporter(Operator, ImportHelper):
    bl_idname = 'import_json.mappedin'
    bl_label = 'Import JSON'
    filename_ext = '.json'

    filter_glob: StringProperty(
        default='*.json',
        options={'HIDDEN'},
        maxlen=255
    )

    def execute(self, context):
        return importJson(self.filepath)

def menu_func_import(self, context):
    self.layout.operator(MIImporter.bl_idname, text='Mappedin Embed Geometry (.json)')

def register():
    bpy.utils.register_class(MIImporter)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(MIImporter)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == '__main__':
    register()
