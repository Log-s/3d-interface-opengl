from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import glm

import numpy as np
import trimesh
import pywavefront
import sys


class Camera():

    def __init__(
        self,
        eye=None, target=None, up=None,
        fov=None, near=0.1, far=100000
    ):
        self.eye = eye or glm.vec3(0, 0, 1)
        self.target = target or glm.vec3(0, 0, 0)
        self.up = up or glm.vec3(0, 1, 0)
        self.original_up = glm.vec3(self.up)
        self.fov = fov or glm.radians(45)
        self.near = near
        self.far = far

    def update(self, aspect):
        self.view = glm.lookAt(
            self.eye, self.target, self.up
        )
        self.projection = glm.perspective(
            self.fov, aspect, self.near, self.far
        )

    def zoom(self, amount):
        delta = amount * 0.1
        self.eye = self.target + (self.eye - self.target) * (delta + 1)

    def load_projection(self):
        width = glutGet(GLUT_WINDOW_WIDTH)
        height = glutGet(GLUT_WINDOW_HEIGHT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(glm.degrees(self.fov), width / height, self.near, self.far)

    def load_modelview(self):
        e = self.eye
        t = self.target
        u = self.up

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(e.x, e.y, e.z, t.x, t.y, t.z, u.x, u.y, u.z)


class CameraMovement(Camera): # from Rabbid76

    def rotate_around_target(self, target, delta):

        # get directions
        los = self.target - self.eye
        losLen = glm.length(los)
        right = glm.normalize(glm.cross(los, self.up))
        up = glm.cross(right, los)

        # upright up vector (Gram–Schmidt orthogonalization)
        fix_right = glm.normalize(glm.cross(los, self.original_up))
        UPdotX = glm.dot(fix_right, up)
        up = glm.normalize(up - UPdotX * fix_right)
        right = glm.normalize(glm.cross(los, up))
        los = glm.cross(up, right)

        # tilt around horizontal axis
        RHor = glm.rotate(glm.mat4(1), delta.y, right)
        up = glm.vec3(RHor * glm.vec4(up, 0.0))
        los = glm.vec3(RHor * glm.vec4(los, 0.0))

        # rotate around up vector
        RUp = glm.rotate(glm.mat4(1), delta.x, up)
        right = glm.vec3(RUp * glm.vec4(right, 0.0))
        los = glm.vec3(RUp * glm.vec4(los, 0.0))

        # set eye, target and up
        self.eye = target - los * losLen
        self.target = target
        self.up = up

    def rotate_around_origin(self, delta):
        return self.rotate_around_target(glm.vec3(0), delta)

    def rotate_target(self, delta):
        return self.rotate_around_target(self.eye, delta)

    def move_right(self):
        self.eye = glm.vec3(self.eye[0]+0.1, self.eye[1], self.eye[2])
        self.target = glm.vec3(self.target[0]+0.1, self.target[1], self.target[2])

    def move_left(self):
        self.eye = glm.vec3(self.eye[0]-0.1, self.eye[1], self.eye[2])
        self.target = glm.vec3(self.target[0]-0.1, self.target[1], self.target[2])

    def move_forward(self):
        self.target = glm.vec3(self.target[0]-0.1, self.target[1], self.target[2])

    def move_back(self):
        self.target = glm.vec3(self.target[0]-0.1, self.target[1], self.target[2])

class GlutController():

    def __init__(self, camera, velocity=100, velocity_wheel=100):
        self.velocity = velocity
        self.velocity_wheel = velocity_wheel
        self.camera = camera

    def glut_mouse(self, button, state, x, y):
        
        WHEEL_UP = 3
        WHEEL_DOWN = 4

        self.mouse_last_pos = glm.vec2(x, y)
        self.mouse_down_pos = glm.vec2(x, y)

        if button == WHEEL_UP:
            self.camera.zoom(-1)
        elif button == WHEEL_DOWN:
            self.camera.zoom(1)

    def glut_motion(self, x, y):
        pos = glm.vec2(x, y)
        move = self.mouse_last_pos - pos
        self.mouse_last_pos = pos

        self.camera.rotate_around_origin(move * 0.005)



scene = pywavefront.Wavefront(sys.argv[1], collect_faces=True)

scene_box = (scene.vertices[0], scene.vertices[0])
for vertex in scene.vertices:
    min_v = [min(scene_box[0][i], vertex[i]) for i in range(3)]
    max_v = [max(scene_box[1][i], vertex[i]) for i in range(3)]
    scene_box = (min_v, max_v)

scene_size     = [scene_box[1][i]-scene_box[0][i] for i in range(3)]
max_scene_size = max(scene_size)
scaled_size    = 5
scene_scale    = [scaled_size/max_scene_size for i in range(3)]
scene_trans    = [-(scene_box[1][i]+scene_box[0][i])/2 for i in range(3)]

def Model():

    glPushMatrix()
    glScalef(*scene_scale)
    glTranslatef(*scene_trans)

    for mesh in scene.mesh_list:
        glBegin(GL_TRIANGLES)
        for face in mesh.faces:
            for vertex_i in face:
                glVertex3f(*scene.vertices[vertex_i])
        glEnd()

    glPopMatrix()



class MyWindow:

    def __init__(self, w, h):
        self.width = w
        self.height = h

        glutInit()
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
        glutInitWindowSize(w, h)
        glutCreateWindow('OpenGL Window')

        self.startup()

        glutReshapeFunc(self.reshape)
        glutDisplayFunc(self.display)
        glutMouseFunc(self.controller.glut_mouse)
        glutMotionFunc(self.controller.glut_motion)
        glutKeyboardFunc(self.keyboard_func)
        glutIdleFunc(self.idle_func)


    def startup(self):
        glEnable(GL_DEPTH_TEST)

        params = {
            "eye": glm.vec3(0, 0, -5),
            "target": glm.vec3(0, 0, 0),
            "up": glm.vec3(0, 1,0)
        }
        self.camera = CameraMovement(**params)
        self.model = glm.mat4(1)
        self.controller = GlutController(self.camera)

    def run(self):
        glutMainLoop()

    def idle_func(self):
        glutPostRedisplay()

    def reshape(self, w, h):
        glViewport(0, 0, w, h)
        self.width = w
        self.height = h

    def keyboard_func(self, *args):
        try:
            key = args[0].decode("utf-8")

            if key == "z":
                pass
            elif key == "q":
                self.camera.move_left()
            elif key == "s":
                pass
            elif key == "d":
                self.camera.move_right()

        except:
            pass


    def display(self):
        self.camera.update(self.width / self.height)

        #glClearColor(0.2, 0.3, 0.3, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.camera.load_projection()
        self.camera.load_modelview()

        # displays your 3d model
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        Model()
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glutSwapBuffers()


if __name__ == '__main__':
    window = MyWindow(800, 600)
    window.run()