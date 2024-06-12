# Videotracking -- YOLOv8 -- gRPC

This project is made to seperate [YOLOv8](https://github.com/ultralytics/ultralytics) instance, render instance and move them to cloud.

## Install

### For testing purposes

**WARNING:** Remember to use `virtualenv` or `conda`!!!

1. Install dependances: `pip install -r requirements.txt`
2. Run: `python YoloServer.py`
3. Run: `python WebServer.py`
4. Open `localhost:8080/?url={video_url}` to try it out (or just `localhost:8080` for quick testing)

### Docker images

- [YoloServer](https://hub.docker.com/repository/docker/jerapiblannett/videotracking-grpc)
- [RenderServer](https://hub.docker.com/repository/docker/jerapiblannett/videotracking-grpc-webserver/general)

### Kubernetes deploy

Apply all configs in `k8s` folder.