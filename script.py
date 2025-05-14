from flask import Flask, render_template
from flask_socketio import SocketIO
import serial
import re
from threading import Lock
import eventlet
eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')
thread = None
thread_lock = Lock()

# Serial setup
ser = serial.Serial('COM3', 115200)  # Change to your port
ser.flushInput()

def background_thread():
    """Read serial data and send to clients"""
    while True:
        line = ser.readline().decode('utf-8').strip()
        
        # Process pitch data
        if re.match(r'^-?\d+\.?\d*$', line):
            socketio.emit('pitch_data', {'value': float(line), 'type': 'pitch'})
        
        # Process state data
        if "Movement:" in line:
            state = 'CP Positive' if "Cerebral Palsy Positive" in line else 'Normal'
            socketio.emit('state_data', {'value': state, 'type': 'state'})

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    global thread
    print('Client connected')
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)