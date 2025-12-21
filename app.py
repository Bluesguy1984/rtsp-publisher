# app.py
from flask import Flask, jsonify

def create_app(camera):
    app = Flask(__name__)

    @app.route("/health")
    def health():
        return jsonify(camera.health_status())

    return app
