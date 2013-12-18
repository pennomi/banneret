"""Wavefront OBJ renderer using pyglet's Batch class.
Based on the public domain code by Juan J. Martinez <jjm@usebox.net>.
"""
import os
import pyglet
from pyglet import gl
from pyglet import graphics
import math
import euclid


class Material(graphics.Group):
    diffuse = [.8, .8, .8]
    ambient = [.2, .2, .2]
    specular = [0., 0., 0.]
    emission = [0., 0., 0.]
    shininess = 0.
    opacity = 1.
    texture = None

    def __init__(self, name, **kwargs):
        self.name = name
        super(Material, self).__init__(**kwargs)

    def set_state(self, face=gl.GL_FRONT_AND_BACK):
        if self.texture:
            gl.glEnable(self.texture.target)
            gl.glBindTexture(self.texture.target, self.texture.id)
        else:
            gl.glDisable(gl.GL_TEXTURE_2D)

        float4 = (gl.GLfloat * 4)
        o = [self.opacity]
        gl.glMaterialfv(face, gl.GL_DIFFUSE, float4(*(self.diffuse + o)))
        gl.glMaterialfv(face, gl.GL_AMBIENT, float4(*(self.ambient + o)))
        gl.glMaterialfv(face, gl.GL_SPECULAR, float4(*(self.specular + o)))
        gl.glMaterialfv(face, gl.GL_EMISSION, float4(*(self.emission + o)))
        gl.glMaterialf(face, gl.GL_SHININESS, self.shininess)

    def unset_state(self):
        if self.texture:
            gl.glDisable(self.texture.target)
        gl.glDisable(gl.GL_COLOR_MATERIAL)

    def __eq__(self, other):
        if self.texture is None:
            return super(Material, self).__eq__(other)
        return (self.__class__ is other.__class__ and
                self.texture.id == other.texture.id and
                self.texture.target == other.texture.target and
                self.parent == other.parent)

    def __hash__(self):
        if self.texture is None:
            return super(Material, self).__hash__()
        return hash((self.texture.id, self.texture.target))


class MaterialGroup(object):
    def __init__(self, material):
        self.material = material

        # Interleaved array of floats in GL_T2F_N3F_V3F format
        self.vertices = []
        self.normals = []
        self.tex_coords = []
        self.array = None


class Mesh(object):
    def __init__(self, name):
        self.name = name
        self.groups = []


