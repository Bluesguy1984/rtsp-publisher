import atexit
import io
import os
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import PyavOutput
import requests
import signal
import threading
import time

class Camera:
    def __init__(self, cam_index=0):
        self.camera_name = os.getenv("CAMERA_NAME", "camera")
        self.camera_index = int(os.getenv("CAMERA_INDEX", "0"))

        width = int(os.getenv("WIDTH", "1280"))
        height = int(os.getenv("HEIGHT", "720"))
        fps = int(os.getenv("FPS", "20"))
        bitrate = int(os.getenv("BITRATE", "4000000"))

        rtsp_port = os.getenv("RTSP_PORT", "8554")
        rtsp_path = os.getenv("RTSP_PATH", self.camera_name)

        self.mediamtx_api = os.getenv("MEDIAMTX_API", "http://127.0.0.1:9997")
        self.last_rtsp_ok = 0
        self.rtsp_check_interval = 5
        self.rtsp_failures = 0
        self.rtsp_failure_limit = 3
        self.restart_lock = threading.Lock()

        self.start_time = time.time()
        self.last_frame_time = None
        
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


    def _restart_camera(self):
        with self.restart_lock:
            try:
                self.stop()
                time.sleep(2)
                self.picam = Picamera2(self.camera_index)
                self.picam.configure(self.video_config)
                self.start()
            except Exception as e:
                print(f"[FATAL] Camera restart failed: {e}")

    def _rtsp_watchdog(self):
        while self.running:
            ok = self.check_rtsp()

            if ok:
                self.rtsp_failures = 0
            else:
                self.rtsp_failures += 1
                print(f"[WARN] RTSP not visible ({self.rtsp_failures})")

                if self.rtsp_failures >= self.rtsp_failure_limit:
                    print("[ERROR] RTSP stalled — restarting camera")
                    self._restart_camera()
                    self.rtsp_failures = 0

            time.sleep(self.rtsp_check_interval)

        
    def health_payload(self):
        return {
            "running": self.running,
            "rtsp_visible": self.check_rtsp(),
            "camera_name": self.camera_name,
            "uptime": int(time.time() - self.start_time),
        }
        
    def is_healthy(self):
        if not self.running:
            return False

        # Optional: add future frame checks here
        uptime = time.time() - self.start_time
        return uptime > 2  # give camera time to start

    def check_rtsp(self) -> bool:
        try:
            r = requests.get(f"{self.mediamtx_api}/v3/paths/list", timeout=2)
            r.raise_for_status()
            data = r.json()

            for item in data.get("items", []):
                if item["name"] == self.rtsp_path:
                    if item.get("sourceReady"):
                        self.last_rtsp_ok = time.time()
                        return True
                    return False
        except Exception:
            return False

    def _rtsp_watchdog(self):
        while self.running:
            ok = self.check_rtsp()
            if not ok:
                print("[WARN] RTSP stream not visible to MediaMTX")
                time.sleep(self.rtsp_check_interval)

        
    def start(self):
        if self.running:
            return
        try:
            self.picam.start()
            self.picam.start_recording(self.h264_encoder, self.rtsp_output)
            self.running = True

            threading.Thread(
                target=self._rtsp_watchdog,
                daemon=True
            ).start()
            
            self.start_health_server()
            
            while True:
                time.sleep(1.0)
        except Exception:
            self.stop()
            raise

    def start_health_server(self, host="0.0.0.0", port=9188):
        from flask import Flask, jsonify

        app = Flask(__name__)
        camera = self  # closure capture

        @app.route("/health", methods=["GET"])
        def health():
            if not camera.is_healthy():
                return jsonify(camera.health_payload()), 503
            return jsonify(camera.health_payload()), 200

        thread = threading.Thread(
            target=app.run,
            kwargs={
                "host": host,
                "port": port,
                "threaded": True,
                "use_reloader": False,
            },
            daemon=True,
        )
        thread.start()

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
