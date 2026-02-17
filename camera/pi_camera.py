import subprocess
import time
from .base import BaseCamera


class PiCamera(BaseCamera):

    def start(self):
        libcamera_cmd = [
            "libcamera-vid",
            "--nopreview",
            "-t", "0",
            "--width", "1280",
            "--height", "720",
            "--framerate", "30",
            "-o", "-"
        ]

        ffmpeg_cmd = [
            "ffmpeg",
            "-re",
            "-i", "pipe:0",
            "-c:v", "copy",
            "-f", "rtsp",
            "-rtsp_transport", "tcp",
            self.rtsp_url
        ]

        self.libcamera = subprocess.Popen(
            libcamera_cmd,
            stdout=subprocess.PIPE
        )

        self.process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=self.libcamera.stdout
        )

        self.running = True
        self.last_frame_time = time.time()
