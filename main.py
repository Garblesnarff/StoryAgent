import eventlet
eventlet.monkey_patch()

from app import app, socketio

if __name__ == "__main__":
    app.config['SESSION_TYPE'] = 'filesystem'
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
