import inspect
import os
import shutil
from .pi_camera import PiCamera
from .usb_camera import USBCamera
from utils import logger

current_filename = inspect.currentframe().f_code.co_filename

class NullCamera:
    def __init__(self):
        current_function_name = inspect.currentframe().f_code.co_name
        logger.log(f"BEGIN {current_filename}.{current_function_name}", level="Trace")
        self.running = False
        self.process = None
        logger.log(f"END {current_filename}.{current_function_name}", level="Trace")

    def start(self):
        current_function_name = inspect.currentframe().f_code.co_name
        logger.log(f"BEGIN {current_filename}.{current_function_name}", level="Trace")
        print("[Camera] No camera mode enabled.")
        self.running = False
        logger.log(f"END {current_filename}.{current_function_name}", level="Trace")

    def stop(self):
        current_function_name = inspect.currentframe().f_code.co_name
        logger.log(f"BEGIN {current_filename}.{current_function_name}", level="Trace")
        pass
        logger.log(f"END {current_filename}.{current_function_name}", level="Trace")

    def health_status(self):
        current_function_name = inspect.currentframe().f_code.co_name
        logger.log(f"BEGIN {current_filename}.{current_function_name}", level="Trace")
        logger.log(f"END {current_filename}.{current_function_name}", level="Trace")
        return {
            "running": False,
            "mode": "none"
        }


def create_camera(rtsp_url):
    current_function_name = inspect.currentframe().f_code.co_name
    logger.log(f"BEGIN {current_filename}.{current_function_name}", level="Trace")
    camera_type = os.getenv("CAMERA_TYPE", "auto").lower()
    logger.log(f"{current_filename}.{current_function_name}.camera_type={camera_type}", level="Info")

    # Explicit None Mode
    if camera_type == "none":
        logger.log(f"END {current_filename}.{current_function_name}", level="Trace")
        return NullCamera()

    # USB Mode
    if camera_type == "usb":
        device = os.getenv("CAMERA_DEVICE", "/dev/video0")
        logger.log(f"END {current_filename}.{current_function_name}", level="Trace")
        return USBCamera(rtsp_url, device)

    # Pi Mode
    if camera_type == "pi":
        if shutil.which("libcamera-vid") is None:
            logger.log(f"END {current_filename}.{current_function_name}", level="Trace")
            raise RuntimeError("libcamera-vid not installed.")
        return PiCamera(rtsp_url)

    # AUTO MODE (recommended default)
    if camera_type == "auto":
        if os.path.exists("/dev/video0"):
            print("[Factory] USB camera detected.")
            logger.log(f"END {current_filename}.{current_function_name}", level="Trace")
            return USBCamera(rtsp_url)
        elif shutil.which("libcamera-vid"):
            print("[Factory] Pi camera detected.")
            logger.log(f"END {current_filename}.{current_function_name}", level="Trace")
            return PiCamera(rtsp_url)
        else:
            print("[Factory] No camera detected. Running in null mode.")
            logger.log(f"END {current_filename}.{current_function_name}", level="Trace")
            return NullCamera()

    logger.log(f"END {current_filename}.{current_function_name}", level="Trace")
    raise RuntimeError(f"Unknown CAMERA_TYPE: {camera_type}")
