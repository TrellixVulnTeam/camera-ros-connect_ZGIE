import pypylon.pylon as py
import numpy as np
import matplotlib.pyplot as plt
import traceback
import time
from datetime import datetime
import cv2
import subprocess as sp
import os

# import rospy
# from sensor_msgs.msg import Image as CameraImage

width = 1080
height = 1920
fps = 30
narrow_AutoExposureTimeUpperLimit = 50000
wide_AutoExposureTimeUpperLimit = 1000
quality_factor = 30
should_feed_video = False
should_visualize = True
should_filter = True

def ffmpeg_filter(frame, w,h):
    command = ['ffmpeg', '-y',
                '-s', '{}x{}'.format(h, w),
                '-f', 'rawvideo',
                '-r', '%.02f' % fps,
                '-an',
                '-pix_fmt', 'bgr24',
                '-i', '-',
                '-vf', "curves=r='0/0 0.25/0.4 0.5/0.5 1/1':g='0/0 0.25/0.4 0.5/0.5 1/1':b='0/0 0.25/0.4 0.5/0.5 1/1', drawtext='fontfile=c\:/Windows/Fonts/Calibri.ttf:text=%{localtime}:fontcolor=yellow:fontsize=35:x=1600:y=20:'",
                '-f', 'image2pipe',
                '-pix_fmt', 'bgr24',
                '-vcodec', 'rawvideo', '-']

    ffmpeg = sp.Popen(command, stderr=sp.DEVNULL ,stdout = sp.PIPE, stdin=sp.PIPE )
    out, err = ffmpeg.communicate(input=frame.tobytes())
    img = np.frombuffer(out, np.uint8).reshape((w, h, 3))
    return img


def image_feed(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2YUV_I420)
    # frame = cv2.cvtColor(frame, cv2.COLOR_BayerBG2BGR)
    return

def visualize(frame):
    # frame= cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.namedWindow("Input")
    cv2.imshow("Input", frame)
    cv2.waitKey(1)
    return

def initialize_cam(cam,camera_name):
    cam.UserSetSelector = 'Default'
    cam.UserSetLoad.Execute()

    # cam.PixelFormat = 'YCbCr422_8'
    # cam.ExposureTime = 200
    cam.PixelFormat = 'BayerGB8'
    cam.ExposureTime = 300
    cam.AcquisitionFrameRate = fps
    # cam.BslBrightness = 0.4
    # cam.BslContrast = 0.4
    if (camera_name == 'Narrow'):
        cam.ReverseX = True
        cam.ReverseY = True
        cam.ExposureAuto = 'Continuous'
        cam.AutoExposureTimeUpperLimit = narrow_AutoExposureTimeUpperLimit
        cam.AutoGainUpperLimit = 5.0

        # cam.LightSourcePreset = 'Off'
        # cam.BalanceWhiteAuto = 'Off'
        # cam.Gain = 1
        # cam.GainAuto = 'Off'
        
        # cam.BalanceRatioSelector = 'Red'
        # cam.BalanceRatio = 2.1875
        # cam.BalanceRatioSelector = 'Green'
        # cam.BalanceRatio = 1.46875
        # cam.BalanceRatioSelector = 'Blue'
        # cam.BalanceRatio = 1.76

    if (camera_name == 'Wide'):
        cam.ExposureAuto = 'Continuous'
        cam.AutoExposureTimeUpperLimit = wide_AutoExposureTimeUpperLimit
        cam.AutoGainUpperLimit = 5.0
        

class ImageHandler (py.ImageEventHandler):
    def __init__(self, *args):
        super().__init__(*args)
        self.time_old = time.time()

        self.converter = py.ImageFormatConverter()
        self.converter.OutputPixelFormat = py.PixelType_RGB8packed
        self.converter.OutputBitAlignment = "MsbAligned"
    
    def OnImageGrabbed(self, camera, grabResult):
        try:
            if grabResult.GrabSucceeded():
                
                if (~self.converter.ImageHasDestinationFormat(grabResult)):
                    grabResult = self.converter.Convert(grabResult)
                    
                img = grabResult.Array
                time_new = time.time()
                rate = 1/(time_new-self.time_old)
                print(rate)
                self.time_old = time_new
                # ret, img = cap.read()
                if (should_filter):
                    img = ffmpeg_filter(frame=img,w=width,h=height)
                if (should_feed_video):
                    image_feed(img)
                if (should_visualize):
                    visualize(img)
            else:
                raise RuntimeError("Grab failed")
        except Exception as e:
            traceback.print_exc()

def BackgroundLoop(cam):
    handler = ImageHandler()

    cam.RegisterImageEventHandler(handler, py.RegistrationMode_ReplaceAll, py.Cleanup_None)

    global feeder
    # with FFMPEG_Image_Feeder((cam.Height.Value, cam.Width.Value), fps=fps, pixfmt="yuv420p", codec="h264_qsv", quality= str(quality_factor), preset= 'fast') as feeder:
        # cam.StartGrabbingMax(100, py.GrabStrategy_LatestImages, py.GrabLoop_ProvidedByInstantCamera)
    cam.StartGrabbing(py.GrabStrategy_LatestImageOnly, py.GrabLoop_ProvidedByInstantCamera)
    # cam.StartGrabbing(py.GrabStrategy_LatestImages, py.GrabLoop_ProvidedByInstantCamera)

    try:
        while cam.IsGrabbing():
            pass
    except KeyboardInterrupt:
        pass

    cam.StopGrabbing()
    cam.DeregisterImageEventHandler(handler)
    cam.Close()
    cv2.destroyAllWindows()

# return handler.img_sum


tlf = py.TlFactory.GetInstance()
cam = py.InstantCamera(tlf.CreateFirstDevice())
cam.Open()

camera_name = cam.DeviceInfo.GetUserDefinedName()
print(f"connected to {camera_name} camera")

initialize_cam(cam, camera_name)

cap = cv2.VideoCapture('input.mp4')

BackgroundLoop(cam)