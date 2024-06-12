import numpy as np
import cv2
import grpc
import time

import yolo_pb2
import yolo_pb2_grpc

from utills import image_to_bts, bts_to_img, drawText

class YoloClient:
    def __init__(self,address:str, imagesize:tuple[int,int]=(640,480), timeout:float=1):
        self.yolo_channel = grpc.insecure_channel(address)
        self.yolo_stub = yolo_pb2_grpc.YoloStub(self.yolo_channel)
        self.imagesize = imagesize
        self.timeout = timeout
    
    def Track(self, frame:np.ndarray) -> tuple[np.ndarray, dict]:
        start_time = time.perf_counter()
        frame = cv2.resize(frame, self.imagesize, interpolation = cv2.INTER_LINEAR)
        frame_str = image_to_bts(frame)
        request = yolo_pb2.Image(
            data = frame_str
        )
        yolo_start_time = time.perf_counter()
        try:
            response = self.yolo_stub.Track(request, timeout=self.timeout)
            yolo_delay = round((time.perf_counter() - yolo_start_time)*1000)
            output_frame_str = response.data
            output_metadata_str = response.metadata
            output_frame = bts_to_img(output_frame_str)
            delay = round((time.perf_counter() - start_time)*1000)
            output_frame = drawText(
                img=output_frame,
                text=f"delay={delay},yolo={yolo_delay},other={delay-yolo_delay}",
                text_color=(0,0,0),
                text_font_scale=1,
                textbg_color=(150,150,150),
                textbg_padding=1
            )
        except Exception as e:
            delay = -1
            yolo_delay = -1
            output_metadata_str = e
            output_frame = None
        
        info = {
            "delay":delay,
            "yolo_delay":yolo_delay,
            "metadata":output_metadata_str
        }
        return output_frame, info
    
##########################
from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
import threading
import argparse
import datetime
import imutils
import time
import cv2

outputFrame = None
lock = threading.Lock()

app = Flask(__name__)

vs = VideoStream(src=0).start()
time.sleep(2.0)

yoloclient = YoloClient(address='simpleapp.j12t-beta.svc.cluster.local:50051', timeout=10)

@app.route("/")
def index():
	# return the rendered template
	return render_template("index.html")
    
def detect_motion():
    # grab global references to the video stream, output frame, and
    # lock variables
    global vs, outputFrame, lock

    # initialize the motion detector and the total number of frames
    # read thus far
    total = 0
    while True:
        frame = vs.read()
        frame, info = yoloclient.Track(frame)
        with lock:
            if frame is None:
                print(f"ERROR: {info['metadata']}")
                continue
            outputFrame = frame.copy()

def generate():
    global outputFrame, lock
    
    while True:
        with lock:
            if outputFrame is None:
                continue
            flag, encodedImage = cv2.imencode(".jpg", outputFrame)
            if not flag:
                continue
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')
        
@app.route("/video_feed")
def video_feed():
    return Response(generate(),
        mimetype = "multipart/x-mixed-replace; boundary=frame")
    
if __name__=="__main__":
    t = threading.Thread(target=detect_motion)
    t.daemon = True
    t.start()
    app.run(
        host="localhost",
        port="8080",
        debug=True,
        threaded=True,
        use_reloader=False
    )
    
vs.stop()