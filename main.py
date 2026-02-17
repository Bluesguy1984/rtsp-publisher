import inspect
import os
import signal
import threading
import time

from app import create_app
from camera.factory import create_camera
from utils import logger


shutdown_event = threading.Event()
current_filename = inspect.currentframe().f_code.co_filename


def camera_supervisor(camera):
    """
    Keeps the camera pipeline alive.
    Restarts if the process exits.
    """
    current_function_name = inspect.currentframe().f_code.co_name
    logger.log(f"BEGIN {current_filename}.{current_function_name}", level="Trace")

    logger.log(f"{current_filename}.{current_function_name}.camera.running = {camera.running}", level="Info")
    
    while not shutdown_event.is_set():

        # If process not running, start it
        if not camera.running:
            print("[Supervisor] Starting camera...")
            try:
                camera.start()
            except Exception as e:
                print(f"[Supervisor] Camera start failed: {e}")
                logger.log(f"{current_filename}.{current_function_name}.Exception = {e}", level="Error")
                time.sleep(5)
                continue

        # If subprocess exited unexpectedly
        if camera.process and camera.process.poll() is not None:
            logger.log(f"{current_filename}.{current_function_name}.Camera process died. Restarting...", level="Debug")
            print("[Supervisor] Camera process died. Restarting...")
            camera.running = False
            logger.log(f"END {current_filename}.{current_function_name}", level="Trace")
            camera.stop()
            time.sleep(2)

        time.sleep(2)

    logger.log(f"END {current_filename}.{current_function_name}", level="Trace")


def graceful_shutdown(signum, frame):
    current_function_name = inspect.currentframe().f_code.co_name
    logger.log(f"BEGIN {current_filename}.{current_function_name}", level="Trace")
    print("Shutting down cleanly...")
    shutdown_event.set()
    if camera:
        camera.stop()
    logger.log(f"END {current_filename}.{current_function_name}", level="Trace")
    os._exit(0)


def main():
    global camera

    current_function_name = inspect.currentframe().f_code.co_name
    logger.log(f"BEGIN {current_filename}.{current_function_name}", level="Trace")
    
    rtsp_url = os.getenv(
        "RTSP_URL",
        "rtsp://127.0.0.1:8554/camera"
    )

    camera = create_camera(rtsp_url)

    # Start supervisor thread
    supervisor_thread = threading.Thread(
        target=camera_supervisor,
        args=(camera,),
        daemon=True
    )
    supervisor_thread.start()

    # Setup signal handlers (important for Docker)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    signal.signal(signal.SIGINT, graceful_shutdown)

    app = create_app(camera)
    app.run(host="0.0.0.0", port=9188)

    logger.log(f"END {current_filename}.{current_function_name}", level="Trace")


if __name__ == "__main__":
    main()
