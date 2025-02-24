import socket
import threading
import json
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
FLASK_PORT = 8080

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class UDPListener(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = False

    def run(self):
        self.sock.bind((UDP_IP, UDP_PORT))
        self.running = True
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = data.decode('utf-8').strip()
                print(f"Received message from {addr}: {message}")

                parts = message.split(",")
                if len(parts) >= 7:
                    sensor_type = parts[1].strip()
                    x, y, z = float(parts[4]), float(parts[5]), float(parts[6])
                    socketio.emit('update', {sensor_type: {'x': x, 'y': y, 'z': z}})

                self.sock.sendto(b"Data received", addr)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error processing UDP packet: {e}")

    def stop(self):
        self.running = False
        self.sock.close()

udp_thread = None

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

if __name__ == '__main__':
    udp_thread = UDPListener()
    udp_thread.start()
    try:
        socketio.run(app, host='0.0.0.0', port=FLASK_PORT, debug=True, use_reloader=False)
    finally:
        if udp_thread:
            udp_thread.stop()
            udp_thread.join()
