# app.py
from flask import Flask, jsonify

def create_app(camera):
    app = Flask(__name__)

    @app.route("/health")
    def health():
        if camera.is_healthy():
            return "OK", 200
        else:
            return "FAIL", 500

    @app.route("/health/details")
    def health_details():
        return camera.health_status(), 200

        
    return app
