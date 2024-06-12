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
    

from flask import Response
from flask import Flask
from flask import render_template, request
import threading
import argparse
import datetime
import time
from vidgear.gears import CamGear, VideoGear
import os
import cv2
from urllib.parse import unquote

import logging

logger = logging.getLogger("videoproc")
logger.setLevel(100)

os.environ.update({
    "PAFY_BACKEND": "internal"
})

app = Flask("Remote YOLOv8")

def img_encode(frame):
    flag, encodedImage = cv2.imencode(".jpg", frame)
    if not flag:
        return b'0'
    return encodedImage

options = {"STREAM_RESOLUTION": "480p"}
def feed(url:str|int):
    imgsize=(640,480)
    yoloclient = YoloClient("simpleapp.j12t-beta.svc.cluster.local:50051", imagesize=imgsize, timeout=5)
    # cap = cv2.VideoCapture(url)
    if type(url) == str:
        cap = CamGear(source=url, stream_mode=True, **options).start()
    else:
        cap = CamGear(source=url).start()
    outputFrame = np.zeros(imgsize).transpose()
    # while cap.isOpened():
    while True:
        # success, frame = cap.read()
        input_frame = cap.read()
        if not (input_frame is None):
            frame, info = yoloclient.Track(input_frame)
            if (frame is None):
                outputFrame = input_frame
            else:
                outputFrame = frame
                logger.info(info)
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(img_encode(outputFrame)) + b'\r\n') 
    
@app.route("/", methods=["GET"])
def feedRoute():
    url = request.args.get("url", default="https://www.youtube.com/watch?v=dQw4w9WgXcQ", type=str)
    if url == "0" or url == "1" or url == "2" or url == "3":
        url = int(url)
    else:
        url = unquote(url)
    return Response(
        feed(url),
        mimetype = "multipart/x-mixed-replace; boundary=frame"
    )
    
if __name__=="__main__":
    app.run(
        host="0.0.0.0",
        port="8080",
        debug=True,
        threaded=True,
        use_reloader=False
    )