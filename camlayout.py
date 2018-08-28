# coding:utf-8
import kivy.core.image
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import cv2
import time

SCREENSHOT_FOLDER_PATH = 'screenshots/'

class KivyCamera(Image):
    def __init__(self, parent, capture, **kwargs):
        super(KivyCamera, self).__init__(**kwargs)
        self.capture = capture  # data to read
        self.parent = parent    # this object's parent (= box layout)
        self.paused = False     # pause state
        self.started = False    # start state <= unused !

    # starts the "Camera", capturing at 30 fps by default
    def start(self, fps=30):
        Clock.schedule_interval(self.update, 1.0 / fps)

    def update(self, dt):
        # should be in start, not update
        rectangle_color = (0, 165, 255)

        ret, self.frame = self.capture.read()

        if ret and not self.paused:
            # Initialize a face cascade using the frontal face haar cascade provided
            # with the OpenCV2 library
            face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

            # For the face detection, we need to make use of a gray colored
            # image so we will convert the baseImage to a gray-based image
            gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

            # Now use the haar cascade detector to find all faces in the image
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            # For now, we are only interested in the 'largest' face, and we
            # determine this based on the largest area of the found
            # rectangle. First initialize the required variables to 0
            max_area = 0
            x = 0
            y = 0
            w = 0
            h = 0

            # Loop over all faces and check if the area for this face is
            # the largest so far
            for (_x, _y, _w, _h) in faces:
                if _w * _h > max_area:
                    x = _x
                    y = _y
                    w = _w
                    h = _h
                    max_area = w * h

            # If one or more faces are found, draw a rectangle around the
            # largest face present in the picture
            if max_area > 0:
                cv2.rectangle(self.frame, (x - 10, y - 20), (x + w + 10, y + h + 20),rectangle_color, 2)

            # Since we want to show something larger on the screen than the
            # original 320x240, we resize the image again
            # Note that it would also be possible to keep the large version
            # of the baseimage and make the result image a copy of this large
            # base image and use the scaling factor to draw the rectangle
            # at the right coordinates.
            resize_frame_result = cv2.resize(self.frame, (self.frame.shape[1], self.frame.shape[0]))

            # convert it to texture
            image_texture = self.get_texture_from_frame(self.frame, 0)

            # display image from the texture
            self.texture = image_texture
            self.parent.ids['imageCamera'].texture = self.texture
            print('updated')

    def stop(self):
        Clock.unschedule(self.update)

    def get_texture_from_frame(self, frame, flipped):
        buffer_frame = cv2.flip(frame, flipped)
        buffer_frame_str = buffer_frame.tostring()
        image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        print('('+str(frame.shape[1])+';'+str(frame.shape[0])+')')
        image_texture.blit_buffer(buffer_frame_str, colorfmt='bgr', bufferfmt='ubyte')
        return image_texture

    def captureImage(self):
        # if self.started
        timestr = time.strftime("%Y%m%d_%H%M%S")

        frameCopy = self.frame.copy()
        image_texture = self.get_texture_from_frame(frameCopy, 1)
        image_texture.save(SCREENSHOT_FOLDER_PATH + format(timestr) + ".png", False)


class CameraBoxLayout(BoxLayout):
    started = False
    # initialize the "Camera"
    # kivyCamera = Image(source='mini.jpg')
    kivyCamera = None

    def startCamera(self, imageCamera, buttonStart, buttonStop, buttonCapture):

        if not self.started:
            self.capture = cv2.VideoCapture(0)

            self.kivyCamera = KivyCamera(self, self.capture)
            imageCamera = self.kivyCamera

            self.kivyCamera.start()

            # Set as started, so next action will be 'Pause'
            self.started = True
            buttonStart.text = 'Pause'
            buttonStop.text = 'Stop' # useless ?
            # when started, set stop to enabled
            # &&
            # when started, let start enabled
            buttonStop.disabled = False  # enabled

            # Enable the capture (button)
            buttonCapture.disabled = False
        else:
            # Set as paused
            self.kivyCamera.paused = not self.kivyCamera.paused
            imageCamera.source = 'mini.jpg'

            if not self.kivyCamera.paused:
                buttonStart.text = 'Pause'
            else:
                buttonStart.text = 'Start'

    # stops the kivy camera (doesn't care either camera is started or paused)
    def stopCamera(self, imageCamera, buttonStart, buttonStop, buttonCapture):

        if self.started: # Was running at click
            buttonStop.disabled = True
            self.started = False  # stop what was "started"
            # Reset kivy camera to 'mini.jpg' (home image)
            self.kivyCamera.stop()
            self.kivyCamera = Image(source='mini.jpg')
            imageCamera.source = self.kivyCamera.source
            imageCamera.reload()

            # Reset Start Button to 'Start value' (e.g. instead of eventually 'Pause value')
            buttonStart.text = 'Start'

            # Disable the capture (button)
            buttonCapture.disabled = True

            # Release the capture
            self.capture.release()

    def takeScreenshot(self, imageCamera):
        self.kivyCamera.captureImage()


class CamApp(App):
    cameraBoxLayout = None

    def build(self):
        self.cameraBoxLayout = CameraBoxLayout()
        return self.cameraBoxLayout

    def on_stop(self):
        # without this, app will not exit even if the window is closed
        self.cameraBoxLayout.stopCamera(
            self.cameraBoxLayout.ids['imageCamera'],
            self.cameraBoxLayout.ids['buttonStart'],
            self.cameraBoxLayout.ids['buttonStop'],
            self.cameraBoxLayout.ids['buttonCapture'])


camApp = CamApp()
camApp.run()