class OBJ(object):
    @staticmethod
    def from_resource(filename):
        """Load an object using the resource framework"""
        loc = pyglet.resource.location(filename)
        return OBJ(filename, infile=loc.open(filename), path=loc.path)

    def __init__(self, filename, infile=None, path=None):
        self.materials = {}
        self.meshes = {}        # Name mapping
        self.mesh_list = []     # Also includes anonymous meshes

        self.transforms = euclid.Matrix4.new_identity()
        self.normalize = False

        if infile is None:
            infile = open(filename, 'r')

        if path is None:
            path = os.path.dirname(filename)
        self.path = path

        mesh = None
        group = None
        material = None

        vertices = [[0., 0., 0.]]
        normals = [[0., 0., 0.]]
        tex_coords = [[0., 0.]]

        for line in infile:
            if line.startswith('#'):
                continue
            values = line.split()
            if not values:
                continue

            if values[0] == 'v':
                vertices.append(map(float, values[1:4]))
            elif values[0] == 'vn':
                normals.append(map(float, values[1:4]))
            elif values[0] == 'vt':
                tex_coords.append(map(float, values[1:3]))
            elif values[0] == 'mtllib':
                self.load_material_library(values[1])
            elif values[0] in ('usemtl', 'usemat'):
                material = self.materials.get(values[1], None)
                if material is None:
                    print('Unknown material: %s'.format(values[1]))
                if mesh is not None:
                    group = MaterialGroup(material)
                    mesh.groups.append(group)
            elif values[0] == 'o':
                mesh = Mesh(values[1])
                self.meshes[mesh.name] = mesh
                self.mesh_list.append(mesh)
                group = None
            elif values[0] == 'f':
                if mesh is None:
                    mesh = Mesh('')
                    self.mesh_list.append(mesh)
                if material is None:
                    # FIXME
                    material = Material("<unknown>")
                if group is None:
                    group = MaterialGroup(material)
                    mesh.groups.append(group)

                # For fan triangulation, remember first and latest vertices
                n1 = None
                nlast = None
                t1 = None
                tlast = None
                v1 = None
                vlast = None
                for i, v in enumerate(values[1:]):
                    v_index, t_index, n_index = \
                        (map(int, [j or 0 for j in v.split('/')]) + [0, 0])[:3]
                    if v_index < 0:
                        v_index += len(vertices) - 1
                    if t_index < 0:
                        t_index += len(tex_coords) - 1
                    if n_index < 0:
                        n_index += len(normals) - 1

                    group.normals += normals[n_index]
                    group.tex_coords += tex_coords[t_index]
                    group.vertices += vertices[v_index]

                    if i >= 3:
                        # Triangulate
                        group.normals += n1 + nlast
                        group.tex_coords += t1 + tlast
                        group.vertices += v1 + vlast

                    if i == 0:
                        n1 = normals[n_index]
                        t1 = tex_coords[t_index]
                        v1 = vertices[v_index]
                    nlast = normals[n_index]
                    tlast = tex_coords[t_index]
                    vlast = vertices[v_index]

        assert len(normals) > 1, \
            ("It appears this .obj file is missing normals data. See this "
             "post for info on how to export from Blender: "
             "http://blender.stackexchange.com/questions/121/"
             "how-do-i-export-a-model-to-obj-format")

    def load_identity(self):
        """Discard any transformation"""
        self.transforms.identity()
        self.normalize = False

    def translate(self, x, y, z):
        self.transforms.translate(x, y, z)

    def rotate(self, angle, x, y, z):
        self.transforms.rotate_axis(math.pi*angle/180.0,
                                    euclid.Vector3(x, y, z))

    def scale(self, x, y, z):
        self.transforms.scale(x, y, z)
        self.normalize = True

    def add_to(self, specified_batch):
        """Add the meshes to a batch applying model transformations"""
        for mesh in self.mesh_list:
            for group in mesh.groups:
                vertices = []
                normals = []
                for index in xrange(0, len(group.vertices), 3):
                    tv = self.transforms * euclid.Point3(
                        group.vertices[index],
                        group.vertices[index+1],
                        group.vertices[index+2]
                    )
                    vertices.extend(tv[:])
                    tn = self.transforms * euclid.Point3(group.normals[index],
                                                         group.normals[index+1],
                                                         group.normals[index+2]
                                                         )
                    if self.normalize:
                        tn = tn.normalized()
                    normals.extend(tn[:])

                specified_batch.add(len(vertices)//3,
                                    gl.GL_TRIANGLES,
                                    group.material,
                                    ('v3f/static', tuple(vertices)),
                                    ('n3f/static', tuple(normals)),
                                    ('t2f/static', tuple(group.tex_coords)),
                                    )

    def open_material_file(self, filename):
        """Override for loading from archive/network etc."""
        return open(os.path.join(self.path, filename), 'r')

    def load_material_library(self, filename):
        material = None
        infile = self.open_material_file(filename)

        for line in infile:
            if line.startswith('#'):
                continue
            values = line.split()
            if not values:
                continue

            if values[0] == 'newmtl':
                material = Material(values[1])
                self.materials[material.name] = material
            elif material is None:
                print('Expected "newmtl" in %s'.format(filename))
                continue

            try:
                if values[0] == 'Kd':
                    material.diffuse = map(float, values[1:])
                elif values[0] == 'Ka':
                    material.ambient = map(float, values[1:])
                elif values[0] == 'Ks':
                    material.specular = map(float, values[1:])
                elif values[0] == 'Ke':
                    material.emissive = map(float, values[1:])
                elif values[0] == 'Ns':
                    material.shininess = float(values[1])
                elif values[0] == 'd':
                    material.opacity = float(values[1])
                elif values[0] == 'map_Kd':
                    try:
                        material.texture = pyglet.resource.image(
                            "resources/textures/{}".format(values[1])).texture
                    except BaseException as ex:
                        print('Could not load texture {}: {}'.format(
                            values[1], ex))
            except BaseException as ex:
                print('Parse error in {}. {}'.format(filename, ex))


if __name__ == "__main__":
    import sys
    import ctypes

    if len(sys.argv) != 2:
        print("Usage: {} file.obj".format(sys.argv[0]))
    else:
        window = pyglet.window.Window()
        fourfv = ctypes.c_float * 4
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, fourfv(0, 200, 5000, 1))
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, fourfv(0.0, 0.0, 0.0, 1.0))
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, fourfv(1.0, 1.0, 1.0, 1.0))
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_SPECULAR, fourfv(1.0, 1.0, 1.0, 1.0))
        gl.glEnable(gl.GL_LIGHT0)
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_DEPTH_TEST)

        @window.event
        def on_resize(width, height):
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()
            gl.gluPerspective(60.0, float(width)/height, 1.0, 100.0)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            return True

        @window.event
        def on_draw():
            window.clear()
            gl.glLoadIdentity()
            gl.gluLookAt(0, 8, 8, 0, 0, 0, 0, 1, 0)
            gl.glRotatef(rot, 1, 0, 0)
            gl.glRotatef(rot/2, 0, 1, 0)
            batch.draw()
            gl.glFinish()

        rot = 0

        def update(dt):
            global rot
            rot += dt*75
        pyglet.clock.schedule_interval(update, 1.0/60)

        obj = OBJ(sys.argv[1])
        batch = pyglet.graphics.Batch()
        obj.add_to(batch)
        pyglet.app.run()
