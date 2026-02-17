import time

class BaseCamera:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.process = None
        self.running = False
        self.last_frame_time = time.time()

    def start(self):
        raise NotImplementedError

    def stop(self):
        if self.process:
            self.process.terminate()
        self.running = False

    def health_status(self):
        return {
            "running": self.running,
            "last_frame_seconds_ago": int(time.time() - self.last_frame_time),
            "rtsp_url": self.rtsp_url,
        }
