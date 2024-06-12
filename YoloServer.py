import grpc
from concurrent import futures

import yolo_pb2
import yolo_pb2_grpc

from ultralytics import YOLO
import numpy as np
import cv2

from utills import image_to_bts, bts_to_img

INSECURE_PORTS = ["[::]:50051",]

MODEL = YOLO(verbose=False)

class YoloServicer(yolo_pb2_grpc.YoloServicer):
    def Detect(self, request, context):
        return super().Detect(request, context)
    
    def Track(self, request, context):
        image_str = request.data
        # image = np.fromstring(image_str)
        image = bts_to_img(image_str)
        results = MODEL.track(image, verbose=False)
        output_image = results[0].plot()
        # _, output_image = cv2.imencode('.webp', output_image)
        # output_image_str = output_image.tobytes()
        output_image_str = image_to_bts(output_image)
        output_response = yolo_pb2.Image(
            data=output_image_str
        )
        return output_response

def serve(silent:bool):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    yolo_pb2_grpc.add_YoloServicer_to_server(YoloServicer(), server)
    for p in INSECURE_PORTS:
        server.add_insecure_port(p)
    server.start()
    print(f"==== Yolo ====")
    INFO = f"Insecure ports: {INSECURE_PORTS}"
    print(INFO)
    if silent:
        server.wait_for_termination()
    else:
        while True:
            print()
            usr_input = input("-> ")
            match usr_input:
                case "/exit":
                    server.stop(grace=True)
                    exit()
                case "/clear":
                    import os
                    os.system("cls")
                    print(f"==== YOLO service ====")
                    print(INFO)
                    continue
                case "/info":
                    print(INFO)
                    continue
                case _:
                    print(usr_input)
                    continue
    
if __name__=="__main__":
    serve(True)