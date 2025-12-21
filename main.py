from app import create_app
from camera import Camera
import threading

camera = Camera(cam_index=0)
camera.start()

# Start camera pipeline in background
threading.Thread(target=camera.start, daemon=True).start()

app = create_app(camera)
app.run(host="0.0.0.0", port=9188)
