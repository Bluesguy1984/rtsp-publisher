import atexit
import io
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import PyavOutput
import signal
import threading
import time

class Camera:
    def __init__(self, cam_index=0):
        self.picam = Picamera2(cam_index)
        self.running = False

        self.video_config = self.picam.create_video_configuration(
            main={"size": (1280, 720), "format": "YUV420"},
            controls={"FrameRate": 20}
        )
        self.picam.configure(self.video_config)

        self.h264_encoder = H264Encoder(bitrate=6_000_000)
        self.rtsp_output = PyavOutput(
            "rtsp://127.0.0.1:8554/camera",
            format="rtsp",
            options={"rtsp_transport": "tcp"}
        )

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        atexit.register(self.stop)

    def start(self):
        if self.running:
            return
        try:
            self.picam.start()
            self.picam.start_recording(self.h264_encoder, self.rtsp_output)
            self.running = True
            while True:
                time.sleep(1.0)
        except Exception:
            self.stop()
            raise

    def stop(self):
        if not self.running:
            return
        try:
            self.picam.stop_recording()
        except Exception:
            pass
        try:
            self.picam.stop()
        except Exception:
            pass
        try:
            self.picam.close()
        except Exception:
            pass
        self.running = False

    def _signal_handler(self, signum, frame):
        self.stop()
        raise SystemExit
