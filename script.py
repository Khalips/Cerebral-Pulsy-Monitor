from flask import Flask, render_template
from flask_socketio import SocketIO
import serial
import re
from threading import Lock
import eventlet
from flask_cors import CORS  # NEW: Add CORS support

eventlet.monkey_patch()

app = Flask(__name__)
CORS(app)  # NEW: Enable CORS for all routes
socketio = SocketIO(app, 
                   async_mode='eventlet',
                   cors_allowed_origins="*",  # NEW: Allow all origins
                   logger=True,              # NEW: Better debugging
                   engineio_logger=True)      # NEW: More debug info

thread = None
thread_lock = Lock()

# Serial setup
ser = serial.Serial('COM3', 115200)  # Change to your port
ser.flushInput()

def background_thread():
    """Read serial data and send to clients"""
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            
            # Process pitch data
            if re.match(r'^-?\d+\.?\d*$', line):
                socketio.emit('pitch_data', {'value': float(line), 'type': 'pitch'})
                print(f"Sent pitch: {line}")  # DEBUG
            
            # Process state data
            if "Movement:" in line:
                state = 'CP Positive' if "Cerebral Palsy Positive" in line else 'Normal'
                socketio.emit('state_data', {'value': state, 'type': 'state'})
                print(f"Sent state: {state}")  # DEBUG
                
        except UnicodeDecodeError:
            print("Serial decode error - skipping line")
        except Exception as e:
            print(f"Error in thread: {str(e)}")
            break

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

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    print("Starting server on http://localhost:5000")
    socketio.run(app, 
                debug=True, 
                port=5000, 
                host='0.0.0.0',  # Allow external access if needed
                use_reloader=False)  # Important for serial port stability