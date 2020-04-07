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

from math import radians, pi

import bpy
from mathutils import *

class Export:
    def __init__ (self, config, context):
        self.cfg = config
        self.ctx = context
        
        self.trace ("Ensuring there is a valid object to export")
        self.mesh = None
        nobj = len (self.ctx.selected_objects)
        if 0 == nobj:
            tmp = None
            num = 0
            #Scan for a single selectable mesh if user forgot to select one
            for obj in self.ctx.selectable_objects:
                if obj.type == 'MESH':
                    tmp = obj
                    num += 1
            if num != 1:
                self.trace ("...No selectable object found!")
            else:
                self.mesh = tmp
        elif 1 < nobj:
            self.trace ("...At most one object must be selected!")
        else:
            tmp = self.ctx.selected_objects[0]
            if tmp.type != 'MESH':
                self.trace ("...Selected object is not a mesh!")
            else:
                self.mesh = tmp
            
    def trace (self, text):
        if self.cfg.verbose is True:
            print (text)

    def main (self):
        from struct import pack
        if self.mesh is None:
            return -3
        
        #Export face data
        self.trace ("Generating header...")
        npoly = len (self.mesh.data.polygons)
        nverts = len (self.mesh.data.vertices)
        header = pack ("<HH44x", npoly, nverts)
        self.trace ("...Mesh has {} tris, {} verts".format (npoly, nverts))
        
        self.trace ("Generating triangle data")
        tris = bytearray ()
        for face in self.mesh.data.polygons:
            v = []
            st = []
            type = 0
            if len (face.loop_indices) < 3:
                self.trace ("Degenerate face found. Aborting")
                return -2
            if len (face.loop_indices) != 3:
                self.trace ("Nontriangular face found. Aborting")
                return -2
            for l in face.loop_indices:
                v.append (self.mesh.data.loops[l].vertex_index)
                #Create ST coords from normalised UVs
                if not self.mesh.data.uv_layers.active is None:
                    uv = self.mesh.data.uv_layers.active.data[l].uv
                    s = int (255.0*uv[0])
                    t = int (255.0*uv[1])
                else:
                    s = 0
                    t = 0
                st.append ((s, t))
            tris += pack ("<3Hbx6Bbx", 
                            v[0], v[1], v[2], 
                            type,
                            st[0][0], st[0][1],
                            st[1][0], st[1][1],
                            st[2][0], st[2][1],
                            face.material_index)
        
        self.trace ("Writing data to {}_d.3d...".format (self.cfg.filepath))
        _d = open (bpy.path.ensure_ext (self.cfg.filepath, "_d.3d"), 'wb')
        if _d is None:
            self.trace ("...Failed to open stream!")
            return -1
        _d.write (header + tris)
        _d.close ()
        
        #Export animation data
        self.trace ("Generating animation data")
        start = self.ctx.scene.frame_start
        end = self.ctx.scene.frame_end + 1
        aniv = bytearray ()
        for i in range (start, end):
            self.ctx.scene.frame_set (i)
            self.ctx.scene.update ()
            
            scale = self.cfg.scale
            m = self.mesh.to_mesh (self.ctx.scene, True, 'PREVIEW')
            for v in m.vertices:
                x = int (8*scale*v.co[0])&0x7ff
                y = int (8*scale*v.co[1])&0x7ff
                z = int (4*scale*v.co[2])&0x3ff
                aniv += pack ("<L", (z<<22)|(y<<11)|x)
            bpy.data.meshes.remove (m)
        
        self.trace ("Generating animation header")
        nframes = end - start
        size = 4*nverts
        aheader = pack ("<HH", nframes, size)
        self.trace ("...Animation is {}/{} frames".format (nframes, size))
        
        self.trace ("Writing data to {}_a.3d...".format (self.cfg.filepath))
        _a = open (bpy.path.ensure_ext (self.cfg.filepath, "_a.3d"), 'wb')
        if _a is None:
            self.trace ("...Failed to open stream!")
            return -1
        _a.write (aheader + aniv)
        _a.close ()
        
        #Create a little template UC file
        self.trace ("Generating {}.uc...".format (self.cfg.filepath))
        uc = open (bpy.path.ensure_ext (self.cfg.filepath, ".uc"), 'w')
        if uc is None:
            self.trace ("...Failed to open stream!")
            return -1
        name = bpy.path.basename (self.cfg.filepath)
        uc.write ("class {} extends Actor;\n".format (name))
        uc.write ("#exec MESH IMPORT MESH={} "
                    "ANIVFILE=MODELS\\{}_a.3d DATAFILE=MODELS\\{}_d.3d "
                    "X=0 Y=0 Z=0\n".format (name, name, name))
        uc.write ("#exec MESH ORIGIN MESH={} X=0 Y=0 Z=0\n".format (name))
        uc.write ("#exec MESH SEQUENCE MESH={} SEQ=All "
                    "STARTFRAME=0 NUMFRAMES={}\n".format (name, nframes))
        for m in self.mesh.data.materials:
            uc.write ("#exec TEXTURE IMPORT NAME={} "
                        "FILE=MODELS\\{}.PCX "
                        "GROUP=\"Skins\"\n".format (m.name, m.name))
        uc.write ("#exec MESHMAP SCALE MESHMAP={} "
                    "X=0.5 Y=0.5 Z=1.0\n".format (name))
        for i in range (len (self.mesh.data.materials)):
            uc.write ("#exec MESHMAP SETTEXTURE MESHMAP={} "
                        "NUM={} TEXTURE={}\n"
                        .format (name, i, self.mesh.data.materials[i].name))
        uc.close ()		
        
        self.trace ("Done")
        return 0
