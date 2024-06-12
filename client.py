import grpc
import cv2
import multiprocessing as mp
import time

import yolo_pb2_grpc
import yolo_pb2

from utills import bts_to_img, image_to_bts, drawText

yolo_addr = 'localhost:50051'


def Main(path=0):
    yolo_channel = grpc.insecure_channel(yolo_addr)
    yolo_stub = yolo_pb2_grpc.YoloStub(yolo_channel)
    cap = cv2.VideoCapture(path)
    dropped = 0
    captured = 0
    while cap.isOpened():
        start_time = time.perf_counter()
        success, frame = cap.read()
        if success:
            captured += 1
            try:
                frame = cv2.resize(frame, (640,480), interpolation = cv2.INTER_LINEAR)
                image_str = image_to_bts(frame)
                request = yolo_pb2.Image(
                    data = image_str
                )
                yolo_start_time = time.perf_counter()
                response = yolo_stub.Track(request, timeout=1)
                yolo_delay = round((time.perf_counter() - yolo_start_time)*1000)
                output_image_str = response.data
                output_image = bts_to_img(output_image_str)
                delay = round((time.perf_counter() - start_time)*1000)
                output_image = drawText(
                    img=output_image,
                    text=f"delay={delay},yolo={yolo_delay},other={delay-yolo_delay}|dropped={dropped}/{captured}",
                    text_color=(0,0,0),
                    text_font_scale=1,
                    textbg_color=(150,150,150),
                    textbg_padding=1
                )
                cv2.imshow(f"YOLOv8 Remote Tracking", output_image)
            except Exception as e:
                dropped += 1
                print(f"ERROR: {e}")
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("QUIT")
            cap.release()
            cv2.destroyAllWindows()
            yolo_channel.close()
            break
        if cv2.waitKey(1) & 0xFF == ord("p"):
            print("PAUSE")
            while True:
                if cv2.waitKey(0) & 0xFF == ord("p"):
                    break
            print("RESUME")
            
if __name__=="__main__":
    args = [
        0,
        # "D:\\jer7nett\\Videos\\Honkai  Star Rail\\Honkai  Star Rail 2024.05.10 - 03.00.16.02.mp4",
        # "D:\\jer7nett\\Videos\\Genshin Impact\\Genshin Impact 2024.05.14 - 20.45.40.01.mp4",
        # "D:\\jer7nett\\Videos\\Genshin Impact\\Genshin Impact 2024.02.29 - 00.02.17.05.mp4",
        # "D:\\jer7nett\\Videos\\Honkai  Star Rail\\Honkai  Star Rail 2024.05.10 - 03.00.16.02.mp4",
        # "D:\\jer7nett\\Videos\\Genshin Impact\\Genshin Impact 2024.02.29 - 00.02.17.05.mp4",
        # "D:\\jer7nett\\Videos\\Genshin Impact\\Genshin Impact 2024.02.29 - 00.02.17.05.mp4"
    ]
    ps = [mp.Process(target=Main, args=(a,)) for a in args]
    for p in ps:
        p.start()
    for p in ps:
        p.join()