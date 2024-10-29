import eventlet
eventlet.monkey_patch()

from app import app, socketio
import os

if __name__ == "__main__":
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = os.urandom(24)
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
