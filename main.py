import eventlet
eventlet.monkey_patch()

from app import app, socketio

if __name__ == "__main__":
    # Use eventlet's WSGI server instead of Flask's default
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
