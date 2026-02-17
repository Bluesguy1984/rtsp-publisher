import inspect
import os
import subprocess
import time
from .base import BaseCamera
from utils import logger


class USBCamera(BaseCamera):

    def __init__(self, rtsp_url, device="/dev/video0"):
        super().__init__(rtsp_url)
        self.device = device
        self.current_filename = inspect.currentframe().f_code.co_filename


    def start(self):
        current_function_name = inspect.currentframe().f_code.co_name
        logger.log(f"BEGIN {self.current_filename}.{current_function_name}", level="Trace")
        
        if not os.path.exists(self.device):
            raise RuntimeError(f"USB camera device {self.device} not found")

        cmd = [
            "ffmpeg",
            "-f", "v4l2",
            "-framerate", os.getenv("FPS", "20"),
            "-video_size", f"{os.getenv('WIDTH', '1280')}x{os.getenv('HEIGHT', '720')}",
            "-i", self.device,

            # FORCE conversion to 4:2:0
            "-vf", "format=yuv420p",

            "-c:v", "libx264",
            "-preset", "veryfast",
            "-tune", "zerolatency",

            "-pix_fmt", "yuv420p",
            "-profile:v", "baseline",
            "-level", "3.1",

            "-f", "rtsp",
            "-rtsp_transport", "tcp",
            "-muxdelay", "0.1",

            self.rtsp_url
        ]

        logger.log(f"{self.current_filename}.{current_function_name}.self.rtsp_url = {self.rtsp_url}", level="Info")
        logger.log(f"{self.current_filename}.{current_function_name}.FFMPEG = {cmd}", level="Info")

        self.process = subprocess.Popen(cmd)

        self.running = True
        self.last_frame_time = time.time()
        
        logger.log(f"END {self.current_filename}.{current_function_name}", level="Trace")
