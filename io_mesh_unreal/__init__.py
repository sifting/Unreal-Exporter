# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation, either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
	"name": "Unreal Gold Format",
	"author": "Sifting",
	"version": (1, 0, 0),
	"blender": (2, 78, 0),
	"location": "File > Export > Unreal Gold",
	"description": "Exports model for use in Unreal Gold type games",
	"wiki_url": "",
	"category": "Import-Export"}


import bpy
from bpy.props import BoolProperty
from bpy.props import FloatProperty
from bpy.props import StringProperty


class ExportUnreal(bpy.types.Operator):
	bl_idname = "export_scene.unreal"
	bl_label = "Export Unreal Gold"

	filepath = StringProperty(subtype='FILE_PATH')

	# Export options
	verbose = BoolProperty(
		name="Verbose",
		description="Spews debugging info to console",
		default=True)

	scale = FloatProperty( 
		name="Scale",
		description="Amount to scale model before export",
		default=32,
		min = 1,
		max = 256,
		step = 8)

	def execute(self, context):
		from . import uexport
		Exporter = uexport.Export (self, context)
		if Exporter.main () != 0:
			def draw (window, ctx):
				window.layout.label ("See console for more info")
			bpy.context.window_manager.popup_menu (draw, title="ERROR")
		else:
			def draw (window, ctx):
				window.layout.label ("Export OK")
			bpy.context.window_manager.popup_menu (draw, title="SUCCESS")			
		return {'FINISHED'}

	def invoke(self, context, event):
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}


def menu_func(self, context):
	self.layout.operator(ExportUnreal.bl_idname, text="Unreal Gold")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.INFO_MT_file_export.append(menu_func)


def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.INFO_MT_file_export.remove(menu_func)


if __name__ == "__main__":
	register()
