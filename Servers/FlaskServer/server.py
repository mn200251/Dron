# from flask import Flask
import base64
import json
import threading
import time

import socket
import struct
import pickle
import cv2
import numpy as np

import requests

# app = Flask(__name__)


# @app.route('/')
# def index():
#     return "TCP Socket Server is Running"


phoneConnected = False
droneConnected = False
phoneSocket: socket = None
droneSocket: socket = None


def getInternalIp():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address


def getExternalIp():
    response = requests.get('https://api.ipify.org?format=json')
    ip_data = response.json()
    ip_address = ip_data['ip']
    return ip_address



def handleCameraStream():
    global phoneSocket, droneSocket, phoneConnected, droneConnected

    # wait for phone to connect
    while not phoneConnected:
        time.sleep(0.2)
    i = 0

    while True:
        try:
            while not phoneConnected:
                time.sleep(0.05)

            size = droneSocket.recv(4)

            # Convert bytes back to integer
            size = int.from_bytes(size, byteorder='big', signed=False)

            # Receive the actual frame
            frame_data = b''
            while len(frame_data) < size:
                packet = droneSocket.recv(size - len(frame_data))
                if not packet:
                    break
                frame_data += packet

            img = base64.b64decode(frame_data)

            if img is None:
                print('img is none')

            npimg = np.frombuffer(img, np.uint8)

            if npimg is None:
                print('npimg is none')

            source = cv2.imdecode(npimg, 1)

            # with open(f"test{i}.jpg", "wb") as f:
            #     f.write(npimg)

            _, jpeg = cv2.imencode('.jpg', source)
            jpeg_bytes = jpeg.tobytes()

            try:
                phoneSocket.sendall(len(jpeg_bytes).to_bytes(4, byteorder='big', signed=False))
                phoneSocket.sendall(jpeg_bytes)
            except:
                print('Phone not connected to send image!')

            cv2.imshow("Stream", source)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            i = i + 1

        except ConnectionResetError:
            print("ConnectionResetError in handleCameraStream")
            break
        except KeyboardInterrupt:
            cv2.destroyAllWindows()
            break
        except:
            print('Exception in handleCameraStream')
            break

    print(f"broj frejmova: {i}")

    droneConnected = False
    droneSocket = None




# drone
def handleControls():
    global phoneSocket, droneSocket, phoneConnected, droneConnected

    # wait for drone to connect
    while not droneConnected:
        time.sleep(0.2)

    while True:
        try:
            if not phoneConnected:
                time.sleep(0.05)

            data = phoneSocket.recv(1024).decode('utf-8')

            if not data:
                continue

            start = data.rfind("{")
            end = data.rfind("}")

            if start == -1 or end == -1:
                print("Received invalid JSON!")
                continue

            controlJson = data[start:end + 1]

            try:
                # print(f"Received data: {controlJson}")
                coordinates = json.loads(controlJson)
                print(f"x={coordinates["x"]}, y={coordinates["y"]}, z={coordinates["z"]}")
            except json.JSONDecodeError:
                print("Received invalid data")
                break

            # droneSocket.sendall(controls.encode())


        except ConnectionResetError:
            print("ConnectionResetError in handleControls")
            break

    phoneConnected = False
    phoneSocket = None

# Function to handle client connections
def handle_client_connection(client_socket):
    global phoneConnected, droneConnected, droneSocket, phoneSocket

    while True:
        try:
            message = client_socket.recv(1024).decode()

            match message:
                case "drone":
                    if droneConnected:
                        print(f"Error: Drone is already connected!")
                        break

                    droneConnected = True
                    droneSocket = client_socket
                    handleCameraStream()

                case "phone":
                    if phoneConnected:
                        print(f"Error: Phone is already connected!")
                        break

                    phoneConnected = True
                    phoneSocket = client_socket
                    phoneSocket.sendall("0\n".encode())  # everything ok
                    handleControls()

                case _:
                    print(f"Received message: {message}")
                    client_socket.sendall("-1\n".encode())
                    break

            # if message:
            # print(f"Received message: {message}")
            # client_socket.sendall("1".encode()) # everything is ok

            # else:
            # break
        except ConnectionResetError:
            break
    client_socket.close()


# Function to start the TCP server
def start_tcp_server(server_ip, server_port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server_socket.bind((server_ip, server_port))
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)
    print(f"TCP Server started on {server_ip}:{server_port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Accepted connection from {addr}")
        client_handler = threading.Thread(target=handle_client_connection, args=(client_socket,))
        client_handler.start()


if __name__ == "__main__":
    server_ip = "0.0.0.0"
    # server_ip = getInternalIp()
    # server_ip = getExternalIp()
    server_port = 6969

    print(f"IP for external connections: {getExternalIp()}:{server_port}")

    # Start the TCP server in a separate thread
    tcp_server_thread = threading.Thread(target=start_tcp_server, args=(server_ip, server_port))
    tcp_server_thread.start()

    tcp_server_thread.join()
    # Start the Flask server
    # app.run(host='0.0.0.0', port=5000)
